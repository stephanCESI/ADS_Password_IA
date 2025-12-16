import joblib
import pandas as pd
import re
from pathlib import Path
import numpy as np
import traceback
import pickle
import secrets
import string
import time

# --- IMPORT ZXCVBN ---
try:
    from zxcvbn import zxcvbn
except ImportError:
    def zxcvbn(pwd):
        return {'score': 0, 'crack_times_display': {'offline_slow_hashing_1e4_per_second': 'N/A'}}

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
loaded_ml_models = {}
loaded_dl_models = {}
meta_model = None
tokenizer = None
dl_config = None
dictionaries = None

LEET_TRANS = str.maketrans({
    '4': 'a', '@': 'a',
    '3': 'e',
    '1': 'i', '!': 'i',
    '0': 'o',
    '5': 's', '$': 's',
    '7': 't', '+': 't'
})


def load_resources():
    global loaded_ml_models, loaded_dl_models, meta_model, tokenizer, dl_config, dictionaries

    # ML
    ml_map = {"rf": "random_forest.pkl", "xgb": "xgboost.pkl", "log": "logistic_regression.pkl"}
    print("--- Chargement ML ---")
    for key, fname in ml_map.items():
        if (MODEL_DIR / fname).exists():
            try:
                loaded_ml_models[key] = joblib.load(MODEL_DIR / fname)
                print(f"✅ ML: {key.upper()} chargé.")
            except:
                print(f"❌ Erreur {fname}")

    # Hybride
    if (MODEL_DIR / "hybrid_meta.pkl").exists():
        try:
            meta_model = joblib.load(MODEL_DIR / "hybrid_meta.pkl")
            print("✅ HYBRIDE (Juge) chargé.")
        except:
            print("❌ Erreur Hybride")

    # DL
    if HAS_TF:
        print("--- Chargement DL ---")
        dl_files = {"cnn": "cnn_scanner.keras", "lstm": "lstm_reader.keras", "dnn": "dnn_simple.keras"}
        for key, fname in dl_files.items():
            if (MODEL_DIR / fname).exists():
                try:
                    loaded_dl_models[key] = tf.keras.models.load_model(MODEL_DIR / fname)
                    print(f"✅ DL: {key.upper()} chargé.")
                except:
                    print(f"❌ Erreur chargement {fname}")

        try:
            with open(DL_DATA_DIR / "tokenizer.pickle", "rb") as f:
                tokenizer = pickle.load(f)
            with open(DL_DATA_DIR / "config.pickle", "rb") as f:
                dl_config = pickle.load(f)
            print(f"✅ Tokenizer chargé.")
        except:
            print("⚠️ Tokenizer introuvable.")

    # Dico
    try:
        corpus = pd.read_csv(DICT_DIR / "linguistic_dictionary.csv")
        corpus['token'] = corpus['token'].astype(str).str.lower().str.strip()
        dictionaries = {
            'words': set(corpus[corpus['category'] == 'word']['token']),
            'names': set(corpus[corpus['category'] == 'name']['token']),
            'places': set(corpus[corpus['category'] == 'place']['token']),
            'weak': set(corpus[corpus['category'] == 'weak_pwd']['token'])
        }
        print(f"✅ Dictionnaire chargé.")
    except:
        dictionaries = None


load_resources()


# --- FONCTIONS UTILITAIRES ---

def get_linguistic_features(password):
    features = {'is_weak_exact': 0, 'has_word': 0, 'has_name': 0, 'has_place': 0, 'has_leetspeak': 0}
    if dictionaries is None: return features

    pwd_lower = password.lower()

    # 1. Nettoyage Standard
    clean_pwd = re.sub(r'[^a-z]', '', pwd_lower)
    clean_rev = clean_pwd[::-1]

    # 2. Nettoyage Leet (Traduction)
    unleeted_pwd = pwd_lower.translate(LEET_TRANS)
    clean_unleeted = re.sub(r'[^a-z]', '', unleeted_pwd)

    # Check Leak Exact
    if pwd_lower in dictionaries['weak'] or pwd_lower[::-1] in dictionaries['weak']:
        features['is_weak_exact'] = 1

    def check_sets(text):
        found = False
        if len(text) < 4: return False
        if text in dictionaries['words'] or text in dictionaries['weak']:
            features['has_word'] = 1;
            found = True
        elif text in dictionaries['names']:
            features['has_name'] = 1;
            found = True
        elif text in dictionaries['places']:
            features['has_place'] = 1;
            found = True
        return found

    # Check Normal & Inversé
    check_sets(clean_pwd)
    check_sets(clean_rev)

    # Check Leet
    if clean_unleeted != clean_pwd:
        if check_sets(clean_unleeted):
            features['has_leetspeak'] = 1

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


# --- FONCTION D'ANALYSE ---

def analyse_password(password: str, model_type: str = "rf"):
    entropy = compute_entropy(password)
    length_norm = compute_length_norm(password)
    diversity = compute_diversity(password)
    linguistic = get_linguistic_features(password)
    crack_time_maths = calculate_bruteforce_time(password)

    zxcvbn_stats = zxcvbn(password)
    zxcvbn_score = zxcvbn_stats['score']  # 0, 1, 2, 3, 4
    zxcvbn_time = zxcvbn_stats['crack_times_display']['offline_slow_hashing_1e4_per_second']  # Temps estimé humain

    features_df = pd.DataFrame([{
        'length_norm': length_norm, 'diversity': diversity, 'entropy': entropy,
        'is_weak_exact': linguistic['is_weak_exact'], 'has_word': linguistic['has_word'],
        'has_name': linguistic['has_name'], 'has_place': linguistic['has_place'],
        'has_leetspeak': linguistic['has_leetspeak']
    }])
    features_df = features_df[
        ['length_norm', 'diversity', 'entropy', 'is_weak_exact', 'has_word', 'has_name', 'has_place', 'has_leetspeak']]

    ai_prob = 0.0

    if model_type == 'hybrid':
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
        # Juge
        if meta_model:
            vote_df = pd.DataFrame(
                [[votes['rf'], votes['xgb'], votes['log'], votes['cnn'], votes['lstm'], votes['dnn']]],
                columns=['rf', 'xgb', 'log', 'cnn', 'lstm', 'dnn'])
            try:
                ai_prob = float(meta_model.predict_proba(vote_df)[0][1])
            except:
                ai_prob = votes['rf']
        else:
            ai_prob = votes['rf']

    elif model_type in ['cnn', 'lstm', 'dnn']:
        if model_type in loaded_dl_models:
            dlin = prepare_dl_input(password)
            if dlin is not None:
                try:
                    ai_prob = float(loaded_dl_models[model_type].predict(dlin, verbose=0)[0][0])
                except:
                    pass
    else:
        mod = loaded_ml_models.get(model_type, loaded_ml_models.get('rf'))
        if mod:
            try:
                ai_prob = float(mod.predict_proba(features_df)[0][1])
            except:
                pass

    score_final = int(ai_prob * 100)
    is_strong = score_final > 50

    feedback = []
    if len(password) < 8: feedback.append("Trop court")
    if diversity < 0.5: feedback.append("Manque de variété")
    if linguistic['is_weak_exact']:
        feedback.append("Ce mot de passe est connu des pirates (Leak)")
    else:
        if linguistic['has_name']: feedback.append("Contient un prénom/nom connu")
        if linguistic['has_word']: feedback.append("Contient un mot du dictionnaire")
        if linguistic['has_place']: feedback.append("Contient un nom de lieu")
        if linguistic['has_leetspeak']: feedback.append("Détection Leet Speak (Mots déguisés)")

    feedback.extend(check_patterns(password))

    if score_final < 20 and (int(entropy * 100) > 50) and not feedback:
        feedback.append("⚠️ Structure linguistique suspecte détectée par l'IA (Pattern humain implicite)")

    if score_final > 80 and not feedback: feedback.append("Mot de passe excellent !")

    return {
        "password": password,
        "score": score_final,
        "is_strong": is_strong,
        "model_used": model_type,
        "details": {
            "entropy_bits": int(entropy * 100),
            "crack_time_display": crack_time_maths,  # Ton calcul maths
            "zxcvbn_score": zxcvbn_score,  # Score Zxcvbn (0-4)
            "zxcvbn_time": zxcvbn_time,  # Temps Zxcvbn
            "ai_probability": round(ai_prob, 4)
        },
        "feedback": feedback
    }


# --- GÉNÉRATEUR OPTIMISÉ ---

def generate_secure_password():
    alphabet = string.ascii_letters + string.digits + string.punctuation
    attempt = 0
    print("\n--- 🎲 Début Génération 'Ultimate' ---")
    start_time = time.time()

    while True:
        attempt += 1

        # 1. Tirage
        pwd = ''.join(secrets.choice(alphabet) for _ in range(16))

        # 2. Filtres Rapides (CPU)
        if re.search(r'(.)\1', pwd): continue  # Répétition
        if not (any(c.islower() for c in pwd) and any(c.isupper() for c in pwd) and
                any(c.isdigit() for c in pwd) and any(c in string.punctuation for c in pwd)):
            continue  # Diversité

        # 3. Pré-Validation par Random Forest (Ultra-Rapide)
        pre_check = analyse_password(pwd, model_type="rf")
        if pre_check['score'] < 90:
            continue

        # 4. Validation Finale par Hybride (Lent mais précis)
        model_check = 'hybrid' if meta_model else 'rf'

        analysis = analyse_password(pwd, model_type=model_check)
        score = analysis['score']

        feedbacks_str = " | ".join(analysis['feedback']) if analysis['feedback'] else "None"

        print(f"   [Essai {attempt}] Candidat : {pwd[:4]}... -> Juge ({model_check}): {score}/100 | "
              f"Feedbacks: {feedbacks_str}")

        has_negative_feedback = False
        for msg in analysis['feedback']:
            if "excellent" not in msg.lower():
                has_negative_feedback = True
                break

        # Condition : Score excellent ET pas de reproche
        if score >= 90 and not has_negative_feedback:
            duration = time.time() - start_time
            print(f"✅ TROUVÉ en {duration:.2f}s et {attempt} essais !")
            return pwd

        # Sécurité
        if attempt > 200:
            print("⚠️ Trop d'essais, on relâche les critères.")
            return pwd