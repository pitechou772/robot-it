import time
from machine import Pin, ADC
import config


class CapteurUltrason:
    """
    Capteur de distance ultrasonique HC-SR04.

    Brochage par defaut :
      TRIG = Pin 2
      ECHO = Pin 3
    """

    def __init__(self, pin_sig=config.ULTRASON_TRIG, distance_max_cm=config.ULTRASON_MAX_CM):
        self._pin_num = pin_sig
        self._distance_max = distance_max_cm

    def mesurer_distance(self):
        """
        Retourne la distance mesuree en centimetres (float).
        Retourne None si hors portee ou timeout.
        """
        # Impulsion TRIG de 10 us (pin en sortie)
        pin = Pin(self._pin_num, Pin.OUT)
        pin.value(0)
        time.sleep_us(2)
        pin.value(1)
        time.sleep_us(10)
        pin.value(0)

        # Basculer en entree pour lire l'echo
        pin = Pin(self._pin_num, Pin.IN)

        # Attente front montant ECHO (timeout 30 ms)
        debut_attente = time.ticks_us()
        while pin.value() == 0:
            if time.ticks_diff(time.ticks_us(), debut_attente) > 30000:
                return None
        debut = time.ticks_us()

        # Attente front descendant ECHO (timeout 30 ms)
        while pin.value() == 1:
            if time.ticks_diff(time.ticks_us(), debut) > 30000:
                return None
        fin = time.ticks_us()

        # Vitesse du son : 0.034 cm/us, aller-retour donc / 2
        duree_us = time.ticks_diff(fin, debut)
        distance = (duree_us * 0.034) / 2

        if distance > self._distance_max:
            return None
        return round(distance, 1)

    def obstacle_detecte(self, seuil_cm=20):
        """Retourne True si un obstacle est detecte a moins de seuil_cm."""
        dist = self.mesurer_distance()
        if dist is None:
            return False
        return dist < seuil_cm


class CapteurLuminosite:
    """
    Capteur de luminosite via photoresistance (LDR) sur entree ADC.

    Brochage par defaut :
      ADC = Pin 26  (ADC0 sur Pico W)

    Montage attendu : diviseur de tension avec pull-down.
    Plus la lumiere est forte, plus la tension (et la valeur ADC) est elevee.
    """

    def __init__(self, pin_adc=config.LUMINOSITE_ADC):
        self._adc = ADC(Pin(pin_adc))

    def lire_brut(self):
        """Retourne la valeur brute ADC (0 a 65535)."""
        return self._adc.read_u16()

    def lire_pourcentage(self):
        """Retourne la luminosite en pourcentage (0 % = sombre, 100 % = lumineux)."""
        return round((self._adc.read_u16() / 65535) * 100, 1)

    def est_sombre(self, seuil_pct=30):
        """Retourne True si la luminosite est inferieure au seuil (en %)."""
        return self.lire_pourcentage() < seuil_pct
