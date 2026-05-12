from pathlib import Path

import joblib
import pandas as pd

from moteur_recommandation import MODELE_HF_DEFAUT, charger_catalogue, entrainer_modele_hybride


BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_PATH = BASE_DIR / "data" / "processed" / "loans_clean.csv"
CATALOGUE_PATH = BASE_DIR / "data" / "raw" / "books_catalog.csv"
MODEL_PATH = BASE_DIR / "models" / "model.pkl"


def main():
    df_emprunts = pd.read_csv(PROCESSED_PATH)
    df_catalogue = charger_catalogue(CATALOGUE_PATH)
    artefact = entrainer_modele_hybride(
        df_emprunts=df_emprunts,
        df_catalogue=df_catalogue,
        modele_hf=MODELE_HF_DEFAUT,
    )
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artefact, MODEL_PATH)
    print(f"Modèle hybride entraîné et sauvegardé: {MODEL_PATH}")


if __name__ == "__main__":
    main()
