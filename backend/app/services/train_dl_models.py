import numpy as np
import pickle
from pathlib import Path
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Conv1D, GlobalMaxPooling1D, Dense, LSTM, Dropout, Flatten
from sklearn.metrics import accuracy_score

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = Path(__file__).resolve().parents[3]
DL_DATA_DIR = BASE_DIR / "datasets" / "deep_learning_data"
MODEL_DIR = BASE_DIR / "backend" / "app" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_dl_data():
    """Charge les matrices pré-calculées et la configuration."""
    try:
        X_train = np.load(DL_DATA_DIR / "X_train.npy")
        y_train = np.load(DL_DATA_DIR / "y_train.npy")
        X_val = np.load(DL_DATA_DIR / "X_val.npy")
        y_val = np.load(DL_DATA_DIR / "y_val.npy")
        X_test = np.load(DL_DATA_DIR / "X_test.npy")
        y_test = np.load(DL_DATA_DIR / "y_test.npy")

        with open(DL_DATA_DIR / "config.pickle", "rb") as f:
            config = pickle.load(f)

        print(f"✅ Données DL chargées. Vocabulaire: {config['vocab_size']}, Longueur max: {config['max_len']}")
        return X_train, y_train, X_val, y_val, X_test, y_test, config
    except Exception as e:
        print(f"❌ Erreur de chargement des données DL : {e}")
        print("Exécutez d'abord dl_data_loader.py")
        exit()


def build_cnn(vocab_size, max_len):
    """CNN 1D : Excellent pour détecter des motifs spatiaux locaux (ex: '1234', 'qwerty')."""
    model = Sequential([
        Embedding(input_dim=vocab_size, output_dim=32, input_length=max_len),
        Conv1D(filters=64, kernel_size=4, activation='relu'),
        GlobalMaxPooling1D(),
        Dense(32, activation='relu'),
        Dropout(0.5),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model


def build_lstm(vocab_size, max_len):
    """LSTM : Excellent pour comprendre la séquence et l'ordre complexe (ex: structure humaine)."""
    model = Sequential([
        Embedding(input_dim=vocab_size, output_dim=32, input_length=max_len),
        LSTM(64, return_sequences=False),
        Dense(32, activation='relu'),
        Dropout(0.5),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model


def build_dnn(vocab_size, max_len):
    """DNN Simple : Modèle de base pour comparaison."""
    model = Sequential([
        Embedding(input_dim=vocab_size, output_dim=16, input_length=max_len),
        Flatten(),
        Dense(64, activation='relu'),
        Dropout(0.5),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model


def train_dl():
    print("--- 🚀 DÉBUT DE L'ENTRAÎNEMENT DEEP LEARNING ---")

    X_train, y_train, X_val, y_val, X_test, y_test, config = load_dl_data()
    vocab_size = config['vocab_size']
    max_len = config['max_len']

    models_config = [
        {"name": "CNN Scanner", "file": "cnn_scanner.keras", "builder": build_cnn},
        {"name": "LSTM Reader", "file": "lstm_reader.keras", "builder": build_lstm},
        {"name": "DNN Simple", "file": "dnn_simple.keras", "builder": build_dnn}
    ]

    for m in models_config:
        print(f"\n⚡ Entraînement de : {m['name']}...")
        model = m['builder'](vocab_size, max_len)

        # Callbacks pour éviter l'overfitting
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss', patience=3, restore_best_weights=True
        )

        model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=10,
            batch_size=128,
            callbacks=[early_stopping],
            verbose=1
        )

        # Évaluation
        y_pred = (model.predict(X_test, verbose=0) > 0.5).astype("int32")
        acc = accuracy_score(y_test, y_pred)
        print(f"   ✅ Précision Test : {acc:.4f}")

        # Sauvegarde (Format Keras recommandé)
        save_path = MODEL_DIR / m['file']
        model.save(save_path)
        print(f"   💾 Sauvegardé dans : {save_path}")

    print("\n--- TERMINE ! Les modèles DL sont prêts. ---")


if __name__ == "__main__":
    train_dl()