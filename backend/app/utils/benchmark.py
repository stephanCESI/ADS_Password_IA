import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import time
from pathlib import Path

# Scikit-Learn Metrics
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, roc_curve

# Gestion XGBoost
try:
    from xgboost import XGBClassifier

    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("⚠️ XGBoost non installé.")

# --- IMPORTS PERSO ---
import sys

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR))

from backend.app.utils.math_features import compute_length_norm, compute_diversity, compute_entropy

# --- CONFIGURATION ---
PROCESSED_DIR = BASE_DIR / "datasets" / "processed"
DICT_DIR = BASE_DIR / "datasets" / "Dictionnaries" / "processed"
OUTPUT_IMG_DIR = BASE_DIR  # Racine du projet


def load_data_and_features():
    print("⏳ Chargement des données...")
    if not (PROCESSED_DIR / "passwords_processed.csv").exists():
        raise FileNotFoundError("passwords_processed.csv manquant.")

    df = pd.read_csv(PROCESSED_DIR / "passwords_processed.csv")

    print("⏳ Chargement du dictionnaire...")
    corpus = pd.read_csv(DICT_DIR / "linguistic_dictionary.csv")
    corpus['token'] = corpus['token'].astype(str).str.lower().str.strip()

    words_set = set(corpus[corpus['category'] == 'word']['token'])
    names_set = set(corpus[corpus['category'] == 'name']['token'])
    places_set = set(corpus[corpus['category'] == 'place']['token'])
    weak_set = set(corpus[corpus['category'] == 'weak_pwd']['token'])

    print("⏳ Calcul des features linguistiques (patience)...")

    def get_ling_features(pwd):
        pwd_str = str(pwd).lower()
        clean = re.sub(r'[^a-z]', '', pwd_str)
        rev = clean[::-1]

        # NOTE : On utilise bien 'is_weak_exact' pour être cohérent avec train_model.py
        f = {'is_weak_exact': 0, 'has_word': 0, 'has_name': 0, 'has_place': 0}

        # 1. Leak
        if pwd_str in weak_set or pwd_str[::-1] in weak_set:
            f['is_weak_exact'] = 1

        # 2. Patterns
        if len(clean) >= 4:
            # Endroit
            if clean in words_set or clean in weak_set:
                f['has_word'] = 1
            elif clean in names_set:
                f['has_name'] = 1
            elif clean in places_set:
                f['has_place'] = 1

            # Envers
            if rev in words_set or rev in weak_set:
                f['has_word'] = 1
            elif rev in names_set:
                f['has_name'] = 1
            elif rev in places_set:
                f['has_place'] = 1

        return pd.Series(f)

    ling_df = df['password'].apply(get_ling_features)

    # Fusion finale (Ordre strict)
    X = pd.concat([df[['length_norm', 'diversity', 'entropy']], ling_df], axis=1)
    y = df['label']

    return train_test_split(X, y, test_size=0.2, random_state=42)


def run_benchmark():
    try:
        X_train, X_test, y_train, y_test = load_data_and_features()
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return

    models = [
        ("Random Forest", RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)),
        ("Logistic Regression", LogisticRegression(max_iter=1000, random_state=42))
    ]

    if HAS_XGB:
        models.append(("XGBoost", XGBClassifier(eval_metric='logloss', random_state=42)))

    results = []
    roc_curves = []

    print("\n--- 🏁 DÉBUT DU BENCHMARK ---")

    for name, model in models:
        print(f"\n⚡ Analyse de : {name}...")
        start_time = time.time()
        model.fit(X_train, y_train)
        train_time = time.time() - start_time

        # Scores
        acc_train = accuracy_score(y_train, model.predict(X_train))

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        acc_test = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_proba)

        results.append({
            "Modèle": name, "Train Acc": acc_train, "Test Acc": acc_test,
            "Precision": prec, "ROC AUC": auc, "Temps (s)": train_time
        })

        fpr, tpr, _ = roc_curve(y_test, y_proba)
        roc_curves.append((name, fpr, tpr, auc))

    # --- RÉSULTATS ---
    df_res = pd.DataFrame(results).set_index("Modèle")
    print("\n📊 RÉSULTATS :")
    print(df_res.round(4))

    # Graphiques
    plt.figure(figsize=(10, 6))
    for name, fpr, tpr, auc in roc_curves:
        plt.plot(fpr, tpr, label=f"{name} (AUC={auc:.4f})")
    plt.plot([0, 1], [0, 1], 'k--')
    plt.title('Courbes ROC')
    plt.legend()
    plt.savefig(OUTPUT_IMG_DIR / "ml_roc_curves.png")
    print(f"✅ Graphique ROC sauvegardé.")

    # Overfitting check
    plt.figure(figsize=(8, 5))
    df_plot = df_res[["Train Acc", "Test Acc"]].reset_index().melt(id_vars="Modèle")
    sns.barplot(x="Modèle", y="value", hue="variable", data=df_plot)
    plt.ylim(0.9, 1.01)
    plt.title("Train vs Test Accuracy")
    plt.savefig(OUTPUT_IMG_DIR / "ml_overfitting.png")
    print(f"✅ Graphique Overfitting sauvegardé.")


if __name__ == "__main__":
    run_benchmark()