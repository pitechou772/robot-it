"""
Systeme de logs fichier pour le robot.

Les messages sont bufferises en memoire et ecrits par batch dans
/robot.log pour limiter l'usure de la flash.

Rotation automatique : quand robot.log depasse LOG_MAX_OCTETS,
il est renomme robot.log.bak et un nouveau fichier est cree.

Recuperation des logs :
  Connecte le Pico a Thonny -> onglet "Fichiers" -> telecharge robot.log
  (ou robot.log.bak pour les anciens logs).
"""
import os
import time

LOG_FICHIER     = "/robot.log"
LOG_BAK_FICHIER = "/robot.log.bak"
LOG_MAX_OCTETS  = 40000   # 40 ko => rotation (flash Pico = 2 Mo)
_FLUSH_APRES    = 10      # ecrire dans le fichier toutes les N lignes

_lignes   = []
_compteur = 0


def log(msg):
    """Affiche sur la console ET bufferise le message pour ecriture fichier."""
    global _compteur
    ligne = "[{:08d}] {}".format(time.ticks_ms(), msg)
    print(ligne)
    _lignes.append(ligne)
    _compteur += 1
    if _compteur >= _FLUSH_APRES:
        flush()


def flush():
    """Force l'ecriture du buffer dans le fichier de log."""
    global _compteur, _lignes
    if not _lignes:
        return
    try:
        try:
            taille = os.stat(LOG_FICHIER)[6]
        except OSError:
            taille = 0

        if taille > LOG_MAX_OCTETS:
            try:
                os.remove(LOG_BAK_FICHIER)
            except OSError:
                pass
            try:
                os.rename(LOG_FICHIER, LOG_BAK_FICHIER)
            except OSError:
                pass

        with open(LOG_FICHIER, "a") as f:
            for l in _lignes:
                f.write(l + "\n")
    except Exception as e:
        print("[LOGGER] Erreur ecriture:", e)
    finally:
        _lignes   = []
        _compteur = 0


def effacer():
    """Supprime les fichiers de log (robot.log et robot.log.bak)."""
    flush()
    for nom in (LOG_FICHIER, LOG_BAK_FICHIER):
        try:
            os.remove(nom)
            print("[LOGGER] Supprime: " + nom)
        except OSError:
            pass


def taille_fichier():
    """Retourne la taille de robot.log en octets, ou 0 si absent."""
    try:
        return os.stat(LOG_FICHIER)[6]
    except OSError:
        return 0
