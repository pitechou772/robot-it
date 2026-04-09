# =============================================================================
#  config.py  -  Configuration materielle du robot
#  Modifie ce fichier pour adapter le code a ton cablage.
# =============================================================================

# --- MOTEUR GAUCHE (L293D canal A) ---
MOTEUR_GAUCHE_PWM = 15   # Enable A (signal PWM)
MOTEUR_GAUCHE_IN1 = 14   # Direction 1
MOTEUR_GAUCHE_IN2 = 13   # Direction 2

# --- MOTEUR DROIT (L293D canal B) ---
MOTEUR_DROIT_PWM  = 10   # Enable B (signal PWM)
MOTEUR_DROIT_IN1  = 11   # Direction 1
MOTEUR_DROIT_IN2  = 12   # Direction 2

# --- FREQUENCE PWM (Hz) ---
MOTEUR_FREQUENCE  = 1000

# --- CAPTEUR ULTRASON HC-SR04 ---
ULTRASON_TRIG     = 2    # Broche TRIG
ULTRASON_ECHO     = 3    # Broche ECHO
ULTRASON_MAX_CM   = 400  # Distance maximale mesurable (cm)

# --- CAPTEURS DE LUMINOSITE (LDR) ---
LUMINOSITE_ADC         = 26   # Broche ADC unique (retrocompatibilite)
LUMINOSITE_GAUCHE_ADC  = 26   # ADC0 — LDR cote gauche du robot
LUMINOSITE_DROITE_ADC  = 27   # ADC1 — LDR cote droit  du robot

# --- BLUETOOTH ---
BLE_NOM           = "UART-VAQ"  # Nom du robot visible en BLE (modifiable dans ton app)

# --- SEUILS ---
SEUIL_OBSTACLE_CM = 20   # Arret d'urgence si obstacle detecte a moins de X cm
SEUIL_SOMBRE_PCT  = 30   # Alerte si luminosite inferieure a X %

# --- TIMING ---
INTERVALLE_CAPTEURS_MS = 500  # Periode de lecture des capteurs (ms)

# --- MODE AUTONOME ---
AUTO_PUISSANCE_SUIVI  = 0.6  # Puissance moteur en suivi de lumiere (0.0 a 1.0)
AUTO_PUISSANCE_EVIT   = 0.7  # Puissance moteur pendant l'evitement d'obstacle
AUTO_SEUIL_DIFF_LDR   = 5.0  # Ecart minimum (%) entre LDR gauche/droite pour tourner
AUTO_DUREE_RECUL_MS   = 500  # Duree de la phase de recul lors de l'evitement (ms)
AUTO_DUREE_PIVOT_MS   = 600  # Duree de la phase de pivot lors de l'evitement (ms)
