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

# --- TABLE DE TRADUCTION LEET SPEAK ---
LEET_TRANS = str.maketrans({
    '4': 'a', '@': 'a',
    '3': 'e',
    '1': 'i', '!': 'i',
    '0': 'o',
    '5': 's', '$': 's',
    '7': 't', '+': 't'
})


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
        models['log'] = joblib.load(MODEL_DIR / "logistic_regression.pkl")
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
        models['dnn'] = tf.keras.models.load_model(MODEL_DIR / "dnn_simple.keras")
    except:
        print("⚠️ DNN manquant")

    # Tokenizer DL
    with open(DL_DATA_DIR / "tokenizer.pickle", "rb") as f:
        tokenizer = pickle.load(f)
    with open(DL_DATA_DIR / "config.pickle", "rb") as f:
        dl_config = pickle.load(f)

    return models, tokenizer, dl_config


def get_ml_features(df):
    """Recalcule les features pour le ML (RF/XGB/LOG) - VERSION COMPLÈTE"""
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

        # 1. Nettoyage Standard
        cl = re.sub(r'[^a-z]', '', p)
        # 2. Nettoyage Inversé
        cl_rev = cl[::-1]
        # 3. Nettoyage Leet
        unleeted_pwd = p.translate(LEET_TRANS)
        cl_unleeted = re.sub(r'[^a-z]', '', unleeted_pwd)

        f = [0, 0, 0, 0, 0]  # is_weak, has_word, has_name, has_place, has_leetspeak

        # Check Leak Exact
        if p in weak or p[::-1] in weak: f[0] = 1

        def check_sets(text):
            found = False
            if len(text) < 4: return False
            if text in words or text in weak:
                f[1] = 1;
                found = True
            elif text in names:
                f[2] = 1;
                found = True
            elif text in places:
                f[3] = 1;
                found = True
            return found

        # Check Normal & Inversé
        check_sets(cl)
        check_sets(cl_rev)

        # Check Leet
        if cl_unleeted != cl:
            if check_sets(cl_unleeted):
                f[4] = 1  # has_leetspeak = 1

        return f

    print("   -> Calcul features ML (avec Leet Speak)...")
    ling_data = df['password'].apply(calc_ling).tolist()

    # AJOUT DE 'has_leetspeak'
    ling_df = pd.DataFrame(ling_data, columns=['is_weak_exact', 'has_word', 'has_name', 'has_place', 'has_leetspeak'])
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

    # ML (Calcul des 8 features)
    X_ml = get_ml_features(df_test)
    X_ml = X_ml[
        ['length_norm', 'diversity', 'entropy', 'is_weak_exact', 'has_word', 'has_name', 'has_place', 'has_leetspeak']]

    if 'rf' in models: preds['rf'] = models['rf'].predict_proba(X_ml)[:, 1]
    if 'xgb' in models: preds['xgb'] = models['xgb'].predict_proba(X_ml)[:, 1]
    if 'log' in models: preds['log'] = models['log'].predict_proba(X_ml)[:, 1]

    # DL
    X_dl = get_dl_input(passwords, tokenizer, config['max_len'])
    if 'cnn' in models: preds['cnn'] = models['cnn'].predict(X_dl, verbose=0).flatten()
    if 'lstm' in models: preds['lstm'] = models['lstm'].predict(X_dl, verbose=0).flatten()
    if 'dnn' in models: preds['dnn'] = models['dnn'].predict(X_dl, verbose=0).flatten()

    # 4. Dataset du Juge
    X_stack = pd.DataFrame(preds)
    print("\n📊 Aperçu des votes (5 lignes) :")
    print(X_stack.head())

    # 5. Entraînement du Juge
    X_s_train, X_s_test, y_s_train, y_s_test = train_test_split(X_stack, y_true, test_size=0.2, random_state=42)

    meta_model = LogisticRegression()
    meta_model.fit(X_s_train, y_s_train)

    # 6. Évaluation
    y_pred_hybrid = meta_model.predict(X_s_test)
    final_acc = accuracy_score(y_s_test, y_pred_hybrid)
    print(f"\n🏆 PERFORMANCE HYBRIDE : {final_acc:.4f}")

    print("   Poids accordés aux experts :")
    weights = list(zip(X_stack.columns, meta_model.coef_[0]))
    for name, coef in sorted(weights, key=lambda x: x[1], reverse=True):
        print(f"   - {name.upper()}: {coef:.2f}")

    # 7. Sauvegarde du modèle
    joblib.dump(meta_model, MODEL_DIR / "hybrid_meta.pkl")
    print(f"\n💾 Modèle Sauvegardé : {MODEL_DIR / 'hybrid_meta.pkl'}")

    # ---------------------------------------------------------
    # 8. EXPORT POUR LE JUPYTER NOTEBOOK (Matrices de confusion)
    # ---------------------------------------------------------
    print("💾 Exportation des prédictions pour l'analyse Jupyter...")

    # On arrondit les probabilités du RF pour avoir des classes 0 ou 1
    y_pred_rf = X_s_test['rf'].round().astype(int)

    df_results = pd.DataFrame({
        'y_true': y_s_test,
        'y_pred_rf': y_pred_rf,
        'y_pred_hybrid': y_pred_hybrid
    })

    results_path = PROCESSED_DIR / "test_results_hybrid.csv"
    df_results.to_csv(results_path, index=False)
    print(f"✅ Fichier d'analyse généré : {results_path.name}")

if __name__ == "__main__":
    train_hybrid()