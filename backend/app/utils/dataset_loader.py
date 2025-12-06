from pathlib import Path
import pandas as pd
import string
import secrets
import random
import csv

# --- IMPORT CENTRALISÉ DES CALCULS ---
# Plus besoin de réécrire les maths ici !
from backend.app.utils.math_features import compute_length_norm, compute_diversity, compute_entropy

# --- CONFIGURATION DES CHEMINS ---
DATASET_DIR = Path(__file__).resolve().parents[3] / "datasets"
RAW_DIR = DATASET_DIR / "raw"
PROCESSED_DIR = DATASET_DIR / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_password_dataset(filename="passwords_labeled.csv"):
    print(f"Chargement de {filename}...")
    df = pd.read_csv(RAW_DIR / filename)
    df = df.drop_duplicates()
    df = df[df['password'].str.len() >= 4]
    df['password'] = df['password'].str.encode('ascii', errors='ignore').str.decode('ascii')
    return df


def add_features(df):
    print("Ajout des features mathématiques (via math_features.py)...")
    df['password'] = df['password'].astype(str)

    # On utilise les fonctions importées
    df['length_norm'] = df['password'].apply(compute_length_norm)
    df['diversity'] = df['password'].apply(compute_diversity)
    df['entropy'] = df['password'].apply(compute_entropy)
    return df


def add_labels(df):
    if 'label' not in df.columns:
        print("Génération des labels manquants (Fallback)...")
        df['label'] = df.apply(
            lambda row: 0 if row['length_norm'] < 0.5 or row['diversity'] < 0.5 else 1, axis=1
        )
    return df


# --- GÉNÉRATEURS ---
def generate_strong_password(min_len=10, max_len=22):
    length = secrets.choice(range(min_len, max_len + 1))
    r = random.random()
    if r < 0.50:
        alphabet = string.ascii_letters + string.digits + string.punctuation
    elif r < 0.80:
        pools = [
            string.ascii_letters + string.digits,
            string.ascii_letters + string.punctuation,
            string.ascii_lowercase + string.ascii_uppercase + string.punctuation,
        ]
        alphabet = secrets.choice(pools)
    else:
        pools = [
            string.ascii_letters + string.digits,
            string.ascii_letters + "!@#$%&?",
        ]
        alphabet = secrets.choice(pools)
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_strong_passwords_csv(n=50000, filename="strong_passwords.csv"):
    print(f"Génération de {n} mots de passe forts...")
    passwords = [generate_strong_password() for _ in range(n)]
    df = pd.DataFrame({"password": passwords})
    df["label"] = 1
    df.to_csv(RAW_DIR / filename, index=False, sep=',', quoting=csv.QUOTE_NONNUMERIC)
    print(f"-> Sauvegardé dans {filename}")
    return df


def load_rockyou_sample(n=50000):
    rockyou_path = RAW_DIR / "rockyou.txt"
    if not rockyou_path.exists():
        raise FileNotFoundError(f"Le fichier RockYou est introuvable ici : {rockyou_path}")

    print(f"Lecture et échantillonnage de RockYou ({n} lignes)... Patience.")
    reservoir = []
    seen = set()
    try:
        with open(rockyou_path, "r", encoding="latin-1") as f:
            for i, line in enumerate(f, start=1):
                pwd = line.strip()
                if not pwd: continue
                if len(pwd) > 50: continue
                if pwd in seen: continue

                if len(reservoir) < n:
                    reservoir.append(pwd)
                    seen.add(pwd)
                else:
                    j = random.randint(1, i)
                    if j <= n:
                        removed = reservoir[j - 1]
                        seen.remove(removed)
                        reservoir[j - 1] = pwd
                        seen.add(pwd)
                if i % 1000000 == 0:
                    print(f"   -> {i} lignes analysées...")
    except KeyboardInterrupt:
        print("\nArrêt manuel.")

    return pd.DataFrame({"password": reservoir})


def create_weak_passwords_csv(n=50000, filename="weak_passwords.csv"):
    print(f"Extraction de {n} mots de passe faibles depuis RockYou...")
    df = load_rockyou_sample(int(n * 1.5))
    allowed = set(string.ascii_letters + string.digits + string.punctuation + " ")
    df = df[df["password"].apply(lambda p: all(c in allowed for c in str(p)))]
    df = df.head(n)
    df["label"] = 0
    df.to_csv(RAW_DIR / filename, index=False, sep=',', quoting=csv.QUOTE_NONNUMERIC)
    print(f"-> Sauvegardé dans {filename} ({len(df)} lignes)")
    return df


def create_labeled_dataset(weak_filename="weak_passwords.csv", strong_filename="strong_passwords.csv",
                           output_filename="passwords_labeled.csv"):
    print("Fusion des datasets...")
    df_weak = pd.read_csv(RAW_DIR / weak_filename)
    df_strong = pd.read_csv(RAW_DIR / strong_filename)
    df_combined = pd.concat([df_weak, df_strong], ignore_index=True)
    df_combined = df_combined.sample(frac=1, random_state=42).reset_index(drop=True)
    df_combined.to_csv(RAW_DIR / output_filename, index=False)
    print(f"Dataset labellisé créé : {output_filename}")
    return df_combined


def create_processed_dataset(raw_filename="passwords_labeled.csv", processed_filename="passwords_processed.csv"):
    df = load_password_dataset(raw_filename)
    df = add_features(df)  # Utilise maintenant les fonctions importées
    df = add_labels(df)
    df.to_csv(PROCESSED_DIR / processed_filename, index=False, sep=',', quoting=csv.QUOTE_NONNUMERIC)
    print(f"Dataset PROCESSED prêt : {processed_filename}")
    return df