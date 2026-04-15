import time
from machine import Pin

import config
from ble_app import BLEApp  # toujours present

try:
    from moteur import ChassisMoteur
    HAS_MOTEUR = True
except ImportError:
    HAS_MOTEUR = False

try:
    from capteur import CapteurUltrason, CapteurLuminosite
    HAS_CAPTEUR = True
except ImportError:
    HAS_CAPTEUR = False

try:
    from mode_auto import ModeAutonome
    HAS_MODE_AUTO = True
except ImportError:
    HAS_MODE_AUTO = False

# --- INITIALISATION ---
led = Pin("LED", Pin.OUT)

chassis    = ChassisMoteur() if HAS_MOTEUR else None
ultrason   = CapteurUltrason() if HAS_CAPTEUR else None
ldr_gauche = CapteurLuminosite(config.LUMINOSITE_GAUCHE_ADC) if HAS_CAPTEUR else None
ldr_droite = CapteurLuminosite(config.LUMINOSITE_DROITE_ADC) if HAS_CAPTEUR else None
mode_auto  = ModeAutonome(chassis, ultrason, ldr_gauche, ldr_droite) if HAS_MODE_AUTO else None
ble        = BLEApp(chassis, mode_auto=mode_auto)

import builtins as _builtins
_orig_print = _builtins.print

def _print_ble(*args, **kwargs):
    _orig_print(*args, **kwargs)
    sep = kwargs.get('sep', ' ')
    msg = sep.join(str(a) for a in args)
    ble.envoyer(msg)

_builtins.print = _print_ble

print("Robot pret ! Connecte ton application...")
if not HAS_MOTEUR:
    print("  [Mode BLE uniquement - moteur.py absent]")
if not HAS_CAPTEUR:
    print("  [Capteurs absents]")
if HAS_MODE_AUTO:
    print("  -> BLE 'AUTO'   : active le mode autonome")
    print("  -> BLE 'MANUEL' : revient en controle manuel")

# --- HELPERS ---

def _annoncer_capacites():
    if HAS_MOTEUR and HAS_CAPTEUR and HAS_MODE_AUTO:
        ble.envoyer("PRET:MOTEUR+CAPTEUR+AUTO")
    elif HAS_MOTEUR and HAS_CAPTEUR:
        ble.envoyer("PRET:MOTEUR+CAPTEUR")
    elif HAS_MOTEUR:
        ble.envoyer("PRET:MOTEUR")
    else:
        ble.envoyer("PRET:BLE")

def _gerer_connexion(connecte, ble_connecte_prec):
    """Gere la LED et les evenements de connexion/deconnexion BLE.
    Retourne le nouvel etat de ble_connecte_prec."""
    if connecte:
        led.on()
        if not ble_connecte_prec:
            _annoncer_capacites()
        return True
    else:
        led.off()
        if chassis is not None and (mode_auto is None or not mode_auto.est_actif()):
            chassis.arreter()  # securite : stop moteurs si BLE coupe
        return False

def _lire_capteurs():
    """Lecture et envoi des valeurs capteurs (mode manuel uniquement)."""
    distance = ultrason.mesurer_distance()
    if distance is not None:
        print("Distance:", distance, "cm")
        if ultrason.obstacle_detecte(config.SEUIL_OBSTACLE_CM):
            print("! OBSTACLE - Arret d'urgence")
            chassis.arreter()
            ble.envoyer("OBSTACLE:{}".format(distance))

    lux_g = ldr_gauche.lire_pourcentage()
    lux_d = ldr_droite.lire_pourcentage()
    print("Luminosite G:{}% D:{}%".format(lux_g, lux_d))
    if lux_g < config.SEUIL_SOMBRE_PCT and lux_d < config.SEUIL_SOMBRE_PCT:
        print("! Environnement sombre")
        ble.envoyer("SOMBRE:{}/{}".format(lux_g, lux_d))

# --- BOUCLE PRINCIPALE ---
dernier_tick      = time.ticks_ms()
ble_connecte_prec = False

while True:
    maintenant = time.ticks_ms()
    connecte   = ble.est_connecte()

    ble_connecte_prec = _gerer_connexion(connecte, ble_connecte_prec)

    if mode_auto is not None and mode_auto.est_actif():
        mode_auto.mise_a_jour()

    if chassis is not None and ultrason is not None and ldr_gauche is not None:
        if time.ticks_diff(maintenant, dernier_tick) >= config.INTERVALLE_CAPTEURS_MS:
            dernier_tick = maintenant
            if mode_auto is None or not mode_auto.est_actif():
                _lire_capteurs()

    time.sleep_ms(50)   # 50 ms pour une meilleure precision du timing autonome
