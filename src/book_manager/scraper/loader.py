"""Item Loader con las reglas de limpieza de cada campo del scraper."""

import re
from decimal import Decimal, InvalidOperation

from itemloaders.processors import Join, MapCompose, TakeFirst
from scrapy.loader import ItemLoader

from book_manager.scraper.items import LibroCoincidenciaItem


def limpiar_texto(valor: str) -> str:
  """Colapsa espacios, saltos de línea y el &nbsp; del HTML.

  Args:
    valor: Texto extraído del HTML.

  Returns:
    str: Texto limpio en una sola línea.
  """
  if not valor:
    return ""
  return " ".join(str(valor).replace("\xa0", " ").split())


def limpiar_pago(valor: str) -> str:
  """Quita el ">" con el que Cúspide prefija cada medio de pago.

  Args:
    valor: Texto de un medio de pago.

  Returns:
    str: Medio de pago limpio.
  """
  return limpiar_texto(valor).removeprefix(">").strip()


def procesar_precio(valores: list[str]) -> list[Decimal]:
  """Convierte textos de precio como "$ 130.999,00" en un Decimal.

  Recibe la lista completa de fragmentos porque Cúspide separa el
  símbolo de la moneda del importe.

  Args:
    valores: Fragmentos de texto del precio.

  Returns:
    list[Decimal]: Lista con el precio o vacía si no se pudo leer.
  """
  limpio = re.sub(r"[^\d.,]", "", " ".join(str(v) for v in valores))
  if not limpio:
    return []
  if "," in limpio:
    limpio = limpio.replace(".", "").replace(",", ".")
  elif re.fullmatch(r"\d{1,3}(\.\d{3})+", limpio):
    limpio = limpio.replace(".", "")
  try:
    return [Decimal(limpio).quantize(Decimal("0.01"))]
  except InvalidOperation:
    return []


class LibroLoader(ItemLoader):
  """Loader de LibroCoincidenciaItem.

  Los procesadores de entrada limpian cada valor y los de salida toman
  el primer valor o unen las listas (formas de pago y descripción).
  """

  default_item_class = LibroCoincidenciaItem
  default_output_processor = TakeFirst()

  titulo_local_in = MapCompose(limpiar_texto)
  titulo_web_in = MapCompose(limpiar_texto)
  isbn_in = MapCompose(limpiar_texto)
  descripcion_in = MapCompose(limpiar_texto)
  formas_pago_in = MapCompose(limpiar_pago)
  precio_in = procesar_precio
  precio_usd_in = procesar_precio

  formas_pago_out = Join(" | ")
  descripcion_out = Join(" ")
