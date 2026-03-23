
# src/extractor.py
# ─────────────────────────────────────────────────────────────────────────────
# Responsabilidad: dado un artículo con su URL real, descargar la página
# y extraer el cuerpo del texto limpio (sin publicidad, sidebar, nav, etc.)
#
# Usa trafilatura, que supera a BeautifulSoup/newspaper3k en precisión
# para medios en español y maneja bien el HTML de Clarín, Página 12 y A24.
# ─────────────────────────────────────────────────────────────────────────────

import time
import trafilatura
import requests

from config import SCRAPER_CONFIG, EXTRACTOR_CONFIG


def extraer_texto(url: str) -> str | None:
    """
    Descarga una página web y extrae su contenido textual principal.

    Usa trafilatura con `favor_precision=True` para minimizar el ruido
    (publicidades, menús, footers) a costa de posiblemente perder algunos
    párrafos del cuerpo. Para análisis de sesgos esto es preferible.

    Args:
        url: URL real del artículo (ya resuelta, no el redirect de Google)

    Returns:
        Texto limpio del artículo, o None si no se pudo extraer contenido válido.
    """
    cfg = EXTRACTOR_CONFIG
    headers = {"User-Agent": SCRAPER_CONFIG["user_agent"]}

    try:
        # Descargar el HTML
        response = requests.get(
            url,
            timeout=SCRAPER_CONFIG["timeout"],
            headers=headers,
        )
        response.raise_for_status()
        html = response.text

    except requests.RequestException as e:
        print(f"   ⚠️  Error de red al acceder a {url}: {e}")
        return None

    # Extraer el texto con trafilatura
    texto = trafilatura.extract(
        html,
        include_comments=cfg["incluir_comentarios"],
        include_tables=cfg["incluir_tablas"],
        favor_precision=cfg["favor_precision"],
        no_fallback=False,  # Si trafilatura falla, intenta con readability como fallback
    )

    # Validar que el texto tiene sustancia
    if not texto or len(texto) < cfg["min_longitud_texto"]:
        return None

    return texto.strip()


def extraer_texto_articulos(noticias: list, verbose: bool = True) -> list:
    """
    Recorre una lista de noticias y le agrega el texto completo a cada una.

    Los artículos donde no se pudo extraer texto son excluidos del resultado
    y se informa cuántos fallaron.

    Args:
        noticias: Lista de dicts (output de scraper.buscar_noticias)
        verbose:  Si True, imprime progreso

    Returns:
        Lista de dicts enriquecidos con la key "texto" agregada.
        Solo incluye artículos donde la extracción fue exitosa.
    """
    if verbose:
        print(f"📄 Extrayendo texto de {len(noticias)} artículos...\n")

    articulos_completos = []
    fallos = []

    for noticia in noticias:
        url = noticia.get("link_real", noticia.get("link", ""))
        dominio = noticia.get("dominio", url)

        if verbose:
            print(f"  Extrayendo [{dominio}]...")

        texto = extraer_texto(url)

        if texto:
            articulo = {**noticia, "texto": texto}  # Copia el dict y agrega "texto"
            articulos_completos.append(articulo)

            if verbose:
                palabras = len(texto.split())
                print(f"  ✅ {palabras} palabras extraídas\n")
        else:
            fallos.append(dominio)
            if verbose:
                print(f"  ❌ No se pudo extraer texto (paywall o estructura no compatible)\n")

        # Esperar entre requests para no saturar los servidores
        time.sleep(SCRAPER_CONFIG["delay_entre_requests"])

    if verbose:
        print(f"Resultado: {len(articulos_completos)} exitosos, {len(fallos)} fallidos")
        if fallos:
            print(f"Fallidos: {', '.join(fallos)}")

    return articulos_completos
