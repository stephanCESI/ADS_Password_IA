# 🛡️ Système Intelligent d'Évaluation de Mots de Passe

> **Projet ADS (Application de la Démarche Scientifique) — CESI École d'Ingénieurs (A4)**
> Un système hybride combinant Machine Learning et Deep Learning pour surpasser l'entropie mathématique classique.

---

## 🧐 Contexte & Problématique

Ce projet est réalisé dans le cadre de la 4ème année à l'école d'ingénieurs **CESI**. Il part d'un constat critique : les méthodes classiques d'évaluation (basées uniquement sur l'entropie de Shannon) ne reflètent plus la vulnérabilité réelle face aux techniques modernes de compromission (attaques par dictionnaire hybride, règles heuristiques).

**Problématique :**
* Les méthodes classiques permettent-elles réellement d'estimer la robustesse d'un mot de passe ?
* Un modèle d'apprentissage automatique peut-il mieux prédire la "devinabilité" d'un mot de passe et permettre la création de mots de passe plus sûrs ?

---

## ✨ Architecture de la Solution

Le projet repose sur une **Architecture Hybride (Stacking)**. Plutôt que de se fier à un seul algorithme, le système fait collaborer **6 modèles experts** dont les prédictions sont arbitrées par un **Juge Suprême (Méta-modèle)**.

### 1. Experts Machine Learning (ML)
* **Random Forest / XGBoost / Logistic Regression :** Analysent des caractéristiques mathématiques (longueur, diversité) et linguistiques (présence dans des dictionnaires de prénoms, lieux, fuites connues).

### 2. Experts Deep Learning (DL)
* **CNN 1D (Scanner) :** Détecte les motifs spatiaux locaux (ex: suites de touches `qwerty`, `1234`).
* **LSTM (Reader) :** Analyse les dépendances séquentielles à long terme (compréhension de la structure sémantique humaine).

### 3. Le Méta-Modèle (Juge)
Une Régression Logistique pondère les scores de chaque expert pour délivrer une probabilité de robustesse finale sur 100.

---

## 🚀 Fonctionnalités Clés

* **Analyse Heuristique & Linguistique :** Détection du Leet Speak (`P@ssw0rd`), des inversions (`drowssap`) et recherche de substrings dans un dictionnaire de +230 000 tokens.
* **Générateurs CSPRNG (Cryptographically Secure) :**
    * **Mode Diceware :** Pour les Master Passwords (haute entropie, haute mémorisabilité).
    * **Mode Apple-Style :** Pour les comptes tiers (aléatoire pur avec formatage lisible).
* **Simulation d'Attaque Ciblée :** Module de détection d'ingénierie sociale basé sur des données OSINT (Nom, Date de naissance, Code Postal).
* **Mode Duel :** Comparaison interactive de deux mots de passe ou de deux modèles d'IA.

---

## 📊 Performances Techniques

L'architecture hybride atteint une précision quasi parfaite en combinant les forces de chaque approche :

| Modèle | Accuracy (Test) | Point Fort |
| :--- | :--- | :--- |
| **Random Forest** | 99.80% | Détection de dictionnaires & règles strictes |
| **CNN 1D** | 99.77% | Motifs spatiaux (suites logiques) |
| **LSTM** | 99.87% | Structure séquentielle complexe |
| **Hybride (Stacking)** | **99.90%** | **Synthèse et élimination des faux positifs** |

---

## 🛠️ Installation & Entraînement

### 1. Pré-requis
* Python 3.10+
* Pip

### 2. Installation
```bash
git clone [https://github.com/stephanCESI/ADS_Password_IA.git](https://github.com/stephanCESI/ADS_Password_IA.git)
cd ADS_Password_IA
pip install -r requirements.txt
```

### 3. Pipeline d'Entraînement Automatisé
Le projet utilise un orchestrateur unique pour gérer l'échantillonnage (Reservoir Sampling sur +29 millions de fuites), la tokenization et l'entraînement des 7 modèles :

```bash
python backend/app/retrain_all.py
```

### 4. Démarrage du Serveur

```bash
uvicorn backend.app.main:app --reload
```

L'interface est accessible sur : http://127.0.0.1:8000

## 📁 Structure du Projet

```text
ADS_Password_IA/
├── backend/app/
│   ├── models/          # Modèles binaires (.pkl, .keras)
│   ├── routers/         # Endpoints FastAPI
│   ├── services/        # Logique d'inférence et d'entraînement
│   ├── utils/           # Mathématiques, Dataset Loader, Tokenizer
│   └── retrain_all.py   # Orchestrateur du pipeline
├── datasets/
│   ├── raw/             # Fuites brutes (RockYou, Top29M)
│   └── processed/       # Datasets finaux
└── frontend/            # Interface Web (HTML/CSS/JS)
```

## 📚 Bibliographie & Normes
ANSSI : Recommandations relatives à l'authentification par mot de passe (2021).

NIST SP 800-63B : Digital Identity Guidelines.

SecLists (Daniel Miessler) : Source des datasets de fuites de données.