import pandas as pd
import numpy as np
import joblib
import re
from pathlib import Path

# Imports des algorithmes
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Gestion de XGBoost (si pas installé, on ne l'utilise pas)
try:
    from xgboost import XGBClassifier

    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("⚠️ XGBoost n'est pas installé (pip install xgboost). Ce modèle sera ignoré.")

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "datasets"
PROCESSED_DIR = DATA_DIR / "processed"
DICT_DIR = DATA_DIR / "Dictionnaries" / "processed"
MODEL_DIR = BASE_DIR / "backend" / "app" / "models"

# Création du dossier pour sauvegarder les modèles
MODEL_DIR.mkdir(parents=True, exist_ok=True)

LEET_TRANS = str.maketrans({
    '4': 'a', '@': 'a',
    '3': 'e',
    '1': 'i', '!': 'i',
    '0': 'o',
    '5': 's', '$': 's',
    '7': 't', '+': 't'
})


def calculate_linguistic_features(password, dicts):
    """Calcule les features linguistiques (Standard, Inversé et Leet Speak)"""
    words_set, names_set, places_set, weak_set = dicts

    pwd_str = str(password).lower()
    clean_pwd = re.sub(r'[^a-z]', '', pwd_str)
    clean_rev = clean_pwd[::-1]

    unleeted_pwd = pwd_str.translate(LEET_TRANS)
    clean_unleeted = re.sub(r'[^a-z]', '', unleeted_pwd)

    # 5 features strictes
    features = {'is_weak_exact': 0, 'has_word': 0, 'has_name': 0, 'has_place': 0, 'has_leetspeak': 0}

    # 1. Check Leak Exact
    if pwd_str in weak_set or pwd_str[::-1] in weak_set:
        features['is_weak_exact'] = 1

    def check_sets(text):
        found = False
        if len(text) < 4: return False
        if text in words_set or text in weak_set:
            features['has_word'] = 1
            found = True
        elif text in names_set:
            features['has_name'] = 1
            found = True
        elif text in places_set:
            features['has_place'] = 1
            found = True
        return found

    # 2. Check Normal & Inversé
    check_sets(clean_pwd)
    check_sets(clean_rev)

    # 3. Check Leet Speak
    if clean_unleeted != clean_pwd:
        if check_sets(clean_unleeted):
            features['has_leetspeak'] = 1

    return pd.Series(features)

def load_dictionaries():
    """Charge les dictionnaires en mémoire (Sets)"""
    print("Chargement du dictionnaire linguistique...")
    try:
        corpus = pd.read_csv(DICT_DIR / "linguistic_dictionary.csv")
        corpus['token'] = corpus['token'].astype(str).str.lower().str.strip()

        words_set = set(corpus[corpus['category'] == 'word']['token'])
        names_set = set(corpus[corpus['category'] == 'name']['token'])
        places_set = set(corpus[corpus['category'] == 'place']['token'])
        weak_set = set(corpus[corpus['category'] == 'weak_pwd']['token'])

        print(f"-> Dictionnaires chargés : {len(corpus)} entrées.")
        return words_set, names_set, places_set, weak_set
    except FileNotFoundError:
        print("ERREUR CRITIQUE : Dictionnaire introuvable.")
        exit()

def train():
    print("--- 🚀 DÉBUT DE L'ENTRAÎNEMENT MULTI-MODÈLES ---")

    # 1. Chargement des données
    df = pd.read_csv(PROCESSED_DIR / "passwords_processed.csv")
    print(f"Dataset chargé : {len(df)} lignes")

    # 2. Préparation des features
    dicts = load_dictionaries()
    print("Calcul des features linguistiques en cours...")
    linguistic_df = df['password'].apply(lambda x: calculate_linguistic_features(x, dicts))

    # Fusion (Maths + Linguistique)
    X = pd.concat([df[['length_norm', 'diversity', 'entropy']], linguistic_df], axis=1)
    y = df['label']

    # 3. Split Train/Test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Liste des modèles à générer
    models_config = [
        {
            "name": "RandomForest",
            "file": "random_forest.pkl",
            "clf": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        },
        {
            "name": "LogisticRegression",
            "file": "logistic_regression.pkl",
            # max_iter élevé pour être sûr que ça converge
            "clf": LogisticRegression(max_iter=1000, random_state=42)
        }
    ]

    # Ajout de XGBoost si disponible
    if HAS_XGB:
        models_config.append({
            "name": "XGBoost",
            "file": "xgboost.pkl",
            "clf": XGBClassifier(eval_metric='logloss', random_state=42)
        })

    # 5. Boucle d'entraînement
    print(f"\nPréparation de {len(models_config)} modèles...")

    for m in models_config:
        print(f"\n⚡ Entraînement de : {m['name']}...")
        clf = m['clf']

        # Entraînement
        clf.fit(X_train, y_train)

        # Vérification rapide
        acc = accuracy_score(y_test, clf.predict(X_test))
        print(f"   ✅ Précision : {acc:.4f}")

        # Sauvegarde
        save_path = MODEL_DIR / m['file']
        joblib.dump(clf, save_path)
        print(f"   💾 Sauvegardé dans : {save_path}")

    print("\n--- TERMINE ! Tes 3 cerveaux sont prêts dans backend/app/models/ ---")


if __name__ == "__main__":
    train()