"""
Test unitaire : capteur ultrason HC-SR04.
Effectue 10 mesures et verifie la coherence des valeurs.
Place un obstacle a environ 10-30 cm pour valider obstacle_detecte().
"""
import sys
sys.path.insert(0, "..")

from time import sleep
from capteur import CapteurUltrason
import config

def ok(msg):  print("[OK]  " + msg)
def ko(msg):  print("[KO]  " + msg)

print("=== TEST CAPTEUR ULTRASON ===")

try:
    u = CapteurUltrason()
    ok("CapteurUltrason cree (TRIG=GP{}, ECHO=GP{})".format(
        config.ULTRASON_TRIG, config.ULTRASON_ECHO))
except Exception as e:
    ko("CapteurUltrason : " + str(e))
    raise SystemExit

# --- 10 mesures de distance ---
print("--- 10 mesures (place un objet devant le capteur) ---")
mesures_valides = 0
for i in range(10):
    d = u.mesurer_distance()
    if d is not None:
        mesures_valides += 1
        print("  Mesure {} : {} cm".format(i + 1, d))
    else:
        print("  Mesure {} : hors portee / timeout".format(i + 1))
    sleep(0.2)

if mesures_valides >= 7:
    ok("mesurer_distance ({}/10 valides)".format(mesures_valides))
else:
    ko("mesurer_distance : trop de timeouts ({}/10 valides)".format(mesures_valides))

# --- Test obstacle_detecte ---
print("--- obstacle_detecte (seuil {} cm) ---".format(config.SEUIL_OBSTACLE_CM))
for i in range(5):
    detecte = u.obstacle_detecte(config.SEUIL_OBSTACLE_CM)
    dist    = u.mesurer_distance()
    print("  {} : dist={} cm -> obstacle={}".format(i + 1, dist, detecte))
    sleep(0.3)
ok("obstacle_detecte")

# --- Test coherence : sans obstacle les valeurs doivent etre > seuil ---
print("--- Retire l'obstacle et appuie sur Entree si possible, ou attend 3s ---")
sleep(3)
d = u.mesurer_distance()
if d is None or d > config.SEUIL_OBSTACLE_CM:
    ok("Pas d'obstacle detecete a distance libre")
else:
    ko("Obstacle signale alors que la voie est libre ({} cm)".format(d))

print("=== FIN TEST CAPTEUR ULTRASON ===")
