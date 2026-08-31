# 🔧 ASSEMBLY — Guide de montage RATISS-BIOLAB

Document exécutable par un ingénieur mécatronicien (ENSPY, Polytech Yaoundé,
diaspora). Chaque étape est vérifiable. **La sécurité thermique est matérielle
— jamais seulement logicielle.**

---

## ⚠️ Consignes de sécurité (lire AVANT)

- **Fusibles thermiques non négociables** : 42 °C sur l'incubateur, 100 °C sur
  le PCR. Ce sont des coupures **matérielles** (fusible thermique en série sur
  l'alimentation de chauffe), indépendantes du logiciel.
- **Les Peltier chauffent fort côté chaud** : toujours un dissipateur + ventilo,
  jamais à nu. Un Peltier sans dissipation grille en secondes.
- **UV 280 nm** : ne jamais regarder la LED allumée (lésions oculaires/cornée).
  Boîtier fermé en fonctionnement.

---

## 🔥 A. Incubateur cellulaire

### A.1 Caisse isolée
1. Assembler la caisse en contreplaqué (50 L interne).
2. Coller la mousse PU 5 cm sur les 6 faces intérieures — **aucun pont thermique**
   (les joints doivent être recouverts).
3. Installer la porte vitrée avec joint d'étanchéité.
4. **Vérification** : la caisse fermée à 35 °C ambiant ne doit pas perdre plus
   de ~1 °C/h à vide (mesurer avec un thermomètre étalon).

### A.2 Chauffage et capteur
1. Coller les 2 résistances Kapton sur une plaque d'aluminium (diffuseur) au
   fond de l'enceinte.
2. Fixer le ventilateur 80 mm pour brasser l'air (homogénéité ±0.1 °C).
3. Fixer la sonde PT100 à hauteur des cultures (pas contre la paroi).
4. **Vérification** : à 37 °C, deux thermomètres à des endroits opposés doivent
   lire la même température à ±0.2 °C.

### A.3 Électronique
1. Câbler : ESP32 GPIO25 → MOSFET → résistances ; PT100 → MAX31865 → SPI ESP32.
2. Installer le **fusible thermique 42 °C en série** sur l'alimentation de chauffe.
3. Flasher `firmware/main.py` (classe `IncubatorController`).
4. **Vérification (test de sécurité)** : forcer la chauffe → le fusible doit
  couper à 42 °C. **Ne jamais utiliser l'incubateur si ce test échoue.**

### A.4 Validation thermique
1. Lancer, atteindre 37 °C, laisser 1 h.
2. Enregistrer la température 10 min : écart-type < 0.1 °C, erreur < 0.1 °C.
3. Comparer à la prédiction du simulateur (`simulate_incubator`) — l'écart
   recalibre le modèle.

---

## 🌡️ B. Thermocycleur PCR

### B.1 Bloc aluminium
1. Usiner le bloc alu 200 g avec 8-16 puits pour tubes PCR 0.2 mL (ENSPY / CNC).
2. **Vérification** : les tubes doivent entrer avec un léger frottement (contact
   thermique), sans jeu.

### B.2 Empilement thermique
1. Enduire le bloc de pâte thermique, poser les 4 Peltier (côté froid vers bloc).
2. Enduire le côté chaud des Peltier, poser le dissipateur + ventilo.
3. **Serrer uniformément** (pression égale = contact thermique homogène).
4. **Vérification** : pas de jour entre les couches ; le dissipateur doit être
   tiède en fonctionnement, jamais brûlant.

### B.3 Électronique
1. Câbler : ESP32 GPIO26/27 → pont H BTS7960 → Peltier ; NTC → ADC ESP32.
2. Installer le **fusible thermique 100 °C** en série.
3. Flasher `firmware/main.py` (classe `PCRController`).

### B.4 Validation des cycles
1. Lancer un profil [(95, 30), (55, 30), (72, 60)] × 2 cycles.
2. Comparer la trajectoire mesurée à `simulate_pcr_cycle` — recalibrer la
   puissance Peltier réelle dans le modèle.
3. Mesurer l'homogénéité : 2 sondes dans 2 puits extrêmes doivent lire la même
   température à ±0.5 °C.

---

## 🔆 C. Spectrophotomètre

### C.1 Chemin optique
1. Imprimer le boîtier 3D noir mat (anti-réflexion).
2. Aligner : LED 280 nm → porte-cuve → capteur AS7341, tout coaxial.
3. **Vérification** : à vide (cuve d'eau), le capteur doit lire un signal fort
   et stable (pas de scintillement).

### C.2 Calibration
1. **Noir** : mesurer avec lumière éteinte → enregistrer l'offset.
2. **Blanc** : mesurer avec cuve d'eau distillée → référence 100 % transmission.
3. Vérifier la linéarité avec des solutions étalons diluées (loi de Beer-Lambert).

### C.3 Validation sur protéine
1. Mesurer une solution de BSA (ou protéine standard) de concentration connue.
2. Comparer la concentration déduite à la valeur attendue — écart < 5 %.
3. Croiser avec la prédiction du simulateur (`concentration_measurement_error`).

---

## 🔄 Procédure d'itération (boucle RATISS)

```
Simuler → Assembler → Mesurer → Comparer → Recalibrer → Re-simuler
```

Chaque mesure physique recalibre le modèle (constantes thermiques, ε280 réel,
bruit capteur réel). Le simulateur s'améliore à chaque appareil construit.
**Documenter les écarts — ne jamais prétendre une précision non mesurée.**

---

*RATIS Labs · Cameroun — Sécurité d'abord, précision toujours.*
