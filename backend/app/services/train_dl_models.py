import numpy as np
import pickle
from pathlib import Path
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Embedding, GlobalAveragePooling1D, Conv1D, GlobalMaxPooling1D, LSTM, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parents[3]
DL_DATA_DIR = BASE_DIR / "datasets" / "deep_learning_data"
MODEL_DIR = BASE_DIR / "backend" / "app" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Paramètres d'entraînement
BATCH_SIZE = 64
EPOCHS = 10  # On peut augmenter si besoin, mais 10 c'est souvent suffisant pour ce problème


def load_data():
    print("⏳ Chargement des données pré-traitées...")
    try:
        X_train = np.load(DL_DATA_DIR / "X_train.npy")
        y_train = np.load(DL_DATA_DIR / "y_train.npy")
        X_val = np.load(DL_DATA_DIR / "X_val.npy")
        y_val = np.load(DL_DATA_DIR / "y_val.npy")
        X_test = np.load(DL_DATA_DIR / "X_test.npy")
        y_test = np.load(DL_DATA_DIR / "y_test.npy")

        # Chargement de la config pour connaître la taille du vocabulaire
        with open(DL_DATA_DIR / "config.pickle", "rb") as f:
            config = pickle.load(f)

        print(f"✅ Données chargées. Train: {X_train.shape}, Vocab: {config['vocab_size']}")
        return X_train, y_train, X_val, y_val, X_test, y_test, config
    except FileNotFoundError:
        print("❌ Erreur : Fichiers .npy introuvables. Lance dl_data_loader.py d'abord.")
        exit()


# --- DÉFINITION DES MODÈLES ---

def build_dnn(vocab_size, max_len):
    """Modèle Simple : Embedding + Moyenne + Dense"""
    model = Sequential([
        Embedding(vocab_size, 16, input_length=max_len),  # Transforme chaque caractère en vecteur de 16 chiffres
        GlobalAveragePooling1D(),  # Fait la moyenne pour avoir une idée globale
        Dense(24, activation='relu'),
        Dropout(0.2),  # Évite le par-cœur
        Dense(1, activation='sigmoid')  # Sortie 0 ou 1
    ], name="DNN_Simple")
    return model


def build_cnn(vocab_size, max_len):
    """Modèle CNN : Scanner de motifs (n-grams)"""
    model = Sequential([
        Embedding(vocab_size, 32, input_length=max_len),
        # Conv1D scanne des groupes de 3 caractères (kernel_size=3)
        Conv1D(64, 3, activation='relu'),
        GlobalMaxPooling1D(),  # Garde le motif le plus fort détecté
        Dense(24, activation='relu'),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ], name="CNN_Scanner")
    return model


def build_lstm(vocab_size, max_len):
    """Modèle LSTM : Lecture séquentielle (Plus lent mais précis sur les suites)"""
    model = Sequential([
        Embedding(vocab_size, 32, input_length=max_len),
        # LSTM lit la séquence et garde une mémoire
        LSTM(32),
        Dense(24, activation='relu'),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ], name="LSTM_Reader")
    return model


def train_and_evaluate(model, data):
    X_train, y_train, X_val, y_val, X_test, y_test, _ = data

    print(f"\n⚡ Entraînement du modèle : {model.name}...")

    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

    # Arrêt automatique si l'entraînement ne progresse plus (évite de perdre du temps)
    early_stop = EarlyStopping(monitor='val_loss', patience=2, restore_best_weights=True)

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[early_stop],
        verbose=1
    )

    print(f"📊 Évaluation sur le Test Set ({model.name})...")
    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    print(f"   ✅ Accuracy Finale : {accuracy:.4f} ({accuracy * 100:.2f}%)")

    # Sauvegarde au format Keras moderne (.keras)
    save_path = MODEL_DIR / f"{model.name.lower()}.keras"
    model.save(save_path)
    print(f"   💾 Modèle sauvegardé : {save_path}")

    return accuracy


def main():
    # 1. Charger les données
    data = load_data()
    X_train, _, _, _, _, _, config = data
    vocab_size = config['vocab_size']
    max_len = config['max_len']

    results = {}

    # 2. Entraîner les 3 champions
    # Modèle 1 : DNN (Rapide, Baseline)
    model_dnn = build_dnn(vocab_size, max_len)
    results['DNN'] = train_and_evaluate(model_dnn, data)

    # Modèle 2 : CNN (Excellent pour les patterns)
    model_cnn = build_cnn(vocab_size, max_len)
    results['CNN'] = train_and_evaluate(model_cnn, data)

    # Modèle 3 : LSTM (Puissant pour la logique)
    model_lstm = build_lstm(vocab_size, max_len)
    results['LSTM'] = train_and_evaluate(model_lstm, data)

    print("\n--- 🏆 PODIUM DEEP LEARNING ---")
    for name, acc in sorted(results.items(), key=lambda x: x[1], reverse=True):
        print(f"{name}: {acc:.4f}")


if __name__ == "__main__":
    main()