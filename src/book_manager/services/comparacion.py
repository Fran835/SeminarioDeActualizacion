"""Comparación de los precios del catálogo con los extraídos de Cúspide."""

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional

from book_manager.entities.entities import Libro, Precio, TipoCotizacion
from book_manager.repositories.repositories import (
  IRepositorio,
  IRepositorioCotizacionDolar,
)
from book_manager.services.services import normalizar

MONEDA_LOCAL = "ARS"
MONEDA_DOLAR = "USD"
UMBRAL_SIMILITUD = 0.82


def _clave_titulo(texto: str) -> str:
  """Normaliza un título para compararlo sin acentos ni puntuación."""
  limpio = re.sub(r"[^a-z0-9 ]", " ", normalizar(texto))
  return " ".join(limpio.split())


@dataclass(frozen=True)
class ComparacionPrecio:
  """Precio interno y precio web de un mismo libro.

  Args:
    libro: Título del libro en el catálogo interno.
    isbn_local: ISBN del libro en el catálogo interno.
    titulo_web: Título tal como aparece en Cúspide.
    isbn_web: ISBN informado por Cúspide.
    precio_interno: Precio interno convertido a pesos.
    precio_web: Precio web en pesos.
    diferencia: Precio interno menos precio web.
    diferencia_porcentaje: Diferencia porcentual sobre el precio web.
    fecha_extraccion: Fecha en la que se extrajo el precio web.
    url_detalle: URL de la ficha del producto en Cúspide.
  """

  libro: str
  isbn_local: str
  titulo_web: str
  isbn_web: str
  precio_interno: Decimal
  precio_web: Decimal
  diferencia: Decimal
  diferencia_porcentaje: Decimal
  fecha_extraccion: datetime
  url_detalle: str


@dataclass(frozen=True)
class ResultadoAlertas:
  """Rutas y totales del proceso de comparación.

  Args:
    ruta_comparaciones: CSV con todas las comparaciones.
    ruta_alertas: CSV con las comparaciones que superan el umbral.
    total_comparaciones: Cantidad de libros comparados.
    total_alertas: Cantidad de libros que superan el umbral.
    umbral: Diferencia porcentual mínima usada para alertar.
  """

  ruta_comparaciones: Path
  ruta_alertas: Path
  total_comparaciones: int
  total_alertas: int
  umbral: float


class ServicioComparacion:
  """Compara el precio propio con el precio web y genera alertas CSV.

  Args:
    libros: Repositorio del catálogo.
    precios: Repositorio de precios internos.
    cotizaciones: Repositorio de cotizaciones del dólar.
    tipos: Repositorio de tipos de cotización.
    carpeta_reportes: Carpeta donde se guardan los CSV.
  """

  def __init__(
    self,
    libros: IRepositorio[Libro],
    precios: IRepositorio[Precio],
    cotizaciones: IRepositorioCotizacionDolar,
    tipos: IRepositorio[TipoCotizacion],
    carpeta_reportes: Path,
  ) -> None:
    self._libros = libros
    self._precios = precios
    self._cotizaciones = cotizaciones
    self._tipos = tipos
    self._carpeta_reportes = Path(carpeta_reportes)

  @property
  def carpeta_reportes(self) -> Path:
    """Path: Carpeta donde se escriben los CSV."""
    return self._carpeta_reportes

  def ultimo_jsonl(self) -> Path:
    """Devuelve el JSONL más reciente generado por el scraper.

    Returns:
      Path: Ruta del archivo más reciente.

    Raises:
      ValueError: Si todavía no hay extracciones.
    """
    archivos = sorted(
      self._carpeta_reportes.glob("scraping_*.jsonl"),
      key=lambda ruta: ruta.stat().st_mtime,
    )
    if not archivos:
      raise ValueError(
        "No hay extracciones. Ejecutá el scraper antes de comparar precios."
      )
    return archivos[-1]

  def leer_extracciones(
    self, ruta: Optional[Path] = None
  ) -> list[dict[str, Any]]:
    """Lee las extracciones del JSONL indicado o del más reciente.

    Args:
      ruta: Archivo a leer. Si es None, se usa el último JSONL.

    Returns:
      list[dict[str, Any]]: Una lista con una extracción por línea.
    """
    origen = ruta or self.ultimo_jsonl()
    return [
      json.loads(linea)
      for linea in origen.read_text(encoding="utf-8").splitlines()
      if linea.strip()
    ]

  def contar_extracciones(self, ruta: Optional[Path] = None) -> int:
    """Cuenta las extracciones disponibles en un JSONL.

    Args:
      ruta: Archivo a contar. Si es None, se usa el último JSONL.

    Returns:
      int: Cantidad de extracciones.
    """
    return len(self.leer_extracciones(ruta))

  def comparar(
    self, ruta: Optional[Path] = None
  ) -> list[ComparacionPrecio]:
    """Compara cada libro con su mejor coincidencia en Cúspide.

    La coincidencia se busca por título normalizado porque los ISBN del
    catálogo de ejemplo no son los mismos que los de Cúspide. Si varios
    resultados coinciden con un libro, se conserva el de mayor similitud.

    Args:
      ruta: JSONL a procesar. Si es None, se usa el último.

    Returns:
      list[ComparacionPrecio]: Una comparación por libro del catálogo.
    """
    extracciones = self.leer_extracciones(ruta)
    libros = self._libros.leer_todos()
    tasa_dolar = self._tasa_dolar()
    mejores: dict[str, tuple[float, ComparacionPrecio]] = {}

    for extraccion in extracciones:
      libro, similitud = self._buscar_libro(extraccion, libros)
      if libro is None:
        continue
      precio_interno = self._precio_interno(libro, tasa_dolar)
      precio_web = self._precio_web(extraccion)
      if precio_interno is None or precio_web is None:
        continue
      diferencia = precio_interno - precio_web
      porcentaje = (
        (diferencia / precio_web * 100).quantize(Decimal("0.01"))
        if precio_web
        else Decimal("0")
      )
      comparacion = ComparacionPrecio(
        libro=libro.titulo,
        isbn_local=libro.isbn,
        titulo_web=str(extraccion.get("titulo_web") or ""),
        isbn_web=str(extraccion.get("isbn") or ""),
        precio_interno=precio_interno.quantize(Decimal("0.01")),
        precio_web=precio_web.quantize(Decimal("0.01")),
        diferencia=diferencia.quantize(Decimal("0.01")),
        diferencia_porcentaje=porcentaje,
        fecha_extraccion=self._fecha(extraccion),
        url_detalle=str(extraccion.get("url_detalle") or ""),
      )
      anterior = mejores.get(libro.isbn)
      if anterior is None or similitud > anterior[0]:
        mejores[libro.isbn] = (similitud, comparacion)

    return [comparacion for _, comparacion in mejores.values()]

  def generar_alertas(
    self, umbral: float, ruta: Optional[Path] = None
  ) -> ResultadoAlertas:
    """Genera el CSV completo y el CSV de alertas para el umbral.

    Args:
      umbral: Diferencia porcentual mínima para considerar una alerta.
      ruta: JSONL a procesar. Si es None, se usa el último.

    Returns:
      ResultadoAlertas: Rutas generadas y totales del proceso.

    Raises:
      ValueError: Si el umbral es negativo.
    """
    if umbral < 0:
      raise ValueError("El umbral de diferencia no puede ser negativo.")
    comparaciones = self.comparar(ruta)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    self._carpeta_reportes.mkdir(parents=True, exist_ok=True)
    ruta_comparaciones = self._carpeta_reportes / f"comparaciones_{marca}.csv"
    ruta_alertas = self._carpeta_reportes / f"alertas_{marca}.csv"
    alertas = [
      comparacion
      for comparacion in comparaciones
      if abs(comparacion.diferencia_porcentaje) >= Decimal(str(umbral))
    ]
    self._escribir_csv(ruta_comparaciones, comparaciones, umbral)
    self._escribir_csv(ruta_alertas, alertas, umbral)
    return ResultadoAlertas(
      ruta_comparaciones=ruta_comparaciones,
      ruta_alertas=ruta_alertas,
      total_comparaciones=len(comparaciones),
      total_alertas=len(alertas),
      umbral=umbral,
    )

  def _buscar_libro(
    self, extraccion: dict[str, Any], libros: list[Libro]
  ) -> tuple[Optional[Libro], float]:
    """Busca el libro del catálogo que mejor coincide con el título web.

    Args:
      extraccion: Datos de una ficha extraída.
      libros: Catálogo interno.

    Returns:
      tuple[Optional[Libro], float]: Libro encontrado y puntaje de similitud.
    """
    clave_web = _clave_titulo(str(extraccion.get("titulo_web") or ""))
    if not clave_web:
      return None, 0.0
    mejor: Optional[Libro] = None
    mejor_puntaje = 0.0
    for libro in libros:
      clave_local = _clave_titulo(libro.titulo)
      if not clave_local:
        continue
      if clave_web == clave_local:
        puntaje = 1.0
      elif clave_local in clave_web or clave_web in clave_local:
        puntaje = 0.95
      else:
        puntaje = SequenceMatcher(None, clave_web, clave_local).ratio()
      if puntaje > mejor_puntaje:
        mejor = libro
        mejor_puntaje = puntaje
    if mejor_puntaje < UMBRAL_SIMILITUD:
      return None, mejor_puntaje
    return mejor, mejor_puntaje

  def _precio_interno(
    self, libro: Libro, tasa_dolar: Optional[Decimal]
  ) -> Optional[Decimal]:
    """Obtiene el precio interno del libro convertido a pesos.

    Args:
      libro: Libro del catálogo.
      tasa_dolar: Pesos por dólar, o None si no hay cotización.

    Returns:
      Optional[Decimal]: Precio en pesos, o None si no se puede convertir.
    """
    precio = self._precios.leer_por_id(libro.isbn)
    if precio is None:
      return None
    valor = Decimal(str(precio.valor))
    if precio.moneda.codigo == MONEDA_LOCAL:
      return valor
    if precio.moneda.codigo == MONEDA_DOLAR and tasa_dolar is not None:
      return valor * tasa_dolar
    return None

  def _tasa_dolar(self) -> Optional[Decimal]:
    """Devuelve la cotización más reciente, priorizando la oficial.

    Returns:
      Optional[Decimal]: Pesos por dólar, o None si no hay cotizaciones.
    """
    tipos = self._tipos.leer_todos()
    ordenados = sorted(
      tipos,
      key=lambda tipo: normalizar(tipo.nombre) != "oficial",
    )
    for tipo in ordenados:
      historico = self._cotizaciones.leer_historico_por_tipo(tipo.id)
      if historico:
        ultima = max(historico, key=lambda cotizacion: cotizacion.fecha)
        return Decimal(str(ultima.valor))
    return None

  @staticmethod
  def _precio_web(extraccion: dict[str, Any]) -> Optional[Decimal]:
    """Convierte el precio web a Decimal.

    Args:
      extraccion: Datos de una ficha extraída.

    Returns:
      Optional[Decimal]: Precio web, o None si no es válido.
    """
    try:
      return Decimal(str(extraccion.get("precio")))
    except (InvalidOperation, TypeError, ValueError):
      return None

  @staticmethod
  def _fecha(extraccion: dict[str, Any]) -> datetime:
    """Recupera la fecha de extracción de una ficha.

    Args:
      extraccion: Datos de una ficha extraída.

    Returns:
      datetime: Fecha informada o la fecha actual si no es válida.
    """
    valor = extraccion.get("fecha_extraccion")
    if isinstance(valor, str):
      try:
        return datetime.fromisoformat(valor)
      except ValueError:
        pass
    return datetime.now()

  @staticmethod
  def _escribir_csv(
    ruta: Path, comparaciones: list[ComparacionPrecio], umbral: float
  ) -> None:
    """Escribe las comparaciones en un CSV compatible con Excel.

    Args:
      ruta: Archivo de destino.
      comparaciones: Filas a escribir.
      umbral: Umbral usado en la ejecución.
    """
    campos = [
      "Libro",
      "ISBN local",
      "Título web",
      "ISBN web",
      "Precio interno",
      "Precio web",
      "Diferencia",
      "Diferencia %",
      "Umbral %",
      "Fecha de extracción",
      "URL detalle",
    ]
    with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
      escritor = csv.DictWriter(archivo, fieldnames=campos)
      escritor.writeheader()
      for comparacion in comparaciones:
        escritor.writerow({
          "Libro": comparacion.libro,
          "ISBN local": comparacion.isbn_local,
          "Título web": comparacion.titulo_web,
          "ISBN web": comparacion.isbn_web,
          "Precio interno": f"{comparacion.precio_interno:.2f}",
          "Precio web": f"{comparacion.precio_web:.2f}",
          "Diferencia": f"{comparacion.diferencia:.2f}",
          "Diferencia %": f"{comparacion.diferencia_porcentaje:.2f}",
          "Umbral %": f"{umbral:.2f}",
          "Fecha de extracción": comparacion.fecha_extraccion.isoformat(
            timespec="seconds"
          ),
          "URL detalle": comparacion.url_detalle,
        })
