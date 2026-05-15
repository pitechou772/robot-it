"""
Test unitaire : moteurs gauche et droit via ChassisMoteur.
Branche le robot sur Thonny et lance ce fichier directement.
"""
import sys
sys.path.insert(0, "..")

from time import sleep
from moteur import ChassisMoteur

def ok(msg):  print("[OK]  " + msg)
def ko(msg):  print("[KO]  " + msg)

def test_avancer():
    print("--- Avancer 2s a 60% ---")
    c.avancer(0.6)
    sleep(2)
    c.arreter()
    ok("avancer")

def test_reculer():
    print("--- Reculer 2s a 60% ---")
    c.reculer(0.6)
    sleep(2)
    c.arreter()
    ok("reculer")

def test_tourner_gauche():
    print("--- Pivot gauche 1s ---")
    c.tourner_gauche(0.6)
    sleep(1)
    c.arreter()
    ok("tourner_gauche")

def test_tourner_droite():
    print("--- Pivot droite 1s ---")
    c.tourner_droite(0.6)
    sleep(1)
    c.arreter()
    ok("tourner_droite")

def test_arreter():
    print("--- Arreter ---")
    c.avancer(0.7)
    sleep(0.5)
    c.arreter()
    sleep(0.5)
    ok("arreter")

def test_executer_commande():
    print("--- executer_commande H/B/G/D/stop ---")
    for cmd, dur in [("H", 1), ("B", 1), ("G", 0.8), ("D", 0.8)]:
        c.executer_commande(cmd, 0.8)
        sleep(dur)
        c.arreter()
        sleep(0.3)
    c.executer_commande("O")
    ok("executer_commande")


print("=== TEST MOTEUR ===")
try:
    c = ChassisMoteur()
    ok("ChassisMoteur cree")
except Exception as e:
    ko("ChassisMoteur : " + str(e))
    raise SystemExit

#test_avancer()
test_reculer()
#test_tourner_gauche()
#test_tourner_droite()
#test_arreter()
#test_executer_commande()

print("=== FIN TEST MOTEUR ===")

