"""Configuración de Scrapy para el spider de Cúspide.

Se aplican reglas de cortesía: una sola petición concurrente, demora
entre peticiones y AutoThrottle. ROBOTSTXT_OBEY queda en False porque el
robots.txt de Cúspide solo restringe /cgi-bin/ y desde Colab responde
403; las búsquedas y las fichas de producto están permitidas.
"""

from pathlib import Path

BOT_NAME = "book_manager"
SPIDER_MODULES = ["book_manager.scraper.spiders"]

ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 2.0
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
COOKIES_ENABLED = True
TELNETCONSOLE_ENABLED = False
LOG_LEVEL = "INFO"
FEED_EXPORT_ENCODING = "utf-8"

RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [403, 429, 500, 502, 503, 504]

USER_AGENT = (
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_REQUEST_HEADERS = {
  "Accept": (
    "text/html,application/xhtml+xml,application/xml;q=0.9,"
    "image/avif,image/webp,image/apng,*/*;q=0.8"
  ),
  "Accept-Language": "es-ES,es;q=0.9",
  "Referer": "https://cuspide.com/",
}

REPORTES_DIR = str(Path(__file__).resolve().parents[1] / "reportes")

ITEM_PIPELINES = {
  "book_manager.scraper.pipelines.ValidacionPipeline": 100,
  "book_manager.scraper.pipelines.DuplicadosPipeline": 200,
  "book_manager.scraper.pipelines.PersistenciaPipeline": 300,
}
