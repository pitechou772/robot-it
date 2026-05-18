import sys
sys.path.insert(0, "..")
import time
import math
from moteur import ChassisMoteur
from capteur import CapteurUltrason
import config

# Initialisation des composants physiques
chassis = ChassisMoteur()
ultrason = CapteurUltrason()

def effectuer_pivot_et_mesurer(direction, temps_ms):
    """Effectue un pivot, prend une mesure et revient à la position initiale."""
    if direction == "GAUCHE":
        chassis.tourner_gauche(config.AUTO_PUISSANCE_EVIT)
    else:
        chassis.tourner_droite(config.AUTO_PUISSANCE_EVIT)
    
    time.sleep_ms(temps_ms)
    chassis.arreter()
    time.sleep_ms(200) # Stabilisation
    
    dist = ultrason.mesurer_distance()
    
    # Retour au centre (mouvement inverse)
    if direction == "GAUCHE":
        chassis.tourner_droite(config.AUTO_PUISSANCE_EVIT)
    else:
        chassis.tourner_gauche(config.AUTO_PUISSANCE_EVIT)
        
    time.sleep_ms(temps_ms)
    chassis.arreter()
    return dist

def algorithme_decision():
    print("=== TEST ARBRE DE DECISION GEOMETRIQUE (SANS SERVO) ===")
    
    # Constante pour un pivot d'environ 45 degrés (à ajuster selon ton châssis)
    TEMPS_45_DEG = 400 
    
    try:
        while True:
            # 1. MARCHE AVANT ET SURVEILLANCE
            dist_face = ultrason.mesurer_distance()
            
            if dist_face is not None and dist_face < config.SEUIL_OBSTACLE_CM:
                # 2. OBSTACLE DETECTE : ARRET ET RECUL
                print(f"Obstacle à {dist_face}cm. Arrêt et recul...")
                chassis.arreter()
                chassis.reculer(config.AUTO_PUISSANCE_EVIT)
                time.sleep_ms(config.AUTO_DUREE_RECUL_MS)
                chassis.arreter()
                
                # 3. PHASE DE SCAN (45° GAUCHE / 45° DROITE)
                print("Lancement du scan par pivot...")
                dist_g = effectuer_pivot_et_mesurer("GAUCHE", TEMPS_45_DEG)
                print(f"Distance Gauche: {dist_g} cm")
                
                time.sleep_ms(200)
                
                dist_d = effectuer_pivot_et_mesurer("DROITE", TEMPS_45_DEG)
                print(f"Distance Droite: {dist_d} cm")

                # 4. ANALYSE ET DÉCISION
                if dist_g is None or dist_d is None:
                    # Sécurité si une mesure échoue
                    print("Erreur mesure : Recul de sécurité supplémentaire")
                    chassis.reculer(config.AUTO_PUISSANCE_EVIT)
                    time.sleep_ms(500)
                    continue

                # Si les valeurs sont identiques (mur plat ou coin)
                if abs(dist_g - dist_d) < 5:
                    print("Même valeur détectée : on recule et on répète.")
                    chassis.reculer(config.AUTO_PUISSANCE_EVIT)
                    time.sleep_ms(config.AUTO_DUREE_RECUL_MS)
                    continue 

                # 5. CHOIX DE LA SORTIE (L'endroit le plus loin)
                if dist_g > dist_d:
                    print("Sortie à GAUCHE. Pivot à 90° pour être parallèle.")
                    chassis.tourner_gauche(config.AUTO_PUISSANCE_EVIT)
                else:
                    print("Sortie à DROITE. Pivot à 90° pour être parallèle.")
                    chassis.tourner_droite(config.AUTO_PUISSANCE_EVIT)
                
                # Temps pour un 90° (environ le double du 45°)
                time.sleep_ms(TEMPS_45_DEG * 2)
                chassis.arreter()
                
                # 6. CALCUL GÉOMÉTRIQUE (Hypoténuse)
                # La distance mesurée à 45° est l'hypoténuse (H).
                # La distance réelle au mur est H * cos(45°)
                dist_max = max(dist_g, dist_d)
                distance_parallele = dist_max * 0.707 # cos(45°)
                print(f"Trajet parallèle amorcé (distance estimée mur: {distance_parallele:.1f}cm)")

                # 7. TRAJET PARALLÈLE AVEC SURVEILLANCE MÉMOIRE
                # On avance un certain temps tout en vérifiant si un nouvel obstacle surgit
                t_fin_parallele = time.ticks_ms() + 1500
                while time.ticks_diff(t_fin_parallele, time.ticks_ms()) > 0:
                    chassis.avancer(config.AUTO_PUISSANCE_SUIVI)
                    dist_check = ultrason.mesurer_distance()
                    if dist_check is not None and dist_check < config.SEUIL_OBSTACLE_CM:
                        print("Nouvel obstacle détecté pendant le trajet ! Mémorisation.")
                        break # Interruption et retour au cycle de décision
                    time.sleep_ms(50)

            else:
                chassis.avancer(config.AUTO_PUISSANCE_SUIVI)
            
            time.sleep_ms(50)

    except KeyboardInterrupt:
        chassis.arreter()
        print("Fin du test.")

# Lancement du test
algorithme_decision()