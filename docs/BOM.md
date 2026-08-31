# 📦 BOM — Bill of Materials RATISS-BIOLAB (3 appareils)

Prix estimés en FCFA (TTC import, sourçables Chine/Dubaï/local). Références de
départ — valider disponibilité avant commande. Taux indicatif : 1 USD ≈ 600 FCFA.

**Objectif doctrine : les 3 appareils complets < 150 000 FCFA**, contre
> 5 000 000 FCFA pour l'équivalent commercial.

---

## 🔥 Incubateur cellulaire (37 °C ± 0.1 °C)

| # | Composant | Référence | Qté | PU (FCFA) | Total | Source |
|---|-----------|-----------|:---:|:---:|:---:|--------|
| 1 | ESP32 DevKit | ESP32-WROOM-32 | 1 | 4 000 | 4 000 | Chine/Dubaï |
| 2 | Capteur PT100 + MAX31865 | PT100 classe A | 1 | 6 000 | 6 000 | Chine |
| 3 | Résistances chauffantes Kapton 12V 50W | flexible | 2 | 3 000 | 6 000 | Chine |
| 4 | MOSFET + driver (PWM chauffage) | IRLZ44N | 2 | 1 000 | 2 000 | local |
| 5 | Mousse polyuréthane 50×50 cm, 5 cm | haute densité | 4 | 3 500 | 14 000 | local |
| 6 | Caisse/boîtier + porte vitrée | contreplaqué + verre | 1 | 12 000 | 12 000 | local |
| 7 | Ventilateur 12V (brassage air) | 80 mm | 1 | 2 500 | 2 500 | local |
| 8 | Fusible thermique 42 °C (sécurité) | coupure matérielle | 1 | 800 | 800 | Chine |
| 9 | Câblage, borniers, visserie | | 1 | 4 000 | 4 000 | local |
| 10 | Alimentation 12V 10A | Mean Well ou clone | 1 | 8 000 | 8 000 | Dubaï |

**Sous-total incubateur : ~59 300 FCFA**

---

## 🌡️ Thermocycleur PCR (Peltier)

| # | Composant | Référence | Qté | PU (FCFA) | Total | Source |
|---|-----------|-----------|:---:|:---:|:---:|--------|
| 1 | Module Peltier TEC1-12706 | 60 W | 4 | 2 500 | 10 000 | Chine |
| 2 | Bloc aluminium usiné (puits PCR) | sur mesure local | 1 | 15 000 | 15 000 | local (ENSPY) |
| 3 | Dissipateur + ventilateur CPU | standard | 2 | 4 000 | 8 000 | local |
| 4 | Pont H (inversion polarité) | BTS7960 43A | 2 | 3 500 | 7 000 | Chine |
| 5 | Thermistance NTC 100k (précision) | + carte conditionnement | 2 | 1 500 | 3 000 | Chine |
| 6 | Pâte thermique haute performance | Arctic MX-4 | 1 | 4 000 | 4 000 | Dubaï |
| 7 | ESP32 DevKit | partagé possible | 1 | 4 000 | 4 000 | Chine |
| 8 | Alimentation 12V 20A | puissance Peltier | 1 | 12 000 | 12 000 | Dubaï |
| 9 | Fusible thermique 100 °C | sécurité | 1 | 800 | 800 | Chine |
| 10 | Boîtier + câblage | | 1 | 6 000 | 6 000 | local |

**Sous-total PCR : ~69 800 FCFA**

---

## 🔆 Spectrophotomètre UV/Visible (Beer-Lambert)

| # | Composant | Référence | Qté | PU (FCFA) | Total | Source |
|---|-----------|-----------|:---:|:---:|:---:|--------|
| 1 | Capteur spectral AS7341 | 11 canaux | 1 | 8 000 | 8 000 | Chine |
| 2 | LED UV 280 nm (ou blanche + filtre) | haute puissance | 1 | 5 000 | 5 000 | Chine |
| 3 | Porte-cuve 1 cm | quartz ou optique | 2 | 3 000 | 6 000 | Chine |
| 4 | Boîtier imprimé 3D noir mat | anti-réflexion | 1 | 3 000 | 3 000 | local (impression) |
| 5 | ESP32 ou Arduino Nano | lecture + affichage | 1 | 4 000 | 4 000 | Chine |
| 6 | Écran OLED 0.96" | SSD1306 | 1 | 2 500 | 2 500 | Chine |
| 7 | Standards de calibration | solutions colorées | 1 | 5 000 | 5 000 | local (bio) |
| 8 | Câblage, connecteurs | | 1 | 2 500 | 2 500 | local |

**Sous-total spectro : ~36 000 FCFA**

---

## 💰 Total projet

| Appareil | Coût (FCFA) |
|----------|:---:|
| Incubateur | ~59 300 |
| Thermocycleur PCR | ~69 800 |
| Spectrophotomètre | ~36 000 |
| **TOTAL (3 appareils)** | **~165 100** |

> ⚠️ Objectif doctrine < 150 000 FCFA. Optimisations possibles : un seul ESP32
> partagé entre appareils pendant le prototypage, récupération de dissipateurs
> CPU, caisses en récup. Budget réaliste avec marge : **~180 000 FCFA**, soit
> **< 4 % du prix commercial équivalent**.

---

*RATIS Labs · Cameroun — Sourçage local et régional privilégié.*
