"""Cálculos de KPIs y tablas para los gráficos (sin dependencias de Dash/Plotly)."""
import numpy as np
import pandas as pd


def filtrar(df, tipo="ALL", genero="ALL", pais="ALL", anios=None):
    d = df
    if tipo and tipo != "ALL":
        d = d[d["tipo"] == tipo]
    if genero and genero != "ALL":
        d = d[d["generos"].apply(lambda lista: genero in lista)]
    if pais and pais != "ALL":
        d = d[d["paises"].apply(lambda lista: pais in lista)]
    if anios:
        d = d[d["release_year"].between(anios[0], anios[1])]
    return d


# ---------- KPIs ----------
def kpis_catalogo(d):
    paises = {p for lista in d["paises"] for p in lista}
    validas = d["vote_valid"].dropna()
    return {
        "total": len(d),
        "paises": len(paises),
        "idiomas": d["language"].nunique(),
        "val_media": validas.mean() if len(validas) else np.nan,
        "pct_bien": (validas >= 7).mean() if len(validas) else np.nan,
    }


def kpis_calidad(d):
    validas = d["vote_valid"].dropna()
    return {
        "pop_mediana": d["popularity"].median() if len(d) else np.nan,
        "val_mediana": validas.median() if len(validas) else np.nan,
        "joyas": int(d["joya"].sum()),
    }


def kpis_fin(f):
    return {
        "roi_mediano": f["roi"].median() if len(f) else np.nan,
        "pct_recupera": (f["roi"] > 1).mean() if len(f) else np.nan,
        "n": len(f),
    }


# ---------- Tablas para gráficos ----------
def _explotar(d, col, extra=()):
    return d[["tipo", col, *extra]].explode(col).dropna(subset=[col])


def top_generos(d, n=10):
    e = _explotar(d, "generos")
    if e.empty:
        return pd.DataFrame(columns=["genero", "tipo", "n"])
    top = e.groupby("generos").size().nlargest(n).index
    return (e[e["generos"].isin(top)].groupby(["generos", "tipo"]).size()
            .reset_index(name="n").rename(columns={"generos": "genero"}))


def paises_proporcion(d, n=10):
    e = _explotar(d, "paises")
    if e.empty:
        return pd.DataFrame(columns=["pais", "tipo", "n"])
    top = e.groupby("paises").size().nlargest(n).index
    return (e[e["paises"].isin(top)].groupby(["paises", "tipo"]).size()
            .reset_index(name="n").rename(columns={"paises": "pais"}))


def valoracion_genero(d, min_n=100, top=12):
    e = _explotar(d.dropna(subset=["vote_valid"]), "generos", extra=("vote_valid",))
    if e.empty:
        return pd.DataFrame(columns=["genero", "tipo", "mediana", "n"])
    g = (e.groupby(["generos", "tipo"])["vote_valid"]
         .agg(mediana="median", n="size").reset_index()
         .rename(columns={"generos": "genero"}))
    g = g[g["n"] >= min_n]
    if g.empty:
        return g
    mejores = g.groupby("genero")["mediana"].max().nlargest(top).index
    return g[g["genero"].isin(mejores)]


def roi_genero(f, min_n=30, top=12):
    e = _explotar(f, "generos", extra=("roi",))
    if e.empty:
        return pd.DataFrame(columns=["genero", "roi", "rec", "n"])
    g = (e.groupby("generos")["roi"]
         .agg(roi="median", rec=lambda x: (x > 1).mean(), n="size").reset_index()
         .rename(columns={"generos": "genero"}))
    return g[g["n"] >= min_n].nlargest(top, "roi")


def roi_tramo(f):
    if f.empty:
        return pd.DataFrame(columns=["tramo", "roi", "rec", "n"])
    return (f.groupby("tramo", observed=True)["roi"]
            .agg(roi="median", rec=lambda x: (x > 1).mean(), n="size").reset_index())


def joyas(d):
    t = d[d["joya"]].sort_values("vote_average", ascending=False)
    return t[["title", "tipo", "pais_principal", "vote_average", "vote_count", "popularity"]]
