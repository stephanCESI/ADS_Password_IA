from pathlib import Path
import pandas as pd
import string
import secrets
import random  # Utilisé UNIQUEMENT pour piocher dans les fichiers, pas pour générer les mots de passe
import csv

# --- IMPORT DES CALCULS MATHÉMATIQUES ---
from backend.app.utils.math_features import compute_length_norm, compute_diversity, compute_entropy

# --- CONFIGURATION DES CHEMINS ---
DATASET_DIR = Path(__file__).resolve().parents[3] / "datasets"
RAW_DIR = DATASET_DIR / "raw"
LEAKS_DIR = RAW_DIR / "leaks"
PROCESSED_DIR = DATASET_DIR / "processed"
DICT_DIR = DATASET_DIR / "Dictionnaries" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
LEAKS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# --- CHARGEMENT DU DICTIONNAIRE POUR DICEWARE ---
def load_word_list_for_diceware():
    """Charge les mots du dictionnaire pour générer des passphrases fortes."""
    dict_path = DICT_DIR / "linguistic_dictionary.csv"
    try:
        df = pd.read_csv(dict_path)
        words = df[(df['category'] == 'word') & (df['token'].str.len() >= 4)]['token'].dropna().tolist()
        if len(words) > 1000:
            return words
    except:
        pass
    return ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf"]


WORD_LIST = load_word_list_for_diceware()


# --- GÉNÉRATION DES MOTS DE PASSE FORTS (LABEL 1) ---
def generate_strong_password(min_len=14, max_len=32):
    """Génération hybride cryptographiquement sûre (70% Aléatoire, 30% Diceware)"""
    sys_random = secrets.SystemRandom()

    # 30% de chances de générer un Diceware
    if sys_random.random() < 0.30 and len(WORD_LIST) > 10:
        num_words = sys_random.randint(5, 7)
        separator = sys_random.choice(['-', '_', '.', '', ' '])
        return separator.join(sys_random.choice(WORD_LIST) for _ in range(num_words))

    # 70% de chances de générer de l'aléatoire
    length = sys_random.randint(min_len, max_len)
    r = sys_random.random()

    if r < 0.50:
        alphabet = string.ascii_letters + string.digits + string.punctuation
    elif r < 0.80:
        pools = [
            string.ascii_letters + string.digits,
            string.ascii_letters + string.punctuation,
            string.ascii_lowercase + string.ascii_uppercase + string.punctuation,
        ]
        alphabet = sys_random.choice(pools)
    else:
        pools = [
            string.ascii_letters + string.digits,
            string.ascii_letters + "!@#$%&?",
        ]
        alphabet = sys_random.choice(pools)

    return ''.join(sys_random.choice(alphabet) for _ in range(length))


def create_strong_passwords_csv(n=50000, filename="strong_passwords.csv"):
    print(f"Génération de {n} mots de passe FORTS (CSPRNG & Diceware)...")
    passwords = [generate_strong_password() for _ in range(n)]
    df = pd.DataFrame({"password": passwords, "label": 1})
    df.to_csv(RAW_DIR / filename, index=False, sep=',', quoting=csv.QUOTE_NONNUMERIC)
    print(f"✅ Sauvegardé dans {filename}")
    return df


# --- EXTRACTION DES MOTS DE PASSE FAIBLES (LABEL 0) ---
def load_weak_passwords_sample(n=50000):
    """Lit TOUS les fichiers .txt dans datasets/raw/leaks/ et échantillonne (Reservoir Sampling)"""
    txt_files = list(LEAKS_DIR.glob("*.txt"))

    if not txt_files:
        print(f"⚠️ Aucun fichier trouvé dans {LEAKS_DIR}. Je cherche dans {RAW_DIR}...")
        txt_files = list(RAW_DIR.glob("*.txt"))

    if not txt_files:
        raise FileNotFoundError(f"❌ AUCUN dictionnaire de fuites (.txt) trouvé ! Ajoutez RockYou ou Top29M.")

    print(f"Lecture et échantillonnage depuis {len(txt_files)} fichiers de leaks...")
    reservoir = []
    seen = set()
    total_lines = 0

    try:
        for filepath in txt_files:
            print(f"   -> Analyse de {filepath.name}...")
            with open(filepath, "r", encoding="latin-1", errors="ignore") as f:
                for line in f:
                    pwd = line.strip()
                    # Ignorer les vides, trop longs ou déjà vus
                    if not pwd or len(pwd) > 50 or pwd in seen:
                        continue

                    total_lines += 1

                    # Logique du Reservoir Sampling
                    if len(reservoir) < n:
                        reservoir.append(pwd)
                        seen.add(pwd)
                    else:
                        # random() classique est suffisant ici (rapidité pour 40M de lignes)
                        j = random.randint(0, total_lines - 1)
                        if j < n:
                            seen.remove(reservoir[j])
                            reservoir[j] = pwd
                            seen.add(pwd)
    except KeyboardInterrupt:
        print("\n⚠️ Arrêt manuel de l'échantillonnage.")

    return pd.DataFrame({"password": reservoir})


def create_weak_passwords_csv(n=50000, filename="weak_passwords.csv"):
    print(f"Extraction de {n} mots de passe FAIBLES depuis les leaks...")
    # On tire un peu plus de lignes au cas où le nettoyage en supprime
    df = load_weak_passwords_sample(int(n * 1.5))

    # Nettoyage : On ne garde que les caractères ASCII standards
    allowed = set(string.ascii_letters + string.digits + string.punctuation + " ")
    df = df[df["password"].apply(lambda p: all(c in allowed for c in str(p)))]

    # On coupe à n exactement
    df = df.head(n)
    df["label"] = 0
    df.to_csv(RAW_DIR / filename, index=False, sep=',', quoting=csv.QUOTE_NONNUMERIC)
    print(f"✅ Sauvegardé dans {filename} ({len(df)} lignes)")
    return df


# --- FUSION ET CRÉATION DU DATASET FINAL ---
def create_labeled_dataset(weak_filename="weak_passwords.csv", strong_filename="strong_passwords.csv",
                           output_filename="passwords_labeled.csv"):
    print("Fusion et mélange des datasets...")
    df_weak = pd.read_csv(RAW_DIR / weak_filename)
    df_strong = pd.read_csv(RAW_DIR / strong_filename)

    df_combined = pd.concat([df_weak, df_strong], ignore_index=True)
    # Mélange aléatoire (shuffle)
    df_combined = df_combined.sample(frac=1, random_state=42).reset_index(drop=True)
    df_combined.to_csv(RAW_DIR / output_filename, index=False)
    print(f"✅ Dataset labellisé brut créé : {output_filename} ({len(df_combined)} lignes)")
    return df_combined


def create_processed_dataset(raw_filename="passwords_labeled.csv", processed_filename="passwords_processed.csv"):
    print("Ajout des features mathématiques...")
    df = pd.read_csv(RAW_DIR / raw_filename)
    df = df.drop_duplicates(subset=['password'])
    df = df[df['password'].str.len() >= 4]
    df['password'] = df['password'].astype(str)

    # Application des fonctions de math_features.py
    df['length_norm'] = df['password'].apply(compute_length_norm)
    df['diversity'] = df['password'].apply(compute_diversity)
    df['entropy'] = df['password'].apply(compute_entropy)

    df.to_csv(PROCESSED_DIR / processed_filename, index=False, sep=',', quoting=csv.QUOTE_NONNUMERIC)
    print(f"✅ Dataset FINAL PRÊT : {processed_filename}")
    return df


# --- POINT D'ENTRÉE ---
if __name__ == "__main__":
    print("--- 🚀 CRÉATION DU DATASET D'ENTRAÎNEMENT ---")
    create_weak_passwords_csv(n=50000)
    create_strong_passwords_csv(n=50000)
    create_labeled_dataset()
    create_processed_dataset()
    print("--- 🎉 OPÉRATION TERMINÉE ---")