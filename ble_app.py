import bluetooth
import config
from lib.BLE_SimplePeripheral import BLESimplePeripheral


class BLEApp:
    """
    Gere la communication Bluetooth BLE du robot.
    Recoit les commandes, les decode et les transmet au chassis.

    Protocole de commande :
      "H:0.8"  -> avancer a 80 %
      "B:0.5"  -> reculer a 50 %
      "G:1.0"  -> pivot gauche pleine puissance
      "D:1.0"  -> pivot droite pleine puissance
      "O"      -> stop
      "AUTO"   -> activer le mode autonome
      "MANUEL" -> desactiver le mode autonome
    """

    def __init__(self, chassis, nom=config.BLE_NOM, mode_auto=None):
        self._chassis   = chassis    # peut etre None si moteur.py absent
        self._mode_auto = mode_auto  # ModeAutonome ou None
        ble = bluetooth.BLE()
        self._peripherique = BLESimplePeripheral(ble, nom)
        self._peripherique.on_write(self._on_reception)
        print("BLE pret : {}".format(nom))

    def _on_reception(self, donnees):
        """Callback appele a chaque message BLE recu."""
        try:
            msg = donnees.decode('utf-8').strip()
            print("Recu BLE:", msg)

            if msg == "O":
                if self._chassis is not None:
                    self._chassis.arreter()
                print("Action: STOP")

            elif msg == "AUTO":
                if self._mode_auto is not None:
                    self._mode_auto.activer()
                    self.envoyer("MODE:AUTO")

            elif msg == "MANUEL":
                if self._mode_auto is not None:
                    self._mode_auto.desactiver()
                    self.envoyer("MODE:MANUEL")

            elif ":" in msg:
                if self._mode_auto is not None and self._mode_auto.est_actif():
                    print("Commande ignoree : mode autonome actif")
                elif self._chassis is not None:
                    parties   = msg.split(":")
                    direction = parties[0]         # H, B, G, D
                    puissance = float(parties[1])  # 0.0 a 1.0
                    self._chassis.executer_commande(direction, puissance)
                    print("Action: {} a {}%".format(direction, int(puissance * 100)))

            else:
                if self._mode_auto is not None and self._mode_auto.est_actif():
                    print("Commande ignoree : mode autonome actif")
                elif self._chassis is not None:
                    self._chassis.executer_commande(msg, 1.0)

        except Exception as e:
            print("Erreur commande BLE:", e)

    def est_connecte(self):
        """Retourne True si un client BLE est connecte."""
        return self._peripherique.is_connected()

    def envoyer(self, message):
        """Envoie un message texte au client BLE connecte."""
        if self.est_connecte():
            self._peripherique.send(message.encode('utf-8'))
