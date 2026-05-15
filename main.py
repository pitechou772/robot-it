import time
from machine import Pin

from ble_app import BLEApp

try:
    from moteur import ChassisMoteur
    chassis = ChassisMoteur()
    print("Moteurs OK")
except Exception as e:
    chassis = None
    print("ERREUR moteur:", e)

try:
    from servo import ServoMoteur
    servo = ServoMoteur()
    print("Servo OK")
except Exception as e:
    servo = None
    print("ERREUR servo:", e)

try:
    from capteur import CapteurUltrason
    ultrason = CapteurUltrason()
    print("Ultrason OK")
except Exception as e:
    ultrason = None
    print("ERREUR ultrason:", e)

mode_auto = None
if chassis is not None and ultrason is not None:
    try:
        from mode_auto import ModeAutonome
        mode_auto = ModeAutonome(chassis, ultrason)
        print("Mode autonome OK")
    except Exception as e:
        print("ERREUR mode_auto:", e)

led = Pin("LED", Pin.OUT)
ble = BLEApp(chassis, mode_auto=mode_auto)

print("Robot pret, en attente de connexion BLE...")

ble_connecte_prec = False

while True:
    connecte = ble.est_connecte()

    if connecte and not ble_connecte_prec:
        led.on()
        print("Client BLE connecte")
        ble.envoyer("PRET:MOTEUR" if chassis is not None else "PRET:BLE")

    if not connecte and ble_connecte_prec:
        led.off()
        print("Client BLE deconnecte")
        if chassis is not None:
            chassis.arreter()
        if mode_auto is not None:
            mode_auto.desactiver()

    ble_connecte_prec = connecte

    if mode_auto is not None and mode_auto.est_actif():
        mode_auto.mise_a_jour()

    ble.tick()
    time.sleep_ms(50)
