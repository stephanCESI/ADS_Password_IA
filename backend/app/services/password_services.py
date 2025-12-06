import joblib
import pandas as pd
import re
from pathlib import Path
import numpy as np

# --- IMPORT CENTRALISÉ DES CALCULS ---
from backend.app.utils.math_features import (
    compute_length_norm,
    compute_diversity,
    compute_entropy,
    calculate_bruteforce_time
)

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = Path(__file__).resolve().parents[3]

# Choix du modèle (Random Forest est le plus performant ~98.8%)
MODEL_PATH = BASE_DIR / "backend" / "app" / "models" / "random_forest.pkl"
# MODEL_PATH = BASE_DIR / "backend" / "app" / "models" / "xgboost.pkl"
# MODEL_PATH = BASE_DIR / "backend" / "app" / "models" / "logistic_regression.pkl"

DICT_DIR = BASE_DIR / "datasets" / "Dictionnaries" / "processed"

# --- VARIABLES GLOBALES ---
model = None
dictionaries = None


def load_resources():
    """Charge le modèle IA et les dictionnaires en mémoire au démarrage"""
    global model, dictionaries

    # 1. Chargement du Modèle
    if MODEL_PATH.exists():
        model = joblib.load(MODEL_PATH)
        print(f"✅ Modèle IA chargé : {MODEL_PATH.name}")
    else:
        print(f"⚠️ ATTENTION : Modèle introuvable ici : {MODEL_PATH}")
        print("   -> Lance 'train_model.py' pour le générer.")

    # 2. Chargement du Dictionnaire
    try:
        corpus = pd.read_csv(DICT_DIR / "linguistic_dictionary.csv")
        # Nettoyage de sécurité pour être sûr que ça matche
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


# Chargement automatique à l'import du fichier
load_resources()


def get_linguistic_features(password):
    """
    Détecte les motifs linguistiques (Mots, Noms, Leaks).
    Gère le sens normal et inversé (ex: 'drowssap').
    """
    features = {'is_weak_exact': 0, 'has_word': 0, 'has_name': 0, 'has_place': 0}

    if dictionaries is None: return features

    pwd_lower = password.lower()
    clean_pwd = re.sub(r'[^a-z]', '', pwd_lower)  # Garde a-z
    clean_rev = clean_pwd[::-1]  # Inversion

    # 1. Check Leak Exact (Endroit / Envers)
    # Si le mot de passe est dans la liste des 100k leaks
    if pwd_lower in dictionaries['weak'] or pwd_lower[::-1] in dictionaries['weak']:
        features['is_weak_exact'] = 1

    # 2. Check Dictionnaire (Substrings)
    if len(clean_pwd) >= 4:
        # --- Sens Normal ---
        # Si c'est un Leak, ça compte aussi comme un Mot (has_word)
        if clean_pwd in dictionaries['words'] or clean_pwd in dictionaries['weak']:
            features['has_word'] = 1
        elif clean_pwd in dictionaries['names']:
            features['has_name'] = 1
        elif clean_pwd in dictionaries['places']:
            features['has_place'] = 1

        # --- Sens Inversé ---
        if clean_rev in dictionaries['words'] or clean_rev in dictionaries['weak']:
            features['has_word'] = 1
        elif clean_rev in dictionaries['names']:
            features['has_name'] = 1
        elif clean_rev in dictionaries['places']:
            features['has_place'] = 1

    return features


def check_patterns(password):
    """Détecte les motifs Regex (Dates, Répétitions, Suites)"""
    feedback_patterns = []

    # Années (1900-2099)
    if re.search(r'(19|20)\d{2}', password):
        feedback_patterns.append("Contient une année (facile à deviner)")

    # Répétitions (aaa, 111)
    if re.search(r'(.)\1{2,}', password):
        feedback_patterns.append("Contient des caractères répétés")

    # Suites logiques (Endroit et Envers)
    # 123, 234... et 321, 432...
    if re.search(r'123|234|345|456|567|678|789|321|432|543|654|765|876|987', password):
        feedback_patterns.append("Contient une suite logique ou inversée")

    return feedback_patterns


def analyse_password(password: str):
    """Fonction principale appelée par l'API"""

    # 1. Calcul des Features (Maths + Linguistique)
    entropy = compute_entropy(password)
    length_norm = compute_length_norm(password)
    diversity = compute_diversity(password)
    linguistic = get_linguistic_features(password)

    # NOUVEAU : Temps de crack théorique
    crack_time = calculate_bruteforce_time(password)

    # 2. Préparation pour le modèle IA
    # L'ordre des colonnes doit être STRICTEMENT identique à train_model.py
    features_df = pd.DataFrame([{
        'length_norm': length_norm,
        'diversity': diversity,
        'entropy': entropy,
        'is_weak_exact': linguistic['is_weak_exact'],
        'has_word': linguistic['has_word'],
        'has_name': linguistic['has_name'],
        'has_place': linguistic['has_place']
    }])

    # 3. Prédiction IA
    score_final = 0
    is_strong = False
    ai_prob = 0

    if model:
        # On demande la probabilité que ce soit Fort (Classe 1)
        ai_prob = model.predict_proba(features_df)[0][1]
        is_strong = bool(ai_prob > 0.5)
        score_final = int(ai_prob * 100)
    else:
        # Mode dégradé (sans IA)
        score_final = int((entropy * 0.5 + diversity * 0.3 + length_norm * 0.2) * 100)

    # 4. Construction du Feedback
    feedback = []

    # A. Défauts structurels de base
    if len(password) < 8: feedback.append("Trop court")
    if diversity < 0.5: feedback.append("Manque de variété (Maj/Min/Chiffres)")

    # B. Défauts IA / Dictionnaire
    if linguistic['is_weak_exact']:
        feedback.append("Ce mot de passe est connu des pirates (Leak RockYou)")
    else:
        # On affiche les détails seulement si ce n'est pas déjà un leak connu
        if linguistic['has_name']: feedback.append("Contient un prénom/nom connu")
        if linguistic['has_word']: feedback.append("Contient un mot du dictionnaire")
        if linguistic['has_place']: feedback.append("Contient un nom de ville ou pays")

    # C. Patterns Regex
    feedback.extend(check_patterns(password))

    # D. Succès
    if score_final > 80 and not feedback:
        feedback.append("Mot de passe excellent !")

    return {
        "password": password,
        "score": score_final,
        "is_strong": is_strong,
        "details": {
            "entropy_bits": int(entropy * 100),
            "length": len(password),
            "ai_probability": round(ai_prob, 4),
            "crack_time_display": crack_time  # Affiché sur le frontend pour comparer
        },
        "feedback": feedback
    }