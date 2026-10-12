"""
Integración de las fuentes de StreamView Analytics.

Une películas, series y el subconjunto financiero de películas en tablas
consistentes, con una llave única (tipo + show_id), y deja listas las
variables derivadas que usan el dashboard y los análisis.

Uso desde la raíz del proyecto:
    python src/integracion.py      # regenera data/processed/master*.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
PROCESSED = BASE / "data" / "processed"

RELLENO_GENERO = {"Sin Género", "Unknown"}
RELLENO_PAIS = {"Sin Información"}

# Etiquetas en español para visualización (los géneros propios de series
# como "Action & Adventure" se conservan tal como vienen en la fuente).
GENEROS_ES = {
    "Animation": "Animación", "Action": "Acción", "Comedy": "Comedia",
    "Horror": "Terror", "Family": "Familia", "Documentary": "Documental",
    "Crime": "Crimen", "Adventure": "Aventura",
    "Science Fiction": "Ciencia ficción", "Fantasy": "Fantasía",
    "Music": "Música", "History": "Historia", "War": "Guerra",
    "Mystery": "Misterio", "TV Movie": "Película de TV",
}
PAISES_ES = {
    "United States of America": "Estados Unidos", "United Kingdom": "Reino Unido",
    "Japan": "Japón", "China": "China", "South Korea": "Corea del Sur",
    "France": "Francia", "Canada": "Canadá", "Germany": "Alemania",
    "India": "India", "Spain": "España", "Italy": "Italia", "Mexico": "México",
    "Brazil": "Brasil", "Australia": "Australia", "Russia": "Rusia",
    "Argentina": "Argentina", "Chile": "Chile", "Colombia": "Colombia",
    "Hong Kong": "Hong Kong", "Taiwan": "Taiwán", "Turkey": "Turquía",
    "Sweden": "Suecia", "Denmark": "Dinamarca", "Norway": "Noruega",
    "Netherlands": "Países Bajos", "Belgium": "Bélgica", "Ireland": "Irlanda",
    "Poland": "Polonia", "Thailand": "Tailandia", "Philippines": "Filipinas",
    "Indonesia": "Indonesia", "Egypt": "Egipto", "South Africa": "Sudáfrica",
    "New Zealand": "Nueva Zelanda", "Switzerland": "Suiza", "Austria": "Austria",
    "Finland": "Finlandia", "Czech Republic": "República Checa",
    "Hungary": "Hungría", "Greece": "Grecia", "Portugal": "Portugal",
    "Israel": "Israel", "Iran": "Irán", "Ukraine": "Ucrania",
}


def _a_lista(serie: pd.Series, relleno: set, traduccion: dict) -> pd.Series:
    """Convierte 'A, B, C' en ['A', 'B', 'C'] sin categorías de relleno."""
    def convertir(texto):
        if not isinstance(texto, str):
            return []
        salida = []
        for x in texto.split(", "):
            x = x.strip()
            if x and x not in relleno:
                salida.append(traduccion.get(x, x))
        return salida
    return serie.apply(convertir)


def cargar_datos():
    """Devuelve (df, dfin).

    df   : todos los títulos (películas + series) con llave única.
    dfin : películas con presupuesto y recaudación válidos, más ROI y tramo.
    """
    peliculas = pd.read_csv(PROCESSED / "netflix_movies_clean.csv").assign(tipo="Película")
    series = pd.read_csv(PROCESSED / "netflix_tv_clean.csv").assign(tipo="Serie TV")
    cols = ["show_id", "tipo", "title", "country", "genres", "language",
            "release_year", "popularity", "vote_count", "vote_average"]
    df = pd.concat([peliculas[cols], series[cols]], ignore_index=True)

    # Llave única: 397 show_id se repiten entre películas y series.
    df["key"] = df["tipo"] + "_" + df["show_id"].astype(str)
    assert df["key"].is_unique, "La llave tipo + show_id debe ser única"

    # Valoración válida: 0 con 0 votos es ausencia de dato, no una nota.
    df["vote_valid"] = df["vote_average"].where(df["vote_count"] > 0)

    # Joya oculta: bien valorada, con votos suficientes y popularidad bajo la mediana.
    pop_mediana = df["popularity"].median()
    df["joya"] = (
        (df["vote_valid"] >= 7.5) & (df["vote_count"] >= 100) & (df["popularity"] < pop_mediana)
    )

    df["generos"] = _a_lista(df["genres"], RELLENO_GENERO, GENEROS_ES)
    df["paises"] = _a_lista(df["country"], RELLENO_PAIS, PAISES_ES)
    df["pais_principal"] = df["paises"].apply(lambda l: l[0] if l else "Sin información")

    # Subconjunto financiero (solo películas).
    fin = pd.read_csv(PROCESSED / "netflix_movies_financial_clean.csv")[
        ["show_id", "budget", "revenue", "roi"]
    ]
    fin["key"] = "Película_" + fin["show_id"].astype(str)
    dfin = df.merge(fin.drop(columns="show_id"), on="key", how="inner")

    # Tramos de presupuesto (terciles de toda la base financiera).
    q1, q2 = dfin["budget"].quantile([1 / 3, 2 / 3])
    etiquetas = [
        f"Bajo (hasta {q1 / 1e6:.0f} M USD)",
        f"Medio ({q1 / 1e6:.0f} a {q2 / 1e6:.0f} M USD)",
        f"Alto (más de {q2 / 1e6:.0f} M USD)",
    ]
    dfin["tramo"] = pd.cut(dfin["budget"], [-np.inf, q1, q2, np.inf],
                           labels=etiquetas, include_lowest=True)
    return df, dfin


def guardar_maestras():
    """Escribe las tablas maestras en data/processed/."""
    df, dfin = cargar_datos()
    cols = ["key", "show_id", "tipo", "title", "country", "genres", "language",
            "release_year", "popularity", "vote_count", "vote_average",
            "vote_valid", "joya"]
    df[cols].to_csv(PROCESSED / "master.csv", index=False)
    dfin[["key", "title", "genres", "release_year", "budget", "revenue",
          "roi", "tramo"]].to_csv(PROCESSED / "master_financial.csv", index=False)
    print(f"master.csv: {len(df):,} filas | master_financial.csv: {len(dfin):,} filas")


if __name__ == "__main__":
    guardar_maestras()
