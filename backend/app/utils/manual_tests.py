import sys
from pathlib import Path

# --- CONFIGURATION DU CHEMIN (Pour trouver les modules) ---
BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR))

# Import du service d'analyse
from backend.app.services.password_services import analyse_password, load_resources

# On force le chargement des ressources (Dico + Modèle)
print("Chargement des ressources...")
load_resources()


def run_suite():
    # Liste des cas à tester : (Mot de passe, Description attendue)
    scenarios = [
        # --- 1. LES SUICIDAIRES (Leaks) ---
        ("123456", "Leak RockYou classique"),
        ("pokemon", "Leak Pop Culture"),
        ("dragon", "Leak Dictionnaire/Commun"),

        # --- 2. LES PIÈGES LINGUISTIQUES (Ton IA brille ici) ---
        ("Summer2024!", "Mot Dico + Date + Symbole"),
        ("Thomas99@", "Prénom + Chiffre + Symbole"),
        ("Paris75000!", "Ville + Code Postal"),
        ("Restructure!!", "Mot Dico complexe + Symboles"),

        # --- 3. LES FAIBLESSES MATHÉMATIQUES ---
        ("j", "Trop court"),
        ("superlongmotdepassesanschiffresnisymboles", "Long mais faible diversité"),

        # --- 4. LES VRAIS FORTS ---
        ("Hk9#mP2$zL", "Aléatoire généré (10 chars)"),
        ("X7!bQz9@wM_LoP", "Aléatoire généré (14 chars)")
    ]

    print("\n" + "=" * 120)
    print(f" {'PASSWORD':<35} | {'SCORE':<5} | {'IA STRONG?':<10} | {'FEEDBACK PRINCIPAL'}")
    print("=" * 120)

    for pwd, desc in scenarios:
        # Appel à ton IA
        result = analyse_password(pwd)

        score = result['score']
        is_strong = result['is_strong']
        feedbacks = result['feedback']

        # Mise en forme visuelle
        score_display = f"{score}/100"

        if score > 80:
            score_color = "🟢"  # Vert
        elif score > 40:
            score_color = "🟠"  # Orange
        else:
            score_color = "🔴"  # Rouge

        strong_display = "OUI ✅" if is_strong else "NON ❌"

        # On prend juste les 2 premiers feedbacks pour que ça rentre dans la ligne
        feedback_str = " | ".join(feedbacks) if feedbacks else "Aucun (Parfait)"

        print(f" {pwd:<35} | {score_display:<5} {score_color} | {strong_display:<10} | {feedback_str}")
        # print(f"   > Contexte testé : {desc}")
        # (Décommente la ligne ci-dessus si tu veux voir la description du test)

    print("=" * 120)


if __name__ == "__main__":
    run_suite()