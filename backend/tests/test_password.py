import unittest
import sys
from pathlib import Path

# --- AJOUT DU CHEMIN POUR LES IMPORTS ---
# Permet de lancer le test depuis n'importe où sans erreur "ModuleNotFound"
BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR))

from backend.app.services.password_services import analyse_password


class TestPasswordAnalysis(unittest.TestCase):

    def test_01_the_ai_paradox(self):
        """
        TEST CRITIQUE : Prouve que l'IA fait la différence entre
        'Structure Humaine' et 'Aléatoire' à entropie égale.
        """
        # Cas A : Fort mathématiquement (Maj, Min, Chiffre, Symbole) mais Humain
        human_pwd = "Thomas2024!"
        res_human = analyse_password(human_pwd)

        # Cas B : Vraiment fort (Généré)
        random_pwd = "Hk9#mP2$zL"
        res_random = analyse_password(random_pwd)

        print(f"\n[VS] Humain ({res_human['score']}) vs Random ({res_random['score']})")

        # Vérifications
        self.assertLess(res_human['score'], 50, "Le mot de passe 'Thomas' devrait avoir un mauvais score IA")
        self.assertGreater(res_random['score'], 80, "Le mot de passe aléatoire devrait avoir un excellent score")
        self.assertTrue(res_random['is_strong'])
        self.assertFalse(res_human['is_strong'])

    def test_02_rockyou_leak(self):
        """
        Vérifie la détection immédiate des mots de passe grillés (Exact Match).
        """
        weak = "123456"
        result = analyse_password(weak)

        print(f"\n[Leak] 123456 -> Score: {result['score']}")

        self.assertLess(result['score'], 10, "123456 doit avoir un score proche de 0")
        # On vérifie que le feedback contient le mot clé "RockYou" ou "pirates"
        feedbacks = " ".join(result['feedback'])
        self.assertIn("RockYou", feedbacks, "Le feedback doit mentionner RockYou")

    def test_03_linguistic_detection(self):
        """
        Vérifie si le dictionnaire détecte les noms et villes cachés.
        """
        # Test Prénom
        res_name = analyse_password("JeanPierre88")
        feedbacks_name = " ".join(res_name['feedback'])
        self.assertIn("prénom", feedbacks_name.lower())

        # Test Ville
        res_city = analyse_password("Marseille2024")
        feedbacks_city = " ".join(res_city['feedback'])
        # Note : adapte le mot clé selon ton password_services.py ("ville", "pays", "lieu")
        self.assertIn("ville", feedbacks_city.lower())

    def test_04_dictionary_word(self):
        """
        Vérifie la détection de mots du dictionnaire anglais.
        """
        # "summer" est confirmé présent dans ton dictionnaire
        # On ajoute des symboles pour avoir un bon score mathématique
        # mais se faire attraper par la linguistique
        res_word = analyse_password("Restructure!!")
        feedbacks = " ".join(res_word['feedback'])

        print(f"\n[Dico] Summer!! -> Feedback: {feedbacks}")

        # On vérifie qu'il détecte bien le dictionnaire OU (cas rare) que le score est bas
        self.assertIn("dictionnaire", feedbacks.lower())
        self.assertLess(res_word['score'], 60, "Un mot du dico + symboles reste moyen/faible")

    def test_05_math_diversity(self):
        """
        Vérifie que la diversité seule est pénalisée.
        """
        # Que des minuscules (même long)
        res_weak = analyse_password("superlongpasswordmaispasdecomplexite")
        feedbacks = " ".join(res_weak['feedback'])

        self.assertIn("variété", feedbacks.lower())
        self.assertLess(res_weak['score'], 50)

    def test_06_edge_cases(self):
        """
        Vérifie que le code ne plante pas sur des cas extrêmes.
        """
        # Vide
        res_empty = analyse_password("")
        self.assertEqual(res_empty['score'], 0)

        # Très court
        res_short = analyse_password("a")
        self.assertIn("Trop court", res_short['feedback'])

        # Caractères bizarres (Emojis)
        # L'IA n'a pas appris les emojis, elle va probablement se baser sur la longueur/entropie
        res_emoji = analyse_password("🔒🔒🔒🔒🔒")
        self.assertIsNotNone(res_emoji['score'])


if __name__ == '__main__':
    unittest.main()