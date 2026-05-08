from pathlib import Path
import json
import os
import subprocess
import sys
from typing import Any

import joblib
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


def determiner_base_dir() -> Path:
    if os.getenv("WORKSPACE_DIR"):
        return Path(os.getenv("WORKSPACE_DIR", ".")).resolve()

    chemin = Path(__file__).resolve()
    return chemin.parents[2] if len(chemin.parents) > 2 else chemin.parent


BASE_DIR = determiner_base_dir()
SCRIPTS_DIR = BASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from moteur_recommandation import recommander_pour_utilisateur  # noqa: E402


MODELE_PATH = BASE_DIR / "models" / "model.pkl"
METRICS_PATH = BASE_DIR / "metrics" / "metrics.json"
PYTHON_BIN = sys.executable
SERVICE_LIVRES_URL = os.getenv("SERVICE_LIVRES_URL", "http://localhost:8001")
SERVICE_EMPRUNTS_URL = os.getenv("SERVICE_EMPRUNTS_URL", "http://localhost:8003")

app = FastAPI(
    title="DIT Librairie - Recommandation",
    description="API de recommandation hybride basée sur l'historique des emprunts et un modèle finetuné Hugging Face.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def charger_modele() -> Any:
    if not MODELE_PATH.exists():
        raise HTTPException(status_code=404, detail="Le modèle n'est pas encore entraîné.")
    return joblib.load(MODELE_PATH)


def recuperer_json(url: str) -> Any:
    response = requests.get(url, timeout=8)
    response.raise_for_status()
    return response.json()


def recuperer_catalogue_runtime() -> list[dict[str, Any]]:
    try:
        return recuperer_json(f"{SERVICE_LIVRES_URL}/api/livres/")
    except requests.RequestException:
        return []


def recuperer_historique_utilisateur(user_id: int) -> list[dict[str, Any]]:
    try:
        return recuperer_json(f"{SERVICE_EMPRUNTS_URL}/api/emprunts/utilisateur/{user_id}/")
    except requests.RequestException:
        return []


@app.get("/health")
def health():
    return {"service": "recommandation", "statut": "ok"}


@app.get("/recommendations/{user_id}")
def recommendations(user_id: int, limite: int = Query(default=5, ge=1, le=20)):
    artefact = charger_modele()
    catalogue_runtime = recuperer_catalogue_runtime()
    historique_runtime = recuperer_historique_utilisateur(user_id)
    recommandations = recommander_pour_utilisateur(
        user_id=user_id,
        artefact=artefact,
        limite=limite,
        catalogue_runtime=catalogue_runtime,
        historique_runtime=historique_runtime,
    )
    return {
        "utilisateur_id": user_id,
        "total": len(recommandations),
        "modele_semantique": artefact.get("modele_hf"),
        "recommandations": recommandations,
    }


@app.post("/train")
def train():
    try:
        subprocess.run([PYTHON_BIN, str(SCRIPTS_DIR / "preprocess.py")], check=True)
        subprocess.run([PYTHON_BIN, str(SCRIPTS_DIR / "train.py")], check=True)
        subprocess.run([PYTHON_BIN, str(SCRIPTS_DIR / "evaluate.py")], check=True)
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=f"Échec du ré-entraînement: {exc}") from exc

    return {"message": "Ré-entraînement terminé avec succès."}


@app.get("/metrics")
def metrics():
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=404, detail="Aucune métrique disponible.")
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


@app.get("/model-info")
def model_info():
    artefact = charger_modele()
    return artefact.get("metadonnees", {})
