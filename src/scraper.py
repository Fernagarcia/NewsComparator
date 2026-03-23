
# src/scraper.py
# ─────────────────────────────────────────────────────────────────────────────
# Responsabilidad: buscar noticias en Google News, resolver los redirects
# de Google y filtrar/rankear resultados por medio.
#
# PROBLEMA QUE RESUELVE:
# GoogleNews devuelve URLs del tipo "https://news.google.com/rss/articles/..."
# que son redirects. Si hacés dominio_de_url() sobre eso, siempre obtenés
# "news.google.com", nunca "clarin.com". Por eso tu lista aparecía vacía.
# Acá resolvemos la URL real antes de cualquier filtrado.
# ─────────────────────────────────────────────────────────────────────────────

import time
import requests
from urllib.parse import urlparse
from GoogleNews import GoogleNews

from config import GOOGLENEWS_CONFIG, SCRAPER_CONFIG, MEDIOS_OBJETIVO, REGLAS_FILTRADO


# ── Helpers de URL ────────────────────────────────────────────────────────────

def dominio_de_url(url: str) -> str:
    """
    Extrae el dominio limpio de una URL.
    Ejemplo: 'https://www.clarin.com/...' → 'clarin.com'
    """
    return urlparse(url).netloc.replace("www.", "")


def resolver_url(url: str) -> str:
    """
    Sigue los redirects de una URL y devuelve la URL final real.
    Necesario porque Google News entrega URLs intermedias que apuntan
    al artículo real recién al final de la cadena de redirects.

    Si algo falla (timeout, error de red), devuelve la URL original.
    """
    headers = {"User-Agent": SCRAPER_CONFIG["user_agent"]}
    try:
        response = requests.get(
            url,
            allow_redirects=True,
            timeout=SCRAPER_CONFIG["timeout"],
            headers=headers,
        )
        return response.url
    except requests.RequestException:
        return url


# ── Filtrado de noticias ──────────────────────────────────────────────────────

def es_valida(noticia: dict) -> bool:
    """
    Determina si una noticia debe incluirse en el análisis.

    Criterios de exclusión:
    - El dominio no está en MEDIOS_OBJETIVO
    - El título o el link están vacíos
    - El título empieza con alguna de las palabras excluidas para ese dominio
      (definidas en REGLAS_FILTRADO en config.py)
    """
    titulo = noticia.get("title", "").strip().lower()
    link = noticia.get("link_real", noticia.get("link", ""))
    dominio = dominio_de_url(link)

    if dominio not in MEDIOS_OBJETIVO:
        return False

    if not link or not titulo:
        return False

    # Aplicar reglas específicas por medio
    prefijos_excluidos = REGLAS_FILTRADO.get(dominio, [])
    if any(titulo.startswith(prefijo) for prefijo in prefijos_excluidos):
        return False

    return True


def elegir_mas_relevante_por_medio(noticias: list, consulta: str) -> list:
    """
    De todas las noticias recolectadas, elige la más relevante por cada medio.

    La relevancia se mide como la cantidad de palabras de la consulta
    que aparecen en el título del artículo. Es una heurística simple
    pero efectiva para este propósito.

    Args:
        noticias: Lista de dicts con keys 'title', 'link', 'link_real', 'media'
        consulta: El tema que buscó el usuario

    Returns:
        Lista con una noticia por medio (la más relevante de cada uno)
    """
    mejores = {}
    palabras_consulta = consulta.lower().split()

    for noticia in noticias:
        if not es_valida(noticia):
            continue

        link = noticia.get("link_real", noticia.get("link", ""))
        dominio = dominio_de_url(link)
        titulo = noticia.get("title", "").lower()

        relevancia = sum(palabra in titulo for palabra in palabras_consulta)

        if dominio not in mejores or relevancia > mejores[dominio]["relevancia"]:
            mejores[dominio] = {"noticia": noticia, "relevancia": relevancia}

    return [data["noticia"] for data in mejores.values()]


# ── Búsqueda principal ────────────────────────────────────────────────────────

def buscar_noticias(query: str, verbose: bool = True) -> list:
    """
    Punto de entrada principal de este módulo.

    1. Busca en Google News por el query dado
    2. Recorre múltiples páginas de resultados
    3. Resuelve cada URL para obtener el link real al artículo
    4. Filtra y rankea para quedarse con la mejor noticia por medio

    Args:
        query:   Tema a buscar (ej: "reforma previsional Argentina")
        verbose: Si True, imprime progreso en pantalla

    Returns:
        Lista de dicts, uno por medio, con keys:
        {
            "title":     título del artículo,
            "media":     nombre del medio según Google News,
            "link":      URL original (redirect de Google),
            "link_real": URL real del artículo después de resolver redirects,
            "dominio":   dominio limpio (ej: "clarin.com"),
            "date":      fecha según Google News,
        }
    """
    cfg = GOOGLENEWS_CONFIG
    if verbose:
        print(f"🔍 Buscando: '{query}' ({cfg['paginas']} páginas)")

    # Inicializar y buscar
    googlenews = GoogleNews(lang=cfg["lang"], region=cfg["region"])
    googlenews.search(query)

    todos_los_resultados = []
    for page in range(1, cfg["paginas"] + 1):
        if verbose:
            print(f"   Página {page}/{cfg['paginas']}...", end="\r")
        googlenews.getpage(page)
        todos_los_resultados.extend(googlenews.result())

    if verbose:
        print(f"   {len(todos_los_resultados)} resultados crudos recolectados")

    # Resolver URLs reales (este es el paso clave que faltaba)
    if verbose:
        print("🔗 Resolviendo redirects de Google News...")

    for i, noticia in enumerate(todos_los_resultados):
        url_original = noticia.get("link", "")
        url_real = resolver_url(url_original)
        noticia["link_real"] = url_real
        noticia["dominio"] = dominio_de_url(url_real)

        if verbose and (i + 1) % 10 == 0:
            print(f"   {i+1}/{len(todos_los_resultados)} URLs resueltas...", end="\r")

        time.sleep(0.2)  # Pequeña pausa para no saturar

    if verbose:
        print(f"   Todas las URLs resueltas                    ")

    # Filtrar y rankear
    noticias_principales = elegir_mas_relevante_por_medio(todos_los_resultados, query)

    if verbose:
        print(f"✅ {len(noticias_principales)} artículos encontrados en medios objetivo:\n")
        for n in noticias_principales:
            print(f"  [{n['dominio']}] {n['title']}")
            print(f"   → {n['link_real']}\n")

    return noticias_principales
