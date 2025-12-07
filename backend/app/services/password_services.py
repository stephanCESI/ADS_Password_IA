import joblib
import pandas as pd
import re
from pathlib import Path
import numpy as np
import traceback

# --- IMPORT OBLIGATOIRE POUR XGBOOST ---
try:
    import xgboost
except ImportError:
    pass  # On gère l'erreur plus bas si besoin

# --- IMPORT CENTRALISÉ DES CALCULS ---
from backend.app.utils.math_features import (
    compute_length_norm,
    compute_diversity,
    compute_entropy,
    calculate_bruteforce_time
)

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_DIR = BASE_DIR / "backend" / "app" / "models"
DICT_DIR = BASE_DIR / "datasets" / "Dictionnaries" / "processed"

# --- VARIABLES GLOBALES ---
loaded_models = {}
dictionaries = None


def load_resources():
    """Charge TOUS les modèles disponibles et le dictionnaire"""
    global loaded_models, dictionaries

    # 1. Chargement des Modèles
    model_files = {
        "rf": "random_forest.pkl",
        "xgb": "xgboost.pkl",
        "log": "logistic_regression.pkl"
    }

    print("--- Chargement des Cerveaux IA ---")
    for key, filename in model_files.items():
        path = MODEL_DIR / filename
        if path.exists():
            try:
                loaded_models[key] = joblib.load(path)
                print(f"✅ {key.upper()} chargé.")
            except Exception as e:
                print(f"❌ Erreur chargement {filename}: {e}")
        else:
            print(f"⚠️ Modèle introuvable : {filename}")

    # 2. Chargement du Dictionnaire
    try:
        corpus = pd.read_csv(DICT_DIR / "linguistic_dictionary.csv")
        corpus['token'] = corpus['token'].astype(str).str.lower().str.strip()
        dictionaries = {
            'words': set(corpus[corpus['category'] == 'word']['token']),
            'names': set(corpus[corpus['category'] == 'name']['token']),
            'places': set(corpus[corpus['category'] == 'place']['token']),
            'weak': set(corpus[corpus['category'] == 'weak_pwd']['token'])
        }
        print(f"✅ Dictionnaires chargés : {len(corpus)} entrées.")
    except Exception as e:
        print(f"⚠️ Erreur chargement dictionnaire : {e}")
        dictionaries = None


# Chargement au démarrage
load_resources()


def get_linguistic_features(password):
    features = {'is_weak_exact': 0, 'has_word': 0, 'has_name': 0, 'has_place': 0}
    if dictionaries is None: return features

    pwd_lower = password.lower()
    clean_pwd = re.sub(r'[^a-z]', '', pwd_lower)
    clean_rev = clean_pwd[::-1]

    if pwd_lower in dictionaries['weak'] or pwd_lower[::-1] in dictionaries['weak']:
        features['is_weak_exact'] = 1

    if len(clean_pwd) >= 4:
        if clean_pwd in dictionaries['words'] or clean_pwd in dictionaries['weak']:
            features['has_word'] = 1
        elif clean_pwd in dictionaries['names']:
            features['has_name'] = 1
        elif clean_pwd in dictionaries['places']:
            features['has_place'] = 1
        if clean_rev in dictionaries['words'] or clean_rev in dictionaries['weak']:
            features['has_word'] = 1
        elif clean_rev in dictionaries['names']:
            features['has_name'] = 1
        elif clean_rev in dictionaries['places']:
            features['has_place'] = 1
    return features


def check_patterns(password):
    fb = []
    if re.search(r'(19|20)\d{2}', password): fb.append("Contient une année")
    if re.search(r'(.)\1{2,}', password): fb.append("Caractères répétés")
    if re.search(r'123|234|345|456|567|678|789|321|432|543|654|765|876|987', password):
        fb.append("Suite logique")
    return fb


def analyse_password(password: str, model_type: str = "rf"):
    entropy = compute_entropy(password)
    length_norm = compute_length_norm(password)
    diversity = compute_diversity(password)
    linguistic = get_linguistic_features(password)
    crack_time = calculate_bruteforce_time(password)

    features_df = pd.DataFrame([{
        'length_norm': length_norm, 'diversity': diversity, 'entropy': entropy,
        'is_weak_exact': linguistic['is_weak_exact'], 'has_word': linguistic['has_word'],
        'has_name': linguistic['has_name'], 'has_place': linguistic['has_place']
    }])

    # Ordre forcé pour XGBoost
    features_df = features_df[
        ['length_norm', 'diversity', 'entropy', 'is_weak_exact', 'has_word', 'has_name', 'has_place']]

    selected_model = loaded_models.get(model_type)
    if not selected_model and loaded_models:
        selected_model = list(loaded_models.values())[0]

    score_final = 0
    is_strong = False
    ai_prob = 0.0  # On l'initialise en float standard

    if selected_model:
        try:
            # --- CORRECTION CRITIQUE ICI ---
            # On récupère la valeur brute (qui est peut-être un numpy.float32)
            raw_prob = selected_model.predict_proba(features_df)[0][1]

            # On la convertit EXPLICITEMENT en float Python natif
            ai_prob = float(raw_prob)

            is_strong = bool(ai_prob > 0.5)
            score_final = int(ai_prob * 100)
        except Exception as e:
            print(f"❌ ERREUR PRÉDICTION ({model_type}) : {e}")
            traceback.print_exc()
            score_final = int((entropy * 0.5 + diversity * 0.3 + length_norm * 0.2) * 100)
    else:
        score_final = int((entropy * 0.5 + diversity * 0.3 + length_norm * 0.2) * 100)

    feedback = []
    if len(password) < 8: feedback.append("Trop court")
    if diversity < 0.5: feedback.append("Manque de variété")
    if linguistic['is_weak_exact']:
        feedback.append("Ce mot de passe est connu des pirates (Leak RockYou)")
    else:
        if linguistic['has_name']: feedback.append("Contient un prénom/nom connu")
        if linguistic['has_word']: feedback.append("Contient un mot du dictionnaire")
        if linguistic['has_place']: feedback.append("Contient un nom de ville ou pays")

    feedback.extend(check_patterns(password))
    if score_final > 80 and not feedback:
        feedback.append("Mot de passe excellent !")

    return {
        "password": password,
        "score": score_final,
        "is_strong": is_strong,
        "model_used": model_type,
        "details": {
            "entropy_bits": int(entropy * 100),
            "length": len(password),
            "ai_probability": round(ai_prob, 4),  # Maintenant c'est un float sûr
            "crack_time_display": crack_time
        },
        "feedback": feedback
    }