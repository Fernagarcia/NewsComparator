
# src/storage.py
# ─────────────────────────────────────────────────────────────────────────────
# Responsabilidad: guardar y cargar artículos en disco como JSON.
#
# Por qué guardar en disco:
# - Evitamos volver a scrapear si queremos re-analizar los mismos artículos.
# - Podemos comparar resultados de distintas búsquedas en el futuro.
# - Construimos un dataset histórico de cobertura mediática.
# ─────────────────────────────────────────────────────────────────────────────

import json
import os
import re
from datetime import datetime

from config import DATA_RAW_DIR


def _slugify(texto: str) -> str:
    """Convierte un string en un nombre de archivo seguro."""
    texto = texto.lower().strip()
    texto = re.sub(r"[^\w\s-]", "", texto)
    texto = re.sub(r"[\s_-]+", "_", texto)
    return texto[:60]  # Máximo 60 caracteres para el nombre


def guardar_articulos(articulos: list, query: str) -> str:
    """
    Guarda una lista de artículos en un archivo JSON dentro de data/raw/.

    El nombre del archivo incluye el query y la fecha/hora para que
    múltiples búsquedas del mismo tema no se sobreescriban.

    Args:
        articulos: Lista de dicts con los artículos completos
        query:     El tema que se buscó

    Returns:
        Ruta completa del archivo guardado
    """
    os.makedirs(DATA_RAW_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    slug = _slugify(query)
    nombre_archivo = f"{timestamp}_{slug}.json"
    ruta = os.path.join(DATA_RAW_DIR, nombre_archivo)

    payload = {
        "query": query,
        "fecha_busqueda": datetime.now().isoformat(),
        "cantidad_articulos": len(articulos),
        "articulos": articulos,
    }

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"💾 Guardado en: {ruta}")
    return ruta


def cargar_articulos(ruta: str) -> dict:
    """
    Carga un archivo JSON previamente guardado.

    Args:
        ruta: Ruta al archivo .json

    Returns:
        Dict con keys: 'query', 'fecha_busqueda', 'cantidad_articulos', 'articulos'
    """
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def listar_busquedas_guardadas() -> list:
    """
    Devuelve una lista de todos los archivos JSON guardados en data/raw/,
    ordenados del más reciente al más antiguo.
    """
    if not os.path.exists(DATA_RAW_DIR):
        return []

    archivos = [
        os.path.join(DATA_RAW_DIR, f)
        for f in os.listdir(DATA_RAW_DIR)
        if f.endswith(".json")
    ]
    return sorted(archivos, reverse=True)
