"""Téléchargement vérifié des données externes.

Chaque fichier est téléchargé une seule fois dans data/external. Son empreinte est
comparée à l'empreinte publiée par la source lorsqu'elle existe, et chaque fichier
obtenu est consigné dans un registre avec son adresse, sa date de téléchargement, sa
taille et son empreinte SHA-256.
"""

import csv
import hashlib
from datetime import datetime, timezone

import requests

from src.data.load import RACINE, empreinte_sha256

DOSSIER_EXTERNE = RACINE / "data" / "external"
REGISTRE = DOSSIER_EXTERNE / "registre.csv"
COLONNES_REGISTRE = ["fichier", "url", "date_telechargement", "octets", "sha256"]


def empreinte_md5(chemin):
    """Retourne l'empreinte MD5 d'un fichier, format publié par Zenodo."""
    empreinte = hashlib.md5()
    with open(chemin, "rb") as fichier:
        for bloc in iter(lambda: fichier.read(1 << 20), b""):
            empreinte.update(bloc)
    return empreinte.hexdigest()


def consigner(chemin, url, registre=REGISTRE):
    """Ajoute un fichier téléchargé au registre des données externes."""
    nouveau = not registre.exists()
    with open(registre, "a", newline="", encoding="utf-8") as fichier:
        ecrivain = csv.writer(fichier)
        if nouveau:
            ecrivain.writerow(COLONNES_REGISTRE)
        ecrivain.writerow([
            chemin.relative_to(registre.parent).as_posix(),
            url,
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            chemin.stat().st_size,
            empreinte_sha256(chemin),
        ])


def _poursuivre(url, partiel):
    """Complète le fichier partiel et indique si le téléchargement est terminé."""
    debut = partiel.stat().st_size if partiel.exists() else 0
    entetes = {"Range": f"bytes={debut}-"} if debut else {}
    with requests.get(url, headers=entetes, stream=True, timeout=60) as reponse:
        if reponse.status_code == 416:
            return True
        reponse.raise_for_status()
        if reponse.status_code != 206:
            debut = 0
        attendu = reponse.headers.get("Content-Length")
        with open(partiel, "ab" if debut else "wb") as fichier:
            for bloc in reponse.iter_content(1 << 20):
                fichier.write(bloc)
    return attendu is None or partiel.stat().st_size == debut + int(attendu)


def telecharger(url, chemin, md5=None, registre=REGISTRE, tentatives=5):
    """Télécharge un fichier s'il est absent et retourne son chemin.

    Un téléchargement interrompu reprend là où il s'était arrêté. Lorsque l'empreinte
    MD5 attendue est fournie, un fichier qui ne la respecte pas est supprimé et une
    erreur est levée, qu'il vienne d'être téléchargé ou qu'il ait été obtenu auparavant.
    """
    if not chemin.exists():
        chemin.parent.mkdir(parents=True, exist_ok=True)
        partiel = chemin.with_name(chemin.name + ".partiel")
        for _ in range(tentatives):
            try:
                if _poursuivre(url, partiel):
                    break
            except requests.RequestException:
                continue
        else:
            raise RuntimeError(f"Téléchargement incomplet après {tentatives} tentatives pour {url}")
        partiel.rename(chemin)
        consigner(chemin, url, registre)

    if md5 is not None and empreinte_md5(chemin) != md5:
        chemin.unlink()
        raise ValueError(f"Empreinte MD5 inattendue pour {chemin.name}, fichier supprimé")
    return chemin
