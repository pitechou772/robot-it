from machine import Pin, PWM
import config


class ServoMoteur:
    """
    Controle un servomoteur standard via PWM 50 Hz.

    Plage angulaire : 0 a 180 degres.
      0 deg   = impulsion 500 us  (tout a droite du robot)
      90 deg  = impulsion 1500 us (centre, face avant)
      180 deg = impulsion 2500 us (tout a gauche du robot)

    Brochage par defaut : SERVO_PIN defini dans config.py
    """

    _FREQ_HZ    = 50       # frequence standard servo
    _US_MIN     = 500      # largeur impulsion a 0 deg
    _US_MAX     = 2500     # largeur impulsion a 180 deg
    _PERIODE_US = 20000    # periode = 1 / 50 Hz = 20 000 us

    def __init__(self, pin=config.SERVO_PIN):
        self._pwm = PWM(Pin(pin))
        self._pwm.freq(self._FREQ_HZ)
        self._angle = None
        self.aller_a(config.SERVO_ANGLE_CENTRE)

    def aller_a(self, angle):
        """Positionne le servo a l'angle voulu (0-180 deg)."""
        angle = max(0, min(180, angle))
        self._angle = angle
        us    = self._US_MIN + (angle / 180) * (self._US_MAX - self._US_MIN)
        duty  = int(us / self._PERIODE_US * 65535)
        self._pwm.duty_u16(duty)

    def centrer(self):
        """Revient a la position centrale (90 deg)."""
        self.aller_a(config.SERVO_ANGLE_CENTRE)

    def gauche(self):
        """Oriente le capteur vers la gauche."""
        self.aller_a(config.SERVO_ANGLE_GAUCHE)

    def droite(self):
        """Oriente le capteur vers la droite."""
        self.aller_a(config.SERVO_ANGLE_DROITE)

    @property
    def angle(self):
        return self._angle

    def desactiver(self):
        """Coupe le signal PWM (economie d'energie, evite le bruit)."""
        self._pwm.duty_u16(0)
