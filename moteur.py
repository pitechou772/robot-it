from machine import Pin, PWM
import config


class Moteur:
    """Contrôle un moteur DC via un canal du driver L293D."""

    def __init__(self, pin_pwm, pin_in1, pin_in2, frequence=1000):
        self._pwm = PWM(Pin(pin_pwm))
        self._pwm.freq(frequence)
        self._in1 = Pin(pin_in1, Pin.OUT)
        self._in2 = Pin(pin_in2, Pin.OUT)
        self.arreter()

    def avancer(self, puissance=1.0):
        """Fait tourner le moteur en avant. puissance : 0.0 a 1.0."""
        self._in1.value(1)
        self._in2.value(0)
        self._pwm.duty_u16(int(puissance * 65535))

    def reculer(self, puissance=1.0):
        """Fait tourner le moteur en arriere. puissance : 0.0 a 1.0."""
        self._in1.value(0)
        self._in2.value(1)
        self._pwm.duty_u16(int(puissance * 65535))

    def arreter(self):
        """Coupe le signal PWM et les sorties de direction."""
        self._in1.value(0)
        self._in2.value(0)
        self._pwm.duty_u16(0)


class ChassisMoteur:
    """
    Controle les deux moteurs du robot (gauche et droit).

    Brochage L293D :
      Moteur gauche : enA=15 (PWM), in1=14, in2=13
      Moteur droit  : enB=10 (PWM), in3=11, in4=12
    """

    def __init__(self):
        self.gauche = Moteur(
            pin_pwm=config.MOTEUR_GAUCHE_PWM,
            pin_in1=config.MOTEUR_GAUCHE_IN1,
            pin_in2=config.MOTEUR_GAUCHE_IN2,
            frequence=config.MOTEUR_FREQUENCE,
        )
        self.droit = Moteur(
            pin_pwm=config.MOTEUR_DROIT_PWM,
            pin_in1=config.MOTEUR_DROIT_IN1,
            pin_in2=config.MOTEUR_DROIT_IN2,
            frequence=config.MOTEUR_FREQUENCE,
        )

    def avancer(self, puissance=1.0):
        self.gauche.avancer(puissance)
        self.droit.avancer(puissance)

    def reculer(self, puissance=1.0):
        self.gauche.reculer(puissance)
        self.droit.reculer(puissance)

    def tourner_gauche(self, puissance=1.0):
        """Pivot gauche : moteur gauche recule, moteur droit avance."""
        self.gauche.reculer(puissance)
        self.droit.avancer(puissance)

    def tourner_droite(self, puissance=1.0):
        """Pivot droite : moteur gauche avance, moteur droit recule."""
        self.gauche.avancer(puissance)
        self.droit.reculer(puissance)

    def arreter(self):
        self.gauche.arreter()
        self.droit.arreter()

    def executer_commande(self, direction, puissance=1.0):
        """
        Execute une commande de direction recue par BLE.
        H = avancer  |  B = reculer
        G = pivot gauche  |  D = pivot droite
        O / X = stop
        """
        if direction == "H":
            self.avancer(puissance)
        elif direction == "B":
            self.reculer(puissance)
        elif direction == "G":
            self.tourner_gauche(puissance)
        elif direction == "D":
            self.tourner_droite(puissance)
        else:
            self.arreter()
