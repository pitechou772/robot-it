"""
Test unitaire : capteurs de luminosite (LDR gauche et droite).
Verifie que les valeurs ADC sont dans la plage 0-100 % et coherentes.
Couvre la LDR gauche (ADC0=GP26) et droite (ADC1=GP27).
"""
import sys
sys.path.insert(0, "..")

from time import sleep
from capteur import CapteurLuminosite
import config

def ok(msg):  print("[OK]  " + msg)
def ko(msg):  print("[KO]  " + msg)

def tester_ldr(ldr, nom, pin):
    print("--- {} (GP{}) ---".format(nom, pin))
    erreurs = 0
    for i in range(8):
        brut = ldr.lire_brut()
        pct  = ldr.lire_pourcentage()
        sombre = ldr.est_sombre(config.SEUIL_SOMBRE_PCT)
        print("  {} : brut={} pct={:.1f}% sombre={}".format(i + 1, brut, pct, sombre))
        if not (0 <= pct <= 100):
            ko("Valeur hors plage : {}%".format(pct))
            erreurs += 1
        sleep(0.2)
    if erreurs == 0:
        ok("{} OK (toutes les valeurs dans 0-100%)".format(nom))
    else:
        ko("{} : {} valeurs hors plage".format(nom, erreurs))

print("=== TEST CAPTEUR LDR ===")

try:
    ldr_g = CapteurLuminosite(config.LUMINOSITE_GAUCHE_ADC)
    ok("LDR gauche creee (GP{})".format(config.LUMINOSITE_GAUCHE_ADC))
except Exception as e:
    ko("LDR gauche : " + str(e))
    ldr_g = None

try:
    ldr_d = CapteurLuminosite(config.LUMINOSITE_DROITE_ADC)
    ok("LDR droite creee (GP{})".format(config.LUMINOSITE_DROITE_ADC))
except Exception as e:
    ko("LDR droite : " + str(e))
    ldr_d = None

if ldr_g:
    tester_ldr(ldr_g, "LDR gauche", config.LUMINOSITE_GAUCHE_ADC)

if ldr_d:
    tester_ldr(ldr_d, "LDR droite", config.LUMINOSITE_DROITE_ADC)

# --- Test differentiel gauche/droite ---
if ldr_g and ldr_d:
    print("--- Differentiel gauche/droite (eclaire un cote a la fois) ---")
    for i in range(5):
        g = ldr_g.lire_pourcentage()
        d = ldr_d.lire_pourcentage()
        diff = g - d
        print("  G={:.1f}%  D={:.1f}%  diff={:.1f}%".format(g, d, diff))
        sleep(0.5)
    ok("Differentiel LDR")

print("=== FIN TEST CAPTEUR LDR ===")
