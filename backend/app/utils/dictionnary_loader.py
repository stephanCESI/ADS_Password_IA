import pandas as pd
import re
from pathlib import Path

# --- GESTION DES CHEMINS ---
BASE_DIR = Path(__file__).resolve().parents[3]
PATH_RAW = BASE_DIR / "datasets" / "Dictionnaries" / "raw"
# Chemin vers le dossier datasets/raw où tu as mis common-passwords.txt
PATH_DATASETS_RAW = BASE_DIR / "datasets" / "raw"
PATH_PROCESSED = BASE_DIR / "datasets" / "Dictionnaries" / "processed"
PATH_PROCESSED.mkdir(parents=True, exist_ok=True)


def clean_token(token):
    if not isinstance(token, str): return ""
    token = re.sub(r"[^a-zA-Z]", "", token).lower()
    return token if len(token) > 2 else ""


print("--- 🚀 GÉNÉRATION DU CORPUS LINGUISTIQUE (FINAL) ---")

# 1. Chargement des Mots Anglais
print("1. Chargement des mots anglais...")
with open(PATH_RAW / "english-words.35", "r", encoding="latin-1", errors="ignore") as f:
    words = [clean_token(w) for w in f]
words_list = list(set(filter(None, words)))
print(f"   -> {len(words_list)} mots conservés.")

# 2. Chargement des Noms et Prénoms
print("2. Chargement des prénoms/noms...")
female = pd.read_csv(PATH_RAW / "dist.female.first.txt", sep=r"\s+", header=None, encoding="latin-1")[0]
male = pd.read_csv(PATH_RAW / "dist.male.first.txt", sep=r"\s+", header=None, encoding="latin-1")[0]
last = pd.read_csv(PATH_RAW / "dist.all.last.txt", sep=r"\s+", header=None, encoding="latin-1")[0]
all_names_raw = pd.concat([female, male, last], ignore_index=True)
names_list = list(set(filter(None, [clean_token(n) for n in all_names_raw])))
print(f"   -> {len(names_list)} noms conservés.")

# 3. Villes (FILTRÉES > 15k Habitants)
print("3. Chargement des lieux (Population > 15k)...")
try:
    df_cities = pd.read_csv(
        PATH_RAW / "geonames-all-cities-with-a-population-1000.csv",
        sep=";", encoding="utf-8", on_bad_lines="skip"
    )
    df_cities = df_cities[df_cities['Population'] > 15000]
    cities = [clean_token(str(n)) for n in df_cities["Name"]]

    with open(PATH_RAW / "countries.txt", "r", encoding="utf-8") as f:
        countries = [clean_token(c) for c in f]

    places_list = list(set(filter(None, cities + countries)))
    print(f"   -> {len(places_list)} lieux conservés (filtrés).")
except Exception as e:
    print(f"⚠️ Erreur chargement villes : {e}")
    places_list = []

# 4. Mots de passe faibles (CORRECTION PATH + ENCODING)
print("4. Chargement de la liste 'Common Passwords'...")
# On cherche le fichier dans datasets/raw/
weak_file = PATH_RAW / "common-passwords.txt"

if weak_file.exists():
    try:
        # CORRECTION ICI : encoding='utf-8' et errors='ignore' pour éviter le crash
        with open(weak_file, "r", encoding="utf-8", errors="ignore") as f:
            weak_pwds = [p.strip().lower() for p in f if p.strip()]

        weak_pwds = list(set(weak_pwds))
        print(f"   -> {len(weak_pwds)} leaks chargés.")
    except Exception as e:
        print(f"❌ Erreur lecture fichier weak : {e}")
        weak_pwds = []
else:
    print(f"❌ ERREUR CRITIQUE : Aucun fichier de mot de passe trouvé !")
    weak_pwds = []

# --- COMPILATION INTELLIGENTE ---
print("5. Compilation et Dédoublonnage avec Priorité...")

corpus = pd.DataFrame({
    "token": words_list + names_list + places_list + weak_pwds,
    "category": ["word"] * len(words_list) + ["name"] * len(names_list) + ["place"] * len(places_list) + [
        "weak_pwd"] * len(weak_pwds)
})

# SYSTEME DE PRIORITE POUR "SUMMER", "PARIS", etc.
# Ordre : Weak (0) > Word (1) > Name (2) > Place (3)
# Si "Summer" est dans Word et Name, on garde Word (car 1 < 2).
corpus['priority'] = corpus['category'].map({'weak_pwd': 0, 'word': 1, 'name': 2, 'place': 3})

# On trie : les prioritaires remontent en haut
corpus = corpus.sort_values('priority')

# On dédoublonne en gardant le premier (donc le plus prioritaire)
corpus = corpus.drop_duplicates(subset=["token"], keep='first')

# On nettoie la colonne temporaire
corpus = corpus.drop('priority', axis=1)

outfile = PATH_PROCESSED / "linguistic_dictionary.csv"
corpus.to_csv(outfile, index=False)

print(f"--- SUCCÈS ---")
print(f"Fichier généré : {outfile}")
print(f"Total entrées uniques : {len(corpus)}")