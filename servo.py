from machine import Pin, PWM
import time
import config


class ServoMoteur:
    """
    Controle un servo a rotation continue (CR) via PWM 50 Hz.

    Calibration requise : a 1500 us le servo doit etre completement a l'arret.
    La position est estimee par suivi des rotations temporisees.

    Brochage par defaut : SERVO_PIN defini dans config.py
    """

    _FREQ_HZ    = 50
    _STOP_US    = 1500
    _PERIODE_US = 20000

    def __init__(self, pin=config.SERVO_PIN):
        self._pwm = PWM(Pin(pin))
        self._pwm.freq(self._FREQ_HZ)
        self._position = "centre"
        self._set_pwm(self._STOP_US)

    def _set_pwm(self, us):
        self._pwm.duty_u16(int(us / self._PERIODE_US * 65535))

    def _tourner(self, us_offset, duree_ms):
        self._set_pwm(self._STOP_US + us_offset)
        time.sleep_ms(duree_ms)
        self._set_pwm(self._STOP_US)

    def aller_a(self, angle):
        """Rotation temporisee proportionnelle a la distance depuis la position courante."""
        angle = max(0, min(180, angle))
        if self._position == "gauche":
            angle_actuel = config.SERVO_ANGLE_GAUCHE
        elif self._position == "droite":
            angle_actuel = config.SERVO_ANGLE_DROITE
        else:
            angle_actuel = config.SERVO_ANGLE_CENTRE
        diff = angle - angle_actuel
        if abs(diff) < 5:
            return
        duree = int(abs(diff) / 90 * config.SERVO_DELAI_MS)
        self._tourner(config.SERVO_VITESSE_US if diff > 0 else -config.SERVO_VITESSE_US, duree)
        if angle <= 45:
            self._position = "droite"
        elif angle >= 135:
            self._position = "gauche"
        else:
            self._position = "centre"

    def centrer(self):
        """Revient en position centrale."""
        if self._position == "gauche":
            self._tourner(-config.SERVO_VITESSE_US, config.SERVO_DELAI_MS)
        elif self._position == "droite":
            self._tourner(config.SERVO_VITESSE_US, config.SERVO_DELAI_MS)
        self._position = "centre"

    def gauche(self):
        """Oriente le capteur vers la gauche."""
        if self._position == "droite":
            self._tourner(config.SERVO_VITESSE_US, config.SERVO_DELAI_MS * 2)
        elif self._position == "centre":
            self._tourner(config.SERVO_VITESSE_US, config.SERVO_DELAI_MS)
        self._position = "gauche"

    def droite(self):
        """Oriente le capteur vers la droite."""
        if self._position == "gauche":
            self._tourner(-config.SERVO_VITESSE_US, config.SERVO_DELAI_MS * 2)
        elif self._position == "centre":
            self._tourner(-config.SERVO_VITESSE_US, config.SERVO_DELAI_MS)
        self._position = "droite"

    @property
    def angle(self):
        if self._position == "gauche":
            return config.SERVO_ANGLE_GAUCHE
        elif self._position == "droite":
            return config.SERVO_ANGLE_DROITE
        return config.SERVO_ANGLE_CENTRE

    def desactiver(self):
        """Coupe le signal PWM."""
        self._pwm.duty_u16(0)
