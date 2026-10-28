"""Spider de Cúspide: busca los libros del catálogo y extrae sus fichas."""

import json
import re
from collections.abc import AsyncIterator, Iterator
from datetime import datetime
from decimal import Decimal, InvalidOperation
from html import unescape
from typing import Any, Optional
from urllib.parse import quote

import scrapy
from scrapy.exceptions import CloseSpider
from scrapy.http import Response
from scrapy.selector import Selector
from sqlalchemy import select
from twisted.python.failure import Failure

from book_manager.database.connection import ConexionDB
from book_manager.models.models import LibroModel
from book_manager.scraper.items import LibroCoincidenciaItem
from book_manager.scraper.loader import LibroLoader

ESTADOS_BLOQUEO: list[int] = [403, 429]


class CuspideSpider(scrapy.Spider):
  """Busca cada título del catálogo y sigue los 10 primeros resultados.

  Solo se buscan títulos del catálogo propio: si no se reciben títulos,
  se leen de la tabla de libros de la base de datos.

  Args:
    titulos: Títulos separados por "|"; si es None se usa el catálogo.
  """

  name = "cuspide"
  allowed_domains = ["cuspide.com"]
  max_resultados = 10
  url_busqueda = "https://cuspide.com/?s={consulta}&post_type=product"
  url_api = (
    "https://cuspide.com/wp-json/wc/store/products"
    "?search={consulta}&per_page={limite}"
  )

  def __init__(
    self, titulos: Optional[str] = None, *args: Any, **kwargs: Any
  ) -> None:
    super().__init__(*args, **kwargs)
    self.titulos = self._leer_titulos(titulos)
    self._api_solicitada: set[str] = set()

  @staticmethod
  def _leer_titulos(titulos: Optional[str]) -> list[str]:
    """Devuelve los títulos recibidos o los del catálogo en la base.

    Args:
      titulos: Títulos separados por "|" o None.

    Returns:
      list[str]: Títulos a buscar.
    """
    if titulos:
      return [t.strip() for t in titulos.split("|") if t.strip()]
    with ConexionDB().transaccion() as sesion:
      consulta = select(LibroModel.titulo).order_by(LibroModel.id)
      return list(sesion.scalars(consulta))

  async def start(self) -> AsyncIterator[scrapy.Request]:
    """Punto de entrada asíncrono de Scrapy 2.13 o superior.

    Yields:
      scrapy.Request: Búsqueda de cada título.
    """
    for peticion in self.start_requests():
      yield peticion

  def start_requests(self) -> Iterator[scrapy.Request]:
    """Genera una búsqueda por cada título del catálogo.

    Yields:
      scrapy.Request: Búsqueda de un título en Cúspide.

    Raises:
      CloseSpider: Si no hay títulos para buscar.
    """
    if not self.titulos:
      raise CloseSpider("No hay títulos del catálogo para buscar.")
    self.logger.info("Títulos a buscar: %d", len(self.titulos))
    for titulo in self.titulos:
      yield scrapy.Request(
        self.url_busqueda.format(consulta=quote(titulo)),
        callback=self.parse_resultados,
        errback=self.parse_error,
        meta={
          "titulo_local": titulo,
          "handle_httpstatus_list": ESTADOS_BLOQUEO,
        },
      )

  def parse_resultados(
    self, response: Response
  ) -> Iterator[scrapy.Request]:
    """Sigue las fichas de los primeros 10 resultados únicos.

    Si Cúspide bloquea la búsqueda o no devuelve tarjetas, se consulta la
    API pública de la tienda como respaldo.

    Args:
      response: Página de resultados de la búsqueda.

    Yields:
      scrapy.Request: Petición a la ficha de cada resultado.
    """
    titulo = response.meta["titulo_local"]
    tarjetas = response.css("div.product-small")
    if response.status in ESTADOS_BLOQUEO or not tarjetas:
      self.logger.warning(
        "Búsqueda de %r con estado %s; se usa la API.",
        titulo,
        response.status,
      )
      yield from self._solicitar_api(titulo)
      return
    vistos: set[str] = set()
    for tarjeta in tarjetas:
      url = tarjeta.css(".product-title a::attr(href)").get()
      if not url or url in vistos:
        continue
      vistos.add(url)
      yield response.follow(
        url,
        callback=self.parse_detalle,
        errback=self.parse_error,
        meta={
          "titulo_local": titulo,
          "handle_httpstatus_list": ESTADOS_BLOQUEO,
        },
      )
      if len(vistos) >= self.max_resultados:
        break
    self.logger.info("Resultados para %r: %d", titulo, len(vistos))

  def parse_detalle(self, response: Response) -> Iterator[Any]:
    """Extrae precio, imagen, formas de pago y descripción de una ficha.

    Args:
      response: Página de la ficha del libro.

    Yields:
      LibroCoincidenciaItem | scrapy.Request: Item cargado o la petición
        de respaldo a la API si la ficha fue bloqueada.
    """
    if response.status in ESTADOS_BLOQUEO:
      yield from self._solicitar_api(response.meta["titulo_local"])
      return
    loader = LibroLoader(response=response)
    loader.add_value("titulo_local", response.meta["titulo_local"])
    loader.add_css("isbn", "p.livriz-code::text")
    loader.add_css("titulo_web", "h1.product-title::text")
    loader.add_css(
      "precio", "p.price .woocommerce-Price-amount bdi::text"
    )
    loader.add_css(
      "precio_usd", 'div.product-info span[style*="1.1em"] span::text'
    )
    loader.add_css(
      "url_imagen",
      "div.woocommerce-product-gallery img.wp-post-image::attr(src)",
    )
    loader.add_css("formas_pago", "#contentPaymentsPopUpArg li::text")
    loader.add_css("descripcion", "p.livriz-text-synopsis::text")
    loader.add_value("url_detalle", response.url)
    loader.add_value(
      "fecha_extraccion", datetime.now().isoformat(timespec="seconds")
    )
    yield loader.load_item()

  def _solicitar_api(self, titulo: str) -> Iterator[scrapy.Request]:
    """Pide los primeros productos del título a la API de la tienda.

    Args:
      titulo: Título del catálogo a buscar.

    Yields:
      scrapy.Request: Petición a la API (una sola vez por título).
    """
    if titulo in self._api_solicitada:
      return
    self._api_solicitada.add(titulo)
    yield scrapy.Request(
      self.url_api.format(
        consulta=quote(titulo), limite=self.max_resultados
      ),
      callback=self.parse_api,
      errback=self.parse_error,
      headers={"Accept": "application/json"},
      meta={
        "titulo_local": titulo,
        "handle_httpstatus_list": ESTADOS_BLOQUEO,
      },
    )

  def parse_api(
    self, response: Response
  ) -> Iterator[LibroCoincidenciaItem]:
    """Convierte la respuesta JSON de la tienda en items.

    Args:
      response: Respuesta de la API de productos.

    Yields:
      LibroCoincidenciaItem: Un item por producto (máximo 10).
    """
    titulo = response.meta["titulo_local"]
    if response.status != 200:
      self.logger.error("La API devolvió %s.", response.status)
      return
    try:
      productos = response.json()
    except (ValueError, json.JSONDecodeError):
      self.logger.error("La API no devolvió JSON para %r.", titulo)
      return
    if not isinstance(productos, list):
      return
    for producto in productos[: self.max_resultados]:
      loader = LibroLoader()
      loader.add_value("titulo_local", titulo)
      loader.add_value("isbn", producto.get("sku") or "")
      loader.add_value("titulo_web", producto.get("name") or "")
      loader.add_value("precio", self._precio_api(producto))
      loader.add_value("url_imagen", self._imagen_api(producto))
      loader.add_value("formas_pago", "")
      loader.add_value("descripcion", self._descripcion_api(producto))
      loader.add_value("url_detalle", producto.get("permalink") or "")
      loader.add_value(
        "fecha_extraccion", datetime.now().isoformat(timespec="seconds")
      )
      yield loader.load_item()

  @staticmethod
  def _precio_api(producto: dict[str, Any]) -> Optional[str]:
    """Convierte el precio en unidades mínimas de la API a pesos.

    Args:
      producto: Producto devuelto por la API.

    Returns:
      Optional[str]: Precio con dos decimales o None.
    """
    precios = producto.get("prices") or {}
    try:
      valor = Decimal(str(precios.get("price")))
      unidad = int(precios.get("currency_minor_unit", 2))
      return f"{valor / (10 ** unidad):.2f}"
    except (InvalidOperation, TypeError, ValueError):
      return None

  @staticmethod
  def _imagen_api(producto: dict[str, Any]) -> str:
    """Devuelve la primera imagen del producto informada por la API.

    Args:
      producto: Producto devuelto por la API.

    Returns:
      str: URL de la imagen o texto vacío.
    """
    imagenes = producto.get("images") or []
    return imagenes[0].get("src", "") if imagenes else ""

  @staticmethod
  def _descripcion_api(producto: dict[str, Any]) -> str:
    """Extrae la sinopsis del HTML de la descripción de la API.

    Args:
      producto: Producto devuelto por la API.

    Returns:
      str: Sinopsis en una sola línea.
    """
    html = producto.get("description") or ""
    selector = Selector(text=html) if html else None
    parrafos = (
      selector.css("p.livriz-text-synopsis::text").getall()
      if selector else []
    )
    texto = (
      " ".join(parrafos) if parrafos
      else unescape(re.sub(r"<[^>]+>", " ", html))
    )
    return " ".join(texto.split())

  def parse_error(self, failure: Failure) -> Iterator[scrapy.Request]:
    """Registra el error y usa la API si falló la búsqueda o la ficha.

    Args:
      failure: Error de la petición.

    Yields:
      scrapy.Request: Petición de respaldo a la API.
    """
    self.logger.error(
      "Error al acceder a %s: %s", failure.request.url, failure.value
    )
    respaldo = (self.parse_resultados, self.parse_detalle)
    if failure.request.callback in respaldo:
      yield from self._solicitar_api(failure.request.meta["titulo_local"])
