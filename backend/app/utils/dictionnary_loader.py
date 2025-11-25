import pandas as pd
import random
import re

path = "../../../datasets/Dictionnaries/raw/"

def clean_token(token):
    if not isinstance(token, str):
        return ""
    token = token.lower()
    token = re.sub(r"[^a-z]", "", token)
    return token

with open(path+"english-words.35", "r", encoding="latin-1", errors="ignore") as f:
    words = [w.strip() for w in f if w.strip()]
words_20k = random.sample(words, 22000)
words_20k = [clean_token(w) for w in words_20k if clean_token(w)]

female = pd.read_csv(path+"dist.female.first.txt", sep=r"\s+", header=None, encoding="latin-1")[0]
male   = pd.read_csv(path+"dist.male.first.txt",   sep=r"\s+", header=None, encoding="latin-1")[0]
last = pd.read_csv(path+"dist.all.last.txt", sep=r"\s+", header=None, encoding="latin-1")[0]
all_names = pd.concat([female, male, last], ignore_index=True).drop_duplicates()
all_names = [clean_token(n) for n in all_names if isinstance(n, str) and clean_token(n)]
names_5k = random.sample(all_names, 5500)

df_cities = pd.read_csv(
    path + "geonames-all-cities-with-a-population-1000.csv",
    sep=";",
    encoding="utf-8",
    on_bad_lines="skip"
)
cities = [clean_token(n) for n in df_cities["Name"].dropna() if clean_token(n)]

with open(path+"countries.txt", "r", encoding="utf-8") as f:
    countries = [clean_token(c) for c in f if clean_token(c)]

places = list(dict.fromkeys(cities + countries))
places_1k = random.sample(places, 1200)

with open(path+"1000-most-common-passwords.txt", "r") as f:
    weak_pwds = [p.strip().lower() for p in f if p.strip()]

corpus = pd.DataFrame({
    "token": words_20k + names_5k + places_1k + weak_pwds,
    "category": ["word"]*len(words_20k) + ["name"]*len(names_5k) + ["place"]*len(places_1k) + ["weak_pwd"]*len(weak_pwds)
})

corpus = corpus.drop_duplicates(subset=["token", "category"]).reset_index(drop=True)

corpus.to_csv("../../../datasets/Dictionnaries/processed/linguistic_dictionary.csv", index=False)
print(f"Corpus final : {len(corpus)} lignes")
print(len(words_20k), len(names_5k), len(places_1k), len(weak_pwds))