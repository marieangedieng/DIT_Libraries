from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = BASE_DIR / "data" / "raw" / "loans.csv"
PROCESSED_PATH = BASE_DIR / "data" / "processed" / "loans_clean.csv"


def main():
    df = pd.read_csv(RAW_PATH)
    df.columns = [colonne.strip().lower() for colonne in df.columns]
    df = df.dropna(subset=["user_id", "book_id", "book_title", "date_emprunt", "date_retour_prevue"])

    df["date_emprunt"] = pd.to_datetime(df["date_emprunt"])
    df["date_retour_prevue"] = pd.to_datetime(df["date_retour_prevue"])
    df["date_retour_effective"] = pd.to_datetime(df["date_retour_effective"], errors="coerce")
    statut_series = df["statut"].fillna("").astype(str).str.lower()
    df["note_interaction"] = np.select(
        [
            statut_series.eq("retourne"),
            statut_series.eq("en_retard"),
            statut_series.eq("en_cours"),
        ],
        [
            1.0,
            0.7,
            0.6,
        ],
        default=0.5,
    )
    df["retard_jours"] = (
        (df["date_retour_effective"].fillna(df["date_retour_prevue"]) - df["date_retour_prevue"])
        .dt.days.clip(lower=0)
    )
    df["a_rendu"] = df["date_retour_effective"].notna().astype(int)

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)
    print(f"Fichier nettoyé généré: {PROCESSED_PATH}")


if __name__ == "__main__":
    main()
