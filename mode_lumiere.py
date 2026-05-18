import time
import config
from capteur import CapteurLuminosite
from logger import log

class ModeSuiviLumiere:
    """Gère le comportement autonome de suivi de lumière basé sur les deux LDR."""
    
    def __init__(self, chassis):
        self._chassis = chassis
        self._ldr_g = CapteurLuminosite(config.LUMINOSITE_GAUCHE_ADC)
        self._ldr_d = CapteurLuminosite(config.LUMINOSITE_DROITE_ADC)
        
        self._actif = False
        self._base_g = 0.0
        self._base_d = 0.0
        
        # Historique pour la moyenne glissante (lissage sur 3 lectures)
        self._hg = [0.0, 0.0, 0.0]
        self._hd = [0.0, 0.0, 0.0]

    def activer(self):
        if not self._actif:
            log("[LUMIERE] Initialisation et Tare en cours... Ne pas bouger la lampe.")
            # Mesure de la lumière ambiante (Tare)
            N = 20
            somme_g = 0
            somme_d = 0
            for _ in range(N):
                somme_g += self._ldr_g.lire_pourcentage()
                somme_d += self._ldr_d.lire_pourcentage()
                time.sleep_ms(20)
                
            self._base_g = somme_g / N
            self._base_d = somme_d / N
            
            # Réinitialisation de l'historique de lissage
            self._hg = [0.0, 0.0, 0.0]
            self._hd = [0.0, 0.0, 0.0]
            
            self._actif = True
            log("[LUMIERE] Mode Suivi Actif ! base_G={:.1f}% base_D={:.1f}%".format(self._base_g, self._base_d))

    def desactiver(self):
        if self._actif:
            self._actif = False
            self._chassis.arreter()
            log("[LUMIERE] Mode Suivi Désactivé")

    def est_actif(self):
        return self._actif

    def mise_a_jour(self):
        if not self._actif:
            return

        # 1. Lecture et calcul par rapport à la tare
        val_g = self._ldr_g.lire_pourcentage() - self._base_g
        val_d = self._ldr_d.lire_pourcentage() - self._base_d
        
        # Mise à jour de l'historique pour le lissage
        self._hg.append(val_g)
        self._hg.pop(0)
        self._hd.append(val_d)
        self._hd.pop(0)
        
        g = sum(self._hg) / 3
        d = sum(self._hd) / 3
        diff = g - d
        
        intensite_max = max(g, d) 

        # 2. Logique de décision (Orientation + Avance)
        if intensite_max < 10.0:  # Seuil à 10% pour s'activer
            self._chassis.arreter()
        elif abs(diff) < config.AUTO_SEUIL_DIFF_LDR:
            # La lampe est en face -> On avance
            self._chassis.avancer(config.AUTO_PUISSANCE_SUIVI)
        elif g > d:
            # Plus de lumière à gauche -> on tourne à gauche
            self._chassis.tourner_droite(config.AUTO_PUISSANCE_SUIVI)
        else:
            # Plus de lumière à droite -> on tourne à droite
            self._chassis.tourner_gauche(config.AUTO_PUISSANCE_SUIVI)