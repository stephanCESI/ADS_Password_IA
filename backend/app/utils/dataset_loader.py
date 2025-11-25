from pathlib import Path
import pandas as pd
import string
import math
import secrets
import random
import csv

DATASET_DIR = Path(__file__).resolve().parents[3] / "datasets"
RAW_DIR = DATASET_DIR / "raw"
PROCESSED_DIR = DATASET_DIR / "processed"

def load_password_dataset(filename="passwords_labeled.csv"):
    df = pd.read_csv(RAW_DIR / filename)
    df = df.drop_duplicates()
    df = df[df['password'].str.len() >= 4]
    df['password'] = df['password'].str.encode('ascii', errors='ignore').str.decode('ascii')
    return df

def compute_length_norm(password, max_len=20):
    return min(len(password) / max_len, 1)

def compute_diversity(password):
    classes = 0
    if any(c.islower() for c in password):
        classes += 1
    if any(c.isupper() for c in password):
        classes += 1
    if any(c.isdigit() for c in password):
        classes += 1
    if any(c in string.punctuation for c in password):
        classes += 1
    return classes / 4

def compute_entropy(password):
    pool = 0
    if any(c.islower() for c in password):
        pool += 26
    if any(c.isupper() for c in password):
        pool += 26
    if any(c.isdigit() for c in password):
        pool += 10
    if any(c in string.punctuation for c in password):
        pool += 32
    ent = len(password) * math.log2(pool) if pool > 0 else 0
    return min(ent / 100, 1)

def add_features(df):
    df['length_norm'] = df['password'].apply(compute_length_norm)
    df['diversity'] = df['password'].apply(compute_diversity)
    df['entropy'] = df['password'].apply(compute_entropy)
    return df

def add_labels(df):
    df['label'] = df['label'] if 'label' in df.columns else df.apply(
        lambda row: 0 if row['length_norm'] < 0.5 or row['diversity'] < 0.5 else 1, axis=1)
    return df

def generate_strong_password(min_len=10, max_len=20):
    length = secrets.choice(range(min_len, max_len + 1))

    # Probabilités de diversité
    r = random.random()

    if r < 0.50:
        # Très forte diversité (4 classes)
        alphabet = (
            string.ascii_lowercase +
            string.ascii_uppercase +
            string.digits +
            string.punctuation
        )
    elif r < 0.80:
        # Diversité moyenne (3 classes)
        pools = [
            string.ascii_letters + string.digits,
            string.ascii_letters + string.punctuation,
            string.ascii_lowercase + string.ascii_uppercase + string.punctuation,
        ]
        alphabet = secrets.choice(pools)
    else:
        # Diversité acceptable mais imparfaite (2 classes)
        pools = [
            string.ascii_letters,
            string.ascii_letters + string.digits,
            string.ascii_letters + "!@#$%&?",
        ]
        alphabet = secrets.choice(pools)

    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_strong_passwords_csv(n=10000, filename="strong_passwords.csv"):
    passwords = [generate_strong_password() for _ in range(n)]
    df = pd.DataFrame({"password": passwords})
    df["label"] = 1
    RAW_DIR.mkdir(exist_ok=True)
    df.to_csv(RAW_DIR / filename, index=False, sep=',', quoting=csv.QUOTE_NONNUMERIC)
    print("create_strong_passwords_csv finished")
    return df

def load_rockyou_sample(n=10000):
    rockyou_path = RAW_DIR / "rockyou.txt"
    reservoir = []
    seen = set()

    with open(rockyou_path, "r", encoding="latin-1") as f:
        for i, line in enumerate(f, start=1):
            pwd = line.strip()
            if not pwd:
                continue
            if pwd in seen:
                continue
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

    return pd.DataFrame({"password": reservoir})

def create_weak_passwords_csv(n=10000, filename="weak_passwords.csv"):
    allowed = set(string.ascii_letters + string.digits + string.punctuation)
    df = load_rockyou_sample(n * 2)  # tirer plus pour compenser le filtre
    df = df[df["password"].apply(lambda p: all(c in allowed for c in p))]
    df = df.head(n)  # garder exactement n mots
    df["label"] = 0
    RAW_DIR.mkdir(exist_ok=True)
    df.to_csv(RAW_DIR / filename, index=False, sep=',', quoting=csv.QUOTE_NONNUMERIC)
    print("create_weak_passwords_csv finished")
    return df

def create_labeled_dataset(weak_filename="weak_passwords.csv",
                           strong_filename="strong_passwords.csv",
                           output_filename="passwords_labeled.csv"):
    df_weak = pd.read_csv(RAW_DIR / weak_filename)
    df_strong = pd.read_csv(RAW_DIR / strong_filename)
    df_combined = pd.concat([df_weak, df_strong], ignore_index=True)
    df_combined = df_combined.sample(frac=1, random_state=42).reset_index(drop=True)
    df_combined.to_csv(RAW_DIR / output_filename, index=False)
    print("create_labeled_dataset finished")
    return df_combined

def create_processed_dataset(raw_filename="passwords_labeled.csv", processed_filename="passwords_processed.csv"):
    df = load_password_dataset(raw_filename)
    df = add_features(df)
    df = add_labels(df)
    PROCESSED_DIR.mkdir(exist_ok=True)
    df.to_csv(PROCESSED_DIR / processed_filename, index=False, sep=',', quoting=csv.QUOTE_NONNUMERIC)
    print("create_processed_dataset finished")
    return df
