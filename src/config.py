
# src/config.py
# ─────────────────────────────────────────────────────────────────────────────
# Configuración central del proyecto.
# Todos los parámetros ajustables están acá para no tener "magic values"
# dispersos en el código.
# ─────────────────────────────────────────────────────────────────────────────

# Medios de comunicación que queremos analizar.
# Agregar o quitar dominios acá afecta todo el pipeline automáticamente.
MEDIOS_OBJETIVO = [
    "clarin.com",
    "a24.com",
    "pagina12.com.ar",
]

# Configuración de la búsqueda en Google News
GOOGLENEWS_CONFIG = {
    "lang": "es",
    "region": "AR",
    "paginas": 1,           # Cuántas páginas de resultados recorrer (1 página ≈ 10 noticias)
}

# Configuración del scraper HTTP
SCRAPER_CONFIG = {
    "timeout": 15,          # Segundos antes de abandonar una request
    "delay_entre_requests": 1.5,  # Segundos de espera entre artículo y artículo (cortesía)
    "resolver_workers": 3,
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
}

# Configuración del extractor de texto
EXTRACTOR_CONFIG = {
    "min_longitud_texto": 200,      # Caracteres mínimos para considerar un artículo válido
    "incluir_comentarios": False,
    "incluir_tablas": False,
    "favor_precision": True,        # trafilatura: priorizar precisión sobre recall
}

# Reglas de filtrado por dominio.
# Clave: dominio. Valor: lista de prefijos de título a excluir.
REGLAS_FILTRADO = {
    "clarin.com": ["video", "galería", "foto"],
    "a24.com": [],
    "pagina12.com.ar": [],
}

# Rutas de directorios de datos
DATA_RAW_DIR = "data/raw"           # Artículos scrapeados sin procesar
DATA_PROCESSED_DIR = "data/processed"  # Resultados de análisis
