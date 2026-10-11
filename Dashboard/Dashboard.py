import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# ==========================================
# 0. TEMA VISUAL
# ==========================================
COLOR_MOVIE = "#F3C80B"
COLOR_SHOW = "#C62C60"
ACCENT = "#C62C60"
BG = "#F5F5F5"
CARD_BG = "#F5F5F5"
TEXT = "#2D3748"
TEXT_MUTED = "#718096"
TEMPLATE = "plotly_white"

BG_PAGE = BG
BG_CARD = CARD_BG
BORDER = "#E2E0DC"
TEXT_MAIN = TEXT
ACCENT_BLUE = "#3B7DC6"
ACCENT_GREEN = "#1A864F"
FONT_FAMILY = "'Helvetica Neue', Helvetica, Arial, sans-serif"

color_map = {'Película': COLOR_MOVIE, 'Serie TV': COLOR_SHOW}

CARD_STYLE = {
    'backgroundColor': BG_CARD,
    'borderRadius': '10px',
    'border': f'1px solid {BORDER}',
    'boxShadow': '0 2px 8px rgba(45,55,72,0.08)',
    'padding': '12px',
}

TAB_STYLE = {
    'padding': '12px 24px',
    'fontWeight': '600',
    'fontFamily': FONT_FAMILY,
    'color': "#291735",
    'border': 'none',
    'borderBottom': f'2px solid {BORDER}',
    'backgroundColor': 'transparent',
    'fontSize': '15px',
    'cursor': 'pointer'
}

TAB_SELECTED_STYLE = {
    'padding': '12px 24px',
    'fontWeight': '700',
    'fontFamily': FONT_FAMILY,
    'color': "#291735",
    'border': 'none',
    'borderBottom': f'3px solid {"#291735"}',
    'backgroundColor': 'transparent',
    'fontSize': '15px',
    'cursor': 'pointer'
}

def apply_theme(fig, height=420):
    fig.update_layout(
        template=TEMPLATE,
        paper_bgcolor=BG_CARD,
        plot_bgcolor=BG_CARD,
        font=dict(family=FONT_FAMILY, color=TEXT_MAIN, size=12),
        title=dict(font=dict(size=15, color=TEXT), x=0.02, xanchor='left', y=0.96),
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            orientation='h', yanchor='top', y=-0.18, xanchor='center', x=0.5,
            title_text=''
        ),
        margin=dict(t=65, l=55, r=30, b=85),
        height=height,
        hoverlabel=dict(bgcolor='#ffffff', font=dict(color=TEXT, family=FONT_FAMILY)),
    )
    fig.update_xaxes(gridcolor=BORDER, zerolinecolor=BORDER, title_font=dict(color=TEXT_MUTED), color=TEXT_MUTED)
    fig.update_yaxes(gridcolor=BORDER, zerolinecolor=BORDER, title_font=dict(color=TEXT_MUTED), color=TEXT_MUTED)
    return fig

# ==========================================
# 1. CARGA DE DATOS BASE
# ==========================================
df_movies = pd.read_csv("data/processed/netflix_movies_clean.csv")
df_tv = pd.read_csv("data/processed/netflix_tv_clean.csv")
df_financial = pd.read_csv("data/processed/netflix_movies_financial_clean.csv")

df_movies['tipo'] = 'Película'
df_tv['tipo'] = 'Serie TV'

df_movies['year_added'] = pd.to_datetime(df_movies['date_added'], errors='coerce').dt.year
df_tv['year_added'] = pd.to_datetime(df_tv['date_added'], errors='coerce').dt.year

df_combined = pd.concat([df_movies, df_tv], ignore_index=True)

min_year = int(df_combined['year_added'].min()) if not df_combined['year_added'].dropna().empty else 2010
max_year = int(df_combined['year_added'].max()) if not df_combined['year_added'].dropna().empty else 2025

df_countries_clean = df_combined.assign(country=df_combined['country'].str.split(', ')).explode('country')
df_countries_clean = df_countries_clean[~df_countries_clean['country'].isin(['Sin Información', np.nan])]
top_countries_opts = [{'label': 'Todos los Países', 'value': 'ALL'}] + [
    {'label': country, 'value': country} for country in sorted(df_countries_clean['country'].unique())
]

# ==========================================
# 2. LAYOUT DEL DASHBOARD
# ==========================================
app = Dash(__name__)

def kpi_card(id_val, label, accent):
    return html.Div([
        html.H4(label, style={
            'margin': '0', 'color': TEXT_MUTED, 'fontSize': '12px',
            'fontWeight': '500', 'letterSpacing': '0.03em', 'textTransform': 'uppercase'
        }),
        html.H2(id=id_val, style={
            'margin': '6px 0 0 0', 'color': accent, 'fontSize': '26px', 'fontWeight': '700'
        })
    ], style={
        **CARD_STYLE,
        'flex': '1',
        'textAlign': 'center',
        'padding': '16px 14px',
        'borderLeft': f'5px solid {accent}'  # Agrega la barra lateral del color asignado
    })

def chart_card(fig_id):
    return html.Div(dcc.Graph(id=fig_id, config={'displayModeBar': False}), style={**CARD_STYLE, 'flex': '1', 'minWidth': '420px'})

app.layout = html.Div(style={
    'backgroundColor': BG_PAGE, 'padding': '32px', 'fontFamily': FONT_FAMILY, 'minHeight': '100vh'
}, children=[

    # Encabezado
    html.Div([
        html.H1("StreamView Analytics - Panorama del Catálogo", style={
            'color': TEXT, 'fontSize': '28px', 'fontWeight': '700', 'margin': '0'
        }),
        html.P("Plataforma interactiva de inteligencia visual de contenido y finanzas", style={
            'color': TEXT_MUTED, 'margin': '6px 0 0 0', 'fontSize': '14px'
        }),
    ], style={'marginBottom': '20px', 'borderBottom': f'1px solid {BORDER}', 'paddingBottom': '16px'}),

 # --- BARRA DE FILTROS INTERACTIVOS ---
    html.Div([
        html.Div([
            html.Label("Tipo de Contenido:", style={'fontWeight': '600', 'fontSize': '13px', 'color': TEXT}),
            dcc.Dropdown(
                id='filter-tipo',
                options=[
                    {'label': 'Todos', 'value': 'ALL'},
                    {'label': 'Películas', 'value': 'Película'},
                    {'label': 'Series TV', 'value': 'Serie TV'}
                ],
                value='ALL', clearable=False, style={'fontSize': '13px', 'marginTop': '4px'}
            )
        ], style={'flex': '1'}),

        html.Div([
            html.Label("País de Origen:", style={'fontWeight': '600', 'fontSize': '13px', 'color': TEXT}),
            dcc.Dropdown(
                id='filter-country', options=top_countries_opts, value='ALL', clearable=False,
                style={'fontSize': '13px', 'marginTop': '4px'}
            )
        ], style={'flex': '1.2'}),

        html.Div([
            html.Label("Año de Incorporación al Catálogo:", style={'fontWeight': '600', 'fontSize': '13px', 'color': TEXT}),
            html.Div(style={'padding': '0 10px', 'marginTop': '8px'}, children=[
                dcc.RangeSlider(
                    id='filter-year',
                    min=min_year, max=max_year, step=1,
                    value=[min_year, max_year],
                    marks={y: str(y) for y in range(min_year, max_year + 1, 3)},
                    tooltip={"placement": "bottom", "always_visible": False}
                )
            ])
        ], style={'flex': '2'}),

    ], style={
        **CARD_STYLE,
        'display': 'flex',
        'gap': '20px',  # Separación entre cada filtro
        'alignItems': 'center',
        'marginBottom': '24px',
        'padding': '16px 20px'
    }),
    # TARJETAS KPI
    html.Div([
        kpi_card("kpi-total", "Total Títulos", TEXT),
        kpi_card("kpi-peliculas", "Películas", COLOR_MOVIE),
        kpi_card("kpi-series", "Series TV", COLOR_SHOW),
        kpi_card("kpi-roi", "ROI Mediano", ACCENT_GREEN),
        kpi_card("kpi-recaudacion", "Recaudación Prom.", ACCENT_BLUE),
    ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '24px', 'flexWrap': 'wrap'}),

    # PESTAÑAS
    dcc.Tabs(parent_style={'marginBottom': '20px'}, children=[
        
        # PESTAÑA 1
        dcc.Tab(
            label='Análisis de Contenido y Audiencia',
            style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE,
            children=[
                html.Div(style={'paddingTop': '16px'}, children=[
                    html.Div([chart_card('fig1'), chart_card('fig2')], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px', 'flexWrap': 'wrap'}),
                    html.Div([chart_card('fig3'), chart_card('fig4')], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px', 'flexWrap': 'wrap'}),
                    html.Div([chart_card('fig8'), chart_card('fig9')], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px', 'flexWrap': 'wrap'}),
                ])
            ]
        ),

        # PESTAÑA 2
        dcc.Tab(
            label='Desempeño Financiero y Mercado',
            style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE,
            children=[
                html.Div(style={'paddingTop': '16px'}, children=[
                    html.Div([chart_card('fig5'), chart_card('fig6')], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px', 'flexWrap': 'wrap'}),
                    html.Div([chart_card('fig7')], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px'}),
                ])
            ]
        )
    ])
])

# ==========================================
# 3. CALLBACKS INTERACTIVOS
# ==========================================
@app.callback(
    [
        Output('kpi-total', 'children'),
        Output('kpi-peliculas', 'children'),
        Output('kpi-series', 'children'),
        Output('kpi-roi', 'children'),
        Output('kpi-recaudacion', 'children'),
        Output('fig1', 'figure'),
        Output('fig2', 'figure'),
        Output('fig3', 'figure'),
        Output('fig4', 'figure'),
        Output('fig5', 'figure'),
        Output('fig6', 'figure'),
        Output('fig7', 'figure'),
        Output('fig8', 'figure'),
        Output('fig9', 'figure'),
    ],
    [
        Input('filter-tipo', 'value'),
        Input('filter-country', 'value'),
        Input('filter-year', 'value')
    ]
)
def update_dashboard(selected_tipo, selected_country, selected_years):
    dff = df_combined.copy()

    if selected_tipo != 'ALL':
        dff = dff[dff['tipo'] == selected_tipo]

    if selected_country != 'ALL':
        dff = dff[dff['country'].str.contains(selected_country, na=False)]

    if selected_years:
        dff = dff[(dff['year_added'] >= selected_years[0]) & (dff['year_added'] <= selected_years[1])]

    dff_movies = dff[dff['tipo'] == 'Película']
    dff_tv = dff[dff['tipo'] == 'Serie TV']
    dff_fin = df_financial[df_financial['show_id'].isin(dff['show_id'])] if 'show_id' in dff.columns else df_financial

    kpi_tot = len(dff)
    kpi_mov = len(dff_movies)
    kpi_tv_val = len(dff_tv)
    kpi_roi_val = f"{dff_fin['roi'].median():.2f}x" if not dff_fin.empty and not dff_fin['roi'].dropna().empty else "N/A"
    kpi_rev_val = f"${dff_fin['revenue'].mean() / 1e6:.1f}M" if not dff_fin.empty and not dff_fin['revenue'].dropna().empty else "N/A"

    # --- FIGURA 1 Top 10 Géneros por Tipo de Contenido---
    df_gen = dff.assign(genres=dff['genres'].str.split(', ')).explode('genres')
    df_gen = df_gen[df_gen['genres'] != 'Sin Género']
    top10_gen = df_gen['genres'].value_counts().head(10).index
    df_top_gen = df_gen[df_gen['genres'].isin(top10_gen)].groupby(['genres', 'tipo']).size().reset_index(name='count')
    
    fig1 = px.bar(
        df_top_gen, y='genres', x='count', color='tipo', barmode='group',
        title='Top 10 Géneros por Tipo de Contenido', labels={'genres': 'Género', 'count': 'Cantidad', 'tipo': 'Tipo'},
        color_discrete_map=color_map, category_orders={'genres': list(reversed(top10_gen))}
    )
    apply_theme(fig1)

    # --- FIGURA 2 Crecimiento Acumulado del Catálogo---
    df_y = dff.dropna(subset=['year_added']).groupby(['year_added', 'tipo']).size().unstack(fill_value=0)
    df_y_cum = df_y.cumsum().reset_index()
    fig2 = go.Figure()
    if 'Película' in df_y_cum.columns:
        fig2.add_trace(go.Scatter(x=df_y_cum['year_added'], y=df_y_cum['Película'], mode='lines+markers', name='Película', line=dict(color=COLOR_MOVIE, width=3)))
    if 'Serie TV' in df_y_cum.columns:
        fig2.add_trace(go.Scatter(x=df_y_cum['year_added'], y=df_y_cum['Serie TV'], mode='lines+markers', name='Serie TV', line=dict(color=COLOR_SHOW, width=3)))
    fig2.update_layout(title='Crecimiento Acumulado del Catálogo', xaxis_title='Año de Incorporación', yaxis_title='Total Acumulado')
    apply_theme(fig2)

    # --- FIGURA 3 Distribución de Popularidad por Tipo---
    fig3 = px.box(
        dff, x='popularity', y='tipo', color='tipo',
        title='Distribución de Popularidad por Tipo', labels={'popularity': 'Popularidad', 'tipo': 'Tipo'},
        color_discrete_map=color_map
    )
    apply_theme(fig3)

    # --- FIGURA 4 Popularidad vs. Calificación Promedio---
    fig4 = px.scatter(
        dff, x='popularity', y='vote_average', color='tipo',
        title='Popularidad vs. Calificación Promedio', labels={'popularity': 'Popularidad', 'vote_average': 'Calificación'},
        color_discrete_map=color_map, opacity=0.65
    )
    apply_theme(fig4)

    # --- FIGURA 5: ROI Mediano por Género ---
    df_fin_gen = dff_fin.assign(genres=dff_fin['genres'].str.split(', ')).explode('genres')
    df_fin_gen = df_fin_gen[df_fin_gen['genres'] != 'Sin Género']
    top_roi = df_fin_gen.groupby('genres')['roi'].median().nlargest(10).reset_index() if not df_fin_gen.empty else pd.DataFrame(columns=['genres', 'roi'])
    
    fig5 = px.bar(
        top_roi, y='genres', x='roi', orientation='h', title='Mediana del ROI por Género en Películas',
        labels={'genres': 'Género', 'roi': 'ROI Mediano'},
        color_discrete_sequence=[ACCENT_GREEN]
    )
    fig5.update_layout(yaxis={'categoryorder': 'total ascending'})
    apply_theme(fig5)

    # --- FIGURA 6 Matriz de Correlación: Finanzas y Audiencia---
    corr_cols = ['budget', 'revenue', 'popularity', 'vote_count', 'vote_average']
    corr_matrix = dff_fin[corr_cols].corr().round(2) if not dff_fin.empty else pd.DataFrame(np.zeros((5,5)), index=corr_cols, columns=corr_cols)
    fig6 = px.imshow(corr_matrix, text_auto=True, color_continuous_scale='PRGn', zmin=-1, zmax=1, title='Matriz de Correlación: Finanzas y Audiencia')
    apply_theme(fig6)

    # --- FIGURA 7 Relación Presupuesto vs. Recaudación---
    fig7 = px.scatter(
        dff_fin, x='budget', y='revenue', trendline='ols' if len(dff_fin) > 1 else None,
        title=f'Relación Presupuesto vs. Recaudación (n={len(dff_fin)})', labels={'budget': 'Presupuesto (USD)', 'revenue': 'Recaudación (USD)'},
        opacity=0.5, color_discrete_sequence=[ACCENT_BLUE], trendline_color_override=ACCENT
    )
    apply_theme(fig7)

    # --- FIGURA 8 Volumen de Votos vs. Popularidad---
    fig8 = px.scatter(
        dff, x='vote_count', y='popularity', color='tipo',
        title='Volumen de Votos vs. Popularidad', labels={'vote_count': 'Votos', 'popularity': 'Popularidad'},
        color_discrete_map=color_map, opacity=0.65
    )
    apply_theme(fig8)

    # --- FIGURA 9 Top 10 Países de Origen---
    df_c = dff.assign(country=dff['country'].str.split(', ')).explode('country')
    df_c = df_c[~df_c['country'].isin(['Sin Información', np.nan])]
    top10_c = df_c['country'].value_counts().head(10).index
    df_top_c = df_c[df_c['country'].isin(top10_c)].groupby(['country', 'tipo']).size().reset_index(name='count')

    fig9 = px.bar(
        df_top_c, y='country', x='count', color='tipo', barmode='group',
        title='Top 10 Países de Origen', labels={'country': 'País', 'count': 'Títulos'},
        color_discrete_map=color_map, category_orders={'country': list(reversed(top10_c))}
    )
    apply_theme(fig9)

    return f"{kpi_tot:,}", f"{kpi_mov:,}", f"{kpi_tv_val:,}", kpi_roi_val, kpi_rev_val, fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9

# ==========================================
# 4. EJECUCIÓN
# ==========================================
if __name__ == '__main__':
    app.run(debug=True)