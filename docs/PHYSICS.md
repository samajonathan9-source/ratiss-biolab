# 🔬 PHYSICS — Références physiques et mathématiques de RATISS-BIOLAB

Chaque constante et chaque loi utilisée dans le simulateur est sourcée par une
publication ou un manuel de référence peer-reviewed. C'est la garantie que le
simulateur prédit la réalité, pas une fantaisie.

---

## 1. Thermique — Incubateur cellulaire

### Transfert thermique (conduction à travers l'isolant)
La puissance de fuite à travers une paroi plane suit la **loi de Fourier** :

```
P = U · A · ΔT        avec   U = λ / e
```

- `λ` (polyuréthane expansé) = **0.024 W/(m·K)** — valeur typique des mousses PU
  rigides. Source : *Incropera, DeWitt, Bergman, Lavine, "Fundamentals of Heat
  and Mass Transfer", 7ᵉ éd., Wiley (2011)* — Table A.3 (isolants).
- `e` = épaisseur d'isolant (m), `A` = surface d'échange (m²), `ΔT` = écart de
  température (K).

### Capacité thermique de l'air
- `c_p(air)` = **1005 J/(kg·K)** à 300 K.
  Source : *Çengel & Boles, "Thermodynamics: An Engineering Approach", 9ᵉ éd.,
  McGraw-Hill (2019)* — Table A-2.
- `ρ(air)` = **1.18 kg/m³** à 35 °C (loi des gaz parfaits, P=101325 Pa).

### Régulation PID
Forme discrète avec **anti-windup** (bornage de l'intégrale) :

```
u[k] = Kp·e[k] + Ki·Σe·dt + Kd·(e[k]−e[k−1])/dt
```

Source : *Åström & Murray, "Feedback Systems: An Introduction for Scientists
and Engineers", Princeton University Press (2008)* — Chapitre 11 (PID).

---

## 2. Thermique — Thermocycleur PCR

### Capacité thermique du bloc aluminium
- `c_p(aluminium)` = **897 J/(kg·K)** à 300 K.
  Source : *CRC Handbook of Chemistry and Physics, 97ᵉ éd., CRC Press (2016)* —
  Section 4 (constantes des éléments).

### Modules Peltier (TEC1-12706)
- Puissance de pompage thermique max ≈ **60 W** par module (ΔT=0).
- La rampe thermique maximale est limitée par le bilan :

```
rampe_max = P_peltier / C_bloc        [°C/s]
```

Pour 4 modules (240 W) sur un bloc alu de 0.2 kg (C ≈ 179 J/K) : **≈ 1.3 °C/s**.
C'est la limite physique dure — cohérente avec les thermocycleurs low-cost
(les commerciaux atteignent 3–5 °C/s avec des blocs plus légers et plus de
puissance). Source : *Tellurex, "Introduction to Thermoelectrics" (2015)* et
fiches techniques TEC1-12706 (pompage max vs ΔT).

### Profil PCR classique
Dénaturation **95 °C**, hybridation (annealing) **~55 °C**, élongation **72 °C**.
Source : *Mullis & Faloona, "Specific synthesis of DNA in vitro via a
polymerase-catalyzed chain reaction", Methods in Enzymology 155:335 (1987)* —
la publication fondatrice de la PCR.

---

## 3. Optique — Spectrophotométrie UV

### Loi de Beer-Lambert
L'absorbance est proportionnelle à la concentration et au trajet optique :

```
A(λ) = ε(λ) · c · ℓ
```

Source : *Beer, "Bestimmung der Absorption des rothen Lichts in farbigen
Flüssigkeiten", Annalen der Physik 162:78 (1852)* ; formulation moderne dans
*Skoog, Holler & Crouch, "Principles of Instrumental Analysis", 7ᵉ éd.,
Cengage (2017)* — Chapitre 13.

### Dosage des protéines à 280 nm
Le coefficient d'extinction molaire à 280 nm se calcule à partir du contenu en
acides aminés aromatiques :

```
ε280 = 5500·n(Trp) + 1490·n(Tyr) + 125·n(Cys)   [M⁻¹·cm⁻¹]
```

Source : *Pace, Vajdos, Fee, Grimsley & Gray, "How to measure and predict the
molar absorption coefficient of a protein", Protein Science 4:2411 (1995)* —
la référence canonique. Voir aussi *Gill & von Hippel, Analytical Biochemistry
182:319 (1989)*.

Pour nos trois cibles (ordres de grandeur réalistes à partir de leur contenu en
Trp/Tyr) :

| Protéine | ε280 (M⁻¹cm⁻¹) | Masse (Da) | Référence masse |
|----------|:---:|:---:|--------------|
| SIRT6    | 42 000 | 39 100 | Uniprot Q8N6T7 |
| Prestin (SLC26A5) | 81 000 | 81 400 | Uniprot P58743 |
| CIRBP    | 18 000 | 18 700 | Uniprot Q14011 |

> ⚠️ Les ε280 exacts dépendent de la séquence réelle (fichiers FASTA). Ce sont
> des **ordres de grandeur réalistes** — le banc physique les mesurera.

### Bruit de capteur low-cost et moyennage
Un capteur RGB low-cost (TCS34725, AS7341) a un bruit de lecture relatif ~2 %.
Le **moyennage de N mesures indépendantes réduit l'écart-type en 1/√N**
(théorème central limite). Source : *Taylor, "An Introduction to Error
Analysis", 2ᵉ éd., University Science Books (1997)* — Chapitre 4.

La calibration 2 points (blanc + noir) corrige l'offset et la dérive thermique.
Source : *Skoog et al. (2017)*, Chapitre 13 (procédures de calibration).

---

## 4. Sécurité thermique

| Appareil | Limite matérielle | Justification |
|----------|:---:|---------------|
| Incubateur | 42 °C | Au-delà, stress thermique létal des cellules (apoptose). Source : *Freshney, "Culture of Animal Cells", 7ᵉ éd., Wiley (2016)*. |
| Thermocycleur | 100 °C | Au-delà, ébullition des échantillons + dégradation Peltier. |

**Principe de conception** : la coupure de sécurité est **matérielle** (fusible
thermique / relais), pas seulement logicielle. Un software peut planter ; un
fusible thermique, non.

---

## 5. Sources complètes

1. Incropera et al., *Fundamentals of Heat and Mass Transfer*, Wiley (2011).
2. Çengel & Boles, *Thermodynamics: An Engineering Approach*, McGraw-Hill (2019).
3. Åström & Murray, *Feedback Systems*, Princeton UP (2008).
4. *CRC Handbook of Chemistry and Physics*, 97ᵉ éd., CRC Press (2016).
5. Mullis & Faloona, *Methods in Enzymology* 155:335 (1987).
6. Pace et al., *Protein Science* 4:2411 (1995).
7. Gill & von Hippel, *Analytical Biochemistry* 182:319 (1989).
8. Skoog et al., *Principles of Instrumental Analysis*, Cengage (2017).
9. Taylor, *An Introduction to Error Analysis*, Univ. Science Books (1997).
10. Freshney, *Culture of Animal Cells*, Wiley (2016).
11. Tellurex, *Introduction to Thermoelectrics* (2015).

---

*RATIS Labs · Cameroun — Toutes les constantes sont vérifiables dans ces sources.*
