# =============================================================================
#  config.py  -  Configuration materielle du robot
#  Modifie ce fichier pour adapter le code a ton cablage.
# =============================================================================

# --- MOTEUR GAUCHE (L293D canal A) ---
MOTEUR_GAUCHE_PWM = 16   # Enable A (signal PWM)
MOTEUR_GAUCHE_IN1 = 14   # Direction 1
MOTEUR_GAUCHE_IN2 = 15   # Direction 2

# --- MOTEUR DROIT (L293D canal B) ---
MOTEUR_DROIT_PWM  = 17   # Enable B (signal PWM)
MOTEUR_DROIT_IN1  = 13   # Direction 1
MOTEUR_DROIT_IN2  = 12   # Direction 2

# --- FREQUENCE PWM (Hz) ---
MOTEUR_FREQUENCE  = 1000

# --- CAPTEUR ULTRASON (mono-broche) ---
ULTRASON_TRIG   = 2    # Broche signal unique (TRIG + ECHO sur la meme pin)
ULTRASON_MAX_CM = 400  # Distance maximale mesurable (cm)

# --- CAPTEURS DE LUMINOSITE (LDR) ---
LUMINOSITE_ADC         = 26   # Broche ADC unique (retrocompatibilite)
LUMINOSITE_GAUCHE_ADC  = 26   # ADC0 — LDR cote gauche du robot
LUMINOSITE_DROITE_ADC  = 27   # ADC1 — LDR cote droit  du robot

# --- SERVO MOTEUR (capteur ultrason monté dessus) ---
SERVO_PIN          = 18   # Broche PWM du servo
SERVO_ANGLE_CENTRE = 90   # Position centrale (face avant)
SERVO_ANGLE_GAUCHE = 150  # Position scan gauche
SERVO_ANGLE_DROITE = 30   # Position scan droite
SERVO_DELAI_MS     = 400  # Duree de rotation du servo CR (ms) — augmente pour aller plus loin
SERVO_VITESSE_US   = 200  # Vitesse du servo CR : offset PWM depuis 1500 us (50=lent, 200=rapide)
                          # Si gauche/droite sont inversees, passer a -200
SERVO_MARGE_CM     = 15   # Ecart minimum entre gauche/droite pour choisir une direction

# --- BLUETOOTH ---
BLE_NOM           = "UART-VAQ"  # Nom du robot visible en BLE (modifiable dans ton app)

# --- SEUILS ---
SEUIL_OBSTACLE_CM = 10   # Arret d'urgence si obstacle detecte a moins de X cm
SEUIL_SOMBRE_PCT  = 30   # Alerte si luminosite inferieure a X %

# --- TIMING ---
INTERVALLE_CAPTEURS_MS = 500  # Periode de lecture des capteurs (ms)

# --- MODE AUTONOME ---
AUTO_PUISSANCE_SUIVI  = 0.6  # Puissance moteur en suivi de lumiere (0.0 a 1.0)
AUTO_PUISSANCE_EVIT   = 0.65  # Puissance moteur pendant l'evitement d'obstacle
AUTO_SEUIL_DIFF_LDR   = 10.0 # Ecart minimum (%) entre LDR gauche/droite pour tourner
AUTO_SEUIL_LAMPE_PCT  = 25.0 # Total minimum (%) pour considerer que c'est une lampe (pas une fenetre)
AUTO_DUREE_RECUL_MS   = 500  # Duree de la phase de recul lors de l'evitement (ms)
AUTO_DUREE_PIVOT_MS   = 600  # Duree de la phase de pivot lors de l'evitement (ms)
