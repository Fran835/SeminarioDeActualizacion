import abc
from datetime import date
from typing import Generic, Hashable, Optional, TypeVar

from book_manager.entities.entities import (
  CotizacionDolar,
  Editorial,
  EntidadBase,
  Genero,
  Libro,
  Moneda,
  Precio,
  Stock,
  TipoCotizacion,
)

T = TypeVar("T", bound=EntidadBase)


class IRepositorio(abc.ABC, Generic[T]):
  """Interfaz para repositorios que manejan entidades con CRUD básico."""

  @abc.abstractmethod
  def crear(self, entidad: T) -> T:
    """Crea una nueva entidad en el repositorio.

    Args:
      entidad: La entidad a crear.

    Returns:
      T: La entidad creada.

    Raises:
      ValueError: Si ya existe una entidad con la misma clave.
    """

  @abc.abstractmethod
  def leer_por_id(self, identificador: Hashable) -> Optional[T]:
    """Lee una entidad del repositorio por su clave.

    Args:
      identificador: La clave de la entidad a leer.

    Returns:
      Optional[T]: La entidad si se encuentra, None en caso contrario.
    """

  @abc.abstractmethod
  def leer_todos(self) -> list[T]:
    """Lee todas las entidades del repositorio.

    Returns:
      list[T]: Una lista con todas las entidades.
    """

  @abc.abstractmethod
  def actualizar(self, entidad: T) -> T:
    """Actualiza una entidad existente en el repositorio.

    Args:
      entidad: La entidad a actualizar (debe tener una clave existente).

    Returns:
      T: La entidad actualizada.

    Raises:
      ValueError: Si no se encuentra la entidad para actualizar.
    """

  @abc.abstractmethod
  def eliminar(self, identificador: Hashable) -> bool:
    """Elimina una entidad del repositorio por su clave.

    Args:
      identificador: La clave de la entidad a eliminar.

    Returns:
      bool: True si la entidad fue eliminada, False si no se encontró.
    """


class RepositorioMemoria(IRepositorio[T]):
  """Repositorio genérico en memoria indexado por la clave de la entidad."""

  def __init__(self) -> None:
    self._entidades: dict[Hashable, T] = {}

  def crear(self, entidad: T) -> T:
    """Crea una nueva entidad en memoria. Ver IRepositorio.crear."""
    if entidad.clave in self._entidades:
      raise ValueError(f"Ya existe un registro con clave {entidad.clave!r}.")
    self._entidades[entidad.clave] = entidad
    return entidad

  def leer_por_id(self, identificador: Hashable) -> Optional[T]:
    """Lee una entidad por su clave. Ver IRepositorio.leer_por_id."""
    return self._entidades.get(identificador)

  def leer_todos(self) -> list[T]:
    """Lee todas las entidades. Ver IRepositorio.leer_todos."""
    return list(self._entidades.values())

  def actualizar(self, entidad: T) -> T:
    """Reemplaza una entidad existente. Ver IRepositorio.actualizar."""
    if entidad.clave not in self._entidades:
      raise ValueError(f"No existe un registro con clave {entidad.clave!r}.")
    self._entidades[entidad.clave] = entidad
    return entidad

  def eliminar(self, identificador: Hashable) -> bool:
    """Elimina una entidad por su clave. Ver IRepositorio.eliminar."""
    return self._entidades.pop(identificador, None) is not None


class RepositorioGenero(RepositorioMemoria[Genero]):
  """Repositorio en memoria de géneros literarios."""


class RepositorioEditorial(RepositorioMemoria[Editorial]):
  """Repositorio en memoria de editoriales."""


class RepositorioMoneda(RepositorioMemoria[Moneda]):
  """Repositorio en memoria de monedas."""


class RepositorioTipoCotizacion(RepositorioMemoria[TipoCotizacion]):
  """Repositorio en memoria de tipos de cotización."""


class RepositorioLibro(RepositorioMemoria[Libro]):
  """Repositorio en memoria de libros indexados por ISBN."""


class RepositorioPrecio(RepositorioMemoria[Precio]):
  """Repositorio en memoria de precios indexados por ISBN del libro."""


class IRepositorioStock(abc.ABC):
  """Interfaz para repositorios del tipo Stock."""

  @abc.abstractmethod
  def crear(self, stock: Stock) -> Stock:
    """Crea un nuevo registro de stock.

    Args:
      stock: El objeto Stock a crear.

    Returns:
      Stock: El objeto Stock creado.

    Raises:
      ValueError: Si ya existe un registro de stock para el mismo libro.
    """

  @abc.abstractmethod
  def leer_por_libro(self, libro_isbn: str) -> Optional[Stock]:
    """Lee un registro de stock por ISBN de libro.

    Args:
      libro_isbn: El ISBN del libro asociado al stock.

    Returns:
      Optional[Stock]: El stock si se encuentra, None en caso contrario.
    """

  @abc.abstractmethod
  def leer_todos(self) -> list[Stock]:
    """Lee todos los registros de stock.

    Returns:
      list[Stock]: Una lista con todos los registros de stock.
    """

  @abc.abstractmethod
  def actualizar(self, stock: Stock) -> Stock:
    """Actualiza un registro de stock existente.

    Args:
      stock: El objeto Stock a actualizar (con un libro existente).

    Returns:
      Stock: El objeto Stock actualizado.

    Raises:
      ValueError: Si no se encuentra el stock para actualizar.
    """

  @abc.abstractmethod
  def eliminar(self, libro_isbn: str) -> bool:
    """Elimina un registro de stock por ISBN de libro.

    Args:
      libro_isbn: El ISBN del libro asociado al stock a eliminar.

    Returns:
      bool: True si el stock fue eliminado, False si no se encontró.
    """


class RepositorioStock(IRepositorioStock):
  """Repositorio en memoria de stock indexado por ISBN del libro."""

  def __init__(self) -> None:
    self._stocks: dict[str, Stock] = {}

  def crear(self, stock: Stock) -> Stock:
    """Crea un registro de stock. Ver IRepositorioStock.crear."""
    if stock.libro_isbn in self._stocks:
      raise ValueError("Ya existe stock para el libro indicado.")
    self._stocks[stock.libro_isbn] = stock
    return stock

  def leer_por_libro(self, libro_isbn: str) -> Optional[Stock]:
    """Lee el stock de un libro. Ver IRepositorioStock.leer_por_libro."""
    return self._stocks.get(libro_isbn)

  def leer_todos(self) -> list[Stock]:
    """Lee todos los registros. Ver IRepositorioStock.leer_todos."""
    return list(self._stocks.values())

  def actualizar(self, stock: Stock) -> Stock:
    """Reemplaza un registro de stock. Ver IRepositorioStock.actualizar."""
    if stock.libro_isbn not in self._stocks:
      raise ValueError("No existe stock para el libro indicado.")
    self._stocks[stock.libro_isbn] = stock
    return stock

  def eliminar(self, libro_isbn: str) -> bool:
    """Elimina el stock de un libro. Ver IRepositorioStock.eliminar."""
    return self._stocks.pop(libro_isbn, None) is not None


class IRepositorioCotizacionDolar(abc.ABC):
  """Interfaz para repositorios del tipo CotizacionDolar."""

  @abc.abstractmethod
  def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    """Crea una nueva cotización de dólar.

    Args:
      cotizacion: El objeto CotizacionDolar a crear.

    Returns:
      CotizacionDolar: El objeto CotizacionDolar creado.

    Raises:
      ValueError: Si ya existe una cotización para el mismo tipo y fecha.
    """

  @abc.abstractmethod
  def leer_por_tipo_y_fecha(
    self, tipo_id: int, fecha: date
  ) -> Optional[CotizacionDolar]:
    """Lee una cotización de dólar por tipo y fecha.

    Args:
      tipo_id: El ID del tipo de cotización.
      fecha: La fecha de la cotización.

    Returns:
      Optional[CotizacionDolar]: La cotización o None si no existe.
    """

  @abc.abstractmethod
  def leer_historico_por_tipo(self, tipo_id: int) -> list[CotizacionDolar]:
    """Lee el histórico de cotizaciones para un tipo específico.

    Args:
      tipo_id: El ID del tipo de cotización.

    Returns:
      list[CotizacionDolar]: Cotizaciones del tipo ordenadas por fecha.
    """

  @abc.abstractmethod
  def leer_todos(self) -> list[CotizacionDolar]:
    """Lee todas las cotizaciones registradas.

    Returns:
      list[CotizacionDolar]: Cotizaciones ordenadas por fecha y tipo.
    """

  @abc.abstractmethod
  def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    """Actualiza una cotización de dólar existente.

    Args:
      cotizacion: El objeto CotizacionDolar a actualizar.

    Returns:
      CotizacionDolar: El objeto CotizacionDolar actualizado.

    Raises:
      ValueError: Si no se encuentra la cotización para actualizar.
    """

  @abc.abstractmethod
  def eliminar(self, tipo_id: int, fecha: date) -> bool:
    """Elimina una cotización de dólar por tipo y fecha.

    Args:
      tipo_id: El ID del tipo de cotización.
      fecha: La fecha de la cotización a eliminar.

    Returns:
      bool: True si la cotización fue eliminada, False si no se encontró.
    """


class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
  """Repositorio en memoria de cotizaciones indexadas por tipo y fecha."""

  def __init__(self) -> None:
    self._cotizaciones: dict[tuple[int, date], CotizacionDolar] = {}

  @staticmethod
  def _clave(cotizacion: CotizacionDolar) -> tuple[int, date]:
    """Obtiene la clave compuesta (tipo, fecha) de una cotización.

    Args:
      cotizacion: Cotización de la que se obtiene la clave.

    Returns:
      tuple[int, date]: ID del tipo de cotización y fecha.
    """
    return cotizacion.tipo_cotizacion.id, cotizacion.fecha

  def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    """Crea una cotización. Ver IRepositorioCotizacionDolar.crear."""
    clave = self._clave(cotizacion)
    if clave in self._cotizaciones:
      raise ValueError("Ya existe una cotización para ese tipo y fecha.")
    self._cotizaciones[clave] = cotizacion
    return cotizacion

  def leer_por_tipo_y_fecha(
    self, tipo_id: int, fecha: date
  ) -> Optional[CotizacionDolar]:
    """Lee una cotización por tipo y fecha. Ver la interfaz."""
    return self._cotizaciones.get((tipo_id, fecha))

  def leer_historico_por_tipo(self, tipo_id: int) -> list[CotizacionDolar]:
    """Lee el histórico de un tipo. Ver la interfaz."""
    historico = [
      cotizacion
      for (tipo, _), cotizacion in self._cotizaciones.items()
      if tipo == tipo_id
    ]
    return sorted(historico, key=lambda cotizacion: cotizacion.fecha)

  def leer_todos(self) -> list[CotizacionDolar]:
    """Lee todas las cotizaciones. Ver la interfaz."""
    return [
      self._cotizaciones[clave]
      for clave in sorted(self._cotizaciones, key=lambda c: (c[1], c[0]))
    ]

  def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    """Reemplaza una cotización existente. Ver la interfaz."""
    clave = self._clave(cotizacion)
    if clave not in self._cotizaciones:
      raise ValueError("No existe la cotización para actualizar.")
    self._cotizaciones[clave] = cotizacion
    return cotizacion

  def eliminar(self, tipo_id: int, fecha: date) -> bool:
    """Elimina una cotización por tipo y fecha. Ver la interfaz."""
    return self._cotizaciones.pop((tipo_id, fecha), None) is not None
