Système Intelligent d'Évaluation de Mots de Passe

> Application de la Démarche Scientifique (ADS) - A4 CESI Ingénieurs

## Contexte du Projet

Ce projet est réalisé dans le cadre de la 4ème année à l’école d’ingénieurs **CESI**, spécialité informatique avec orientation **cybersécurité**.

Il a été motivé par l’observation que les failles liées aux mots de passe restent une cause majeure d’intrusion dans les systèmes d’information. Malgré l’existence d’outils d’évaluation et de générateurs automatiques, de nombreux utilisateurs continuent d’adopter des mots de passe faibles. Les méthodes classiques d’évaluation (basées sur l'entropie mathématique) ne reflètent pas toujours la vulnérabilité réelle face aux techniques modernes de compromission, car elles peinent à détecter les patterns sémantiques ou structurels exploités par les attaquants.

## Problématique

* Les méthodes classiques d’évaluation de mots de passe permettent-elles réellement d’estimer leur robustesse face aux attaques modernes ?
* Un modèle d’apprentissage automatique peut-il mieux prédire la vulnérabilité d’un mot de passe et permettre la création de secrets plus sûrs que les générateurs traditionnels ?

## Description de la Solution

L’objectif est de concevoir un **système d’évaluation intelligent** capable d’attribuer un score de robustesse (0 à 100) en combinant mathématiques et intelligence artificielle.

Contrairement aux validateurs classiques, Cyber Sentry AI utilise une architecture **Hybride (Stacking)** qui fait collaborer 6 modèles d'IA pour détecter trois types de faiblesses :

1. **Faiblesse Mathématique** (Longueur, Diversité, Entropie brute).
2. **Faiblesse Sémantique** (Mots du dictionnaire, Prénoms, Lieux, Leaks connus).
3. **Faiblesse Structurelle** (Suites logiques, Inversions de mots, Répétitions).

Le système intègre également un comparateur de méthodes de génération et un module de simulation d'ingénierie sociale.

## Fonctionnalités Clés

* **Architecture Hybride (Stacking)** : Un "Juge Suprême" (Meta-Modèle de Régression Logistique) pondère les avis de 6 experts :
  * Machine Learning : Random Forest, XGBoost, Logistic Regression.
  * Deep Learning : CNN 1D (Scanner de patterns), LSTM, DNN.
* **Détection Linguistique Avancée** : Repère les mots cachés, les prénoms, les villes et les leaks connus (basé sur le Top 100k RockYou et NCSC). Détecte également les inversions (ex: "drowssap") et le Leet Speak partiel.
* **Mode Duel** : Une interface comparative permettant de visualiser la différence de robustesse entre deux mots de passe.
* **Simulation d'Ingénierie Sociale** : Un module contextuel pour tester la résistance d'un mot de passe face à une attaque ciblée (Nom, Date de naissance, Code postal, Mot-clé).
* **Générateur Quantum** : Un générateur aléatoire (CSPRNG) qui s'auto-corrige en utilisant le Juge IA pour garantir une robustesse supérieure à 95/100.

## Performances et Résultats

Sur le jeu de test (20 000 mots de passe inconnus du modèle), l'architecture Hybride surpasse les modèles individuels en combinant leurs forces :

| Modèle | Accuracy | Point Fort |
| :--- | :--- | :--- |
| **Random Forest** | 98.8% | Règles strictes, Détection dictionnaire |
| **CNN (Deep Learning)** | 99.7% | Détection de patterns subtils (prononçabilité) |
| **Hybride (Stacking)** | **99.82%** | Élimine les faux positifs et combine les approches |

## Installation et Démarrage

### 1. Pré-requis
* Python 3.10 ou supérieur
* Un navigateur web moderne

### 2. Installation
Cloner le projet et installer les dépendances nécessaires :

```bash
git clone [https://github.com/stephanCESI/ADS_Password_IA.git](https://github.com/stephanCESI/ADS_Password_IA.git)
cd ADS_Password_IA
pip install -r requirements.txt
```

(Assurez-vous d'avoir tensorflow, xgboost, scikit-learn, fastapi, uvicorn, pandas, numpy installés)

### 3. Initialisation des Données (Premier lancement)
Le projet nécessite la génération des dictionnaires et l'entraînement des modèles avant de pouvoir fonctionner. Exécutez les scripts dans l'ordre suivant :

```bash
# A. Créer le dictionnaire linguistique (Mots, Leaks, Villes)
python backend/app/utils/dictionary_loader.py

# B. Créer le dataset d'entraînement (50k Forts / 50k Faibles)
python backend/app/utils/dataset_loader.py

# C. Préparer les données Deep Learning (Tokenization)
python backend/app/utils/dl_data_loader.py

# D. Entraîner les modèles ML (Random Forest, XGB...)
python backend/app/services/train_model.py

# E. Entraîner les modèles DL (CNN, LSTM...)
python backend/app/services/train_dl_models.py

# F. Entraîner le Juge Hybride (Stacking)
python backend/app/services/train_hybrid.py
```

### 4. Lancer l'Application
Démarrez le serveur FastAPI :

```bash
uvicorn backend.app.main:app --reload
```

L'interface sera accessible sur : http://127.0.0.1:8000

## Structure Technique

* **`backend/`** : API FastAPI et logique IA
  * `models/` : Fichiers binaires des modèles (.pkl, .keras)
  * `services/` : Scripts d'entraînement et de prédiction
  * `utils/` : Outils de chargement de données, calculs mathématiques et benchmarks
* **`frontend/`** : Interface Web (HTML/CSS/JS Vanilla)
* **`datasets/`** : Données brutes et traitées (RockYou, Dictionnaires)

## Mots-clés :
* Cybersécurité

* Intelligence Artificielle (Machine Learning & Deep Learning)

* Robustesse de mots de passe

* Évaluation & Génération

* Ingénierie Sociale