import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = Path(__file__).resolve().parents[3]
PROCESSED_DATASET = BASE_DIR / "datasets" / "processed" / "passwords_processed.csv"
LINGUISTIC_DICT = BASE_DIR / "datasets" / "Dictionnaries" / "processed" / "linguistic_dictionary.csv"


def print_header(title):
    print(f"\n{'=' * 60}")
    print(f" {title.upper()}")
    print(f"{'=' * 60}")


def audit_passwords():
    print_header("AUDIT 1 : DATASET D'ENTRAÎNEMENT (Passwords)")

    if not PROCESSED_DATASET.exists():
        print("❌ ERREUR : Le fichier passwords_processed.csv est introuvable.")
        return

    df = pd.read_csv(PROCESSED_DATASET)
    total = len(df)
    print(f"Total lignes : {total}")

    # 1. Équilibre des Classes (Fort vs Faible)
    counts = df['label'].value_counts()

    # On gère le cas où il manquerait une classe
    nb_weak = counts.get(0, 0)
    nb_strong = counts.get(1, 0)

    pct_weak = (nb_weak / total) * 100
    pct_strong = (nb_strong / total) * 100

    print(f"\n--- Répartition des Labels ---")
    print(f"🔴 Faibles (Label 0) : {nb_weak} ({pct_weak:.2f}%)")
    print(f"🟢 Forts   (Label 1) : {nb_strong} ({pct_strong:.2f}%)")

    # Diagnostic
    if 40 <= pct_weak <= 60:
        print("✅ DIAGNOSTIC : Dataset parfaitement équilibré.")
    else:
        print("⚠️ DIAGNOSTIC : Déséquilibre détecté ! L'IA risque d'être biaisée.")

    # 2. Doublons
    duplicates = df.duplicated(subset=['password']).sum()
    if duplicates > 0:
        print(f"\n⚠️ ATTENTION : Il y a {duplicates} doublons de mots de passe !")
    else:
        print("\n✅ Aucun doublon détecté.")


def audit_dictionary():
    print_header("AUDIT 2 : DICTIONNAIRE LINGUISTIQUE")

    if not LINGUISTIC_DICT.exists():
        print("❌ ERREUR : Le fichier linguistic_dictionary.csv est introuvable.")
        return

    df = pd.read_csv(LINGUISTIC_DICT)
    total = len(df)
    print(f"Total tokens : {total}")

    # Répartition par catégorie
    counts = df['category'].value_counts()

    print(f"\n--- Répartition par Catégorie ---")
    for category, count in counts.items():
        pct = (count / total) * 100
        print(f"- {category:<10} : {count:6d} ({pct:.2f}%)")

    # Vérification des proportions
    nb_weak_exact = counts.get('weak_pwd', 0)

    print("\n--- Analyse Qualitive ---")
    if nb_weak_exact < 1000:
        print(
            f"⚠️ ATTENTION : Seulement {nb_weak_exact} mots de passe 'leakés'. C'est peu pour détecter les leaks exacts.")
    else:
        print(f"✅ Liste de Leaks : {nb_weak_exact} entrées (Suffisant pour couvrir le Top 1000/10k).")

    if 'word' in counts and counts['word'] > 10000:
        print("✅ Vocabulaire Anglais : Riche (>10k mots).")
    else:
        print("⚠️ Vocabulaire Anglais : Pauvre. Risque de rater des attaques par dictionnaire.")


def main():
    try:
        audit_passwords()
        audit_dictionary()
        print("\n=== AUDIT TERMINÉ ===")
    except Exception as e:
        print(f"\n❌ Une erreur est survenue pendant l'audit : {e}")


if __name__ == "__main__":
    main()