import math
import string

# --- CONSTANTES ---
# Le seuil où la longueur est considérée "parfaite"
MAX_LENGTH_CEILING = 20
# Le seuil où l'entropie est "parfaite" (bits)
MAX_ENTROPY = 100.0


def compute_length_norm(password: str) -> float:
    """
    Calcule la longueur normalisée via une Sigmoïde.

    Logique :
    - On veut pénaliser fort les mots de passe courts (< 8).
    - On veut récompenser vite ceux qui atteignent 12-14.
    - On sature vers 1.0 autour de 20.

    Formule Sigmoïde ajustée :
    Centre (x0) = 11 caractères (c'est le pivot moyen/fort)
    Pente (k) = 0.5 (courbe assez douce)
    """
    L = len(str(password))
    if L == 0: return 0.0

    # Formule Sigmoïde standard : 1 / (1 + e^-k(x-x0))
    # Centre à 11, pente 0.5
    sigmoid_value = 1 / (1 + math.exp(-0.5 * (L - 11)))

    return sigmoid_value


def compute_diversity(password: str) -> float:
    """
    Calcule la diversité avec une échelle NON-LINÉAIRE (Récompense les standards).

    Logique :
    - 0 type  : 0.0
    - 1 type  : 0.1 (Très mauvais, ex: "password")
    - 2 types : 0.4 (Moyen, ex: "Password")
    - 3 types : 0.8 (Bon standard Web, ex: "Password1")
    - 4 types : 1.0 (Excellent, ex: "Password1!")
    """
    password = str(password)
    count = 0

    # Détection des classes
    if any(c.islower() for c in password): count += 1
    if any(c.isupper() for c in password): count += 1
    if any(c.isdigit() for c in password): count += 1
    if any(c in string.punctuation for c in password): count += 1

    # Mapping des scores (Ton idée est la bonne)
    scores = {
        0: 0.0,
        1: 0.1,
        2: 0.4,
        3: 0.8,
        4: 1.0
    }

    return scores.get(count, 0.0)


def compute_entropy(password: str) -> float:
    """
    Entropie de Shannon normalisée (Inchangée, c'est la référence).
    """
    password = str(password)
    if not password: return 0.0

    pool_size = 0
    if any(c.islower() for c in password): pool_size += 26
    if any(c.isupper() for c in password): pool_size += 26
    if any(c.isdigit() for c in password): pool_size += 10
    if any(c in string.punctuation for c in password): pool_size += 32

    if pool_size == 0: return 0.0

    entropy_bits = len(password) * math.log2(pool_size)

    return min(entropy_bits / MAX_ENTROPY, 1.0)

def calculate_bruteforce_time(password):
    """
    Estime le temps de craquage par force brute pure (hors dictionnaire).
    Hypothèse : Hacker avec un bon GPU (RTX 3090/4090) -> 100 Milliards hash/sec (MD5)
    """
    # 1. Calcul du Pool (N)
    pool_size = 0
    if any(c.islower() for c in password): pool_size += 26
    if any(c.isupper() for c in password): pool_size += 26
    if any(c.isdigit() for c in password): pool_size += 10
    if any(c in string.punctuation for c in password): pool_size += 33

    if pool_size == 0: return "Instant"

    # 2. Calcul des combinaisons (N^L)
    combinations = pool_size ** len(password)

    # 3. Vitesse (Hashrate)
    # 100 GigaHashes/seconde (très rapide, scénario pessimiste pour l'utilisateur)
    hashrate = 100_000_000_000

    # 4. Temps en secondes (Moyenne = 50% de l'espace)
    seconds = (combinations / 2) / hashrate

    # 5. Conversion lisible
    if seconds < 1: return "Instantané"
    if seconds < 60: return f"{int(seconds)} secondes"
    if seconds < 3600: return f"{int(seconds / 60)} minutes"
    if seconds < 86400: return f"{int(seconds / 3600)} heures"
    if seconds < 31536000: return f"{int(seconds / 86400)} jours"

    years = int(seconds / 31536000)
    if years > 1000000: return "Des millions d'années"
    return f"{years} ans"