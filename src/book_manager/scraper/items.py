"""Items del scraper: estructura de los datos extraídos de Cúspide."""

import scrapy


class LibroCoincidenciaItem(scrapy.Item):
  """Datos extraídos de la ficha de un libro en el sitio de Cúspide.

  Attributes:
    titulo_local: Título del catálogo propio que originó la búsqueda.
    isbn: ISBN informado en la ficha web.
    titulo_web: Título publicado en Cúspide.
    precio: Precio en pesos de la ficha.
    precio_usd: Precio de referencia en dólares, si se publica.
    url_imagen: URL de la imagen de tapa.
    formas_pago: Formas de pago con su precio o cuotas.
    descripcion: Descripción detallada (sinopsis).
    url_detalle: URL de la ficha del libro.
    fecha_extraccion: Fecha y hora de la extracción en formato ISO.
  """

  titulo_local = scrapy.Field()
  isbn = scrapy.Field()
  titulo_web = scrapy.Field()
  precio = scrapy.Field()
  precio_usd = scrapy.Field()
  url_imagen = scrapy.Field()
  formas_pago = scrapy.Field()
  descripcion = scrapy.Field()
  url_detalle = scrapy.Field()
  fecha_extraccion = scrapy.Field()
