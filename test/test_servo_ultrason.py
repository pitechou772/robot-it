"""
Test servo + capteur ultrason : balayage continu gauche/droite avec mesure de distance.
"""
import sys
sys.path.insert(0, "..")

from servo import ServoMoteur
from capteur import CapteurUltrason
from time import sleep
import config

print("=== TEST SERVO + ULTRASON ===")

servo    = ServoMoteur()
ultrason = CapteurUltrason()

servo.centrer()
sleep(0.5)

print("Balayage continu... (Ctrl+C pour arreter)\n")

try:
    while True:
        servo.gauche()
        sleep(0.2)
        dist = ultrason.mesurer_distance()
        print("GAUCHE  -> {} cm".format(dist if dist is not None else "hors portee"))

        servo.centrer()
        sleep(0.2)
        dist = ultrason.mesurer_distance()
        print("CENTRE  -> {} cm".format(dist if dist is not None else "hors portee"))

        servo.droite()
        sleep(0.2)
        dist = ultrason.mesurer_distance()
        print("DROITE  -> {} cm".format(dist if dist is not None else "hors portee"))

        servo.centrer()
        sleep(0.2)
        dist = ultrason.mesurer_distance()
        print("CENTRE  -> {} cm\n".format(dist if dist is not None else "hors portee"))
        sleep(1)

except KeyboardInterrupt:
    servo.desactiver()
    print("Arret.")
