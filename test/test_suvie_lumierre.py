import sys
sys.path.insert(0, "..")

import time
from moteur import ChassisMoteur
from capteur import CapteurLuminosite
import config

print("=== TEST SUIVI LUMIERE ===")

# --- Initialisation du matériel ---
chassis = ChassisMoteur()
ldr_g   = CapteurLuminosite(config.LUMINOSITE_GAUCHE_ADC)
ldr_d   = CapteurLuminosite(config.LUMINOSITE_DROITE_ADC)

# --- Tare : mesure de la lumiere ambiante ---
print("Tare en cours, ne pas bouger la lampe...")
N = 20
base_g = sum(ldr_g.lire_pourcentage() for _ in range(N)) / N
base_d = sum(ldr_d.lire_pourcentage() for _ in range(N)) / N
print("Tare OK  base_G={:.1f}%  base_D={:.1f}%".format(base_g, base_d))
print("Pointez la lampe, le robot va la suivre. (Ctrl+C pour arreter)\n")
time.sleep(2) # Réduit à 2s pour attendre moins longtemps

# Historique pour lissage (moyenne glissante sur 3 lectures)
hg = [0.0, 0.0, 0.0]
hd = [0.0, 0.0, 0.0]

try:
    while True:
        # 1. Lecture et calcul par rapport à la tare
        val_g = ldr_g.lire_pourcentage() - base_g
        val_d = ldr_d.lire_pourcentage() - base_d
        
        # Historique pour le lissage
        hg.append(val_g)
        hg.pop(0)
        hd.append(val_d)
        hd.pop(0)
        
        g = sum(hg) / 3
        d = sum(hd) / 3
        diff = g - d
        
        # On prend le max des deux pour détecter la lampe
        intensite_max = max(g, d) 

        # 2. Logique de décision (Orientation + Avance)
        if intensite_max < 10.0:  # Seuil à 10% pour s'activer
            chassis.arreter()
            etat = "PAS DE LUMIERE"
        
        elif abs(diff) < config.AUTO_SEUIL_DIFF_LDR:
            # La lampe est en face -> On avance !
            chassis.avancer(config.AUTO_PUISSANCE_SUIVI)
            etat = "AVANCE"
        
        elif g > d:
            # Plus de lumière à gauche -> on tourne à gauche
            chassis.tourner_droite(config.AUTO_PUISSANCE_SUIVI)
            etat = "CORRIGE G"
        
        else:
            # Plus de lumière à droite -> on tourne à droite
            chassis.tourner_gauche(config.AUTO_PUISSANCE_SUIVI)
            etat = "CORRIGE D"

        print("G={:+.1f}%  D={:+.1f}%  diff={:+.1f}%  -> {}".format(g, d, diff, etat))
        
        time.sleep_ms(50)

except KeyboardInterrupt:
    chassis.arreter()
    print("Arret.")
