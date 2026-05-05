"""
Test d'integration : mode autonome complet avec servo + ultrason + moteurs.
Le robot doit :
  1. Demarrer en AVANCE
  2. Detecter un obstacle, scanner gauche/droite
  3. Choisir la voie libre et tourner
  4. Reprendre l'avance

Lance ce test dans un espace ouvert avec au moins 50 cm devant le robot.
Place un obstacle a moins de 20 cm pour declencher le scan.
"""
import sys
sys.path.insert(0, "..")

from time import sleep
from moteur import ChassisMoteur
from capteur import CapteurUltrason
from servo import ServoMoteur
from mode_auto import ModeAutonome
import config

def ok(msg):  print("[OK]  " + msg)
def ko(msg):  print("[KO]  " + msg)

print("=== TEST MODE AUTONOME ===")

# --- Initialisation ---
try:
    chassis  = ChassisMoteur()
    ultrason = CapteurUltrason()
    servo    = ServoMoteur()
    ok("Tous les composants initialises")
except Exception as e:
    ko("Initialisation : " + str(e))
    raise SystemExit

try:
    auto = ModeAutonome(chassis, ultrason, servo)
    ok("ModeAutonome cree")
except Exception as e:
    ko("ModeAutonome : " + str(e))
    raise SystemExit

# --- Test activer/desactiver ---
print("--- Test activer / desactiver ---")
if auto.est_actif():
    ko("Ne doit pas etre actif avant activer()")
else:
    ok("Inactif au depart")

auto.activer()
if auto.est_actif():
    ok("activer() -> actif")
else:
    ko("activer() n'a pas fonctionne")

auto.desactiver()
if not auto.est_actif():
    ok("desactiver() -> inactif")
else:
    ko("desactiver() n'a pas fonctionne")

# --- Test scan servo seul ---
print("--- Test scan servo (sans moteurs, etat ARRET) ---")
servo.centrer(); sleep(0.5)
servo.gauche();  sleep(0.6)
d_g = ultrason.mesurer_distance()
servo.droite();  sleep(0.6)
d_d = ultrason.mesurer_distance()
servo.centrer(); sleep(0.5)
print("  Distance gauche : {} cm".format(d_g))
print("  Distance droite : {} cm".format(d_d))
if d_g is not None or d_d is not None:
    ok("Scan servo + ultrason fonctionnels")
else:
    ko("Aucune mesure valide pendant le scan")

# --- Test boucle autonome (10 s) ---
print("--- Boucle autonome 10 s (place un obstacle pour tester le scan) ---")
print("    Appuie sur Stop/Restart pour interrompre si necessaire")
auto.activer()
import time
t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < 10000:
    auto.mise_a_jour()
    sleep(0.05)

auto.desactiver()
ok("Boucle autonome 10 s terminee")

print("=== FIN TEST MODE AUTONOME ===")
