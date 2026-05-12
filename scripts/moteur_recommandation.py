
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors


BASE_DIR = Path(__file__).resolve().parent.parent
HF_CACHE_DIR = BASE_DIR / ".hf_cache"
HF_CACHE_DIR.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("HF_HOME", str(HF_CACHE_DIR))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(HF_CACHE_DIR / "hub"))
os.environ.setdefault("TRANSFORMERS_CACHE", str(HF_CACHE_DIR / "transformers"))

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    SentenceTransformer = None


MODELE_HF_DEFAUT = os.getenv(
    "BOOK_EMBEDDING_MODEL_NAME",
    "AventIQ-AI/all-MiniLM-L6-v2-book-recommendation-system",
)


@dataclass
class Recommandation:
    book_id: int
    titre: str
    score: float
    categorie: str
    auteur: str
    justification: str
    score_semantique: float
    score_collaboratif: float
    score_popularite: float


def normaliser_texte(valeur: Any) -> str:
    if valeur is None:
        return ""
    texte = str(valeur).strip()
    return "" if texte.lower() == "nan" else texte


def construire_texte_livre(ligne: pd.Series) -> str:
    segments = [
        normaliser_texte(ligne.get("title")),
        normaliser_texte(ligne.get("authors")),
        normaliser_texte(ligne.get("categories")),
        normaliser_texte(ligne.get("simple_categories")),
        normaliser_texte(ligne.get("description")),
    ]
    return " | ".join(segment for segment in segments if segment)


@lru_cache(maxsize=2)
def charger_encodeur(modele_hf: str = MODELE_HF_DEFAUT):
    if SentenceTransformer is None:
        raise RuntimeError(
            "sentence-transformers n'est pas installé. "
            "Installez-le pour utiliser le moteur hybride finetuné."
        )
    return SentenceTransformer(modele_hf)


def charger_catalogue(path_catalogue: str | os.PathLike[str]) -> pd.DataFrame:
    catalogue = pd.read_csv(path_catalogue)
    catalogue["book_id"] = catalogue["book_id"].astype(int)
    for colonne in [
        "title",
        "authors",
        "categories",
        "description",
        "simple_categories",
        "thumbnail",
    ]:
        if colonne not in catalogue.columns:
            catalogue[colonne] = ""
        catalogue[colonne] = catalogue[colonne].fillna("")

    for colonne in ["average_rating", "ratings_count", "num_pages", "published_year"]:
        if colonne not in catalogue.columns:
            catalogue[colonne] = 0.0
        catalogue[colonne] = pd.to_numeric(catalogue[colonne], errors="coerce").fillna(0.0)

    catalogue["texte_recommandation"] = catalogue.apply(construire_texte_livre, axis=1)
    return catalogue.drop_duplicates(subset=["book_id"]).reset_index(drop=True)


def preparer_interactions(df: pd.DataFrame) -> pd.DataFrame:
    colonnes = ["user_id", "book_id", "book_title", "note_interaction"]
    interactions = df[colonnes].copy()
    interactions["user_id"] = interactions["user_id"].astype(int)
    interactions["book_id"] = interactions["book_id"].astype(int)
    interactions["note_interaction"] = interactions["note_interaction"].astype(float)
    return interactions.groupby(["user_id", "book_id", "book_title"], as_index=False)["note_interaction"].sum()


def _construire_modele_collaboratif(interactions: pd.DataFrame) -> tuple[Any, pd.DataFrame]:
    matrice = interactions.pivot_table(
        index="user_id",
        columns="book_id",
        values="note_interaction",
        aggfunc="sum",
        fill_value=0.0,
    )

    modele = None
    if len(matrice.index) >= 2:
        modele = NearestNeighbors(metric="cosine", algorithm="brute")
        modele.fit(matrice.values)

    return modele, matrice


def _calculer_popularite(interactions: pd.DataFrame, catalogue: pd.DataFrame) -> dict[int, float]:
    popularite_emprunts = interactions.groupby("book_id")["note_interaction"].sum().to_dict()
    max_emprunts = max(popularite_emprunts.values(), default=1.0)
    max_ratings = max(float(catalogue["ratings_count"].max()), 1.0)

    scores: dict[int, float] = {}
    for ligne in catalogue.itertuples():
        score_emprunts = float(popularite_emprunts.get(int(ligne.book_id), 0.0)) / max_emprunts
        score_note = float(getattr(ligne, "average_rating", 0.0)) / 5.0
        score_volume = float(getattr(ligne, "ratings_count", 0.0)) / max_ratings
        scores[int(ligne.book_id)] = round(
            (0.6 * score_emprunts) + (0.25 * score_note) + (0.15 * score_volume),
            6,
        )
    return scores


def _embedder_catalogue(catalogue: pd.DataFrame, modele_hf: str) -> np.ndarray:
    encodeur = charger_encodeur(modele_hf)
    textes = catalogue["texte_recommandation"].tolist()
    embeddings = encodeur.encode(
        textes,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(embeddings, dtype=np.float32)


def entrainer_modele_hybride(
    df_emprunts: pd.DataFrame,
    df_catalogue: pd.DataFrame,
    modele_hf: str = MODELE_HF_DEFAUT,
) -> dict[str, Any]:
    interactions = preparer_interactions(df_emprunts)
    modele_collaboratif, matrice = _construire_modele_collaboratif(interactions)

    catalogue = df_catalogue.copy()
    titres_par_id = catalogue.set_index("book_id")["title"].to_dict()
    catalogue_embeddings = _embedder_catalogue(catalogue, modele_hf)
    popularite = _calculer_popularite(interactions, catalogue)

    livres_populaires = sorted(
        [
            {
                "book_id": int(ligne.book_id),
                "book_title": ligne.title,
                "score_popularite": float(popularite.get(int(ligne.book_id), 0.0)),
            }
            for ligne in catalogue.itertuples()
        ],
        key=lambda item: item["score_popularite"],
        reverse=True,
    )

    return {
        "modele_collaboratif": modele_collaboratif,
        "matrice": matrice,
        "titres_par_id": titres_par_id,
        "livres_populaires": livres_populaires,
        "popularite_par_livre": popularite,
        "catalogue": catalogue.to_dict(orient="records"),
        "catalogue_embeddings": catalogue_embeddings,
        "modele_hf": modele_hf,
        "metadonnees": {
            "nombre_utilisateurs": int(len(matrice.index)),
            "nombre_livres": int(len(catalogue.index)),
            "algorithme": "Hybride collaboratif + sémantique",
            "modele_semantique": modele_hf,
            "filtres": [
                "exclusion des livres déjà empruntés",
                "exclusion des livres indisponibles",
                "prise en compte de la popularité",
            ],
        },
    }


def _normaliser_scores(scores: dict[int, float]) -> dict[int, float]:
    if not scores:
        return {}
    maximum = max(scores.values())
    if maximum <= 0:
        return {cle: 0.0 for cle in scores}
    return {cle: round(valeur / maximum, 6) for cle, valeur in scores.items()}


def _scores_collaboratifs(user_id: int, artefact: dict[str, Any]) -> dict[int, float]:
    matrice: pd.DataFrame = artefact["matrice"]
    modele = artefact["modele_collaboratif"]

    if modele is None or user_id not in matrice.index:
        return {}

    ligne = matrice.loc[[user_id]]
    k = min(4, len(matrice.index))
    distances, indices = modele.kneighbors(ligne.values, n_neighbors=k)

    deja_vus = set(matrice.loc[user_id][matrice.loc[user_id] > 0].index.tolist())
    scores: dict[int, float] = {}

    for distance, indice in zip(distances[0], indices[0]):
        voisin_id = matrice.index[indice]
        if voisin_id == user_id:
            continue
        similarite = 1.0 - float(distance)
        livres_voisin = matrice.loc[voisin_id]
        for book_id, valeur in livres_voisin.items():
            if float(valeur) <= 0 or int(book_id) in deja_vus:
                continue
            scores[int(book_id)] = scores.get(int(book_id), 0.0) + (similarite * float(valeur))

    return _normaliser_scores(scores)


def _construire_df_catalogue_runtime(
    artefact: dict[str, Any],
    catalogue_runtime: list[dict[str, Any]] | None,
) -> pd.DataFrame:
    base = pd.DataFrame(artefact["catalogue"]).copy()
    if not catalogue_runtime:
        if "actif" not in base.columns:
            base["actif"] = True
        if "quantite_disponible" not in base.columns:
            base["quantite_disponible"] = 1
        return base

    runtime = pd.DataFrame(catalogue_runtime).rename(
        columns={
            "id": "book_id",
            "titre": "title",
            "auteur": "authors",
            "categorie": "categories",
        }
    )
    runtime["book_id"] = runtime["book_id"].astype(int)
    if "description" not in runtime.columns:
        runtime["description"] = ""
    if "categories" not in runtime.columns:
        runtime["categories"] = ""
    if "authors" not in runtime.columns:
        runtime["authors"] = ""

    fusion = base.merge(
        runtime,
        on="book_id",
        how="outer",
        suffixes=("_entrainement", "_runtime"),
    )

    for colonne in [
        "title",
        "authors",
        "categories",
        "description",
        "simple_categories",
        "thumbnail",
        "average_rating",
        "ratings_count",
        "num_pages",
        "published_year",
        "actif",
        "quantite_disponible",
    ]:
        colonne_runtime = f"{colonne}_runtime"
        colonne_entrainement = f"{colonne}_entrainement"
        if colonne_runtime in fusion.columns or colonne_entrainement in fusion.columns:
            fusion[colonne] = fusion.get(colonne_runtime, pd.Series(dtype=object)).combine_first(
                fusion.get(colonne_entrainement, pd.Series(dtype=object))
            )

    for colonne in ["actif"]:
        if colonne in fusion.columns:
            fusion[colonne] = (
                fusion[colonne]
                .apply(lambda valeur: True if str(valeur).strip().lower() in {"", "nan", "none"} else valeur)
                .fillna(True)
                .astype(bool)
            )
    for colonne in ["quantite_disponible"]:
        if colonne in fusion.columns:
            fusion[colonne] = pd.to_numeric(fusion[colonne], errors="coerce").fillna(1).astype(int)

    colonnes_finales = [
        "book_id",
        "title",
        "authors",
        "categories",
        "description",
        "simple_categories",
        "thumbnail",
        "average_rating",
        "ratings_count",
        "num_pages",
        "published_year",
        "actif",
        "quantite_disponible",
    ]
    for colonne in colonnes_finales:
        if colonne not in fusion.columns:
            fusion[colonne] = ""

    if "actif" in fusion.columns:
        fusion["actif"] = (
            fusion["actif"]
            .apply(lambda valeur: True if str(valeur).strip().lower() in {"", "nan", "none"} else valeur)
            .fillna(True)
            .astype(bool)
        )
    if "quantite_disponible" in fusion.columns:
        fusion["quantite_disponible"] = pd.to_numeric(fusion["quantite_disponible"], errors="coerce").fillna(1).astype(int)

    fusion["texte_recommandation"] = fusion.apply(construire_texte_livre, axis=1)
    return fusion[colonnes_finales + ["texte_recommandation"]].drop_duplicates("book_id").reset_index(drop=True)


def _index_catalogue(df_catalogue: pd.DataFrame) -> dict[int, int]:
    return {int(ligne.book_id): index for index, ligne in enumerate(df_catalogue.itertuples())}


def _embeddings_catalogue_runtime(
    artefact: dict[str, Any],
    df_catalogue_runtime: pd.DataFrame,
) -> np.ndarray:
    base = pd.DataFrame(artefact["catalogue"])
    embeddings_base = np.asarray(artefact["catalogue_embeddings"], dtype=np.float32)
    index_base = _index_catalogue(base)
    embeddings_runtime: list[np.ndarray | None] = [None] * len(df_catalogue_runtime.index)
    lignes_a_encoder: list[str] = []
    positions_a_encoder: list[int] = []

    for position, ligne in enumerate(df_catalogue_runtime.itertuples()):
        book_id = int(ligne.book_id)
        if book_id in index_base:
            embeddings_runtime[position] = embeddings_base[index_base[book_id]]
        else:
            lignes_a_encoder.append(ligne.texte_recommandation)
            positions_a_encoder.append(position)

    if lignes_a_encoder:
        encodeur = charger_encodeur(artefact["modele_hf"])
        embeddings_nouveaux = encodeur.encode(
            lignes_a_encoder,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        for position, embedding in zip(positions_a_encoder, embeddings_nouveaux):
            embeddings_runtime[position] = np.asarray(embedding, dtype=np.float32)

    return np.vstack(embeddings_runtime).astype(np.float32)


def _historique_runtime_vers_ids(historique_runtime: list[dict[str, Any]] | None) -> set[int]:
    if not historique_runtime:
        return set()
    return {
        int(item["livre_id"])
        for item in historique_runtime
        if item.get("livre_id") is not None
    }


def _ids_empruntes_par_utilisateur(
    user_id: int,
    artefact: dict[str, Any],
    historique_runtime: list[dict[str, Any]] | None = None,
) -> set[int]:
    matrice: pd.DataFrame = artefact["matrice"]
    ids = set()
    if user_id in matrice.index:
        ids |= {int(book_id) for book_id in matrice.loc[user_id][matrice.loc[user_id] > 0].index.tolist()}
    ids |= _historique_runtime_vers_ids(historique_runtime)
    return ids


def _profil_semantique_utilisateur(
    ids_empruntes: set[int],
    index_par_book_id: dict[int, int],
    embeddings_catalogue: np.ndarray,
) -> np.ndarray | None:
    positions = [index_par_book_id[book_id] for book_id in ids_empruntes if book_id in index_par_book_id]
    if not positions:
        return None
    profil = np.mean(embeddings_catalogue[positions], axis=0)
    norme = np.linalg.norm(profil)
    if norme == 0:
        return None
    return (profil / norme).astype(np.float32)


def _scores_semantiques(
    profil_utilisateur: np.ndarray | None,
    df_catalogue_runtime: pd.DataFrame,
    embeddings_catalogue: np.ndarray,
    ids_exclus: set[int],
) -> dict[int, float]:
    if profil_utilisateur is None:
        return {}

    similarites = cosine_similarity([profil_utilisateur], embeddings_catalogue)[0]
    scores = {
        int(df_catalogue_runtime.iloc[index]["book_id"]): float(score)
        for index, score in enumerate(similarites)
        if int(df_catalogue_runtime.iloc[index]["book_id"]) not in ids_exclus
    }
    return _normaliser_scores(scores)


def recommander_pour_utilisateur(
    user_id: int,
    artefact: dict[str, Any],
    limite: int = 5,
    catalogue_runtime: list[dict[str, Any]] | None = None,
    historique_runtime: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    df_catalogue_runtime = _construire_df_catalogue_runtime(artefact, catalogue_runtime)
    embeddings_runtime = _embeddings_catalogue_runtime(artefact, df_catalogue_runtime)
    index_runtime = _index_catalogue(df_catalogue_runtime)
    deja_empruntes = _ids_empruntes_par_utilisateur(user_id, artefact, historique_runtime)

    profil = _profil_semantique_utilisateur(deja_empruntes, index_runtime, embeddings_runtime)
    scores_semantiques = _scores_semantiques(profil, df_catalogue_runtime, embeddings_runtime, deja_empruntes)
    scores_collaboratifs = _scores_collaboratifs(user_id, artefact)
    scores_popularite = artefact["popularite_par_livre"]

    resultats: list[Recommandation] = []
    for ligne in df_catalogue_runtime.itertuples():
        book_id = int(ligne.book_id)
        if book_id in deja_empruntes:
            continue
        if not bool(getattr(ligne, "actif", True)):
            continue
        if int(getattr(ligne, "quantite_disponible", 1)) <= 0:
            continue

        score_semantique = float(scores_semantiques.get(book_id, 0.0))
        score_collaboratif = float(scores_collaboratifs.get(book_id, 0.0))
        score_popularite = float(scores_popularite.get(book_id, 0.0))

        if profil is None and score_collaboratif == 0.0 and score_popularite == 0.0:
            continue

        score_total = (0.5 * score_semantique) + (0.3 * score_collaboratif) + (0.2 * score_popularite)
        justification = (
            f"score sémantique={score_semantique:.2f}, "
            f"collaboratif={score_collaboratif:.2f}, popularité={score_popularite:.2f}"
        )
        resultats.append(
            Recommandation(
                book_id=book_id,
                titre=normaliser_texte(ligne.title),
                score=round(score_total, 4),
                categorie=normaliser_texte(getattr(ligne, "categories", "")),
                auteur=normaliser_texte(getattr(ligne, "authors", "")),
                justification=justification,
                score_semantique=round(score_semantique, 4),
                score_collaboratif=round(score_collaboratif, 4),
                score_popularite=round(score_popularite, 4),
            )
        )

    resultats = sorted(resultats, key=lambda item: item.score, reverse=True)
    return [item.__dict__ for item in resultats[:limite]]


def predire_score(
    user_id: int,
    book_id: int,
    artefact: dict[str, Any],
    historique_runtime: list[dict[str, Any]] | None = None,
) -> float:
    catalogue = artefact["catalogue"]
    recommandations = recommander_pour_utilisateur(
        user_id=user_id,
        artefact=artefact,
        limite=max(10, len(catalogue)),
        catalogue_runtime=catalogue,
        historique_runtime=historique_runtime,
    )
    correspondance = next((item for item in recommandations if int(item["book_id"]) == int(book_id)), None)
    if correspondance:
        return float(correspondance["score"])
    return float(artefact["popularite_par_livre"].get(int(book_id), 0.0))


def normaliser_predictions(predictions: list[float]) -> list[float]:
    if not predictions:
        return []
    maximum = max(predictions)
    if maximum == 0:
        return [0.0 for _ in predictions]
    return [prediction / maximum for prediction in predictions]


def calculer_rmse_mae(reels: list[float], predictions: list[float]) -> dict[str, float]:
    if not reels:
        return {"rmse": 0.0, "mae": 0.0}
    reels_np = np.array(reels, dtype=float)
    preds_np = np.array(predictions, dtype=float)
    rmse = float(np.sqrt(np.mean((reels_np - preds_np) ** 2)))
    mae = float(np.mean(np.abs(reels_np - preds_np)))
    return {"rmse": round(rmse, 4), "mae": round(mae, 4)}
