from pathlib import Path
import pandas as pd

DATASET_DIR = Path(__file__).resolve().parents[2] / "datasets"

def load_password_dataset():
    df = pd.read_csv(DATASET_DIR / "passwords.csv")
    return df

def analyse_password(pw: str):
    return {
        "length": len(pw),
        "has_digit": any(c.isdigit() for c in pw),
        "has_upper": any(c.isupper() for c in pw),
        "has_lower": any(c.islower() for c in pw),
        "has_special": any(not c.isalnum() for c in pw)
    }
