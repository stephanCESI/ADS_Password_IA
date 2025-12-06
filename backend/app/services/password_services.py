import joblib
import pandas as pd
import re
from pathlib import Path
import numpy as np

# --- IMPORT CENTRALISÉ DES CALCULS ---
from backend.app.utils.math_features import compute_length_norm, compute_diversity, compute_entropy

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = Path(__file__).resolve().parents[3]
#MODEL_PATH = BASE_DIR / "backend" / "app" / "models" / "logistic_regression.pkl"
MODEL_PATH = BASE_DIR / "backend" / "app" / "models" / "random_forest.pkl"
#MODEL_PATH = BASE_DIR / "backend" / "app" / "models" / "xgboost.pkl"

DICT_DIR = BASE_DIR / "datasets" / "Dictionnaries" / "processed"

# --- VARIABLES GLOBALES ---
model = None
dictionaries = None

def load_resources():
    global model, dictionaries
    if MODEL_PATH.exists():
        model = joblib.load(MODEL_PATH)
        print("✅ Modèle IA chargé avec succès.")
    else:
        print(f"⚠️ ATTENTION : Modèle introuvable ici : {MODEL_PATH}")

    try:
        corpus = pd.read_csv(DICT_DIR / "linguistic_dictionary.csv")
        corpus['token'] = corpus['token'].astype(str).str.lower().str.strip()
        dictionaries = {
            'words': set(corpus[corpus['category'] == 'word']['token']),
            'names': set(corpus[corpus['category'] == 'name']['token']),
            'places': set(corpus[corpus['category'] == 'place']['token']),
            'weak': set(corpus[corpus['category'] == 'weak_pwd']['token'])
        }
        print("✅ Dictionnaires chargés en mémoire.")
    except Exception as e:
        print(f"⚠️ Erreur chargement dictionnaire : {e}")
        dictionaries = None

load_resources()

# Plus de fonctions compute_... locales ici !

def get_linguistic_features(password):
    features = {'is_weak_exact': 0, 'has_word': 0, 'has_name': 0, 'has_place': 0}
    if dictionaries is None: return features

    pwd_lower = password.lower()
    clean_pwd = re.sub(r'[^a-z]', '', pwd_lower)

    if pwd_lower in dictionaries['weak']:
        features['is_weak_exact'] = 1

    if len(clean_pwd) >= 4:
        if clean_pwd in dictionaries['words']: features['has_word'] = 1
        if clean_pwd in dictionaries['names']: features['has_name'] = 1
        if clean_pwd in dictionaries['places']: features['has_place'] = 1
    return features

def analyse_password(password: str):
    # 1. Calcul des Features (via math_features.py)
    entropy = compute_entropy(password)
    length_norm = compute_length_norm(password)
    diversity = compute_diversity(password)
    linguistic = get_linguistic_features(password)

    # 2. Préparation
    features_df = pd.DataFrame([{
        'length_norm': length_norm,
        'diversity': diversity,
        'entropy': entropy,
        'is_weak_exact': linguistic['is_weak_exact'],
        'has_word': linguistic['has_word'],
        'has_name': linguistic['has_name'],
        'has_place': linguistic['has_place']
    }])

    # 3. Prédiction
    score_final = 0
    is_strong = False
    ai_probability = 0

    if model:
        ai_probability = model.predict_proba(features_df)[0][1]
        is_strong = bool(ai_probability > 0.5)
        score_final = int(ai_probability * 100)
    else:
        score_final = int((entropy * 0.5 + diversity * 0.3 + length_norm * 0.2) * 100)

    # 4. Feedback
    feedback = []
    if len(password) < 8: feedback.append("Trop court")
    if diversity < 0.5: feedback.append("Manque de variété (Maj/Min/Chiffres)")
    if linguistic['is_weak_exact']: feedback.append("Ce mot de passe est connu des pirates (Leak RockYou)")
    if linguistic['has_name']: feedback.append("Contient un prénom/nom connu")
    if linguistic['has_word']: feedback.append("Contient un mot du dictionnaire")
    if linguistic['has_place']: feedback.append("Contient un nom de ville ou pays")
    if score_final > 80 and not feedback: feedback.append("Mot de passe excellent !")

    return {
        "password": password,
        "score": score_final,
        "is_strong": is_strong,
        "details": {
            "entropy_bits": int(entropy * 100),
            "length": len(password),
            "ai_probability": round(ai_probability, 4)
        },
        "feedback": feedback
    }