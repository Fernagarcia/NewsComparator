# ─────────────────────────────────────────────────────────────────────────────
# Responsabilidad: buscar noticias en Google News, resolver los redirects
# de Google y filtrar/rankear resultados por medio.
# ─────────────────────────────────────────────────────────────────────────────

import time
import random
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    # GoogleNews a veces devuelve la URL como bytes en lugar de str
    if isinstance(url, bytes):
        url = url.decode("utf-8")

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


def _resolver_url_noticia(noticia: dict) -> dict:
    """
    Wrapper de resolver_url() que opera sobre un dict de noticia completo.
    Diseñado para ser usado con ThreadPoolExecutor — recibe y devuelve
    el dict entero para no perder los metadatos (título, media, etc.)
    """
    url_real = resolver_url(noticia.get("link", ""))
    return {
        **noticia,
        "link_real": url_real,
        "dominio": dominio_de_url(url_real),
    }


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

    prefijos_excluidos = REGLAS_FILTRADO.get(dominio, [])
    if any(titulo.startswith(prefijo) for prefijo in prefijos_excluidos):
        return False

    return True


def elegir_mas_relevante_por_medio(noticias: list, consulta: str) -> list:
    """
    De todas las noticias recolectadas, elige la más relevante por cada medio.
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


# ── Resolución de URLs en paralelo ────────────────────────────────────────────

def resolver_urls_en_paralelo(noticias: list, verbose: bool = True) -> list:
    """
    Resuelve los redirects de todas las noticias en paralelo usando threads.

    Usamos ThreadPoolExecutor porque resolver_url() es I/O-bound: la CPU
    queda idle esperando respuestas HTTP, por lo que múltiples hilos pueden
    trabajar simultáneamente sin bloquearse entre sí.

    El número de workers está definido en SCRAPER_CONFIG para poder ajustarlo
    sin tocar el código. Un valor de 10 es razonable: suficiente paralelismo
    sin saturar los servidores ni generar un 429.

    Args:
        noticias: Lista de dicts con key 'link' (URL original de Google News)
        verbose:  Si True, imprime progreso

    Returns:
        Lista de dicts enriquecidos con 'link_real' y 'dominio'
    """
    workers = SCRAPER_CONFIG["resolver_workers"]

    if verbose:
        print(f"Resolviendo {len(noticias)} URLs en paralelo ({workers} workers)...")

    resultados = [None] * len(noticias)  # Preallocamos para mantener el orden original

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Mapeamos cada future a su índice original para mantener el orden
        futures = {
            executor.submit(_resolver_url_noticia, noticia): i
            for i, noticia in enumerate(noticias)
        }

        completadas = 0
        for future in as_completed(futures):
            i = futures[future]
            resultados[i] = future.result()
            completadas += 1
            if verbose:
                print(f"   {completadas}/{len(noticias)} URLs resueltas...", end="\r")

    if verbose:
        print(f"   {len(noticias)}/{len(noticias)} URLs resueltas.           ")

    return resultados


# ── Búsqueda principal ────────────────────────────────────────────────────────

def buscar_noticias(query: str, verbose: bool = True) -> list:
    """
    Punto de entrada principal de este módulo.

    1. Busca en Google News por el query dado
    2. Recorre múltiples páginas de resultados deduplicando por link
    3. Resuelve todas las URLs en paralelo con ThreadPoolExecutor
    4. Filtra y rankea para quedarse con la mejor noticia por medio
    """
    cfg = GOOGLENEWS_CONFIG
    if verbose:
        print(f"Buscando: '{query}' ({cfg['paginas']} páginas)")

    googlenews = GoogleNews(lang=cfg["lang"], region=cfg["region"])
    googlenews.search(query)

    todos_los_resultados = []
    links_vistos = set()

    for page in range(1, cfg["paginas"] + 1):
        googlenews.getpage(page)
        nuevos = 0
        resultados = googlenews.result()

        for noticia in resultados:
            print("Llegue a la noticia:", noticia.get("title"))
            link = noticia.get("link", "")
            if link and link not in links_vistos:
                links_vistos.add(link)
                todos_los_resultados.append(noticia)
                nuevos += 1
            delay = random.uniform(1, 5)
        if verbose:
            print(f"   Página {page}/{cfg['paginas']} ({nuevos} nuevas, {len(todos_los_resultados)} únicas). Esperando {delay:.1f}s...")
        time.sleep(delay)

    if verbose:
        print(f"   {len(todos_los_resultados)} resultados únicos recolectados")

    # Resolución en paralelo en lugar de secuencial
    todos_los_resultados = resolver_urls_en_paralelo(todos_los_resultados, verbose=verbose)

    noticias_principales = elegir_mas_relevante_por_medio(todos_los_resultados, query)

    if verbose:
        print(f"\n{len(noticias_principales)} artículos encontrados en medios objetivo:\n")
        for n in noticias_principales:
            print(f"  [{n['dominio']}] {n['title']}")
            print(f"   -> {n['link_real']}\n")

    return noticias_principales