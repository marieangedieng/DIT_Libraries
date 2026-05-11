import json
from pathlib import Path

import pandas as pd

from moteur_recommandation import (
    MODELE_HF_DEFAUT,
    calculer_rmse_mae,
    charger_catalogue,
    entrainer_modele_hybride,
    normaliser_predictions,
    predire_score,
)


BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_PATH = BASE_DIR / "data" / "processed" / "loans_clean.csv"
CATALOGUE_PATH = BASE_DIR / "data" / "raw" / "books_catalog.csv"
METRICS_PATH = BASE_DIR / "metrics" / "metrics.json"


def main():
    df = pd.read_csv(PROCESSED_PATH)
    df_catalogue = charger_catalogue(CATALOGUE_PATH)

    if len(df) < 6:
        metrics = {"rmse": 0.0, "mae": 0.0, "observations_test": 0}
        METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return

    test_df = df.groupby("user_id", group_keys=False).tail(1)
    train_df = df.drop(index=test_df.index)
    artefact = entrainer_modele_hybride(
        df_emprunts=train_df,
        df_catalogue=df_catalogue,
        modele_hf=MODELE_HF_DEFAUT,
    )

    reels = test_df["note_interaction"].astype(float).tolist()
    predictions_brutes = []
    for ligne in test_df.itertuples():
        historique_utilisateur = train_df.loc[train_df["user_id"] == int(ligne.user_id), ["book_id"]]
        historique_runtime = [{"livre_id": int(item.book_id)} for item in historique_utilisateur.itertuples()]
        predictions_brutes.append(
            predire_score(
                user_id=int(ligne.user_id),
                book_id=int(ligne.book_id),
                artefact=artefact,
                historique_runtime=historique_runtime,
            )
        )

    predictions = normaliser_predictions(predictions_brutes)
    metrics = calculer_rmse_mae(reels, predictions)
    metrics["observations_test"] = int(len(test_df))
    metrics["utilisateurs_train"] = int(train_df["user_id"].nunique())
    metrics["livres_train"] = int(train_df["book_id"].nunique())
    metrics["algorithme"] = "Hybride collaboratif + sémantique"
    metrics["modele_semantique"] = MODELE_HF_DEFAUT

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Métriques générées: {METRICS_PATH}")


if __name__ == "__main__":
    main()
