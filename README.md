# StreamView Analytics – Panorama del Catálogo

Solución de **Visual Analytics** para transformar el catálogo audiovisual de StreamView Analytics en información clara y accionable, mediante un dashboard interactivo y narrativas visuales que apoyen la toma de decisiones.

> Proyecto grupal de la asignatura **ADY1104 – Visualización de Datos** (Duoc UC).
> **Integrantes:** _(completar)_ · **Docente:** _(completar)_ · **Sección:** _(completar)_

---

## Contenido

1. [Problema de negocio](#1-problema-de-negocio)
2. [Objetivos](#2-objetivos)
3. [Audiencia y propósito comunicacional](#3-audiencia-y-propósito-comunicacional)
4. [Fuentes de datos](#4-fuentes-de-datos)
5. [Hallazgos del análisis exploratorio](#5-hallazgos-del-análisis-exploratorio)
6. [Representaciones gráficas utilizadas](#6-representaciones-gráficas-utilizadas)
7. [Dashboard interactivo](#7-dashboard-interactivo)
8. [Evaluación crítica](#8-evaluación-crítica)
9. [Conclusiones y recomendaciones](#9-conclusiones-y-recomendaciones)
10. [Estructura del proyecto](#10-estructura-del-proyecto)
11. [Instalación y ejecución](#11-instalación-y-ejecución)

---

## 1. Problema de negocio

**Contexto.** StreamView Analytics es una plataforma de streaming latinoamericana, fundada en 2018, cuyo catálogo (películas, series y documentales de múltiples países, idiomas y géneros) ha crecido de forma sostenida gracias a acuerdos con estudios y proveedores internacionales. Esa expansión no ha ido acompañada de una capacidad equivalente para integrar y analizar la información de manera centralizada.

**Problema.** Las áreas de Marketing, Gerencia de Contenidos y Producto generan reportes con criterios y metodologías distintas. Esto produce indicadores inconsistentes, dificulta comparar resultados y limita el análisis interactivo.

**Consecuencia.** Se pierde tiempo validando reportes, cuesta identificar oportunidades por género o país y se pueden tomar decisiones con información parcial.

> El problema no es la falta de datos, sino la ausencia de una solución de Visual Analytics que permita integrar, estandarizar y transformar los datos en información útil.

## 2. Objetivos

**Objetivo general:** diseñar e implementar una solución de Visual Analytics que transforme el catálogo audiovisual de StreamView Analytics en información clara y accionable, mediante dashboards interactivos y narrativas visuales que apoyen decisiones estratégicas.

**Objetivos específicos**

- Caracterizar el catálogo según tipo de contenido, género, país e idioma.
- Identificar tendencias de producción e incorporación de contenidos en el tiempo.
- Comparar la popularidad y valoración del público entre géneros y países.
- Analizar la relación entre presupuesto e ingresos en el contenido cinematográfico.
- Diseñar un dashboard ejecutivo que consolide los principales KPIs del catálogo.
- Formular recomendaciones basadas en evidencia para decisiones de adquisición y promoción.

## 3. Audiencia y propósito comunicacional

| Stakeholder | Necesidad de información | Decisión que apoya |
|---|---|---|
| Directorio | Indicadores clave, tendencias y resultados generales | Inversión y crecimiento |
| Gerencia General | Visión global del catálogo y su desempeño | Planificación estratégica |
| Gerencia de Contenidos y Adquisición | Géneros, países y contenidos con mayor potencial | Adquisición y renovación de licencias |
| Gerencia de Marketing | Contenidos y categorías de mayor popularidad | Campañas promocionales |
| Gerencia de Producto | Características y composición del catálogo | Mejora de la experiencia de navegación |
| Data & Analytics | Calidad, consistencia y actualización de los datos | Mantención de dashboards |

El nivel de detalle se adapta a cada audiencia: indicadores y tendencias ejecutivas para Directorio y Gerencia General, y mayor detalle y segmentación por género, país y tipo para las gerencias.

## 4. Fuentes de datos

### Datasets originales (`data/raw/`)

| Archivo | Registros | Variables |
|---|---|---|
| `netflix_movies_detailed_up_to_2025.csv` | 16.000 | 18 |
| `netflix_tv_shows_detailed_up_to_2025.csv` | 16.000 | 16 |

### Datasets procesados (`data/processed/`)

| Archivo | Registros | Descripción |
|---|---|---|
| `netflix_movies_clean.csv` | 16.000 | Películas sin duplicados, con nulos imputados y `year_added` |
| `netflix_tv_clean.csv` | 15.991 | Series sin duplicados, con `year_added` y `seasons_count` |
| `netflix_movies_financial_clean.csv` | 3.540 | Películas con `budget > 0` y `revenue > 0`, con la columna `roi` |

### Variables relevantes

- **Categóricas:** `type`, `genres`, `country`, `language`, `rating`.
- **Temporales:** `date_added`, `year_added`, `release_year`.
- **Desempeño / audiencia:** `popularity`, `vote_count`, `vote_average`.
- **Financieras (solo películas):** `budget`, `revenue`, `roi` (`revenue / budget`).

### Integración

Ambos datasets comparten la estructura de columnas base y se etiquetan con el campo `type` (Movie / TV Show) para consolidarlos en un único catálogo. El análisis financiero se limita a películas, ya que solo ese dataset incluye `budget` y `revenue`.

### Calidad de datos y tratamiento

| Hallazgo | Tratamiento |
|---|---|
| **Duplicados** en series: 18 filas (9 títulos) repetidas por `show_id` | Se conserva la primera instancia. Quedan 15.991 series |
| **Nulos** en `director`, `cast`, `country`, `genres` (hasta 68,5 % en `director` de series) | Se imputan con `"Sin Información"` / `"Sin Género"`; no se elimina ninguna fila |
| **Ceros disfrazados de dato faltante** en `budget` (11.153) y `revenue` (10.355) en películas | Se aísla el subconjunto con valores `> 0` (3.540 películas, 22,1 % del catálogo de películas) |
| **ROI distorsionado** por presupuestos irrisorios | Se reporta la **mediana** del ROI como estadístico principal |
| **Campos multivalor** (`genres`, `country`) | Se desanidan (`explode`) para los rankings |
| **Variables no utilizables:** `duration` en películas (100 % nula) y `seasons_count` en series (valor constante) | Se excluyen del análisis |

## 5. Hallazgos del análisis exploratorio

- **Géneros:** Drama y Comedia concentran el mayor volumen; las películas dominan en casi todas las categorías principales.
- **Crecimiento:** la incorporación de títulos crece de forma sostenida entre 2010 y 2025, con más películas que series en el acumulado.
- **Popularidad:** la mediana es similar entre películas y series, pero las series muestran más valores atípicos de alta tracción.
- **Popularidad vs. calificación:** mayor popularidad no implica mejor calificación; los contenidos más vistos se concentran en notas de 6,0 a 7,5 y existen "joyas ocultas" con buena nota y poco consumo.
- **ROI por género:** géneros de presupuesto moderado (Horror, Comedia, Animación) lideran la rentabilidad frente a producciones de alto costo como Acción.
- **Correlaciones:** alta correlación positiva entre presupuesto e ingresos, y entre votos y popularidad; la calificación no depende linealmente del presupuesto.
- **Presupuesto vs. recaudación:** más presupuesto aumenta la probabilidad de alta recaudación, pero la dispersión revela producciones con pérdidas severas.
- **Votos vs. popularidad:** la popularidad está respaldada por el volumen de votos, con una interacción más marcada en series.
- **Países:** Estados Unidos lidera con holgura; Corea del Sur y Reino Unido destacan por su especialización relativa en series.

## 6. Representaciones gráficas utilizadas

| Visualización | Gráfico | Por qué |
|---|---|---|
| Top 10 géneros por tipo | Barras horizontales agrupadas | Comparar magnitudes de categorías discretas con etiquetas legibles |
| Crecimiento acumulado del catálogo | Líneas con marcadores | Mostrar continuidad y trayectoria temporal |
| Distribución de popularidad | Diagrama de caja | Comparar distribuciones asimétricas (mediana y rango intercuartílico) |
| Popularidad vs. calificación | Dispersión | Examinar relación, dispersión y densidad entre dos variables continuas |
| ROI mediano por género | Barras horizontales ordenadas | Clasificar una métrica agregada por categoría |
| Matriz de correlación | Mapa de calor | Condensar coeficientes de correlación en una matriz |
| Presupuesto vs. recaudación | Dispersión con línea de regresión | Modelar la relación lineal y su variabilidad |
| Votos vs. popularidad | Dispersión agrupada por tipo | Analizar patrones de interacción |
| Top 10 países de origen | Barras horizontales agrupadas | Comparar frecuencias nominales por territorio |

**Criterios de diseño:** color categórico consistente (amarillo = películas, fucsia = series, verde = rentabilidad, azul = ingresos), transparencia para controlar la densidad en dispersiones y principios de percepción visual (procesamiento pre-atentivo, leyes de proximidad y continuidad, jerarquía visual).

## 7. Dashboard interactivo

Construido con **Python + Plotly Dash**, con interactividad mediante callbacks en tiempo real entre filtros, KPIs y gráficos.

### KPIs

| KPI | Valor (sin filtros) | Descripción |
|---|---|---|
| Total títulos | 31.991 | Volumen global del catálogo consolidado |
| Películas | 16.000 | Total de largometrajes |
| Series TV | 15.991 | Total de series |
| ROI mediano | 1,70x | Retorno mediano de las películas con datos financieros válidos |
| Recaudación promedio | $103,8 M | Ingreso promedio por película con datos financieros válidos |

### Filtros

- **Tipo de contenido:** Todos / Películas / Series TV.
- **País de origen:** todos o un país específico.
- **Año de incorporación al catálogo:** deslizador de rango (2010–2025).

### Navegación

- **Análisis de Contenido y Audiencia:** composición del catálogo, crecimiento, origen geográfico, popularidad y engagement.
- **Desempeño Financiero y Mercado:** ROI por género, correlaciones y presupuesto vs. recaudación.

## 8. Evaluación crítica

**Fortalezas**

- Integra distintas fuentes en una herramienta interactiva para analizar composición, evolución temporal, popularidad, origen geográfico y desempeño financiero.
- Las representaciones gráficas se eligieron según la naturaleza de las variables y el objetivo del análisis.
- Los filtros por tipo, país y año permiten explorar según la necesidad de cada usuario.

**Limitaciones**

- La calidad de las conclusiones depende de la preparación de los datos (nulos, duplicados, ceros disfrazados, variables inútiles).
- Los datos corresponden al catálogo, no al comportamiento de los usuarios (reproducciones, suscripciones, dispositivos).
- El análisis financiero cubre solo el 22,1 % de las películas.
- La integración mediante el campo `type` limita algunos análisis por la heterogeneidad entre fuentes.

**Oportunidades de mejora**

- Incorporar datos de comportamiento de usuarios, reproducciones e interacción.
- Automatizar la actualización de los datos.
- Ampliar los filtros y las métricas del dashboard.

## 9. Conclusiones y recomendaciones

**Conclusiones**

- El catálogo se concentra en Drama y Comedia y crece de forma sostenida entre 2010 y 2025.
- Mayor popularidad no implica mejor valoración: conviene evaluar los contenidos con múltiples indicadores.
- Los géneros de presupuesto moderado ofrecen mejor ROI mediano que las producciones de alto costo, y una mayor inversión no garantiza recuperar los costos.

**Recomendaciones**

1. Considerar el **ROI** como criterio en futuras adquisiciones o producciones, especialmente en géneros con mejor rendimiento relativo.
2. Evitar decisiones basadas solo en popularidad y complementarla con calificaciones e interacción.
3. Usar el dashboard como herramienta de planificación estratégica para comparar contenidos por género, país, tipo y período.
4. Incorporar nuevas fuentes de datos y automatizar la actualización para mejorar la consistencia y vigencia de la información.

## 10. Estructura del proyecto

```
proyecto/
├── data/
│   ├── raw/                  # Datasets originales
│   │   ├── netflix_movies_detailed_up_to_2025.csv
│   │   └── netflix_tv_shows_detailed_up_to_2025.csv
│   └── processed/            # Datasets limpios
│       ├── netflix_movies_clean.csv
│       ├── netflix_tv_clean.csv
│       └── netflix_movies_financial_clean.csv
├── notebooks/
│   └── Limpieza_DataSet_corregido.ipynb   # Limpieza, EDA y gráficos
├── dashboard/
│   └── Dashboard.py          # Aplicación Dash
├── images/                   # Gráficos exportados e infografía
├── src/                      # Código auxiliar (opcional)
├── informe/                  # Informe ejecutivo y resumen ejecutivo
├── requirements.txt
└── README.md
```

## 11. Instalación y ejecución

**Requisitos:** Python 3.10 o superior.

```bash
# 1. (Opcional) crear un entorno virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar el dashboard
python dashboard/Dashboard.py
```

Luego abrir en el navegador la dirección que muestra la consola (por defecto `http://127.0.0.1:8050`).

**Para reproducir la limpieza de datos:** abrir `notebooks/Limpieza_DataSet_corregido.ipynb` y ejecutarlo completo. Genera los tres CSV de `data/processed/` a partir de los de `data/raw/`.

**Dependencias principales** (`requirements.txt`):

```
pandas
numpy
plotly
dash
statsmodels
matplotlib
seaborn
jupyter
```

> `statsmodels` es necesario para la línea de tendencia (OLS) del gráfico de presupuesto vs. recaudación. `matplotlib` y `seaborn` se usan en el notebook.
