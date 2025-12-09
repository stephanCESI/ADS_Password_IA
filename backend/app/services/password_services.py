import joblib
import pandas as pd
import re
from pathlib import Path
import numpy as np
import traceback
import pickle

# --- GESTION DES DÉPENDANCES LOURDES ---
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
loaded_ml_models = {}  # RF, XGB, LOG
loaded_dl_models = {}  # CNN, LSTM, DNN
meta_model = None  # Le Juge Hybride
tokenizer = None
dl_config = None
dictionaries = None


def load_resources():
    global loaded_ml_models, loaded_dl_models, meta_model, tokenizer, dl_config, dictionaries

    # 1. Chargement ML (Sklearn/XGB)
    # On gère les noms de fichiers spécifiques
    ml_map = {
        "rf": "random_forest.pkl",
        "xgb": "xgboost.pkl",
        "log": "logistic_regression.pkl"
    }
    print("--- Chargement ML ---")
    for key, fname in ml_map.items():
        if (MODEL_DIR / fname).exists():
            try:
                loaded_ml_models[key] = joblib.load(MODEL_DIR / fname)
                print(f"✅ ML: {key.upper()} chargé.")
            except:
                print(f"❌ Erreur {fname}")

    # 2. Chargement Hybride (Meta-Modèle)
    if (MODEL_DIR / "hybrid_meta.pkl").exists():
        try:
            meta_model = joblib.load(MODEL_DIR / "hybrid_meta.pkl")
            print("✅ HYBRIDE (Juge) chargé.")
        except:
            print("❌ Erreur Hybride")

    # 3. Chargement DL (Keras)
    if HAS_TF:
        print("--- Chargement DL ---")
        dl_files = {
            "cnn": "cnn_scanner.keras",
            "lstm": "lstm_reader.keras",
            "dnn": "dnn_simple.keras"
        }
        for key, fname in dl_files.items():
            if (MODEL_DIR / fname).exists():
                try:
                    loaded_dl_models[key] = tf.keras.models.load_model(MODEL_DIR / fname)
                    print(f"✅ DL: {key.upper()} chargé.")
                except:
                    print(f"❌ Erreur chargement {fname}")

        # Tokenizer
        try:
            with open(DL_DATA_DIR / "tokenizer.pickle", "rb") as f:
                tokenizer = pickle.load(f)
            with open(DL_DATA_DIR / "config.pickle", "rb") as f:
                dl_config = pickle.load(f)
            print(f"✅ Tokenizer chargé (Max Len: {dl_config['max_len']})")
        except:
            print("⚠️ Tokenizer introuvable.")

    # 4. Chargement Dictionnaire
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
        dictionaries = None


# Chargement au démarrage
load_resources()


# --- FONCTIONS UTILITAIRES ---

def get_linguistic_features(password):
    features = {'is_weak_exact': 0, 'has_word': 0, 'has_name': 0, 'has_place': 0}
    if dictionaries is None: return features
    pwd_lower = password.lower()
    clean_pwd = re.sub(r'[^a-z]', '', pwd_lower)
    clean_rev = clean_pwd[::-1]

    # Leak check
    if pwd_lower in dictionaries['weak'] or pwd_lower[::-1] in dictionaries['weak']:
        features['is_weak_exact'] = 1

    if len(clean_pwd) >= 4:
        # Endroit
        if clean_pwd in dictionaries['words'] or clean_pwd in dictionaries['weak']:
            features['has_word'] = 1
        elif clean_pwd in dictionaries['names']:
            features['has_name'] = 1
        elif clean_pwd in dictionaries['places']:
            features['has_place'] = 1

        # Envers
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
    if not tokenizer or not dl_config: return None
    seq = tokenizer.texts_to_sequences([str(password)])
    return pad_sequences(seq, maxlen=dl_config['max_len'], padding='post', truncating='post')


# --- FONCTION PRINCIPALE ---

def analyse_password(password: str, model_type: str = "rf"):
    # 1. Calculs
    entropy = compute_entropy(password)
    length_norm = compute_length_norm(password)
    diversity = compute_diversity(password)
    linguistic = get_linguistic_features(password)
    crack_time = calculate_bruteforce_time(password)

    # 2. Prépa ML (Features)
    features_df = pd.DataFrame([{
        'length_norm': length_norm, 'diversity': diversity, 'entropy': entropy,
        'is_weak_exact': linguistic['is_weak_exact'], 'has_word': linguistic['has_word'],
        'has_name': linguistic['has_name'], 'has_place': linguistic['has_place']
    }])
    # Ordre strict
    features_df = features_df[
        ['length_norm', 'diversity', 'entropy', 'is_weak_exact', 'has_word', 'has_name', 'has_place']]

    ai_prob = 0.0

    # --- LOGIQUE DE PRÉDICTION ---

    # CAS 1 : MODE HYBRIDE (Tous les modèles votent)
    if model_type == 'hybrid':
        # On collecte les votes de tout le monde
        votes = {}

        # ML
        for m in ['rf', 'xgb', 'log']:
            votes[m] = 0.0
            if m in loaded_ml_models:
                try:
                    votes[m] = float(loaded_ml_models[m].predict_proba(features_df)[0][1])
                except:
                    pass

        # DL
        dl_in = prepare_dl_input(password)
        for m in ['cnn', 'lstm', 'dnn']:
            votes[m] = 0.0
            if m in loaded_dl_models and dl_in is not None:
                try:
                    votes[m] = float(loaded_dl_models[m].predict(dl_in, verbose=0)[0][0])
                except:
                    pass

        # Le Juge (Meta-Model) décide
        if meta_model:
            # Ordre des colonnes CRITIQUE (doit matcher train_hybrid.py)
            vote_df = pd.DataFrame(
                [[votes['rf'], votes['xgb'], votes['log'], votes['cnn'], votes['lstm'], votes['dnn']]],
                columns=['rf', 'xgb', 'log', 'cnn', 'lstm', 'dnn'])
            try:
                ai_prob = float(meta_model.predict_proba(vote_df)[0][1])
            except:
                ai_prob = votes['rf']  # Fallback sur RF si le juge plante
        else:
            ai_prob = votes['rf']  # Fallback sur RF si pas de juge

    # CAS 2 : Modèle Deep Learning Spécifique
    elif model_type in ['cnn', 'lstm', 'dnn']:
        if model_type in loaded_dl_models:
            dlin = prepare_dl_input(password)
            if dlin is not None:
                try:
                    ai_prob = float(loaded_dl_models[model_type].predict(dlin, verbose=0)[0][0])
                except:
                    pass

    # CAS 3 : Modèle Machine Learning Spécifique
    else:
        # On récupère le modèle, ou RF par défaut
        mod = loaded_ml_models.get(model_type, loaded_ml_models.get('rf'))
        if mod:
            try:
                ai_prob = float(mod.predict_proba(features_df)[0][1])
            except:
                pass

    # 3. Score Final
    score_final = int(ai_prob * 100)
    is_strong = score_final > 50

    # 4. Feedback
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