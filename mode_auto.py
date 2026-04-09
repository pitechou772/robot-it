import time
import config

# ---------------------------------------------------------------------------
# Constantes d'etat (entiers pour eviter les comparaisons de chaines)
# ---------------------------------------------------------------------------
ETAT_ARRET     = 0
ETAT_SUIVI     = 1
ETAT_EVITEMENT = 2

PHASE_RECUL = 0
PHASE_PIVOT = 1


class ModeAutonome:
    """
    Mode autonome du robot : suivi de lumiere avec evitement d'obstacles.

    Principe du debrayage :
      En etat SUIVI, si un obstacle est detecte, le mode debraye
      (suspend le suivi), execute une manoeuvre d'evitement en deux phases
      (recul puis pivot), puis reembraye automatiquement vers le SUIVI.

    Activation / desactivation via BLE :
      Commande "AUTO"   -> activer()
      Commande "MANUEL" -> desactiver()

    La methode mise_a_jour() doit etre appelee a chaque iteration
    de la boucle principale pour garantir la precision du timing.
    """

    def __init__(self, chassis, capteur_ultrason, ldr_gauche, ldr_droite):
        """
        Parameters
        ----------
        chassis           : ChassisMoteur
        capteur_ultrason  : CapteurUltrason
        ldr_gauche        : CapteurLuminosite  (LDR cote gauche, ADC0)
        ldr_droite        : CapteurLuminosite  (LDR cote droit,  ADC1)
        """
        self._chassis   = chassis
        self._ultrason  = capteur_ultrason
        self._ldr_g     = ldr_gauche
        self._ldr_d     = ldr_droite

        self._etat            = ETAT_ARRET
        self._phase_evitement = PHASE_RECUL
        self._t_phase_debut   = 0      # ticks_ms() au debut de la phase courante
        self._cote_pivot      = "D"    # "G" ou "D", determine lors du debrayage

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def activer(self):
        """Active le mode autonome (passe en SUIVI)."""
        if self._etat == ETAT_ARRET:
            self._etat = ETAT_SUIVI
            print("[AUTO] Mode autonome ACTIVE")

    def desactiver(self):
        """Desactive le mode autonome et arrete les moteurs."""
        self._etat = ETAT_ARRET
        self._chassis.arreter()
        print("[AUTO] Mode autonome DESACTIVE")

    def est_actif(self):
        """Retourne True si le robot est en SUIVI ou EVITEMENT."""
        return self._etat != ETAT_ARRET

    def mise_a_jour(self):
        """
        Dispatcher principal de la machine a etats.
        Doit etre appele a chaque iteration de la boucle principale.
        """
        if self._etat == ETAT_SUIVI:
            self._executer_suivi()
        elif self._etat == ETAT_EVITEMENT:
            self._executer_evitement()
        # ETAT_ARRET : rien a faire

    # ------------------------------------------------------------------
    # Logique interne
    # ------------------------------------------------------------------

    def _executer_suivi(self):
        """
        Suivi de lumiere differentiel.
        Verifie l'obstacle en priorite — declenche le debrayage si besoin.
        """
        # 1. Detection d'obstacle (debrayage)
        if self._ultrason.obstacle_detecte(config.SEUIL_OBSTACLE_CM):
            self._declencher_evitement()
            return

        # 2. Lecture differentielle des deux LDR
        lux_g = self._ldr_g.lire_pourcentage()
        lux_d = self._ldr_d.lire_pourcentage()
        diff  = lux_g - lux_d   # positif => gauche plus lumineuse

        # 3. Commande du chassis
        if diff > config.AUTO_SEUIL_DIFF_LDR:
            # Lumiere a gauche : tourner a gauche
            self._chassis.tourner_gauche(config.AUTO_PUISSANCE_SUIVI)
        elif diff < -config.AUTO_SEUIL_DIFF_LDR:
            # Lumiere a droite : tourner a droite
            self._chassis.tourner_droite(config.AUTO_PUISSANCE_SUIVI)
        else:
            # Lumiere centree : avancer
            self._chassis.avancer(config.AUTO_PUISSANCE_SUIVI)

    def _declencher_evitement(self):
        """
        Debrayage : suspend le suivi et demarre la manoeuvre d'evitement.
        Le pivot se fait vers le cote le moins eclaire : l'obstacle bloque
        la lumiere de ce cote, donc on s'ecarte dans la direction opposee.
        """
        lux_g = self._ldr_g.lire_pourcentage()
        lux_d = self._ldr_d.lire_pourcentage()
        # Pivoter vers le cote le moins eclaire
        self._cote_pivot = "D" if lux_g >= lux_d else "G"

        self._etat            = ETAT_EVITEMENT
        self._phase_evitement = PHASE_RECUL
        self._t_phase_debut   = time.ticks_ms()
        self._chassis.reculer(config.AUTO_PUISSANCE_EVIT)
        print("[AUTO] DEBRAYAGE - debut evitement (pivot: {})".format(self._cote_pivot))

    def _executer_evitement(self):
        """
        Manoeuvre d'evitement en deux phases :
          Phase 1 (RECUL)  : reculer pendant AUTO_DUREE_RECUL_MS
          Phase 2 (PIVOT)  : pivoter pendant AUTO_DUREE_PIVOT_MS
          Fin              : retour en SUIVI (reembrayage)
        """
        maintenant = time.ticks_ms()
        elapsed    = time.ticks_diff(maintenant, self._t_phase_debut)

        if self._phase_evitement == PHASE_RECUL:
            if elapsed >= config.AUTO_DUREE_RECUL_MS:
                # Transition vers la phase pivot
                self._phase_evitement = PHASE_PIVOT
                self._t_phase_debut   = maintenant
                if self._cote_pivot == "G":
                    self._chassis.tourner_gauche(config.AUTO_PUISSANCE_EVIT)
                else:
                    self._chassis.tourner_droite(config.AUTO_PUISSANCE_EVIT)
                print("[AUTO] Evitement - phase PIVOT ({})".format(self._cote_pivot))

        elif self._phase_evitement == PHASE_PIVOT:
            if elapsed >= config.AUTO_DUREE_PIVOT_MS:
                # Manoeuvre terminee : reembrayage vers SUIVI
                self._etat = ETAT_SUIVI
                print("[AUTO] Evitement termine - REEMBRAYAGE vers SUIVI")
                # Le prochain appel a _executer_suivi() reprendra le suivi
