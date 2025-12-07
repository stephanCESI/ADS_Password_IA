import joblib
import pandas as pd
import re
from pathlib import Path
import numpy as np
import traceback
import pickle

# --- GESTION DES DÉPENDANCES LOURDES ---
# On gère le cas où TensorFlow ou XGBoost ne seraient pas installés
try:
    import tensorflow as tf
    from tensorflow.keras.preprocessing.sequence import pad_sequences

    HAS_TF = True
except ImportError:
    HAS_TF = False
    print("⚠️ TensorFlow non trouvé. Les modèles Deep Learning (CNN, LSTM) seront indisponibles.")

try:
    import xgboost
except ImportError:
    pass

# --- IMPORT CALCULS ---
from backend.app.utils.math_features import (
    compute_length_norm, compute_diversity, compute_entropy, calculate_bruteforce_time
)

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_DIR = BASE_DIR / "backend" / "app" / "models"
DL_DATA_DIR = BASE_DIR / "datasets" / "deep_learning_data"
DICT_DIR = BASE_DIR / "datasets" / "Dictionnaries" / "processed"

# --- VARIABLES GLOBALES ---
loaded_ml_models = {}  # Pour RF, XGB, LogReg
loaded_dl_models = {}  # Pour CNN, LSTM, DNN
tokenizer = None  # Pour convertir le texte en chiffres (DL)
dl_config = None  # Pour connaître la taille max (32 chars)
dictionaries = None


def load_resources():
    global loaded_ml_models, loaded_dl_models, tokenizer, dl_config, dictionaries

    # 1. Chargement des Modèles Machine Learning (.pkl)
    ml_files = {
        "rf": "random_forest.pkl",
        "xgb": "xgboost.pkl",
        "log": "logistic_regression.pkl"
    }
    print("--- Chargement ML ---")
    for key, fname in ml_files.items():
        path = MODEL_DIR / fname
        if path.exists():
            try:
                loaded_ml_models[key] = joblib.load(path)
                print(f"✅ ML: {key.upper()} chargé.")
            except:
                print(f"❌ Erreur chargement {fname}")

    # 2. Chargement des Modèles Deep Learning (.keras)
    if HAS_TF:
        print("--- Chargement DL ---")
        dl_files = {
            "cnn": "cnn_scanner.keras",
            "lstm": "lstm_reader.keras",
            "dnn": "dnn_simple.keras"
        }
        for key, fname in dl_files.items():
            path = MODEL_DIR / fname
            if path.exists():
                try:
                    loaded_dl_models[key] = tf.keras.models.load_model(path)
                    print(f"✅ DL: {key.upper()} chargé.")
                except:
                    print(f"❌ Erreur chargement {fname}")

        # Chargement du Tokenizer (Indispensable pour le DL)
        try:
            with open(DL_DATA_DIR / "tokenizer.pickle", "rb") as f:
                tokenizer = pickle.load(f)
            with open(DL_DATA_DIR / "config.pickle", "rb") as f:
                dl_config = pickle.load(f)
            print(f"✅ Tokenizer chargé (Max Len: {dl_config['max_len']})")
        except:
            print("⚠️ Tokenizer introuvable. Le DL ne pourra pas traiter le texte.")

    # 3. Chargement du Dictionnaire Linguistique
    try:
        corpus = pd.read_csv(DICT_DIR / "linguistic_dictionary.csv")
        corpus['token'] = corpus['token'].astype(str).str.lower().str.strip()
        dictionaries = {
            'words': set(corpus[corpus['category'] == 'word']['token']),
            'names': set(corpus[corpus['category'] == 'name']['token']),
            'places': set(corpus[corpus['category'] == 'place']['token']),
            'weak': set(corpus[corpus['category'] == 'weak_pwd']['token'])
        }
        print(f"✅ Dictionnaire chargé : {len(corpus)} entrées.")
    except:
        print("⚠️ Dictionnaire introuvable.")
        dictionaries = None


# On lance tout au démarrage
load_resources()


# --- FONCTIONS UTILITAIRES ---

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
    if re.search(r'123|234|345|321|432|543', password): fb.append("Suite logique")
    return fb


def prepare_dl_input(password):
    """Prépare le mot de passe pour le CNN/LSTM (Tokenization + Padding)"""
    if not tokenizer or not dl_config: return None
    # Transformation en suite de chiffres
    seq = tokenizer.texts_to_sequences([str(password)])
    # Padding pour atteindre 32 caractères (avec des 0)
    padded = pad_sequences(seq, maxlen=dl_config['max_len'], padding='post', truncating='post')
    return padded


# --- FONCTION PRINCIPALE (ROUTAGE) ---

def analyse_password(password: str, model_type: str = "rf"):
    # 1. Calculs classiques (On les fait TOUJOURS pour le feedback et l'entropie)
    entropy = compute_entropy(password)
    length_norm = compute_length_norm(password)
    diversity = compute_diversity(password)
    linguistic = get_linguistic_features(password)
    crack_time = calculate_bruteforce_time(password)

    # 2. Prédiction IA
    ai_prob = 0.0

    # CAS A : Modèle Deep Learning (CNN, LSTM...)
    if model_type in ['cnn', 'lstm', 'dnn']:
        if HAS_TF and model_type in loaded_dl_models:
            try:
                input_data = prepare_dl_input(password)
                if input_data is not None:
                    # Prédiction DL (retourne [[0.998]])
                    ai_prob = float(loaded_dl_models[model_type].predict(input_data, verbose=0)[0][0])
            except Exception as e:
                print(f"❌ Erreur DL ({model_type}): {e}")
        else:
            print(f"⚠️ Modèle DL '{model_type}' non disponible.")

    # CAS B : Modèle Machine Learning Classique (RF, XGB...)
    else:
        # On prépare le DataFrame de features
        features_df = pd.DataFrame([{
            'length_norm': length_norm, 'diversity': diversity, 'entropy': entropy,
            'is_weak_exact': linguistic['is_weak_exact'], 'has_word': linguistic['has_word'],
            'has_name': linguistic['has_name'], 'has_place': linguistic['has_place']}
        ])
        # Ordre forcé
        features_df = features_df[
            ['length_norm', 'diversity', 'entropy', 'is_weak_exact', 'has_word', 'has_name', 'has_place']]

        # On récupère le modèle ML
        model = loaded_ml_models.get(model_type, loaded_ml_models.get('rf'))
        if model:
            try:
                ai_prob = float(model.predict_proba(features_df)[0][1])
            except:
                pass

    # 3. Résultat Final
    score_final = int(ai_prob * 100)
    is_strong = score_final > 50

    # 4. Feedback (Indépendant du modèle, basé sur les règles)
    feedback = []
    if len(password) < 8: feedback.append("Trop court")
    if diversity < 0.5: feedback.append("Manque de variété")
    if linguistic['is_weak_exact']:
        feedback.append("Ce mot de passe est connu des pirates (Leak)")
    else:
        if linguistic['has_name']: feedback.append("Contient un prénom/nom connu")
        if linguistic['has_word']: feedback.append("Contient un mot du dictionnaire")
        if linguistic['has_place']: feedback.append("Contient un nom de lieu")
    feedback.extend(check_patterns(password))

    if score_final > 80 and not feedback: feedback.append("Mot de passe excellent !")

    return {
        "password": password,
        "score": score_final,
        "is_strong": is_strong,
        "model_used": model_type,
        "details": {
            "entropy_bits": int(entropy * 100),
            "crack_time_display": crack_time,
            "ai_probability": round(ai_prob, 4)
        },
        "feedback": feedback
    }