# NewsComparator

Proyecto de ciencia de datos para analizar cómo distintos medios de comunicación
cubren una misma noticia y detectar diferencias en enfoque, tono y posibles sesgos narrativos.

## Estructura del proyecto

```
media-bias-analyzer/
│
├── src/                        # Módulos Python reutilizables
│   ├── __init__.py
│   ├── config.py               # ← Parámetros ajustables (medios, timeouts, etc.)
│   ├── scraper.py              # Búsqueda en Google News + resolución de URLs
│   ├── extractor.py            # Extracción de texto con trafilatura
│   └── storage.py              # Guardado/carga de artículos en JSON
│
├── notebooks/
│   ├── 01_scraping.ipynb       # ← Etapa 1: recolección de datos (ACTUAL)
│   ├── 02_analisis.ipynb       # Etapa 2: NLP y análisis (próximamente)
│   └── 03_visualizacion.ipynb  # Etapa 3: visualizaciones (próximamente)
│
├── data/
│   ├── raw/                    # Artículos scrapeados (JSON)
│   └── processed/              # Resultados del análisis
│
└── requirements.txt
```

## Setup

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Correr el notebook de scraping
jupyter notebook notebooks/01_scraping.ipynb
```

## Agregar nuevos medios

Editá `src/config.py` y agregá el dominio a `MEDIOS_OBJETIVO`:

```python
MEDIOS_OBJETIVO = [
    "clarin.com",
    "a24.com",
    "pagina12.com.ar",
    "infobae.com"
]
```

Si el medio tiene tipos de contenido a excluir (videos, galerías), agregalos también en `REGLAS_FILTRADO`.

## Estado del proyecto

- [x] Etapa 1 — Scraping y extracción de texto
- [ ] Etapa 2 — Preprocesamiento NLP (spaCy, entidades)
- [ ] Etapa 3 — Análisis (sentimiento, embeddings, framing)
- [ ] Etapa 4 — Visualizaciones comparativas
