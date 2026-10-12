"""
Exporta las figuras estáticas del informe a images/ (matplotlib).

Uso desde la raíz del proyecto:
    python src/figuras_estaticas.py
Las figuras usan los mismos cálculos (src/metricas.py) y la misma paleta que el dashboard.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import metricas as M
from integracion import cargar_datos

OUT = Path(__file__).resolve().parent.parent / "images"
C_PELI, C_SERIE, C_VERDE, C_AZUL, C_JOYA, C_GRIS, C_TEXTO = (
    "#E3A008", "#C62C60", "#1A864F", "#3B7DC6", "#6D28D9", "#B8BEC8", "#1F2937")
COLORES = {"Película": C_PELI, "Serie TV": C_SERIE}

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": "#D1D5DB", "axes.labelcolor": C_TEXTO,
    "xtick.color": C_TEXTO, "ytick.color": C_TEXTO, "axes.spines.top": False,
    "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 12,
    "axes.titlelocation": "left", "figure.dpi": 100,
})


def dec(x, d=1):
    return f"{x:,.{d}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def miles(n):
    return f"{int(n):,}".replace(",", ".")


def guardar(fig, nombre):
    fig.tight_layout()
    fig.savefig(OUT / nombre, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("OK", nombre)


def barras_agrupadas(ax, t, cat, valor, orden, texto=None):
    """Barras horizontales agrupadas por tipo; orden = categorías de abajo hacia arriba."""
    pos = {c: i for i, c in enumerate(orden)}
    alto = 0.38
    for j, tipo in enumerate(["Película", "Serie TV"]):
        s = t[t["tipo"] == tipo]
        y = [pos[c] + (j - 0.5) * alto for c in s[cat]]
        ax.barh(y, s[valor], height=alto, color=COLORES[tipo], label=tipo)
        if texto is not None:
            for yy, v, tx in zip(y, s[valor], texto(s)):
                ax.text(v, yy, " " + tx, va="center", fontsize=8)
    ax.set_yticks(range(len(orden)))
    ax.set_yticklabels(orden)
    ax.legend(frameon=False, loc="lower right")


def main():
    OUT.mkdir(exist_ok=True)
    df, dfin = cargar_datos()
    pop_med = df["popularity"].median()

    # Figura 1: top 10 géneros por tipo
    t = M.top_generos(df)
    orden = t.groupby("genero")["n"].sum().sort_values().index.tolist()
    fig, ax = plt.subplots(figsize=(8, 5))
    barras_agrupadas(ax, t, "genero", "n", orden)
    ax.set_xlabel("Títulos")
    ax.set_title(f"{orden[-1]} y {orden[-2]} concentran el mayor volumen")
    ax.xaxis.set_major_formatter(lambda x, _: f"{int(x):,}".replace(",", "."))
    guardar(fig, "fig1_top_generos_por_tipo.png")

    # Figura 2: proporción película/serie por país
    t = M.paises_proporcion(df)
    piv = t.pivot_table(index="pais", columns="tipo", values="n", fill_value=0)
    piv["tot"] = piv.sum(axis=1)
    piv = piv.sort_values("tot")
    pct_s = piv["Serie TV"] / piv["tot"] * 100
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(piv.index, 100 - pct_s, color=C_PELI, label="Película")
    ax.barh(piv.index, pct_s, left=100 - pct_s, color=C_SERIE, label="Serie TV")
    for i, (v, p) in enumerate(zip(pct_s, pct_s)):
        ax.text(100 - p / 2, i, f"{p:.0f}%", ha="center", va="center", color="white",
                fontsize=8, fontweight="bold")
    ax.set_xlim(0, 100)
    ax.set_xlabel("Proporción de títulos (%)")
    ax.set_title(f"{pct_s.idxmax()} es el más especializado en series ({pct_s.max():.0f}%)")
    ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    guardar(fig, "fig2_proporcion_pelicula_serie_por_pais.png")

    # Figura 3: popularidad por tipo (escala log)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    datos = [df[df["tipo"] == tp]["popularity"] for tp in ["Película", "Serie TV"]]
    bp = ax.boxplot(datos, vert=False, patch_artist=True, showfliers=False, widths=0.5,
                    medianprops=dict(color=C_TEXTO, linewidth=2))
    for caja, tp in zip(bp["boxes"], ["Película", "Serie TV"]):
        caja.set_facecolor(COLORES[tp]); caja.set_alpha(0.85)
    ax.set_xscale("log")
    ax.set_yticklabels(["Película", "Serie TV"])
    ax.set_xlabel("Popularidad (escala logarítmica)")
    m = df.groupby("tipo")["popularity"].median()
    ax.set_title(f"Popularidad mediana: {dec(m['Serie TV'])} series vs {dec(m['Película'])} películas")
    guardar(fig, "fig3_popularidad_por_tipo.png")

    # Figura 4: valoración mediana por género
    t = M.valoracion_genero(df)
    orden = t.groupby("genero")["mediana"].max().sort_values().index.tolist()
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    barras_agrupadas(ax, t, "genero", "mediana", orden,
                     texto=lambda s: [f"{dec(m)} · n={miles(n)}"
                                      for m, n in zip(s["mediana"], s["n"])])
    ax.set_xlim(0, 10.5)
    ax.set_xlabel("Valoración mediana (0 a 10)")
    ax.set_title("Valoración mediana por género (mín. 100 títulos con votos)")
    guardar(fig, "fig4_valoracion_mediana_por_genero.png")

    # Figura 5: popularidad vs valoración con joyas ocultas
    v = df.dropna(subset=["vote_valid"])
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    r, j = v[~v["joya"]], v[v["joya"]]
    ax.scatter(r["popularity"], r["vote_valid"], s=5, color=C_GRIS, alpha=0.35, label="Resto del catálogo")
    ax.scatter(j["popularity"], j["vote_valid"], s=10, color=C_JOYA, alpha=0.8, label="Joyas ocultas")
    ax.axvline(pop_med, color="#6B7280", linestyle=":", linewidth=1)
    ax.axhline(7.5, color="#6B7280", linestyle=":", linewidth=1)
    ax.set_xscale("log"); ax.set_ylim(0, 10.5)
    ax.set_xlabel("Popularidad (escala logarítmica)"); ax.set_ylabel("Valoración (0 a 10)")
    ax.set_title(f"{miles(len(j))} joyas ocultas: bien valoradas, poco populares")
    ax.legend(frameon=False, loc="lower right")
    guardar(fig, "fig5_popularidad_vs_valoracion.png")

    # Figura 6: ROI mediano por género
    t = M.roi_genero(dfin).sort_values("roi")
    fig, ax = plt.subplots(figsize=(8, 5.2))
    ax.barh(t["genero"], t["roi"], color=C_VERDE)
    for i, (rr, n) in enumerate(zip(t["roi"], t["n"])):
        ax.text(rr, i, f" {dec(rr, 2)}x · n={miles(n)}", va="center", fontsize=8)
    ax.axvline(1, color="#6B7280", linestyle=":", linewidth=1)
    ax.set_xlim(0, t["roi"].max() * 1.35)
    ax.set_xlabel("ROI mediano (recaudación / presupuesto)")
    ax.set_title(f"{t.iloc[-1]['genero']} lidera el ROI mediano ({dec(t.iloc[-1]['roi'], 2)}x)")
    guardar(fig, "fig6_roi_mediano_por_genero.png")

    # Figura 7: ROI por tramo de presupuesto
    t = M.roi_tramo(dfin)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    etiquetas = [str(x).replace(" (", "\n(") for x in t["tramo"]]
    ax.bar(etiquetas, t["roi"], color=C_VERDE, width=0.55)
    for i, (rr, p, n) in enumerate(zip(t["roi"], t["rec"], t["n"])):
        ax.text(i, rr, f"{dec(rr, 2)}x\n{p * 100:.0f}% recupera\nn={miles(n)}",
                ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, t["roi"].max() * 1.5)
    ax.set_ylabel("ROI mediano")
    ax.set_title(f"El tramo {str(t.loc[t['roi'].idxmax(), 'tramo']).split(' ')[0].lower()} rinde más: "
                 f"ROI mediano de {dec(t['roi'].max(), 2)}x")
    guardar(fig, "fig7_roi_por_tramo_presupuesto.png")

    # Figura 8: presupuesto vs recaudación
    g = dfin[(dfin["budget"] > 0) & (dfin["revenue"] > 0)]
    r_ = np.corrcoef(g["budget"], g["revenue"])[0, 1]
    pend, orig = np.polyfit(np.log10(g["budget"]), np.log10(g["revenue"]), 1)
    xs = np.linspace(np.log10(g["budget"].min()), np.log10(g["budget"].max()), 50)
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.scatter(g["budget"], g["revenue"], s=8, color=C_AZUL, alpha=0.45, label="Películas")
    ax.plot(10 ** xs, 10 ** (orig + pend * xs), color=C_SERIE, linewidth=2, label="Tendencia (ajuste log-log)")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Presupuesto (USD, escala logarítmica)"); ax.set_ylabel("Recaudación (USD, escala logarítmica)")
    fuerza = "fuerte" if abs(r_) >= 0.6 else "moderada" if abs(r_) >= 0.3 else "débil"
    ax.set_title(f"Presupuesto y recaudación: relación {fuerza} (r = {dec(r_, 2)})")
    ax.legend(frameon=False, loc="lower right")
    guardar(fig, "fig8_presupuesto_vs_recaudacion.png")

    # Tabla 1: ranking de joyas ocultas (top 10) + CSV completo
    jo = M.joyas(df)
    jo.to_csv(OUT.parent / "data" / "processed" / "joyas_ocultas.csv", index=False)
    top = jo.head(10).copy()
    top["vote_average"] = top["vote_average"].map(dec)
    top["popularity"] = top["popularity"].map(dec)
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.axis("off")
    tabla = ax.table(
        cellText=top.values.tolist(),
        colLabels=["Título", "Tipo", "País", "Valoración", "Votos", "Popularidad"],
        loc="center", cellLoc="left")
    tabla.auto_set_font_size(False); tabla.set_fontsize(8.5); tabla.scale(1, 1.35)
    tabla.auto_set_column_width(list(range(6)))
    for (fila, _), celda in tabla.get_celld().items():
        celda.set_edgecolor("#E5E7EB")
        if fila == 0:
            celda.set_facecolor("#F3F4F6"); celda.set_text_props(fontweight="bold")
    ax.set_title("Joyas ocultas: 10 títulos mejor valorados", pad=8)
    guardar(fig, "tabla1_joyas_ocultas_top10.png")


if __name__ == "__main__":
    main()
