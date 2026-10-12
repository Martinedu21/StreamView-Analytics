"""
StreamView Analytics - Panel para la Gerencia de Contenidos y Adquisición

Ejecución (desde la raíz del proyecto):
    pip install -r requirements.txt
    python dashboard/Dashboard.py
Luego abrir http://127.0.0.1:8050

Estructura: 3 páginas (pestañas), cada una asociada a una decisión de Contenidos:
  1. Panorama del catálogo      -> ¿Qué tenemos y qué nos falta?
  2. Calidad y atractivo        -> ¿Qué priorizar, renovar o destacar?
  3. Rentabilidad de películas  -> ¿Dónde invertir en películas?
Filtros globales: tipo, género, país y año de estreno. Clic en una barra de
género o país filtra el resto del tablero.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, ctx, dash_table, dcc, html, no_update

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
import metricas as M  # noqa: E402
from integracion import cargar_datos  # noqa: E402

# =====================================================================
# 1. DATOS
# =====================================================================
DF, DFIN = cargar_datos()
POP_MED = DF["popularity"].median()
ANIO_MIN, ANIO_MAX = int(DF["release_year"].min()), int(DF["release_year"].max())
GENEROS = sorted({g for lista in DF["generos"] for g in lista})
PAISES = sorted({p for lista in DF["paises"] for p in lista})

# =====================================================================
# 2. TEMA Y UTILIDADES
# =====================================================================
C_PELI = "#E3A008"
C_SERIE = "#C62C60"
C_VERDE = "#1A864F"
C_AZUL = "#3B7DC6"
C_JOYA = "#6D28D9"
C_GRIS = "#B8BEC8"
C_TEXTO = "#1F2937"
C_SUAVE = "#6B7280"
C_BORDE = "#E5E7EB"
C_FONDO = "#F3F4F6"
FUENTE = "'Helvetica Neue', Helvetica, Arial, sans-serif"
COLORES = {"Película": C_PELI, "Serie TV": C_SERIE}
ORDEN_TIPO = ["Película", "Serie TV"]

CARD = {
    "backgroundColor": "white", "borderRadius": "10px", "border": f"1px solid {C_BORDE}",
    "boxShadow": "0 1px 4px rgba(31,41,55,0.06)", "padding": "12px",
}


def f_int(n):
    return "N/D" if n is None or pd.isna(n) else f"{int(n):,}".replace(",", ".")


def f_dec(x, d=1):
    if x is None or pd.isna(x):
        return "N/D"
    return f"{x:,.{d}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def f_pct(x):
    return "N/D" if x is None or pd.isna(x) else f"{x * 100:.0f}%"


def estilo(fig, titulo, alto=400):
    fig.update_layout(
        template="plotly_white", height=alto, paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family=FUENTE, color=C_TEXTO, size=12),
        title=dict(text=titulo, x=0.01, xanchor="left", font=dict(size=14, color=C_TEXTO)),
        margin=dict(t=60, l=10, r=25, b=70),
        legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5, title_text=""),
        hoverlabel=dict(bgcolor="white", font=dict(family=FUENTE, color=C_TEXTO)),
    )
    fig.update_xaxes(gridcolor=C_BORDE, zerolinecolor=C_BORDE, automargin=True)
    fig.update_yaxes(gridcolor=C_BORDE, zerolinecolor=C_BORDE, automargin=True)
    return fig


def vacio(titulo, msg="No hay datos para esta selección. Ajusta los filtros."):
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.5, xref="paper", yref="paper",
                       showarrow=False, font=dict(size=13, color=C_SUAVE))
    estilo(fig, titulo)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


# =====================================================================
# 3. FIGURAS (cada una recibe los datos ya filtrados)
# =====================================================================
def fig_generos(d):
    t = M.top_generos(d)
    if t.empty:
        return vacio("Géneros con mayor volumen")
    orden = t.groupby("genero")["n"].sum().sort_values().index.tolist()  # el mayor queda arriba
    titulo = (f"{orden[-1]} y {orden[-2]} concentran el mayor volumen"
              if len(orden) > 1 else f"{orden[-1]} concentra el mayor volumen")
    fig = px.bar(t, x="n", y="genero", color="tipo", orientation="h", barmode="group",
                 color_discrete_map=COLORES,
                 category_orders={"genero": orden, "tipo": ORDEN_TIPO},
                 labels={"n": "Títulos", "genero": "Género", "tipo": "Tipo"})
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>%{y}: %{x:,} títulos<extra></extra>")
    return estilo(fig, titulo, alto=440)


def fig_paises(d):
    t = M.paises_proporcion(d)
    if t.empty:
        return vacio("Países con mayor volumen")
    orden = t.groupby("pais")["n"].sum().sort_values().index.tolist()
    piv = t.pivot_table(index="pais", columns="tipo", values="n", fill_value=0)
    if "Serie TV" in piv.columns and "Película" in piv.columns:
        pct = piv["Serie TV"] / (piv["Serie TV"] + piv["Película"])
        mx = pct.idxmax()
        titulo = f"{mx} es el más especializado en series ({pct[mx] * 100:.0f}%)"
    else:
        titulo = f"{orden[-1]} lidera el volumen del catálogo"
    fig = px.bar(t, x="n", y="pais", color="tipo", orientation="h",
                 color_discrete_map=COLORES, custom_data=["n"],
                 category_orders={"pais": orden, "tipo": ORDEN_TIPO},
                 labels={"n": "Proporción de títulos", "pais": "País", "tipo": "Tipo"})
    fig.update_layout(barmode="stack", barnorm="percent")
    fig.update_xaxes(ticksuffix="%")
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>%{y}: %{customdata[0]:,} títulos<extra></extra>")
    return estilo(fig, titulo, alto=440)


def fig_box(d):
    if d.empty:
        return vacio("Popularidad por tipo de contenido")
    meds = d.groupby("tipo")["popularity"].median()
    if len(meds) == 2:
        titulo = f"Popularidad mediana: {f_dec(meds['Serie TV'])} series vs {f_dec(meds['Película'])} películas"
    else:
        titulo = f"Popularidad mediana: {f_dec(meds.iloc[0])}"
    fig = px.box(d, x="popularity", y="tipo", color="tipo", log_x=True, points=False,
                 color_discrete_map=COLORES, category_orders={"tipo": ORDEN_TIPO},
                 labels={"popularity": "Popularidad (escala logarítmica)", "tipo": ""})
    fig.update_layout(showlegend=False)
    return estilo(fig, titulo, alto=380)


def fig_valgen(d):
    t = M.valoracion_genero(d)
    titulo = "Valoración mediana por género (mín. 100 títulos con votos)"
    if t.empty:
        return vacio(titulo, "Ningún género alcanza 100 títulos con votos en esta selección.")
    orden = t.groupby("genero")["mediana"].max().sort_values().index.tolist()
    t = t.assign(txt=[f"{f_dec(m)} · n={f_int(n)}" for m, n in zip(t["mediana"], t["n"])])
    fig = px.bar(t, x="mediana", y="genero", color="tipo", orientation="h", barmode="group",
                 text="txt", color_discrete_map=COLORES,
                 category_orders={"genero": orden, "tipo": ORDEN_TIPO},
                 labels={"mediana": "Valoración mediana (0 a 10)", "genero": "Género", "tipo": "Tipo"})
    fig.update_traces(textposition="outside", cliponaxis=False,
                      hovertemplate="<b>%{fullData.name}</b><br>%{y}: %{x:.1f}<extra></extra>")
    fig.update_xaxes(range=[0, 11.5])
    return estilo(fig, titulo, alto=520)


def fig_disp(d):
    v = d.dropna(subset=["vote_valid"])
    if v.empty:
        return vacio("Popularidad vs. valoración")
    resto, jo = v[~v["joya"]], v[v["joya"]]
    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        x=resto["popularity"], y=resto["vote_valid"], mode="markers", name="Resto del catálogo",
        marker=dict(size=4, color=C_GRIS, opacity=0.35), text=resto["title"],
        hovertemplate="<b>%{text}</b><br>Popularidad: %{x:.1f}<br>Valoración: %{y:.1f}<extra></extra>"))
    fig.add_trace(go.Scattergl(
        x=jo["popularity"], y=jo["vote_valid"], mode="markers", name="Joyas ocultas",
        marker=dict(size=6, color=C_JOYA, opacity=0.8), text=jo["title"],
        hovertemplate="<b>%{text}</b><br>Popularidad: %{x:.1f}<br>Valoración: %{y:.1f}<extra></extra>"))
    xmin = max(float(v["popularity"].min()), 0.1)
    xmax = float(v["popularity"].max())
    for xs, ys in (([POP_MED, POP_MED], [0, 10]), ([xmin, xmax], [7.5, 7.5])):
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", showlegend=False, hoverinfo="skip",
                                 line=dict(color=C_SUAVE, width=1, dash="dot")))
    fig.update_xaxes(type="log", title="Popularidad (escala logarítmica)")
    fig.update_yaxes(range=[0, 10.5], title="Valoración (0 a 10)")
    return estilo(fig, f"{f_int(len(jo))} joyas ocultas: bien valoradas, poco populares", alto=460)


def fig_roigen(f):
    t = M.roi_genero(f)
    titulo = "ROI mediano por género de película"
    if t.empty:
        return vacio(titulo, "Ningún género alcanza 30 películas con datos financieros en esta selección.")
    t = t.sort_values("roi")
    t = t.assign(txt=[f"{f_dec(r, 2)}x · n={f_int(n)}" for r, n in zip(t["roi"], t["n"])])
    mejor = t.iloc[-1]
    fig = px.bar(t, x="roi", y="genero", orientation="h", text="txt",
                 color_discrete_sequence=[C_VERDE],
                 category_orders={"genero": t["genero"].tolist()},
                 labels={"roi": "ROI mediano (recaudación / presupuesto)", "genero": "Género"})
    fig.update_traces(textposition="outside", cliponaxis=False,
                      hovertemplate="<b>%{y}</b><br>ROI mediano: %{x:.2f}x<extra></extra>")
    fig.add_vline(x=1, line_dash="dot", line_color=C_SUAVE)
    fig.update_xaxes(range=[0, float(t["roi"].max()) * 1.35])
    return estilo(fig, f"{mejor['genero']} lidera el ROI mediano ({f_dec(mejor['roi'], 2)}x)", alto=480)


def fig_tramo(f):
    t = M.roi_tramo(f)
    titulo = "ROI mediano por tramo de presupuesto"
    if t.empty:
        return vacio(titulo)
    t = t.assign(tramo=t["tramo"].astype(str))
    t = t.assign(txt=[f"{f_dec(r, 2)}x<br>{f_pct(p)} recupera<br>n={f_int(n)}"
                      for r, p, n in zip(t["roi"], t["rec"], t["n"])])
    mejor = t.loc[t["roi"].idxmax(), "tramo"].split(" ")[0].lower()
    fig = px.bar(t, x="tramo", y="roi", text="txt", color_discrete_sequence=[C_VERDE],
                 category_orders={"tramo": t["tramo"].tolist()},
                 labels={"tramo": "Tramo de presupuesto", "roi": "ROI mediano"})
    fig.update_traces(textposition="outside", cliponaxis=False,
                      hovertemplate="<b>%{x}</b><br>ROI mediano: %{y:.2f}x<extra></extra>")
    fig.update_yaxes(range=[0, float(t["roi"].max()) * 1.4])
    return estilo(fig, f"El tramo {mejor} rinde más: ROI mediano de {f_dec(t['roi'].max(), 2)}x", alto=480)


def fig_fin(f):
    g = f[(f["budget"] > 0) & (f["revenue"] > 0)]
    if len(g) < 3:
        return vacio("Presupuesto vs. recaudación")
    r = float(np.corrcoef(g["budget"], g["revenue"])[0, 1])
    fuerza = "fuerte" if abs(r) >= 0.6 else "moderada" if abs(r) >= 0.3 else "débil"
    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        x=g["budget"], y=g["revenue"], mode="markers", name="Películas",
        marker=dict(size=5, color=C_AZUL, opacity=0.45), text=g["title"],
        hovertemplate="<b>%{text}</b><br>Presupuesto: $%{x:,.0f}<br>Recaudación: $%{y:,.0f}<extra></extra>"))
    lx, ly = np.log10(g["budget"]), np.log10(g["revenue"])
    pendiente, origen = np.polyfit(lx, ly, 1)
    xs = np.linspace(lx.min(), lx.max(), 50)
    fig.add_trace(go.Scatter(x=10 ** xs, y=10 ** (origen + pendiente * xs), mode="lines",
                             name="Tendencia (ajuste log-log)", hoverinfo="skip",
                             line=dict(color=C_SERIE, width=2)))
    fig.update_xaxes(type="log", title="Presupuesto (USD, escala logarítmica)")
    fig.update_yaxes(type="log", title="Recaudación (USD, escala logarítmica)")
    return estilo(fig, f"Presupuesto y recaudación: relación {fuerza} (r = {f_dec(r, 2)})", alto=480)


def datos_tabla(d):
    t = M.joyas(d).copy()
    t["vote_average"] = t["vote_average"].round(1)
    t["popularity"] = t["popularity"].round(1)
    return t.to_dict("records")


# =====================================================================
# 4. LAYOUT
# =====================================================================
TAB = {"padding": "12px 22px", "fontWeight": "600", "fontFamily": FUENTE, "color": C_SUAVE,
       "border": "none", "borderBottom": f"2px solid {C_BORDE}", "backgroundColor": "transparent"}
TAB_SEL = {**TAB, "color": C_TEXTO, "fontWeight": "700", "borderBottom": f"3px solid {C_SERIE}"}
ETIQUETA = {"fontWeight": "600", "fontSize": "13px", "color": C_TEXTO}


def opciones(valores, etiqueta_todos):
    return [{"label": etiqueta_todos, "value": "ALL"}] + [{"label": v, "value": v} for v in valores]


def kpi(id_, etiqueta, color, sub_id=None):
    hijos = [
        html.Div(etiqueta, style={"fontSize": "12px", "color": C_SUAVE, "textTransform": "uppercase",
                                  "letterSpacing": "0.03em", "fontWeight": "500"}),
        html.Div("-", id=id_, style={"fontSize": "26px", "fontWeight": "700", "color": color,
                                     "marginTop": "4px"}),
    ]
    if sub_id:
        hijos.append(html.Div("", id=sub_id, style={"fontSize": "11px", "color": C_SUAVE, "marginTop": "2px"}))
    return html.Div(hijos, style={**CARD, "flex": "1 1 170px", "textAlign": "center",
                                  "borderLeft": f"5px solid {color}", "padding": "14px 12px"})


def grafico(id_, flex="1 1 480px"):
    return html.Div(dcc.Graph(id=id_, config={"displayModeBar": False}),
                    style={**CARD, "flex": flex, "minWidth": "420px"})


def fila(*hijos, margen="16px"):
    return html.Div(list(hijos), style={"display": "flex", "gap": "16px", "flexWrap": "wrap",
                                        "marginBottom": margen})


def cabecera_pagina(decision, ayuda):
    return html.Div([
        html.Span("Decisión que facilita: ", style={"fontWeight": "700", "color": C_SERIE}),
        html.Span(decision, style={"fontWeight": "600", "color": C_TEXTO}),
        html.Div(ayuda, style={"fontSize": "12px", "color": C_SUAVE, "marginTop": "4px"}),
    ], style={"margin": "16px 0", "padding": "10px 14px", "backgroundColor": "white",
              "borderLeft": f"4px solid {C_SERIE}", "borderRadius": "6px"})


def nota(texto):
    return html.Div(texto, style={"fontSize": "12px", "color": C_SUAVE, "margin": "0 0 16px 4px"})


app = Dash(__name__, title="StreamView Analytics · Panel de Contenidos")

app.layout = html.Div(style={"backgroundColor": C_FONDO, "padding": "28px", "fontFamily": FUENTE,
                             "minHeight": "100vh", "color": C_TEXTO}, children=[

    html.Div([
        html.H1("StreamView Analytics · Panel del catálogo",
                style={"margin": "0", "fontSize": "26px", "fontWeight": "700"}),
        html.P("Para: Gerencia de Contenidos y Adquisición. Evidencia para decidir qué adquirir, "
               "renovar o destacar.", style={"margin": "6px 0 0 0", "color": C_SUAVE, "fontSize": "14px"}),
    ], style={"paddingBottom": "14px", "borderBottom": f"1px solid {C_BORDE}", "marginBottom": "18px"}),

    # ---- Filtros globales ----
    html.Div([
        html.Div([html.Label("Tipo de contenido", style=ETIQUETA),
                  dcc.Dropdown(id="filter-tipo", value="ALL", clearable=False,
                               options=[{"label": "Todos", "value": "ALL"},
                                        {"label": "Películas", "value": "Película"},
                                        {"label": "Series", "value": "Serie TV"}])],
                 style={"flex": "1 1 150px"}),
        html.Div([html.Label("Género", style=ETIQUETA),
                  dcc.Dropdown(id="filter-genre", value="ALL", clearable=False,
                               options=opciones(GENEROS, "Todos los géneros"))],
                 style={"flex": "1.2 1 180px"}),
        html.Div([html.Label("País", style=ETIQUETA),
                  dcc.Dropdown(id="filter-country", value="ALL", clearable=False,
                               options=opciones(PAISES, "Todos los países"))],
                 style={"flex": "1.2 1 180px"}),
        html.Div([html.Label("Año de estreno", style=ETIQUETA),
                  html.Div(dcc.RangeSlider(
                      id="filter-year", min=ANIO_MIN, max=ANIO_MAX, step=1, value=[ANIO_MIN, ANIO_MAX],
                      marks={y: str(y) for y in range(ANIO_MIN, ANIO_MAX + 1, 3)},
                      tooltip={"placement": "bottom", "always_visible": False}),
                      style={"padding": "0 8px", "marginTop": "8px"})],
                 style={"flex": "2 1 280px"}),
        html.Div(html.Button("Restablecer filtros", id="btn-reset", n_clicks=0,
                             style={"padding": "8px 14px", "border": f"1px solid {C_BORDE}",
                                    "borderRadius": "6px", "backgroundColor": "white",
                                    "cursor": "pointer", "fontWeight": "600", "color": C_TEXTO}),
                 style={"alignSelf": "flex-end"}),
    ], style={**CARD, "display": "flex", "gap": "18px", "alignItems": "flex-start",
              "flexWrap": "wrap", "padding": "14px 18px"}),

    dcc.Tabs(id="tabs", value="p1", style={"marginTop": "16px"}, children=[

        # ------------------ PÁGINA 1 ------------------
        dcc.Tab(label="1 · Panorama del catálogo", value="p1", style=TAB, selected_style=TAB_SEL, children=[
            cabecera_pagina("¿Qué tenemos y qué nos falta?",
                            "Composición del catálogo por género, país y formato. Clic en una barra "
                            "para filtrar el resto del tablero."),
            fila(kpi("kpi-total", "Total de títulos", C_TEXTO),
                 kpi("kpi-paises", "Países", C_AZUL),
                 kpi("kpi-idiomas", "Idiomas", C_AZUL),
                 kpi("kpi-val", "Valoración media", C_VERDE),
                 kpi("kpi-bien", "Con nota ≥ 7", C_VERDE), margen="16px"),
            fila(grafico("fig-generos"), grafico("fig-paises"), margen="8px"),
            nota("Los géneros no son comparables entre tipos: Thriller, Acción, Romance y Terror existen solo "
                 "en películas; Action & Adventure, Sci-Fi & Fantasy, Reality, Soap y Talk, solo en series."),
        ]),

        # ------------------ PÁGINA 2 ------------------
        dcc.Tab(label="2 · Calidad y atractivo", value="p2", style=TAB, selected_style=TAB_SEL, children=[
            cabecera_pagina("¿Qué priorizar, renovar o destacar?",
                            "Popularidad y valoración por formato y género, y los títulos bien valorados "
                            "que hoy se ven poco (joyas ocultas)."),
            fila(kpi("kpi-pop", "Popularidad mediana", C_AZUL, sub_id="kpi-pop-sub"),
                 kpi("kpi-valmed", "Valoración mediana", C_VERDE),
                 kpi("kpi-joyas", "Joyas ocultas", C_JOYA, sub_id="kpi-joyas-sub"), margen="16px"),
            fila(grafico("fig-box", "1 1 420px"), grafico("fig-valgen", "1.3 1 520px")),
            fila(grafico("fig-disp", "1 1 100%"), margen="8px"),
            nota("Joya oculta: valoración ≥ 7,5, al menos 100 votos y popularidad bajo la mediana del catálogo. "
                 "Valoración calculada solo con títulos que tienen votos."),
            html.Div([
                html.Div("Joyas ocultas en la selección actual (clic en un encabezado para ordenar)",
                         style={"fontWeight": "700", "fontSize": "14px", "marginBottom": "8px"}),
                dash_table.DataTable(
                    id="tabla-joyas", data=[], page_size=10, sort_action="native",
                    style_as_list_view=True, style_table={"overflowX": "auto"},
                    columns=[{"name": "Título", "id": "title"},
                             {"name": "Tipo", "id": "tipo"},
                             {"name": "País", "id": "pais_principal"},
                             {"name": "Valoración", "id": "vote_average", "type": "numeric"},
                             {"name": "Votos", "id": "vote_count", "type": "numeric"},
                             {"name": "Popularidad", "id": "popularity", "type": "numeric"}],
                    style_header={"fontWeight": "700", "backgroundColor": C_FONDO, "border": "none"},
                    style_cell={"fontFamily": FUENTE, "fontSize": "13px", "padding": "6px 10px",
                                "textAlign": "left"},
                    style_cell_conditional=[{"if": {"column_id": c}, "textAlign": "right"}
                                            for c in ("vote_average", "vote_count", "popularity")]),
            ], style={**CARD, "marginBottom": "8px"}),
        ]),

        # ------------------ PÁGINA 3 ------------------
        dcc.Tab(label="3 · Rentabilidad de películas", value="p3", style=TAB, selected_style=TAB_SEL, children=[
            cabecera_pagina("¿Dónde invertir en películas?",
                            "ROI = recaudación / presupuesto. Solo películas con presupuesto y recaudación "
                            "válidos."),
            html.Div(id="aviso-fin", style={"fontSize": "13px", "color": C_SERIE, "fontWeight": "600",
                                            "marginBottom": "10px"}),
            fila(kpi("kpi-roi", "ROI mediano", C_VERDE),
                 kpi("kpi-rec", "Recupera la inversión (ROI > 1)", C_VERDE),
                 kpi("kpi-nfin", "Películas con datos financieros", C_AZUL), margen="16px"),
            fila(grafico("fig-roigen", "1.2 1 520px"), grafico("fig-tramo", "1 1 420px")),
            fila(grafico("fig-fin", "1 1 100%"), margen="8px"),
            nota("Solo el 22% de las películas tiene datos financieros: puede haber sesgo de selección. "
                 "Los tramos de presupuesto son terciles de toda la base financiera."),
        ]),
    ]),

    html.Div("Limitaciones: los datos no incluyen comportamiento de usuarios (no miden retención ni "
             "engagement); hay 1.000 títulos por año, por lo que no se analiza la evolución del catálogo; "
             "la popularidad es un indicador de la fuente, no reproducciones reales.",
             style={"fontSize": "11px", "color": C_SUAVE, "marginTop": "14px",
                    "borderTop": f"1px solid {C_BORDE}", "paddingTop": "10px"}),
])

# =====================================================================
# 5. CALLBACKS
# =====================================================================
FILTROS = [Input("filter-tipo", "value"), Input("filter-genre", "value"),
           Input("filter-country", "value"), Input("filter-year", "value")]


@app.callback(
    [Output("kpi-total", "children"), Output("kpi-paises", "children"),
     Output("kpi-idiomas", "children"), Output("kpi-val", "children"),
     Output("kpi-bien", "children"), Output("fig-generos", "figure"),
     Output("fig-paises", "figure")],
    FILTROS)
def pagina_1(tipo, genero, pais, anios):
    d = M.filtrar(DF, tipo, genero, pais, anios)
    k = M.kpis_catalogo(d)
    return (f_int(k["total"]), f_int(k["paises"]), f_int(k["idiomas"]),
            f_dec(k["val_media"], 2), f_pct(k["pct_bien"]),
            fig_generos(d), fig_paises(d))


@app.callback(
    [Output("kpi-pop", "children"), Output("kpi-pop-sub", "children"),
     Output("kpi-valmed", "children"), Output("kpi-joyas", "children"),
     Output("kpi-joyas-sub", "children"), Output("fig-box", "figure"),
     Output("fig-valgen", "figure"), Output("fig-disp", "figure"),
     Output("tabla-joyas", "data")],
    FILTROS)
def pagina_2(tipo, genero, pais, anios):
    d = M.filtrar(DF, tipo, genero, pais, anios)
    k = M.kpis_calidad(d)
    meds = d.groupby("tipo")["popularity"].median()
    sub_pop = (f"Series {f_dec(meds['Serie TV'])} · Películas {f_dec(meds['Película'])}"
               if len(meds) == 2 else "")
    cuenta = d[d["joya"]].groupby("tipo").size()
    sub_joyas = (f"{f_int(cuenta.get('Película', 0))} películas · {f_int(cuenta.get('Serie TV', 0))} series"
                 if len(d) else "")
    return (f_dec(k["pop_mediana"]), sub_pop, f_dec(k["val_mediana"]), f_int(k["joyas"]), sub_joyas,
            fig_box(d), fig_valgen(d), fig_disp(d), datos_tabla(d))


@app.callback(
    [Output("aviso-fin", "children"), Output("kpi-roi", "children"),
     Output("kpi-rec", "children"), Output("kpi-nfin", "children"),
     Output("fig-roigen", "figure"), Output("fig-tramo", "figure"),
     Output("fig-fin", "figure")],
    FILTROS)
def pagina_3(tipo, genero, pais, anios):
    # Solo hay datos financieros de películas: el filtro de tipo no aplica aquí.
    f = M.filtrar(DFIN, "ALL", genero, pais, anios)
    k = M.kpis_fin(f)
    aviso = ("Esta página muestra solo películas: las series no tienen datos financieros."
             if tipo == "Serie TV" else "")
    return (aviso, f"{f_dec(k['roi_mediano'], 2)}x" if k["n"] else "N/D", f_pct(k["pct_recupera"]),
            f_int(k["n"]), fig_roigen(f), fig_tramo(f), fig_fin(f))


# ---- Interacción: clic en una barra filtra el resto ----
@app.callback(
    Output("filter-genre", "value", allow_duplicate=True),
    [Input("fig-generos", "clickData"), Input("fig-valgen", "clickData"),
     Input("fig-roigen", "clickData")],
    State("filter-genre", "value"), prevent_initial_call=True)
def clic_genero(cd_gen, cd_val, cd_roi, actual):
    datos = {"fig-generos": cd_gen, "fig-valgen": cd_val, "fig-roigen": cd_roi}.get(ctx.triggered_id)
    if not datos:
        return no_update
    genero = datos["points"][0].get("y")
    if genero not in GENEROS:
        return no_update
    return "ALL" if genero == actual else genero


@app.callback(
    Output("filter-country", "value", allow_duplicate=True),
    Input("fig-paises", "clickData"),
    State("filter-country", "value"), prevent_initial_call=True)
def clic_pais(datos, actual):
    if not datos:
        return no_update
    pais = datos["points"][0].get("y")
    if pais not in PAISES:
        return no_update
    return "ALL" if pais == actual else pais


@app.callback(
    [Output("filter-tipo", "value"),
     Output("filter-genre", "value", allow_duplicate=True),
     Output("filter-country", "value", allow_duplicate=True),
     Output("filter-year", "value")],
    Input("btn-reset", "n_clicks"), prevent_initial_call=True)
def restablecer(_):
    return "ALL", "ALL", "ALL", [ANIO_MIN, ANIO_MAX]


if __name__ == "__main__":
    app.run(debug=False)
