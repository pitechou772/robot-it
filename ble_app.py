import bluetooth
import config
from lib.BLE_SimplePeripheral import BLESimplePeripheral


class BLEApp:
    """
    Gere la communication Bluetooth BLE du robot.
    Recoit les commandes, les decode et les transmet au chassis.

    Protocole accepte (flexible) :
      "H:0.8" ou "A:0.8"  -> avancer a 80 %
      "B:0.5"              -> reculer a 50 %
      "G:1.0"              -> pivot gauche pleine puissance
      "D:1.0"              -> pivot droite pleine puissance
      "H", "A", "B", "G", "D" -> direction a pleine puissance
      "0.8"                -> puissance pour la derniere direction
      "0"                  -> stop
      "O", "S", "X"        -> stop
      "AUTO"               -> activer le mode autonome
      "MANUEL"             -> desactiver le mode autonome
    """

    # Correspondance lettres app -> lettres moteur
    _ALIAS_DIR = {"A": "H", "F": "H"}  # A/F = Avancer -> H

    def __init__(self, chassis, nom=config.BLE_NOM, mode_auto=None):
        self._chassis    = chassis    # peut etre None si moteur.py absent
        self._mode_auto  = mode_auto  # ModeAutonome ou None
        self._direction  = None       # direction active (H/B/G/D) ou None si arrete
        self._puissance  = 0.5        # puissance courante du slider (0.0 a 1.0)
        ble = bluetooth.BLE()
        self._peripherique = BLESimplePeripheral(ble, nom)
        self._peripherique.on_write(self._on_reception)
        print("BLE pret : {}".format(nom))

    def _on_reception(self, donnees):
        """Callback appele a chaque message BLE recu."""
        try:
            # Nettoyage : null bytes + espaces
            msg = donnees.decode('utf-8').replace('\x00', '').strip()
            if not msg:
                return
            print("[BLE] Recu: {!r}".format(msg))

            if self._chassis is None:
                print("[BLE] ATTENTION: chassis=None, moteur.py absent")
                return

            if self._mode_auto is not None and self._mode_auto.est_actif():
                if msg not in ("MANUEL", "O", "S", "X"):
                    print("[BLE] Ignore (mode autonome actif)")
                    return

            # --- Commandes textuelles ---
            if msg in ("O", "S", "X"):
                self._direction = None
                self._chassis.arreter()
                print("[BLE] Moteur -> STOP")

            elif msg == "AUTO":
                if self._mode_auto is not None:
                    self._mode_auto.activer()
                    self.envoyer("MODE:AUTO")
                    print("[BLE] Mode autonome active")
                else:
                    print("[BLE] AUTO ignore (mode_auto.py absent)")

            elif msg == "MANUEL":
                if self._mode_auto is not None:
                    self._mode_auto.desactiver()
                    self.envoyer("MODE:MANUEL")
                    print("[BLE] Mode manuel active")
                else:
                    print("[BLE] MANUEL ignore (mode_auto.py absent)")

            # --- Commande combinee direction:puissance ---
            elif ":" in msg:
                parties          = msg.split(":")
                self._direction  = self._ALIAS_DIR.get(parties[0], parties[0])
                self._puissance  = max(0.0, min(1.0, float(parties[1])))
                print("[BLE] Moteur -> {} {}%".format(self._direction, int(self._puissance * 100)))
                self._chassis.executer_commande(self._direction, self._puissance)

            # --- Nombre = mise a jour du slider ---
            elif self._est_nombre(msg):
                puissance = max(0.0, min(1.0, float(msg)))
                self._puissance = puissance
                if puissance == 0.0 or self._direction is None:
                    self._direction = None
                    self._chassis.arreter()
                    print("[BLE] Slider -> 0% => STOP")
                else:
                    print("[BLE] Slider -> {} {}%".format(self._direction, int(puissance * 100)))
                    self._chassis.executer_commande(self._direction, puissance)

            # --- Lettre = nouvelle direction, demarre immediatement ---
            else:
                direction = self._ALIAS_DIR.get(msg, msg)
                self._direction = direction
                print("[BLE] Direction -> {} {}%".format(direction, int(self._puissance * 100)))
                self._chassis.executer_commande(direction, self._puissance)

        except Exception as e:
            print("[BLE] Erreur: {} | brut={!r}".format(e, donnees))

    @staticmethod
    def _est_nombre(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def est_connecte(self):
        """Retourne True si un client BLE est connecte."""
        return self._peripherique.is_connected()

    def envoyer(self, message):
        """Envoie un message texte au client BLE connecte."""
        if self.est_connecte():
            self._peripherique.send(message.encode('utf-8'))
