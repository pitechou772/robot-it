import bluetooth
import config
from lib.BLE_SimplePeripheral import BLESimplePeripheral
from logger import log, flush as _log_flush, effacer as _log_effacer, taille_fichier


class BLEApp:
    """
    Gere la communication Bluetooth BLE du robot.
    Recoit les commandes, les decode et les transmet au chassis.

    Protocole accepte :
      "H:0.8" ou "A:0.8"  -> avancer a 80 %
      "B:0.5"              -> reculer a 50 %
      "G:1.0"              -> pivot gauche pleine puissance
      "D:1.0"              -> pivot droite pleine puissance
      "H", "A", "B", "G", "D" -> direction a puissance courante
      "0.8"                -> puissance slider (met a jour sans changer direction)
      "0"                  -> stop
      "O", "S", "X"        -> stop
      "AUTO"               -> activer le mode autonome
      "MANUEL"             -> desactiver le mode autonome
      "LOG:FLUSH"          -> forcer l'ecriture du buffer de logs sur la flash
      "LOG:EFFACE"         -> effacer les fichiers de log
      "LOG:TAILLE"         -> envoie la taille actuelle du fichier de log
    """

    _ALIAS_DIR = {"A": "H", "F": "H"}

    def __init__(self, chassis, nom=config.BLE_NOM, mode_auto=None):
        self._chassis       = chassis
        self._mode_auto     = mode_auto
        self._direction     = None
        self._puissance     = 0.5
        self._slider_actif  = False
        ble = bluetooth.BLE()
        self._peripherique = BLESimplePeripheral(ble, nom)
        self._peripherique.on_write(self._on_reception)
        log("BLE pret : {}".format(nom))

    def _on_reception(self, donnees):
        """Callback appele a chaque message BLE recu."""
        try:
            msg = donnees.decode('utf-8').replace('\x00', '').strip()
            if not msg:
                return
            log("[BLE] Recu: {!r}".format(msg))

            # --- Gestion des logs ---
            if msg == "LOG:FLUSH":
                _log_flush()
                self.envoyer("LOG:OK")
                return

            if msg == "LOG:EFFACE":
                _log_effacer()
                self.envoyer("LOG:EFFACE:OK")
                return

            if msg == "LOG:TAILLE":
                self.envoyer("LOG:{}o".format(taille_fichier()))
                return

            if self._chassis is None:
                log("[BLE] ATTENTION: chassis=None, moteur.py absent")
                return

            if self._mode_auto is not None and self._mode_auto.est_actif():
                if msg not in ("MANUEL", "O", "S", "X"):
                    log("[BLE] Ignore (mode autonome actif)")
                    return

            # --- Commandes textuelles ---
            if msg in ("O", "S", "X"):
                self._direction = None
                self._chassis.arreter()
                log("[BLE] Moteur -> STOP")

            elif msg == "AUTO":
                if self._mode_auto is not None:
                    self._mode_auto.activer()
                    self.envoyer("MODE:AUTO")
                    log("[BLE] Mode autonome active")
                else:
                    log("[BLE] AUTO ignore (mode_auto absent)")

            elif msg == "MANUEL":
                if self._mode_auto is not None:
                    self._mode_auto.desactiver()
                    self.envoyer("MODE:MANUEL")
                    log("[BLE] Mode manuel active")
                else:
                    log("[BLE] MANUEL ignore (mode_auto absent)")

            # --- Commande combinee direction:puissance ---
            elif ":" in msg:
                parties         = msg.split(":")
                self._direction = self._ALIAS_DIR.get(parties[0], parties[0])
                self._puissance = max(0.0, min(1.0, float(parties[1])))
                log("[BLE] Moteur -> {} {}%".format(self._direction, int(self._puissance * 100)))
                self._chassis.executer_commande(self._direction, self._puissance)

            # --- Nombre = mise a jour du slider ---
            elif self._est_nombre(msg):
                puissance = max(0.0, min(1.0, float(msg)))
                if puissance > 0.0:
                    self._slider_actif = True
                    self._puissance = puissance
                    if self._direction is not None:
                        log("[BLE] Slider -> {} {}%".format(self._direction, int(puissance * 100)))
                        self._chassis.executer_commande(self._direction, puissance)
                elif self._slider_actif or self._direction is None:
                    self._slider_actif = False
                    self._direction = None
                    self._chassis.arreter()
                    log("[BLE] Slider -> 0% => STOP")

            # --- Lettre = nouvelle direction ---
            else:
                self._slider_actif = False
                direction = self._ALIAS_DIR.get(msg, msg)
                self._direction = direction
                log("[BLE] Direction -> {} {}%".format(direction, int(self._puissance * 100)))
                self._chassis.executer_commande(direction, self._puissance)

        except Exception as e:
            log("[BLE] Erreur: {} | brut={!r}".format(e, donnees))

    @staticmethod
    def _est_nombre(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def est_connecte(self):
        return self._peripherique.is_connected()

    def envoyer(self, message):
        if self.est_connecte():
            self._peripherique.send(message.encode('utf-8'))

    def tick(self):
        """Appele dans la boucle principale — flush periodique des logs."""
        _log_flush()
