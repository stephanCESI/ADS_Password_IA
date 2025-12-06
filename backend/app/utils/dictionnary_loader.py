import pandas as pd
import re
from pathlib import Path

# --- GESTION DES CHEMINS ---
BASE_DIR = Path(__file__).resolve().parents[3]
PATH_RAW = BASE_DIR / "datasets" / "Dictionnaries" / "raw"
PATH_PROCESSED = BASE_DIR / "datasets" / "Dictionnaries" / "processed"
PATH_PROCESSED.mkdir(parents=True, exist_ok=True)

def clean_token(token):
    """
    Nettoie un token : minuscules, lettres uniquement.
    Renvoie vide si le token fait moins de 3 lettres (évite le bruit comme 'le', 'at', 'in')
    """
    if not isinstance(token, str):
        return ""
    # On ne garde que les lettres de a à z
    token = re.sub(r"[^a-zA-Z]", "", token).lower()
    return token if len(token) > 2 else ""

print("--- GÉNÉRATION DU CORPUS LINGUISTIQUE (FULL) ---")

# 1. Chargement des Mots Anglais
print("1. Chargement des mots anglais...")
with open(PATH_RAW / "english-words.35", "r", encoding="latin-1", errors="ignore") as f:
    # On nettoie à la volée
    words = [clean_token(w) for w in f]
# On retire les vides et les doublons immédiatement via set()
words_list = list(set(filter(None, words)))
print(f"   -> {len(words_list)} mots conservés.")


# 2. Chargement des Noms et Prénoms
print("2. Chargement des prénoms/noms...")
# Lecture rapide sans header
female = pd.read_csv(PATH_RAW / "dist.female.first.txt", sep=r"\s+", header=None, encoding="latin-1")[0]
male   = pd.read_csv(PATH_RAW / "dist.male.first.txt",   sep=r"\s+", header=None, encoding="latin-1")[0]
last   = pd.read_csv(PATH_RAW / "dist.all.last.txt",     sep=r"\s+", header=None, encoding="latin-1")[0]

all_names_raw = pd.concat([female, male, last], ignore_index=True)
# Nettoyage
names_clean = [clean_token(n) for n in all_names_raw]
# Pas de random ! On garde tout.
names_list = list(set(filter(None, names_clean)))
print(f"   -> {len(names_list)} noms conservés.")


# 3. Chargement des Villes et Pays
print("3. Chargement des lieux...")
df_cities = pd.read_csv(
    PATH_RAW / "geonames-all-cities-with-a-population-1000.csv",
    sep=";",
    encoding="utf-8",
    on_bad_lines="skip"
)
# On convertit en string pour être sûr
cities = [clean_token(str(n)) for n in df_cities["Name"]]

with open(PATH_RAW / "countries.txt", "r", encoding="utf-8") as f:
    countries = [clean_token(c) for c in f]

# Fusion et dédoublonnage
places_list = list(set(filter(None, cities + countries)))
print(f"   -> {len(places_list)} lieux conservés.")


# 4. Chargement des mots de passe faibles (RockYou/Common)
print("4. Chargement des mots de passe faibles...")
with open(PATH_RAW / "1000-most-common-passwords.txt", "r") as f:
    # Ici on garde tel quel (juste strip/lower), on veut le mdp exact
    weak_pwds = [p.strip().lower() for p in f if p.strip()]
print(f"   -> {len(weak_pwds)} weak passwords.")


# --- CRÉATION DU DATAFRAME FINAL ---
print("5. Compilation et Sauvegarde...")

corpus = pd.DataFrame({
    "token": words_list + names_list + places_list + weak_pwds,
    "category": ["word"]*len(words_list) + ["name"]*len(names_list) + ["place"]*len(places_list) + ["weak_pwd"]*len(weak_pwds)
})

# Dernier dédoublonnage au cas où un token soit dans plusieurs catégories (ex: 'paris' est un nom et une ville)
# On peut garder les doublons si on veut savoir qu'il appartient aux deux, mais pour simplifier on drop
# Si on veut garder la priorité : on peut trier par catégorie avant, mais ici drop_duplicates garde le premier trouvé
corpus = corpus.drop_duplicates(subset=["token", "category"])

outfile = PATH_PROCESSED / "linguistic_dictionary.csv"
corpus.to_csv(outfile, index=False)

print(f"--- SUCCÈS ---")
print(f"Fichier généré : {outfile}")
print(f"Total entrées  : {len(corpus)}")