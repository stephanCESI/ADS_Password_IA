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

# Gestion XGBoost (optionnel)
try:
    from xgboost import XGBClassifier

    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("⚠️ XGBoost non installé. Il sera ignoré.")

# --- IMPORTS PERSO ---
# On ajoute le chemin racine pour trouver le backend
import sys

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR))

from backend.app.utils.math_features import compute_length_norm, compute_diversity, compute_entropy

# --- CONFIGURATION ---
PROCESSED_DIR = BASE_DIR / "datasets" / "processed"
DICT_DIR = BASE_DIR / "datasets" / "Dictionnaries" / "processed"
OUTPUT_IMG_DIR = BASE_DIR  # Racine du projet pour les images


def load_data_and_features():
    """
    Charge les données et recalcule les features exactement comme lors de l'entraînement.
    """
    print("⏳ Chargement des données...")
    if not (PROCESSED_DIR / "passwords_processed.csv").exists():
        raise FileNotFoundError("Le fichier passwords_processed.csv n'existe pas. Lance dataset_loader.py.")

    df = pd.read_csv(PROCESSED_DIR / "passwords_processed.csv")

    print("⏳ Chargement du dictionnaire...")
    if not (DICT_DIR / "linguistic_dictionary.csv").exists():
        raise FileNotFoundError("Le dictionnaire n'existe pas. Lance dictionary_loader.py.")

    corpus = pd.read_csv(DICT_DIR / "linguistic_dictionary.csv")
    corpus['token'] = corpus['token'].astype(str).str.lower().str.strip()

    # Création des sets pour recherche rapide
    words_set = set(corpus[corpus['category'] == 'word']['token'])
    names_set = set(corpus[corpus['category'] == 'name']['token'])
    places_set = set(corpus[corpus['category'] == 'place']['token'])
    weak_set = set(corpus[corpus['category'] == 'weak_pwd']['token'])

    print("⏳ Calcul des features linguistiques (patience, ~10-20s)...")

    def get_ling_features(pwd):
        # Logique identique à train_model.py
        pwd_str = str(pwd).lower()
        clean = re.sub(r'[^a-z]', '', pwd_str)
        rev = clean[::-1]  # Inversion

        f = {'is_weak': 0, 'has_word': 0, 'has_name': 0, 'has_place': 0}

        # 1. Leak Exact (Endroit/Envers)
        if pwd_str in weak_set or pwd_str[::-1] in weak_set:
            f['is_weak'] = 1

        # 2. Patterns (Substrings)
        if len(clean) >= 4:
            # Endroit
            if clean in words_set or clean in weak_set:
                f['has_word'] = 1
            elif clean in names_set:
                f['has_name'] = 1
            elif clean in places_set:
                f['has_place'] = 1

            # Envers (ex: drowssap)
            if rev in words_set or rev in weak_set:
                f['has_word'] = 1
            elif rev in names_set:
                f['has_name'] = 1
            elif rev in places_set:
                f['has_place'] = 1

        return pd.Series(f)

    ling_df = df['password'].apply(get_ling_features)

    # Fusion finale
    # On s'assure de l'ordre des colonnes : length, diversity, entropy, is_weak, word, name, place
    X = pd.concat([df[['length_norm', 'diversity', 'entropy']], ling_df], axis=1)
    y = df['label']

    return train_test_split(X, y, test_size=0.2, random_state=42)


def run_benchmark():
    try:
        X_train, X_test, y_train, y_test = load_data_and_features()
    except Exception as e:
        print(f"❌ Erreur lors du chargement des données : {e}")
        return

    # Liste des modèles à comparer
    models = [
        ("Random Forest", RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)),
        ("Logistic Regression", LogisticRegression(max_iter=1000, random_state=42))
    ]

    if HAS_XGB:
        models.append(("XGBoost", XGBClassifier(eval_metric='logloss', random_state=42)))

    results = []
    roc_curves = []

    print("\n--- 🏁 DÉBUT DU BENCHMARK COMPARATIF ---")

    for name, model in models:
        print(f"\n⚡ Analyse de : {name}...")
        start_time = time.time()

        # Entraînement
        model.fit(X_train, y_train)
        train_time = time.time() - start_time

        # --- 1. SCORES D'ENTRAÎNEMENT (Pour vérifier le surapprentissage) ---
        y_pred_train = model.predict(X_train)
        acc_train = accuracy_score(y_train, y_pred_train)

        # --- 2. SCORES DE TEST (La vraie performance) ---
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]  # Probabilité

        # Métriques détaillées
        acc_test = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_proba)

        results.append({
            "Modèle": name,
            "Train Accuracy": acc_train,
            "Test Accuracy": acc_test,
            "Precision": prec,
            "Recall": rec,
            "F1-Score": f1,
            "ROC AUC": auc,
            "Temps (s)": train_time
        })

        # Stockage pour le graphique ROC
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        roc_curves.append((name, fpr, tpr, auc))

    # --- TABLEAU RÉCAPITULATIF ---
    df_res = pd.DataFrame(results).set_index("Modèle")
    print("\n📊 RÉSULTATS DÉTAILLÉS (Train vs Test) :")
    print(df_res[["Train Accuracy", "Test Accuracy", "Precision", "ROC AUC"]].round(4))

    # ==========================
    # GÉNÉRATION DES GRAPHIQUES
    # ==========================

    # Graphique 1 : Analyse Overfitting (Train vs Test)
    plt.figure(figsize=(10, 6))
    df_overfit = df_res[["Train Accuracy", "Test Accuracy"]].reset_index().melt(id_vars="Modèle", var_name="Dataset",
                                                                                value_name="Accuracy")
    sns.barplot(x="Modèle", y="Accuracy", hue="Dataset", data=df_overfit, palette="pastel")
    plt.ylim(0.90, 1.01)
    plt.title("Analyse de Surapprentissage : Écart Train / Test")
    plt.ylabel("Accuracy (Précision Globale)")
    plt.savefig(OUTPUT_IMG_DIR / "ml_overfitting_analysis.png")
    print(f"\n✅ Graphique 1 sauvegardé : ml_overfitting_analysis.png")

    # Graphique 2 : Comparaison des Métriques Test
    plt.figure(figsize=(12, 6))
    df_metrics = df_res[["Precision", "Recall", "F1-Score"]].reset_index().melt(id_vars="Modèle", var_name="Métrique",
                                                                                value_name="Score")
    sns.barplot(x="Métrique", y="Score", hue="Modèle", data=df_metrics, palette="viridis")
    plt.ylim(0.90, 1.0)
    plt.title("Comparaison des Performances sur Données Inconnues")
    plt.legend(loc='lower right')
    plt.savefig(OUTPUT_IMG_DIR / "ml_metrics_comparison.png")
    print(f"✅ Graphique 2 sauvegardé : ml_metrics_comparison.png")

    # Graphique 3 : Courbes ROC
    plt.figure(figsize=(10, 8))
    for name, fpr, tpr, auc in roc_curves:
        plt.plot(fpr, tpr, label=f"{name} (AUC = {auc:.4f})")

    plt.plot([0, 1], [0, 1], 'k--', label="Hasard (AUC = 0.5)")
    plt.xlabel('Taux de Faux Positifs (Erreurs)')
    plt.ylabel('Taux de Vrais Positifs (Réussites)')
    plt.title('Courbes ROC - Capacité de Discrimination')
    plt.legend(loc='lower right')
    plt.grid(True, alpha=0.3)
    plt.savefig(OUTPUT_IMG_DIR / "ml_roc_curves.png")
    print(f"✅ Graphique 3 sauvegardé : ml_roc_curves.png")

    # Affichage final
    plt.show()


if __name__ == "__main__":
    run_benchmark()