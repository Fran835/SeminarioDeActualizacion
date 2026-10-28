"""Ejecuta el spider de Cúspide en un proceso independiente.

El reactor de Twisted no se puede reiniciar dentro del mismo proceso,
por eso cada ejecución del scraper se lanza con
"python -m book_manager.scraper.runner" y arranca un reactor limpio.
"""

import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from book_manager.scraper.spiders.cuspide import CuspideSpider

RAIZ_REPO: Path = Path(__file__).resolve().parents[3]


def ejecutar(titulos: Optional[str] = None) -> None:
  """Lanza el scraping y espera a que termine.

  Args:
    titulos: Títulos separados por "|"; si es None se usa el catálogo.
  """
  load_dotenv(RAIZ_REPO / ".env")
  configuracion = Settings()
  configuracion.setmodule(
    "book_manager.scraper.settings", priority="project"
  )
  proceso = CrawlerProcess(configuracion)
  proceso.crawl(CuspideSpider, titulos=titulos)
  proceso.start()


if __name__ == "__main__":
  ejecutar(sys.argv[1] if len(sys.argv) > 1 else None)
