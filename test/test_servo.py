"""
Test unitaire : servo moteur.
Verifie que le servo atteint les positions gauche, centre et droite.
Observe visuellement que le servo tourne correctement.
"""
import sys
sys.path.insert(0, "..")

from time import sleep
from servo import ServoMoteur
import config

def ok(msg):  print("[OK]  " + msg)
def ko(msg):  print("[KO]  " + msg)

print("=== TEST SERVO ===")

try:
    s = ServoMoteur()
    ok("ServoMoteur cree (pin GP{})".format(config.SERVO_PIN))
except Exception as e:
    ko("ServoMoteur : " + str(e))
    raise SystemExit

print("--- Centre (90 deg) ---")
s.centrer()
sleep(1)
ok("centrer")

print("--- Gauche ({} deg) ---".format(config.SERVO_ANGLE_GAUCHE))
s.gauche()
sleep(1)
ok("gauche")

print("--- Droite ({} deg) ---".format(config.SERVO_ANGLE_DROITE))
s.droite()
sleep(1)
ok("droite")

print("--- Balayage 0 -> 180 par pas de 30 deg ---")
for angle in range(0, 181, 30):
    s.aller_a(angle)
    print("  -> {} deg (angle lu: {})".format(angle, s.angle))
    sleep(0.5)
ok("balayage")

print("--- Retour centre ---")
s.centrer()
sleep(0.5)

print("--- Desactivation PWM ---")
s.desactiver()
ok("desactiver")

print("=== FIN TEST SERVO ===")
