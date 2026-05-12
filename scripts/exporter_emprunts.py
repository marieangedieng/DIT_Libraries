from pathlib import Path
import os

import pandas as pd
import pymysql


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = BASE_DIR / "data" / "raw" / "loans.csv"


def exporter_depuis_mysql():
    connexion = pymysql.connect(
        database=os.getenv("MYSQL_EMPRUNTS_DB_NAME", "emprunts_db"),
        user=os.getenv("MYSQL_USER", "dit"),
        password=os.getenv("MYSQL_PASSWORD", "dit"),
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

    requete = """
        SELECT
            utilisateur_id AS user_id,
            utilisateur_nom AS user_name,
            livre_id AS book_id,
            livre_titre AS book_title,
            date_emprunt,
            date_retour_prevue,
            date_retour_effective,
            statut
        FROM gestion_emprunts_emprunt
        ORDER BY date_emprunt DESC
    """

    with connexion.cursor() as curseur:
        curseur.execute(requete)
        lignes = curseur.fetchall()

    connexion.close()
    df = pd.DataFrame(lignes)
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_PATH, index=False)
    print(f"Historique exporté vers {RAW_PATH}")


if __name__ == "__main__":
    exporter_depuis_mysql()
