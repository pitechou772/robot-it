# Robot IT — MicroPython sur Raspberry Pi Pico W

Robot mobile à deux roues contrôlable via Bluetooth BLE, avec un mode autonome de suivi de lumière et d'évitement d'obstacles. Inclut un serveur de logs Wi-Fi accessible depuis n'importe quel navigateur.

---

## Sommaire

1. [Matériel requis](#matériel-requis)
2. [Brochage](#brochage)
3. [Installation](#installation)
4. [Structure du projet](#structure-du-projet)
5. [Explication de chaque fichier](#explication-de-chaque-fichier)
   - [main.py — le chef d'orchestre](#mainpy--le-chef-dorchestre)
   - [config.py — les réglages](#configpy--les-réglages)
   - [moteur.py — les roues](#moteurpy--les-roues)
   - [capteur.py — les yeux](#capteurpy--les-yeux)
   - [ble_app.py — la télécommande Bluetooth](#ble_apppy--la-télécommande-bluetooth)
   - [mode_auto.py — le pilote automatique](#mode_autopy--le-pilote-automatique)
   - [wifi_server.py — le journal de bord Wi-Fi](#wifi_serverpy--le-journal-de-bord-wi-fi)
6. [Protocole BLE](#protocole-ble)
7. [Serveur de logs Wi-Fi](#serveur-de-logs-wi-fi)
8. [Mode autonome](#mode-autonome)
9. [Configuration](#configuration-configpy)

---

## Matériel requis

| Composant | Quantité |
|---|---|
| Raspberry Pi Pico W | 1 |
| Driver moteur L293D | 1 |
| Moteurs DC + châssis 2 roues | 1 kit |
| Capteur ultrason HC-SR04 | 1 |
| Photo-résistances LDR | 2 |
| Résistances (diviseur de tension LDR) | 2 |
| Alimentation (pile / batterie) | 1 |

---

## Brochage

### Moteurs (L293D)

| Signal | Broche Pico W |
|---|---|
| Moteur gauche — Enable A (PWM) | GP11 |
| Moteur gauche — IN1 | GP10 |
| Moteur gauche — IN2 | GP12 |
| Moteur droit — Enable B (PWM) | GP7 |
| Moteur droit — IN3 | GP8 |
| Moteur droit — IN4 | GP9 |

### Capteur ultrason HC-SR04

| Signal | Broche Pico W |
|---|---|
| TRIG | GP2 |
| ECHO | GP3 |

### Capteurs de luminosité (LDR)

| Capteur | Broche Pico W |
|---|---|
| LDR gauche | GP26 (ADC0) |
| LDR droite | GP27 (ADC1) |

> Les LDR sont montées en diviseur de tension avec une résistance de pull-down.  
> Plus la lumière est forte, plus la tension (et la valeur ADC) est élevée.

---

## Installation

1. **Installer MicroPython** sur le Pico W :
   - Télécharger le firmware depuis [micropython.org](https://micropython.org/download/RPI_PICO_W/)
   - Maintenir le bouton `BOOTSEL` et brancher le Pico W en USB
   - Copier le fichier `.uf2` sur le lecteur `RPI-RP2`

2. **Copier les fichiers** sur le Pico W (via Thonny, rshell ou mpremote) :
   ```bash
   mpremote cp main.py config.py moteur.py capteur.py ble_app.py mode_auto.py wifi_server.py :
   mpremote mkdir lib
   mpremote cp lib/BLE_SimplePeripheral.py lib/ble_advertising.py :lib/
   ```

3. **Adapter `config.py`** si ton câblage diffère des valeurs par défaut.

4. **Redémarrer** le Pico W — le robot démarre automatiquement.

---

## Structure du projet

```
robot-it/
├── main.py            # Point d'entrée — boucle principale
├── config.py          # Tous les réglages matériels et seuils
├── moteur.py          # Contrôle des moteurs (vitesse, direction)
├── capteur.py         # Lecture du capteur ultrason et des LDR
├── ble_app.py         # Réception et décodage des commandes Bluetooth
├── mode_auto.py       # Pilote automatique (suivi lumière + évitement)
├── wifi_server.py     # Point d'accès Wi-Fi + serveur de logs web
└── lib/
    ├── BLE_SimplePeripheral.py   # Bibliothèque BLE (ne pas modifier)
    └── ble_advertising.py        # Utilitaires BLE (ne pas modifier)
```

---

## Explication de chaque fichier

---

### `main.py` — le chef d'orchestre

C'est le **point de départ** du programme. Quand le Pico W démarre, c'est ce fichier qui s'exécute en premier.

**Ce qu'il fait, étape par étape :**

1. **Essaie de démarrer les moteurs** — si le fichier `moteur.py` est présent et que le câblage est correct, les moteurs sont prêts. Sinon, le robot continue de fonctionner en mode BLE uniquement (utile pour tester sans châssis).

2. **Allume la LED** du Pico W quand un téléphone se connecte en Bluetooth, l'éteint quand il se déconnecte.

3. **Tourne en boucle toutes les 50 ms** pour :
   - Vérifier si un client BLE est connecté ou non
   - Appeler `ble.tick()` pour traiter les éventuelles requêtes HTTP du serveur de logs

> 50 ms = 20 vérifications par seconde. C'est suffisamment rapide pour réagir aux commandes sans surcharger le microcontrôleur.

---

### `config.py` — les réglages

Ce fichier centralise **tous les numéros de broches et tous les seuils** du robot. Tu n'as à modifier que ce fichier si tu changes le câblage.

| Ce qu'on y trouve | Exemple |
|---|---|
| Numéros de broches des moteurs | `MOTEUR_GAUCHE_PWM = 11` |
| Numéros de broches des capteurs | `ULTRASON_TRIG = 2` |
| Nom Bluetooth du robot | `BLE_NOM = "UART-VAQ"` |
| Seuil de détection d'obstacle | `SEUIL_OBSTACLE_CM = 20` |
| Puissance en mode autonome | `AUTO_PUISSANCE_SUIVI = 0.6` |
| Durée des manœuvres d'évitement | `AUTO_DUREE_RECUL_MS = 500` |

**Pourquoi tout centraliser ici ?**  
Pour ne pas avoir à fouiller dans 5 fichiers différents quand tu veux changer un réglage. Modifie `config.py`, tout le reste s'adapte automatiquement.

---

### `moteur.py` — les roues

Ce fichier contient deux classes qui contrôlent les moteurs physiques via le driver L293D.

#### Classe `Moteur` — un seul moteur

Gère **un moteur DC** (gauche ou droit). Elle envoie des signaux électriques sur trois broches :

- **PWM (Enable)** : contrôle la vitesse (0 % = arrêt, 100 % = pleine puissance)
- **IN1 / IN2** : contrôlent le sens de rotation (avant ou arrière)

| Méthode | Effet |
|---|---|
| `avancer(puissance)` | Fait tourner le moteur en avant |
| `reculer(puissance)` | Fait tourner le moteur en arrière |
| `arreter()` | Coupe l'alimentation du moteur |

La puissance est un nombre entre `0.0` (arrêt) et `1.0` (pleine puissance). Exemple : `0.6` = 60 % de puissance.

#### Classe `ChassisMoteur` — les deux moteurs ensemble

Regroupe les deux moteurs (gauche et droit) et propose des commandes de haut niveau :

| Méthode | Effet |
|---|---|
| `avancer(puissance)` | Les deux moteurs tournent en avant |
| `reculer(puissance)` | Les deux moteurs tournent en arrière |
| `tourner_gauche(puissance)` | Moteur gauche recule, moteur droit avance → pivot sur place |
| `tourner_droite(puissance)` | Moteur gauche avance, moteur droit recule → pivot sur place |
| `arreter()` | Les deux moteurs s'arrêtent |
| `executer_commande(direction, puissance)` | Traduit une lettre BLE (`H`, `B`, `G`, `D`) en mouvement |

---

### `capteur.py` — les yeux

Contient deux classes qui lisent les capteurs physiques du robot.

#### Classe `CapteurUltrason` — détecter les obstacles

Fonctionne comme un sonar : il envoie une impulsion sonore ultrasonique et mesure le temps que met l'écho à revenir. Ce temps est converti en distance (cm).

**Fonctionnement interne :**
1. Le Pico envoie une impulsion de 10 microsecondes sur la broche `TRIG`
2. Le capteur émet une salve ultrasonique et attend l'écho
3. La broche `ECHO` reste à l'état haut pendant le trajet aller-retour du son
4. La durée mesurée × vitesse du son (0,034 cm/µs) ÷ 2 = distance

| Méthode | Résultat |
|---|---|
| `mesurer_distance()` | Distance en cm (ou `None` si hors portée) |
| `obstacle_detecte(seuil_cm)` | `True` si un objet est détecté à moins de `seuil_cm` cm |

#### Classe `CapteurLuminosite` — mesurer la lumière

Lit la tension sur une photo-résistance (LDR) branchée sur une entrée ADC. Plus il fait clair, plus la tension est élevée.

| Méthode | Résultat |
|---|---|
| `lire_brut()` | Valeur brute 0–65535 |
| `lire_pourcentage()` | Luminosité de 0 % (sombre) à 100 % (très lumineux) |
| `est_sombre(seuil_pct)` | `True` si en dessous du seuil |

---

### `ble_app.py` — la télécommande Bluetooth

Ce fichier gère toute la communication Bluetooth BLE entre ton téléphone et le robot.

**Principe :**  
Le Pico W se publie sur le réseau Bluetooth sous le nom `UART-VAQ` (modifiable dans `config.py`). Quand ton téléphone envoie un message texte, la méthode `_on_reception()` est appelée automatiquement.

#### Décodage des commandes

Le message reçu est d'abord nettoyé (suppression des caractères nuls, des espaces), puis analysé :

| Type de message reçu | Exemple | Action |
|---|---|---|
| Commande stop | `O`, `S`, `X` | Arrêt immédiat des moteurs |
| Direction + puissance | `H:0.8` | Avancer à 80 % |
| Lettre seule | `G` | Pivot gauche à la dernière puissance connue |
| Nombre seul | `0.6` | Mise à jour de la puissance sans changer la direction |
| `0` ou `0.0` | — | Arrêt (puissance nulle) |
| `AUTO` | — | Active le pilote automatique |
| `MANUEL` | — | Désactive le pilote automatique |
| `1` | — | Démarre le point d'accès Wi-Fi et le serveur de logs |
| `4` | — | Coupe le point d'accès Wi-Fi |

#### Méthode `tick()`

Appelée toutes les 50 ms depuis `main.py`. Elle délègue au serveur Wi-Fi la vérification des connexions HTTP entrantes — sans jamais bloquer le Bluetooth.

---

### `mode_auto.py` — le pilote automatique

Ce fichier implémente le comportement autonome du robot sous forme d'une **machine à états** : le robot est toujours dans l'un des trois états suivants.

```
ARRÊT ──► SUIVI ──────────────► SUIVI
               └──► ÉVITEMENT ──┘
```

#### État ARRÊT

Les moteurs sont éteints. Les commandes BLE manuelles fonctionnent normalement. C'est l'état par défaut au démarrage.

#### État SUIVI (suivi de lumière)

Le robot cherche la lumière grâce aux deux LDR (gauche et droite) :

- Si la LDR gauche reçoit plus de lumière → le robot pivote à gauche
- Si la LDR droite reçoit plus de lumière → le robot pivote à droite
- Si les deux sont équilibrées (écart < `AUTO_SEUIL_DIFF_LDR`) → le robot avance tout droit

En priorité, avant chaque mouvement, il vérifie si un obstacle est présent. Si oui → passage en ÉVITEMENT.

#### État ÉVITEMENT

Manœuvre en deux phases chronométrées :

| Phase | Durée | Action |
|---|---|---|
| **Recul** | `AUTO_DUREE_RECUL_MS` (500 ms) | Le robot recule pour s'éloigner de l'obstacle |
| **Pivot** | `AUTO_DUREE_PIVOT_MS` (600 ms) | Le robot pivote vers le côté le plus éclairé |

Après le pivot, le robot repasse automatiquement en SUIVI.

> **Pourquoi pivoter vers le côté le plus éclairé ?** L'obstacle bloque souvent la lumière d'un côté. En pivotant vers la lumière, le robot s'éloigne naturellement de l'obstacle et retrouve sa cible.

---

### `wifi_server.py` — le journal de bord Wi-Fi

Ce fichier permet de **suivre en temps réel ce que fait le robot** depuis n'importe quel téléphone ou ordinateur connecté au réseau Wi-Fi du robot.

#### Fonction `log(msg)`

Remplace `print()` dans tout le projet. Elle fait deux choses à la fois :
1. Affiche le message dans la console (câble USB)
2. Le stocke dans un buffer interne pour le serveur web

#### Classe `WifiServer`

##### Comment ça marche côté réseau

Quand tu envoies `1` via BLE :

1. Le Pico W crée un **point d'accès Wi-Fi** (comme une box Internet miniature)
2. Il démarre un **mini serveur web** sur le port 80
3. Ton téléphone/PC peut se connecter à ce réseau et ouvrir `http://192.168.4.1`

##### Comment ça marche côté logs (mode incrémental)

Au lieu de recharger toute la page toutes les 3 secondes (ce qui causerait des coupures), le système fonctionne ainsi :

1. La page HTML est chargée **une seule fois** par le navigateur
2. Un script JavaScript tourne en arrière-plan et interroge `/logs?depuis=N` toutes les 3 secondes
3. Le serveur répond **uniquement avec les nouvelles lignes** apparues depuis la dernière demande
4. Le JavaScript les ajoute en bas de la liste, sans recharger la page

Chaque ligne de log a un **numéro absolu** (`_total`). Le navigateur retient le dernier numéro reçu (`depuis`) et ne demande que la suite. Même si le buffer interne se tronque au bout de 500 lignes, le numérotage reste cohérent.

##### Pourquoi ça ne perturbe pas le Bluetooth

La méthode `tick()` est conçue pour **ne jamais bloquer** :
- Si aucun navigateur n'est connecté → elle retourne immédiatement (en moins d'une microseconde)
- Si un navigateur est connecté → elle lit la requête en 50 ms max, envoie la réponse en 500 ms max, puis rend la main
- La boucle BLE continue de tourner normalement pendant ce temps

| Méthode | Rôle |
|---|---|
| `demarrer()` | Crée le point d'accès Wi-Fi et ouvre le port 80 |
| `arreter()` | Coupe le Wi-Fi et libère le port 80 |
| `tick()` | Traite une connexion HTTP si elle attend (non-bloquant) |

---

## Protocole BLE

Le robot se publie sous le nom **`UART-VAQ`** (modifiable dans `config.py`).

### Commandes envoyées vers le robot

| Commande | Action |
|---|---|
| `H:0.8` | Avancer à 80 % de puissance |
| `B:0.5` | Reculer à 50 % de puissance |
| `G:1.0` | Pivot gauche pleine puissance |
| `D:1.0` | Pivot droite pleine puissance |
| `H`, `B`, `G`, `D` | Direction à la dernière puissance connue |
| `0.6` | Changer la puissance sans changer la direction |
| `O` / `S` / `X` | Stop |
| `AUTO` | Activer le pilote automatique |
| `MANUEL` | Désactiver le pilote automatique |
| `1` | Démarrer le point d'accès Wi-Fi et le serveur de logs |
| `4` | Couper le point d'accès Wi-Fi |

> En mode autonome, seules les commandes `MANUEL`, `O`, `S`, `X` sont acceptées. Les commandes de direction sont ignorées.

### Messages envoyés par le robot

| Message | Signification |
|---|---|
| `PRET:MOTEUR` | Connexion établie, moteurs opérationnels |
| `PRET:BLE` | Connexion établie, moteurs absents |
| `MODE:AUTO` | Pilote automatique activé |
| `MODE:MANUEL` | Pilote automatique désactivé |
| `OBSTACLE:<dist>` | Obstacle détecté à `<dist>` cm |
| `SOMBRE:<g>/<d>` | Luminosité faible (gauche / droite en %) |
| `WIFI:OK` | Point d'accès Wi-Fi démarré |
| `WIFI:OFF` | Point d'accès Wi-Fi coupé |

---

## Serveur de logs Wi-Fi

### Démarrage

Envoie `1` via BLE. Le robot répond `WIFI:OK` et affiche dans les logs :

```
[WiFi] AP : Robot-A3F2  |  MDP : robot1234  |  IP : 192.168.4.1
[WiFi] Ouvre http://192.168.4.1 pour voir les logs
```

### Connexion

| Paramètre | Valeur |
|---|---|
| SSID | `Robot-XXXX` — les 4 derniers caractères sont uniques à chaque Pico W |
| Mot de passe | `robot1234` |
| Adresse web | `http://192.168.4.1` |

### Ce que tu vois sur la page

- Tous les événements du robot en temps réel (commandes BLE reçues, état des moteurs, obstacles détectés…)
- Mise à jour automatique toutes les **3 secondes** sans rechargement de page
- Les nouvelles lignes s'ajoutent en bas, comme un terminal

### Arrêt

Envoie `4` via BLE. Le réseau Wi-Fi disparaît et le serveur se coupe.

> **Note** : sur Pico W, BLE et Wi-Fi partagent la même puce radio (CYW43). Les deux peuvent fonctionner en même temps, mais une légère interférence est possible selon l'environnement.

---

## Mode autonome

| État | Comportement |
|---|---|
| **SUIVI** | Lecture différentielle des deux LDR. Tourne vers la source lumineuse, avance si la lumière est centrée. Vérifie en priorité la présence d'obstacles. |
| **ÉVITEMENT** | Obstacle détecté. Phase 1 : recul (`AUTO_DUREE_RECUL_MS`). Phase 2 : pivot vers le côté le plus éclairé (`AUTO_DUREE_PIVOT_MS`). Retour automatique en SUIVI. |
| **ARRÊT** | Moteurs coupés. Commandes BLE manuelles actives. |

---

## Configuration (`config.py`)

| Paramètre | Valeur par défaut | Description |
|---|---|---|
| `SEUIL_OBSTACLE_CM` | `20` | Distance (cm) déclenchant l'évitement |
| `SEUIL_SOMBRE_PCT` | `30` | Seuil de luminosité (%) pour l'alerte |
| `AUTO_PUISSANCE_SUIVI` | `0.6` | Puissance moteur en suivi de lumière |
| `AUTO_PUISSANCE_EVIT` | `0.7` | Puissance moteur pendant l'évitement |
| `AUTO_SEUIL_DIFF_LDR` | `5.0` | Écart minimum (%) entre les deux LDR pour tourner |
| `AUTO_DUREE_RECUL_MS` | `500` | Durée de la phase de recul (ms) |
| `AUTO_DUREE_PIVOT_MS` | `600` | Durée de la phase de pivot (ms) |
| `INTERVALLE_CAPTEURS_MS` | `500` | Période de lecture des capteurs (ms) |
| `BLE_NOM` | `"UART-VAQ"` | Nom Bluetooth visible par les appareils |
| `MOTEUR_FREQUENCE` | `1000` | Fréquence PWM des moteurs (Hz) |

---

## Licence

Projet libre — usage éducatif.
