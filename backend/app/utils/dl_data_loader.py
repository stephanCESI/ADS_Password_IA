import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parents[3]
PROCESSED_DIR = BASE_DIR / "datasets" / "processed"
DL_DATA_DIR = BASE_DIR / "datasets" / "deep_learning_data"
DL_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Paramètres cruciaux pour le Deep Learning
MAX_LEN = 32  # On regarde les 32 premiers caractères (suffisant pour 99.9% des mdp)


# Tout mot de passe plus court sera complété par des 0.
# Tout mot de passe plus long sera coupé.

def prepare_dl_data():
    print("\n--- 🧠 PRÉPARATION DES DONNÉES DEEP LEARNING ---")

    # 1. Chargement du dataset brut (juste le texte et le label)
    csv_path = PROCESSED_DIR / "passwords_processed.csv"
    if not csv_path.exists():
        print(f"❌ Erreur : {csv_path} introuvable. Lance dataset_loader.py d'abord.")
        return

    print("⏳ Chargement du CSV...")
    df = pd.read_csv(csv_path)

    # Conversion en string pur pour éviter les bugs (ex: "NaN" ou chiffres interprétés)
    passwords = df['password'].astype(str).tolist()
    labels = df['label'].values

    print(f"   -> {len(passwords)} mots de passe chargés.")

    # 2. Tokenisation (Character Level)
    print("⏳ Création du Tokenizer (Apprentissage des caractères)...")

    # char_level=True est VITAL : on veut découper par lettre, pas par mot
    tokenizer = Tokenizer(char_level=True, lower=False)  # lower=False car 'A' != 'a' en mdp
    tokenizer.fit_on_texts(passwords)

    # On récupère le nombre de caractères uniques trouvés (le vocabulaire)
    vocab_size = len(tokenizer.word_index) + 1  # +1 pour le padding (0)
    print(f"   -> Vocabulaire détecté : {vocab_size} caractères uniques.")

    # 3. Transformation en Séquences d'entiers
    print("⏳ Conversion en séquences numériques...")
    sequences = tokenizer.texts_to_sequences(passwords)

    # Exemple pour visualiser
    print(f"   Exemple : '{passwords[0]}' devient {sequences[0]}")

    # 4. Padding (Mise à la même longueur)
    print(f"⏳ Padding (Standardisation à {MAX_LEN} caractères)...")
    X = pad_sequences(sequences, maxlen=MAX_LEN, padding='post', truncating='post')

    # X est maintenant une matrice géante de nombres [100000, 32]
    y = np.array(labels)

    # 5. Split Train/Test/Validation
    print("⏳ Séparation Train / Test / Val...")

    # D'abord on sépare Test (20%)
    X_train_full, X_test, y_train_full, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Ensuite on sépare une petite part de Validation (10% du Train) pour le monitoring pendant l'entraînement
    X_train, X_val, y_train, y_val = train_test_split(X_train_full, y_train_full, test_size=0.1, random_state=42)

    print(f"   Train shape : {X_train.shape}")
    print(f"   Val shape   : {X_val.shape}")
    print(f"   Test shape  : {X_test.shape}")

    # 6. Sauvegarde
    print("💾 Sauvegarde des tenseurs et du tokenizer...")

    # On sauve les matrices numpy (très rapide à charger)
    np.save(DL_DATA_DIR / "X_train.npy", X_train)
    np.save(DL_DATA_DIR / "y_train.npy", y_train)
    np.save(DL_DATA_DIR / "X_val.npy", X_val)
    np.save(DL_DATA_DIR / "y_val.npy", y_val)
    np.save(DL_DATA_DIR / "X_test.npy", X_test)
    np.save(DL_DATA_DIR / "y_test.npy", y_test)

    # On sauve le tokenizer (INDISPENSABLE pour le site web)
    # Sans lui, on ne saura pas que 'a' = 1 lors de la prédiction
    with open(DL_DATA_DIR / "tokenizer.pickle", "wb") as handle:
        pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # On sauve aussi les infos de config pour les charger dynamiquement
    config = {"max_len": MAX_LEN, "vocab_size": vocab_size}
    with open(DL_DATA_DIR / "config.pickle", "wb") as handle:
        pickle.dump(config, handle, protocol=pickle.HIGHEST_PROTOCOL)

    print("\n✅ PRÉPARATION TERMINÉE ! Les données sont prêtes pour le Deep Learning.")
    print(f"   Dossier : {DL_DATA_DIR}")


if __name__ == "__main__":
    prepare_dl_data()