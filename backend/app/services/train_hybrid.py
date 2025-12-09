import pandas as pd
import numpy as np
import joblib
import pickle
import re
from pathlib import Path

# IA Libs
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Nos outils
from backend.app.utils.math_features import compute_length_norm, compute_diversity, compute_entropy

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parents[3]
PROCESSED_DIR = BASE_DIR / "datasets" / "processed"
MODEL_DIR = BASE_DIR / "backend" / "app" / "models"
DL_DATA_DIR = BASE_DIR / "datasets" / "deep_learning_data"
DICT_DIR = BASE_DIR / "datasets" / "Dictionnaries" / "processed"


def load_base_models():
    print("⏳ Chargement des 6 experts...")
    models = {}

    # --- MACHINE LEARNING ---
    try:
        models['rf'] = joblib.load(MODEL_DIR / "random_forest.pkl")
    except:
        print("⚠️ RF manquant")
    try:
        models['xgb'] = joblib.load(MODEL_DIR / "xgboost.pkl")
    except:
        print("⚠️ XGB manquant")
    try:
        models['log'] = joblib.load(MODEL_DIR / "logistic_regression.pkl")  # AJOUTÉ
    except:
        print("⚠️ LOG manquant")

    # --- DEEP LEARNING ---
    try:
        models['cnn'] = tf.keras.models.load_model(MODEL_DIR / "cnn_scanner.keras")
    except:
        print("⚠️ CNN manquant")
    try:
        models['lstm'] = tf.keras.models.load_model(MODEL_DIR / "lstm_reader.keras")
    except:
        print("⚠️ LSTM manquant")
    try:
        models['dnn'] = tf.keras.models.load_model(MODEL_DIR / "dnn_simple.keras")  # AJOUTÉ
    except:
        print("⚠️ DNN manquant")

    # Tokenizer DL
    with open(DL_DATA_DIR / "tokenizer.pickle", "rb") as f:
        tokenizer = pickle.load(f)
    with open(DL_DATA_DIR / "config.pickle", "rb") as f:
        dl_config = pickle.load(f)

    return models, tokenizer, dl_config


def get_ml_features(df):
    """Recalcule les features pour le ML (RF/XGB/LOG)"""
    try:
        corpus = pd.read_csv(DICT_DIR / "linguistic_dictionary.csv")
        corpus['token'] = corpus['token'].astype(str).str.lower().str.strip()
        words = set(corpus[corpus['category'] == 'word']['token'])
        names = set(corpus[corpus['category'] == 'name']['token'])
        places = set(corpus[corpus['category'] == 'place']['token'])
        weak = set(corpus[corpus['category'] == 'weak_pwd']['token'])
    except:
        print("❌ Erreur Dico")
        return None

    def calc_ling(pwd):
        p = str(pwd).lower()
        cl = re.sub(r'[^a-z]', '', p)
        f = [0, 0, 0, 0]  # weak, word, name, place
        if p in weak: f[0] = 1
        if len(cl) >= 4:
            if cl in words or cl in weak:
                f[1] = 1
            elif cl in names:
                f[2] = 1
            elif cl in places:
                f[3] = 1
        return f

    print("   -> Calcul features ML...")
    ling_data = df['password'].apply(calc_ling).tolist()
    ling_df = pd.DataFrame(ling_data, columns=['is_weak_exact', 'has_word', 'has_name', 'has_place'])
    ling_df.index = df.index  # Alignement index critique

    return pd.concat([df[['length_norm', 'diversity', 'entropy']], ling_df], axis=1)


def get_dl_input(passwords, tokenizer, max_len):
    """Prépare les séquences pour le DL (CNN/LSTM/DNN)"""
    print("   -> Calcul features DL...")
    seq = tokenizer.texts_to_sequences(passwords.astype(str))
    return pad_sequences(seq, maxlen=max_len, padding='post', truncating='post')


def train_hybrid():
    print("--- 🧬 ENTRAÎNEMENT DU MODÈLE HYBRIDE (6 MODÈLES) ---")

    # 1. Données
    df = pd.read_csv(PROCESSED_DIR / "passwords_processed.csv")
    _, df_test = train_test_split(df, test_size=0.2, random_state=42)

    y_true = df_test['label'].values
    passwords = df_test['password']

    # 2. Experts
    models, tokenizer, config = load_base_models()

    # 3. Prédictions
    preds = {}

    # ML
    X_ml = get_ml_features(df_test)
    X_ml = X_ml[['length_norm', 'diversity', 'entropy', 'is_weak_exact', 'has_word', 'has_name', 'has_place']]

    if 'rf' in models: preds['rf'] = models['rf'].predict_proba(X_ml)[:, 1]
    if 'xgb' in models: preds['xgb'] = models['xgb'].predict_proba(X_ml)[:, 1]
    if 'log' in models: preds['log'] = models['log'].predict_proba(X_ml)[:, 1]  # AJOUTÉ

    # DL
    X_dl = get_dl_input(passwords, tokenizer, config['max_len'])
    if 'cnn' in models: preds['cnn'] = models['cnn'].predict(X_dl, verbose=0).flatten()
    if 'lstm' in models: preds['lstm'] = models['lstm'].predict(X_dl, verbose=0).flatten()
    if 'dnn' in models: preds['dnn'] = models['dnn'].predict(X_dl, verbose=0).flatten()  # AJOUTÉ

    # 4. Dataset du Juge (DataFrame avec 6 colonnes si tout va bien)
    X_stack = pd.DataFrame(preds)
    print("\n📊 Aperçu des votes (5 lignes) :")
    print(X_stack.head())

    # 5. Entraînement du Juge
    X_s_train, X_s_test, y_s_train, y_s_test = train_test_split(X_stack, y_true, test_size=0.2, random_state=42)

    meta_model = LogisticRegression()
    meta_model.fit(X_s_train, y_s_train)

    # 6. Évaluation
    final_acc = accuracy_score(y_s_test, meta_model.predict(X_s_test))
    print(f"\n🏆 PERFORMANCE HYBRIDE : {final_acc:.4f}")

    print("   Poids accordés aux experts :")
    # On trie pour voir qui est le chef
    weights = list(zip(X_stack.columns, meta_model.coef_[0]))
    for name, coef in sorted(weights, key=lambda x: x[1], reverse=True):
        print(f"   - {name.upper()}: {coef:.2f}")

    # 7. Sauvegarde
    joblib.dump(meta_model, MODEL_DIR / "hybrid_meta.pkl")
    print(f"\n💾 Sauvegardé : {MODEL_DIR / 'hybrid_meta.pkl'}")


if __name__ == "__main__":
    train_hybrid()