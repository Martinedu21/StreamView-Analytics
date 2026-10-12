# StreamView Analytics · Visual Analytics del catálogo

Proyecto de la asignatura ADY1104 Visualización de Datos (EP3).
Audiencia: **Gerencia de Contenidos y Adquisición**. Pregunta central: ¿qué contenidos debería adquirir, priorizar o promocionar StreamView?

## Estructura

| Carpeta o archivo | Contenido |
|---|---|
| `data/raw/` | Archivos originales (`*_detailed_up_to_2025.csv`) |
| `data/processed/` | Archivos limpios (`netflix_*_clean.csv`), tablas maestras (`master.csv`, `master_financial.csv`) y `joyas_ocultas.csv` |
| `notebooks/` | `Limpieza_DataSet_corregido.ipynb`: limpieza y análisis exploratorio |
| `src/` | `integracion.py` (integración con llave única), `metricas.py` (KPIs y tablas), `figuras_estaticas.py` (figuras del informe) |
| `dashboard/` | `Dashboard.py`: dashboard interactivo (Dash + Plotly) |
| `images/` | Figuras estáticas 1 a 8 y tabla 1 del informe |
| `requirements.txt` | Dependencias |

## Cómo ejecutar (desde la raíz del proyecto)

```bash
pip install -r requirements.txt
python dashboard/Dashboard.py
```

Abrir <http://127.0.0.1:8050> en el navegador.

Opcional:

```bash
python src/integracion.py          # regenera data/processed/master*.csv
python src/figuras_estaticas.py    # regenera images/ y data/processed/joyas_ocultas.csv
```

Para rehacer la limpieza desde los datos originales, ejecutar `notebooks/Limpieza_DataSet_corregido.ipynb`
(lee `data/raw/` y escribe `data/processed/`).

## Fuentes de datos e integración

| Fuente | Registros | Contenido |
|---|---|---|
| `netflix_movies_clean.csv` | 16.000 | Películas |
| `netflix_tv_clean.csv` | 15.991 | Series |
| `netflix_movies_financial_clean.csv` | 3.540 | Películas con presupuesto y recaudación válidos, más ROI |

Películas y series se unen con la llave única `tipo + show_id` (397 `show_id` se repiten entre ambos tipos).
El archivo financiero se enlaza solo con películas mediante esa llave.

## Dashboard

Tres páginas, cada una asociada a una decisión de Contenidos:

1. **Panorama del catálogo**: ¿qué tenemos y qué nos falta?
2. **Calidad y atractivo**: ¿qué priorizar, renovar o destacar? (incluye tabla de joyas ocultas)
3. **Rentabilidad de películas**: ¿dónde invertir en películas?

Filtros globales: tipo, género, país y año de estreno, más un botón para restablecerlos.
Clic en una barra de género o país filtra el resto del tablero (otro clic en la misma barra la quita).
En la página 3 el filtro de tipo no aplica: solo las películas tienen datos financieros.

## KPIs

| KPI | Cálculo |
|---|---|
| Total de títulos | Conteo de `tipo + show_id` únicos |
| Países e idiomas | Valores distintos (se excluye la categoría de relleno «Sin Información») |
| Valoración media | Promedio de `vote_average` solo con `vote_count` > 0 |
| % con nota ≥ 7 | Sobre títulos con votos |
| Popularidad mediana | Mediana de `popularity` |
| Joyas ocultas | Valoración ≥ 7,5, votos ≥ 100 y popularidad bajo la mediana del catálogo |
| ROI mediano | Mediana de recaudación / presupuesto (películas) |
| % que recupera inversión | Películas con ROI > 1 |

## Limitaciones

- Los datos no incluyen comportamiento de usuarios: no se mide retención ni engagement.
- Hay exactamente 1.000 títulos por año y `date_added` coincide con `release_year`: no se analiza la evolución del catálogo.
- Solo el 22% de las películas tiene datos financieros (posible sesgo de selección); las series no tienen datos financieros.
- Los géneros de películas y series usan taxonomías distintas: se comparan dentro de cada tipo.
