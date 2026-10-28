"""Item Pipelines: validación, duplicados y persistencia de resultados."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import IO, Any, Optional

import scrapy
from itemadapter import ItemAdapter
from scrapy.crawler import Crawler
from scrapy.exceptions import DropItem

from book_manager.scraper.items import LibroCoincidenciaItem


class ValidacionPipeline:
  """Descarta items sin los datos mínimos para comparar precios."""

  def process_item(self, item: Any, spider: scrapy.Spider) -> Any:
    """Valida que el item tenga título local y precio web.

    Args:
      item: Item extraído por el spider.
      spider: Spider que generó el item.

    Returns:
      Any: El mismo item si es válido.

    Raises:
      DropItem: Si falta el título local o el precio.
    """
    datos = ItemAdapter(item)
    if not datos.get("titulo_local"):
      raise DropItem(f"Item sin título local: {dict(item)}")
    if datos.get("precio") is None:
      raise DropItem(f"Sin precio web para {datos.get('titulo_web')!r}")
    return item


class DuplicadosPipeline:
  """Evita guardar dos veces la misma ficha (misma URL de detalle)."""

  def open_spider(self, spider: scrapy.Spider) -> None:
    """Inicializa el conjunto de URLs procesadas.

    Args:
      spider: Spider que se abre.
    """
    self.vistos: set[str] = set()

  def process_item(self, item: Any, spider: scrapy.Spider) -> Any:
    """Descarta el item si su ficha ya fue procesada.

    Args:
      item: Item extraído por el spider.
      spider: Spider que generó el item.

    Returns:
      Any: El mismo item si no está repetido.

    Raises:
      DropItem: Si la URL de detalle ya fue procesada.
    """
    url = ItemAdapter(item).get("url_detalle")
    if url in self.vistos:
      raise DropItem(f"Ficha repetida: {url}")
    self.vistos.add(url)
    return item


class PersistenciaPipeline:
  """Guarda los items en reportes/scraping_<fecha>.jsonl y .csv.

  El JSON Lines es la entrada de las alertas (Ejercicio 04) y del
  reporte Excel (Ejercicio 05).

  Args:
    carpeta: Carpeta donde se guardan los archivos.
  """

  def __init__(self, carpeta: Path) -> None:
    self.carpeta = carpeta
    self.ruta_jsonl: Optional[Path] = None
    self.ruta_csv: Optional[Path] = None
    self.archivo_jsonl: Optional[IO[str]] = None
    self.archivo_csv: Optional[IO[str]] = None
    self.escritor: Optional[csv.DictWriter] = None

  @classmethod
  def from_crawler(cls, crawler: Crawler) -> "PersistenciaPipeline":
    """Crea el pipeline con la carpeta definida en settings.py.

    Args:
      crawler: Crawler que ejecuta el spider.

    Returns:
      PersistenciaPipeline: Pipeline configurado.
    """
    return cls(Path(crawler.settings.get("REPORTES_DIR", "reportes")))

  def open_spider(self, spider: scrapy.Spider) -> None:
    """Abre los archivos de salida con la fecha de la ejecución.

    Args:
      spider: Spider que se abre.
    """
    self.carpeta.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    self.ruta_jsonl = self.carpeta / f"scraping_{marca}.jsonl"
    self.ruta_csv = self.carpeta / f"scraping_{marca}.csv"
    self.archivo_jsonl = self.ruta_jsonl.open("w", encoding="utf-8")
    self.archivo_csv = self.ruta_csv.open(
      "w", encoding="utf-8", newline=""
    )
    self.escritor = csv.DictWriter(
      self.archivo_csv, fieldnames=list(LibroCoincidenciaItem.fields)
    )
    self.escritor.writeheader()

  def process_item(self, item: Any, spider: scrapy.Spider) -> Any:
    """Escribe el item en el JSONL y en el CSV.

    Args:
      item: Item validado.
      spider: Spider que generó el item.

    Returns:
      Any: El mismo item.
    """
    datos = ItemAdapter(item).asdict()
    self.archivo_jsonl.write(
      json.dumps(datos, ensure_ascii=False, default=str) + "\n"
    )
    self.escritor.writerow(
      {campo: datos.get(campo, "") for campo in LibroCoincidenciaItem.fields}
    )
    return item

  def close_spider(self, spider: scrapy.Spider) -> None:
    """Cierra los archivos de salida.

    Args:
      spider: Spider que se cierra.
    """
    self.archivo_jsonl.close()
    self.archivo_csv.close()
    spider.logger.info("Resultados guardados en %s", self.ruta_jsonl)
