# 🧬 RATISS-BIOLAB — DOCUMENT DE CONCEPTION COMPLET

<div align="center">

![RATIS Labs](docs/images/07_logo_ratis_labs.png)

**Le laboratoire biochimique low-cost souverain — Priorité 2 de la doctrine RATISS**

Manuel d'ingénierie complet : physique, conception, simulation, itérations.

*RATIS Labs · Cameroun · Propriété : JOHNKING0 & Jonathan Evina · ORCID 0009-0000-4092-5313*

</div>

---

> 🇨🇲 **Un mot au Gouvernement de la République du Cameroun**
>
> Nos chercheurs tiennent entre leurs mains des séquences prometteuses — SIRT6,
> Prestin, CIRBP — mais ne peuvent les tester, faute d'équipements qui coûtent
> des millions et se réparent à l'étranger. Ce verrou matériel est une fausse
> fatalité. RATISS-BIOLAB démontre que l'incubateur, le thermocycleur et le
> spectrophotomètre peuvent être conçus, simulés et assemblés par nos propres
> ingénieurs, pour le prix d'une moto. Ce document est un manuel de fabrication
> national : il rend la recherche biochimique camerounaise autonome. **La
> souveraineté scientifique n'attend pas : elle se construit.**

---

## 📑 Table des matières

1. [Vue d'ensemble et philosophie](#1-vue-densemble)
2. [Le problème : l'otage de l'équipement](#2-le-problème)
3. [Conception de l'incubateur cellulaire](#3-lincubateur-cellulaire)
4. [Conception du thermocycleur PCR](#4-le-thermocycleur-pcr)
5. [Conception du spectrophotomètre](#5-le-spectrophotomètre)
6. [Les appareils une fois montés](#6-les-appareils-montés)
7. [Le simulateur : architecture du code](#7-le-simulateur)
8. [Validation mathématique et physique](#8-validation)
9. [Guide de montage](#9-guide-de-montage)
10. [Itérations de conception](#10-itérations)
11. [Sécurité](#11-sécurité)
12. [Feuille de route](#12-feuille-de-route)

---

## 1. Vue d'ensemble

RATISS-BIOLAB est un **laboratoire biochimique complet low-cost**, conçu selon
la méthode transdisciplinaire RATISS : **simuler d'abord, assembler ensuite,
recalibrer toujours**. Trois appareils complémentaires :

| Appareil | Fonction | Cible |
|----------|----------|-------|
| Incubateur | culture cellulaire | 37.0 °C ± 0.1 °C |
| Thermocycleur PCR | amplification ADN | cycles 95/55/72 °C |
| Spectrophotomètre | dosage protéines | A280 (Beer-Lambert) |

Ensemble, ils permettent de **tester physiquement les cibles RATISS** (SIRT6,
Prestin, CIRBP) — cultiver les cellules, amplifier l'ADN, doser les protéines —
sans aucun équipement importé.

---

## 2. Le problème

Les machines de laboratoire standard sont des **boîtes noires hyper-facturées** :
- incubateur CO2 : 3–15 millions FCFA,
- thermocycleur PCR : 2–10 millions FCFA,
- spectrophotomètre : 2–8 millions FCFA.

Impossibles à réparer localement, dépendantes de pièces détachées introuvables,
soumises aux délais d'import. **La recherche camerounaise est prise en otage.**

La rupture RATISS : la **simulation compense l'absence d'équipement**. On
modélise la physique, on valide le régulateur et l'optique in silico, puis on
assemble avec des composants low-cost et on recalibre sur la mesure réelle.

---

## 3. L'incubateur cellulaire

![Plan incubateur](docs/images/01_plan_incubateur.png)

### Principe physique

L'enceinte isolée (mousse PU 5 cm) limite les fuites thermiques à **~0.8 W**
pour tenir 37 °C dans une ambiante à 35 °C (loi de Fourier, voir
`docs/PHYSICS.md`). Une résistance Kapton de 50 W est donc largement
suffisante — le défi n'est pas la puissance, mais la **stabilité**.

### La régulation PID

Le maintien à ±0.1 °C exige une régulation fine. Le régulateur **PID discret
avec anti-windup** (validé en simulation) ajuste la puissance en continu :

```
u[k] = Kp·e[k] + Ki·Σe·dt + Kd·de/dt
```

- `Kp` réagit à l'écart instantané,
- `Ki` élimine l'erreur résiduelle (le "offset" thermique),
- `Kd` anticipe les variations (évite le dépassement).

Résultat de simulation : **erreur RMS 9 mK, écart-type 9 mK** — bien sous la
tolérance biologique de ±0.1 °C.

### Choix de conception

| Choix | Justification |
|-------|--------------|
| Mousse PU 5 cm (λ=0.024) | Isole si bien que ~1 W suffit → faible puissance, faible bruit thermique |
| Résistances Kapton | Chauffage flexible, uniforme, pilotable en PWM |
| Capteur PT100 | Précision médicale (±0.1 °C), stable dans le temps |
| Ventilateur de brassage | Homogénéise l'air — sans lui, gradient vertical > 0.5 °C |
| Fusible thermique 42 °C | Sécurité **matérielle**, indépendante du logiciel |

---

## 4. Le thermocycleur PCR

![Plan PCR](docs/images/02_plan_pcr.png)

### Principe physique

La PCR exige des **cycles thermiques rapides** : dénaturation 95 °C, hybridation
~55 °C, élongation 72 °C, répétés 25-35 fois. Le défi : chauffer et refroidir
vite, uniformément, sans dépassement.

### Les modules Peltier

Un module Peltier **pompe la chaleur dans les deux sens** selon la polarité du
courant — il chauffe OU refroidit. C'est l'actionneur idéal pour un
thermocycleur. Avec 4 modules TEC1-12706 (240 W) sur un bloc alu de 200 g :

```
rampe_max = P / C = 240 W / 179 J/K ≈ 1.3 °C/s
```

C'est la **limite physique dure** — réaliste pour un low-cost (les commerciaux
font 3-5 °C/s avec plus de puissance et des blocs plus légers).

### Le contrôle prédictif

L'inertie thermique du bloc fait que la température continue de monter après
coupure — d'où un risque de dépassement. Le contrôle **prédictif (MPC)** ou un
PID bien réglé anticipe cette inertie pour des rampes nettes.

### Homogénéité inter-puits

L'aluminium (λ=167 W/m·K) diffuse la chaleur uniformément → tous les puits à la
même température à **±0.5 °C**. C'est vital : un puits plus froid amplifierait
moins, faussant la PCR quantitative.

---

## 5. Le spectrophotomètre

### La loi de Beer-Lambert

```
A(λ) = ε(λ) · c · ℓ
```

On dose les protéines à **280 nm** (absorption des aromatiques Trp/Tyr). Le
coefficient d'extinction ε280 se prédit à partir de la séquence (formule de
Pace, voir `docs/PHYSICS.md`).

### Le défi low-cost

Un capteur RGB bon marché (TCS34725, AS7341) a un bruit de ~2 %, un offset de
noir et une dérive thermique. Sans correction, il est inutilisable. La solution
RATISS :

1. **Calibration 2 points** (blanc + noir) → corrige offset et dérive.
2. **Moyennage ×16** → réduit le bruit en 1/√16 = 4× (théorème central limite).

Résultat de simulation Monte Carlo : **erreur < 5 % pour la gamme de travail
(≥ 5 µM)** — suffisant pour le dosage de paillasse. Aux très faibles
concentrations (< 5 µM), l'offset domine le signal : il faut mesurer plus
concentré.

![Spectres](docs/images/05_spectres_proteines.png)

![Erreur spectro](docs/images/06_erreur_spectro.png)

---

## 6. Les appareils montés

![Appareils](docs/images/03_appareils_montes.png)

Les trois appareils sont des **boîtiers de paillasse** avec affichage temps
réel : l'incubateur affiche 37.0 °C, le PCR son cycle courant, le spectro
l'absorbance et la concentration déduite. Aucun n'est une salle blanche —
ils tiennent sur une table de laboratoire.

---

## 7. Le simulateur

| Module | Rôle | Classe/fonction clé |
|--------|------|---------------------|
| `thermal.py` | Incubateur + PCR, régulation | `Incubator`, `PCRBlock`, `PID` |
| `optics.py` | Spectrophotomètre, Beer-Lambert | `ProteinTarget`, `LowCostSpectrometer` |
| `firmware/main.py` | ESP32 MicroPython | `IncubatorController`, `PCRController` |
| `scripts/generate_figures.py` | 7 figures | plans, appareils, courbes, logo |
| `scripts/validate_physics.py` | Validation croisée | recalcul indépendant |

Le firmware MicroPython utilise **la même loi PID que le simulateur** — on flash
la logique prouvée, le hardware n'a qu'à suivre. Un test (`test_pid_mirror`)
vérifie que le PID du firmware produit exactement la même sortie que celui du
simulateur pour les mêmes entrées.

---

## 8. Validation

L'outil `scripts/validate_physics.py` **recalcule indépendamment** chaque
résultat et le confronte à des références peer-reviewed :

```
PYTHONPATH=. python scripts/validate_physics.py
→ 8/8 validations réussies ✅
```

- Bilan thermique : numérique (ODE) vs analytique (Fourier) — coïncidence exacte.
- Capacité thermique alu : m·c_p = 179 J/K (CRC Handbook).
- Beer-Lambert : réversibilité A↔c exacte.
- ε280 : dans la gamme publiée (Pace 1995).
- Moyennage : réduction du bruit en 1/√N confirmée par Monte Carlo.

**Le simulateur ne s'auto-valide pas** — chaque résultat est croisé avec une
méthode indépendante ou une référence externe.

---

## 9. Guide de montage

> 📖 **Guide d'assemblage détaillé et exécutable → [docs/ASSEMBLY.md](docs/ASSEMBLY.md)**
> 📦 **Liste de matériel (~165 k FCFA) → [docs/BOM.md](docs/BOM.md)**

Résumé : construire la caisse isolée, câbler le chauffage + capteur + fusible
de sécurité, flasher le firmware, valider la température, recalibrer le modèle.
Chaque appareil suit la boucle **Simuler → Assembler → Mesurer → Recalibrer**.

---

## 10. Itérations

### Itération 1 : le PID sans anti-windup dépasse
- **Problème** : à la montée initiale, l'intégrale s'accumule et fait dépasser
  la consigne de plusieurs degrés.
- **Solution** : anti-windup (bornage de l'intégrale). Leçon : **le dépassement
  thermique tue les cellules — l'anti-windup n'est pas optionnel**.

### Itération 2 : le bloc PCR chauffait trop lentement
- **Problème** : avec 2 Peltier, la rampe était trop lente pour atteindre 95 °C
  en un cycle.
- **Solution** : 4 modules (240 W) → rampe 1.3 °C/s. Leçon : **la limite
  physique P/C dicte le dimensionnement — la simulation la révèle avant achat**.

### Itération 3 : le spectro surestimait aux faibles concentrations
- **Problème** : l'offset d'absorbance dominait le signal < 5 µM (> 20 % d'erreur).
- **Solution** : calibration 2 points + honnêteté sur la gamme de travail
  (≥ 5 µM). Leçon : **connaître et documenter les limites de son instrument**.

---

## 11. Sécurité

| Danger | Mitigation |
|--------|-----------|
| Surchauffe incubateur (tue les cellules) | Fusible thermique **matériel** 42 °C |
| Surchauffe PCR (ébullition, Peltier) | Fusible thermique **matériel** 100 °C |
| UV 280 nm (lésions oculaires) | Boîtier fermé, jamais regarder la LED |
| Peltier sans dissipation (grille) | Dissipateur + ventilo obligatoires |

**La sécurité thermique est matérielle, jamais seulement logicielle.**

---

## 12. Feuille de route

| Phase | Statut | Livrable |
|-------|:------:|----------|
| 1 — Simulateur thermique + optique | ✅ FAIT | 19/19 tests, 8/8 validations |
| 2 — Firmware ESP32 | ✅ FAIT | PID incubateur + cycles PCR |
| 3 — Documentation + validation | ✅ FAIT | DESIGN, BOM, ASSEMBLY, PHYSICS |
| 4 — Prototype physique | 🔜 À FAIRE | Assembler les 3 appareils, recalibrer |
| 5 — Tests sur cibles RATISS | 🔮 FUTUR | SIRT6, Prestin, CIRBP mesurées |

---

<div align="center">

**RATIS Labs · Cameroun** — *Toujours itérer, jamais figé. Prouver, pas prétendre.* 🦇🧬

![RATIS Labs](docs/images/07_logo_ratis_labs.png)

</div>
