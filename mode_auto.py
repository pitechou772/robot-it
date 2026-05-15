import time
import config

ETAT_ARRET  = 0
ETAT_AVANCE = 1
ETAT_TOURNE = 2
ETAT_RECULE = 3


class ModeAutonome:
    """
    Mode autonome sans servo : le capteur ultrason est fixe face avant.
    Quand un obstacle est detecte, le robot recule puis pivote.
    La direction de pivot alterne gauche/droite a chaque obstacle.

    Machine a etats :
      AVANCE -> obstacle detecte -> RECULE
      RECULE -> duree ecoulee    -> TOURNE (G ou D en alternance)
      TOURNE -> duree ecoulee    -> AVANCE
    """

    def __init__(self, chassis, capteur_ultrason):
        self._chassis  = chassis
        self._ultrason = capteur_ultrason

        self._etat          = ETAT_ARRET
        self._t_debut       = 0
        self._pivot_suivant = "G"

    def activer(self):
        if self._etat == ETAT_ARRET:
            self._etat = ETAT_AVANCE
            print("[AUTO] Actif - AVANCE")

    def desactiver(self):
        self._etat = ETAT_ARRET
        self._chassis.arreter()
        print("[AUTO] Desactive")

    def est_actif(self):
        return self._etat != ETAT_ARRET

    def mise_a_jour(self):
        if self._etat == ETAT_AVANCE:
            self._avancer()
        elif self._etat == ETAT_RECULE:
            self._reculer()
        elif self._etat == ETAT_TOURNE:
            self._tourner()

    def _avancer(self):
        dist = self._ultrason.mesurer_distance()
        if dist is not None and dist < config.SEUIL_OBSTACLE_CM:
            self._chassis.arreter()
            print("[AUTO] Obstacle a {} cm - RECULE".format(dist))
            self._chassis.reculer(config.AUTO_PUISSANCE_EVIT)
            self._etat    = ETAT_RECULE
            self._t_debut = time.ticks_ms()
        else:
            self._chassis.avancer(config.AUTO_PUISSANCE_SUIVI)

    def _reculer(self):
        if time.ticks_diff(time.ticks_ms(), self._t_debut) >= config.AUTO_DUREE_RECUL_MS:
            self._chassis.arreter()
            if self._pivot_suivant == "G":
                print("[AUTO] TOURNE G")
                self._chassis.tourner_gauche(config.AUTO_PUISSANCE_EVIT)
            else:
                print("[AUTO] TOURNE D")
                self._chassis.tourner_droite(config.AUTO_PUISSANCE_EVIT)
            self._pivot_suivant = "D" if self._pivot_suivant == "G" else "G"
            self._etat    = ETAT_TOURNE
            self._t_debut = time.ticks_ms()

    def _tourner(self):
        if time.ticks_diff(time.ticks_ms(), self._t_debut) >= config.AUTO_DUREE_PIVOT_MS:
            print("[AUTO] Pivot termine - AVANCE")
            self._etat = ETAT_AVANCE
            self._chassis.avancer(config.AUTO_PUISSANCE_SUIVI)
