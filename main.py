import time
from machine import Pin

import config
from moteur import ChassisMoteur
from capteur import CapteurUltrason, CapteurLuminosite
from ble_app import BLEApp
from mode_auto import ModeAutonome

# --- INITIALISATION ---
led        = Pin("LED", Pin.OUT)
chassis    = ChassisMoteur()
ultrason   = CapteurUltrason()
ldr_gauche = CapteurLuminosite(config.LUMINOSITE_GAUCHE_ADC)
ldr_droite = CapteurLuminosite(config.LUMINOSITE_DROITE_ADC)
mode_auto  = ModeAutonome(chassis, ultrason, ldr_gauche, ldr_droite)
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
print("  -> BLE 'AUTO'   : active le mode autonome")
print("  -> BLE 'MANUEL' : revient en controle manuel")

# --- BOUCLE PRINCIPALE ---
dernier_tick = time.ticks_ms()

while True:
    maintenant = time.ticks_ms()

    # LED : allumee si BLE connecte, eteinte sinon
    if ble.est_connecte():
        led.on()
    else:
        led.off()
        # Securite : stop moteurs si BLE coupe (sauf si mode autonome actif)
        if not mode_auto.est_actif():
            chassis.arreter()

    # Mode autonome : mise a jour a chaque iteration pour la precision du timing
    if mode_auto.est_actif():
        mode_auto.mise_a_jour()

    # Lecture periodique des capteurs (mode manuel uniquement)
    if time.ticks_diff(maintenant, dernier_tick) >= config.INTERVALLE_CAPTEURS_MS:
        dernier_tick = maintenant

        if not mode_auto.est_actif():
            # -- Capteur ultrason (mode manuel) --
            distance = ultrason.mesurer_distance()
            if distance is not None:
                print("Distance:", distance, "cm")
                if ultrason.obstacle_detecte(config.SEUIL_OBSTACLE_CM):
                    print("! OBSTACLE - Arret d'urgence")
                    chassis.arreter()
                    ble.envoyer("OBSTACLE:{}".format(distance))

            # -- Capteurs de luminosite (mode manuel) --
            lux_g = ldr_gauche.lire_pourcentage()
            lux_d = ldr_droite.lire_pourcentage()
            print("Luminosite G:{}% D:{}%".format(lux_g, lux_d))
            if lux_g < config.SEUIL_SOMBRE_PCT and lux_d < config.SEUIL_SOMBRE_PCT:
                print("! Environnement sombre")
                ble.envoyer("SOMBRE:{}/{}".format(lux_g, lux_d))

    time.sleep_ms(50)   # 50 ms pour une meilleure precision du timing autonome
