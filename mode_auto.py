import time
import config

# ---------------------------------------------------------------------------
# Etats principaux
# ---------------------------------------------------------------------------
ETAT_ARRET  = 0
ETAT_AVANCE = 1   # avance tout droit, servo centre
ETAT_SCAN   = 2   # servo scanne gauche puis droite pour choisir une direction
ETAT_TOURNE = 3   # pivot en cours (gauche ou droite)
ETAT_RECULE = 4   # recul en cours (chemin bloque des deux cotes)

# Sous-etats du scan
_SCAN_GAUCHE       = 0   # servo va a gauche, on attend
_SCAN_MES_GAUCHE   = 1   # on mesure a gauche, servo va a droite
_SCAN_MES_DROITE   = 2   # on mesure a droite, servo centre, on decide


class ModeAutonome:
    """
    Mode autonome avec servo-scanner : le capteur ultrason est monte sur un
    servo qui balaie gauche/centre/droite pour choisir la meilleure voie.

    Machine a etats :
      AVANCE  -> obstacle detecte         -> SCAN
      SCAN    -> voie libre trouvee       -> TOURNE
      SCAN    -> bloque partout           -> RECULE
      TOURNE  -> duree ecoulee            -> AVANCE
      RECULE  -> duree ecoulee            -> SCAN  (re-evaluate)

    Activation / desactivation via BLE :
      Commande "AUTO"   -> activer()
      Commande "MANUEL" -> desactiver()

    Appeler mise_a_jour() a chaque iteration de la boucle principale.
    """

    def __init__(self, chassis, capteur_ultrason, servo):
        self._chassis  = chassis
        self._ultrason = capteur_ultrason
        self._servo    = servo

        self._etat        = ETAT_ARRET
        self._sous_etat   = _SCAN_GAUCHE
        self._t_debut     = 0
        self._cote_pivot  = "G"
        self._d_gauche    = 0.0
        self._d_droite    = 0.0

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def activer(self):
        if self._etat == ETAT_ARRET:
            self._servo.centrer()
            self._etat = ETAT_AVANCE
            print("[AUTO] Actif - AVANCE")

    def desactiver(self):
        self._etat = ETAT_ARRET
        self._servo.centrer()
        self._chassis.arreter()
        print("[AUTO] Desactive")

    def est_actif(self):
        return self._etat != ETAT_ARRET

    def mise_a_jour(self):
        if self._etat == ETAT_AVANCE:
            self._avancer()
        elif self._etat == ETAT_SCAN:
            self._scanner()
        elif self._etat == ETAT_TOURNE:
            self._tourner()
        elif self._etat == ETAT_RECULE:
            self._reculer()

    # ------------------------------------------------------------------
    # Logique interne
    # ------------------------------------------------------------------

    def _avancer(self):
        dist = self._ultrason.mesurer_distance()
        if dist is not None and dist < config.SEUIL_OBSTACLE_CM:
            self._chassis.arreter()
            print("[AUTO] Obstacle a {} cm - SCAN".format(dist))
            self._lancer_scan()
        else:
            self._chassis.avancer(config.AUTO_PUISSANCE_SUIVI)

    def _lancer_scan(self):
        self._etat      = ETAT_SCAN
        self._sous_etat = _SCAN_GAUCHE
        self._servo.gauche()
        self._t_debut = time.ticks_ms()

    def _scanner(self):
        elapsed = time.ticks_diff(time.ticks_ms(), self._t_debut)

        if self._sous_etat == _SCAN_GAUCHE:
            if elapsed >= config.SERVO_DELAI_MS:
                d = self._ultrason.mesurer_distance()
                self._d_gauche = d if d is not None else 0.0
                print("[AUTO] Scan gauche : {} cm".format(self._d_gauche))
                self._servo.droite()
                self._t_debut   = time.ticks_ms()
                self._sous_etat = _SCAN_MES_GAUCHE

        elif self._sous_etat == _SCAN_MES_GAUCHE:
            if elapsed >= config.SERVO_DELAI_MS:
                d = self._ultrason.mesurer_distance()
                self._d_droite = d if d is not None else 0.0
                print("[AUTO] Scan droite : {} cm".format(self._d_droite))
                self._servo.centrer()
                self._t_debut   = time.ticks_ms()
                self._sous_etat = _SCAN_MES_DROITE

        elif self._sous_etat == _SCAN_MES_DROITE:
            if elapsed >= config.SERVO_DELAI_MS // 2:
                self._decider()

    def _decider(self):
        dg = self._d_gauche
        dd = self._d_droite
        marge = config.SERVO_MARGE_CM

        if dg <= marge and dd <= marge:
            # Bloque des deux cotes : reculer
            print("[AUTO] Bloque partout - RECULE")
            self._chassis.reculer(config.AUTO_PUISSANCE_EVIT)
            self._etat    = ETAT_RECULE
            self._t_debut = time.ticks_ms()
        elif dg >= dd:
            print("[AUTO] Voie gauche plus libre ({} > {}) - TOURNE G".format(dg, dd))
            self._cote_pivot = "G"
            self._chassis.tourner_gauche(config.AUTO_PUISSANCE_EVIT)
            self._etat    = ETAT_TOURNE
            self._t_debut = time.ticks_ms()
        else:
            print("[AUTO] Voie droite plus libre ({} > {}) - TOURNE D".format(dd, dg))
            self._cote_pivot = "D"
            self._chassis.tourner_droite(config.AUTO_PUISSANCE_EVIT)
            self._etat    = ETAT_TOURNE
            self._t_debut = time.ticks_ms()

    def _tourner(self):
        if time.ticks_diff(time.ticks_ms(), self._t_debut) >= config.AUTO_DUREE_PIVOT_MS:
            print("[AUTO] Pivot termine - AVANCE")
            self._etat = ETAT_AVANCE
            self._chassis.avancer(config.AUTO_PUISSANCE_SUIVI)

    def _reculer(self):
        if time.ticks_diff(time.ticks_ms(), self._t_debut) >= config.AUTO_DUREE_RECUL_MS:
            print("[AUTO] Recul termine - SCAN")
            self._chassis.arreter()
            self._lancer_scan()
