import subprocess
import sys
import time
from pathlib import Path

# --- CONFIGURATION DES CHEMINS ---
# Ce script se trouve dans backend/app/
APP_DIR = Path(__file__).resolve().parent
UTILS_DIR = APP_DIR / "utils"
SERVICES_DIR = APP_DIR / "services"

# Définition du pipeline avec les chemins exacts
PIPELINE = [
    ("1. Création du Dictionnaire", UTILS_DIR / "dictionnary_loader.py"),
    ("2. Génération du Dataset", UTILS_DIR / "dataset_loader.py"),
    ("3. Préparation Tenseurs DL", UTILS_DIR / "dl_data_loader.py"),
    ("4. Entraînement ML Classique", SERVICES_DIR / "train_model.py"),
    ("5. Entraînement Deep Learning", SERVICES_DIR / "train_dl_models.py"),
    ("6. Entraînement Modèle Hybride", SERVICES_DIR / "train_hybrid.py"),
    ("7. Audit Final", UTILS_DIR / "audit_datasets.py")
]


def run_pipeline():
    print("=" * 60)
    print(" 🚀 LANCEMENT DU PIPELINE D'ENTRAÎNEMENT COMPLET")
    print("=" * 60)

    start_time_global = time.time()

    for step_name, script_path in PIPELINE:
        print(f"\n⏳ ÉTAPE : {step_name}")
        print(f"📄 Fichier : {script_path.name}")
        print("-" * 40)

        if not script_path.exists():
            print(f"❌ ERREUR : Fichier introuvable ({script_path})")
            sys.exit(1)

        start_time_step = time.time()

        # Exécution du script dans un sous-processus
        result = subprocess.run([sys.executable, str(script_path)])

        if result.returncode != 0:
            print(f"\n❌ ERREUR FATALE lors de l'étape : {step_name}")
            print("Arrêt du pipeline.")
            sys.exit(result.returncode)

        step_duration = time.time() - start_time_step
        print(f"✅ ÉTAPE TERMINÉE en {step_duration:.2f}s")

    total_duration = time.time() - start_time_global
    print("\n" + "=" * 60)
    print(f" 🎉 PIPELINE TERMINÉ AVEC SUCCÈS EN {total_duration:.2f}s !")
    print(" Les modèles sont prêts dans backend/app/models/")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()