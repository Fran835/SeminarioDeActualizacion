import os
import unicodedata
from datetime import date, datetime
from typing import Any, Generic, Hashable, Optional, TypeVar
from zoneinfo import ZoneInfo

import requests

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
from book_manager.repositories.repositories import (
  IRepositorio,
  IRepositorioCotizacionDolar,
  IRepositorioStock,
)

T = TypeVar("T", bound=EntidadBase)

ZONA_HORARIA = ZoneInfo("America/Argentina/Buenos_Aires")
CAMPOS_API = ("casa", "nombre", "venta", "fechaActualizacion")
# Nombres de la API que en el sistema se registran con otro nombre de tipo.
ALIAS_TIPOS: dict[str, str] = {
  "bolsa": "mep",
  "contadoconliqui": "ccl",
  "contado con liquidacion": "ccl",
}


def normalizar(texto: str) -> str:
  """Pasa un texto a minúsculas y sin acentos para poder compararlo.

  Args:
    texto: Texto a normalizar.

  Returns:
    str: Texto en minúsculas, sin tildes ni espacios extremos.
  """
  descompuesto = unicodedata.normalize("NFKD", texto.strip().lower())
  return "".join(c for c in descompuesto if not unicodedata.combining(c))


class ServicioCrud(Generic[T]):
  """Servicio genérico con la lógica común de las operaciones CRUD.

  Args:
    repositorio: Repositorio donde se persisten las entidades.
  """

  def __init__(self, repositorio: IRepositorio[T]) -> None:
    self._repositorio = repositorio

  def crear(self, entidad: T) -> T:
    """Valida y crea una entidad.

    Args:
      entidad: Entidad a crear.

    Returns:
      T: La entidad creada.

    Raises:
      ValueError: Si la entidad no es válida o su clave ya existe.
    """
    self._validar(entidad)
    return self._repositorio.crear(entidad)

  def leer_por_id(self, identificador: Hashable) -> Optional[T]:
    """Obtiene una entidad por su clave.

    Args:
      identificador: Clave de la entidad.

    Returns:
      Optional[T]: La entidad encontrada o None.
    """
    return self._repositorio.leer_por_id(identificador)

  def leer_todos(self) -> list[T]:
    """Obtiene todas las entidades.

    Returns:
      list[T]: Lista de entidades registradas.
    """
    return self._repositorio.leer_todos()

  def actualizar(self, entidad: T) -> T:
    """Valida y actualiza una entidad existente.

    Args:
      entidad: Entidad con los datos nuevos.

    Returns:
      T: La entidad actualizada.

    Raises:
      ValueError: Si la entidad no es válida o no existe.
    """
    self._validar(entidad)
    return self._repositorio.actualizar(entidad)

  def eliminar(self, identificador: Hashable) -> bool:
    """Elimina una entidad si no está referenciada por otras.

    Args:
      identificador: Clave de la entidad a eliminar.

    Returns:
      bool: True si se eliminó, False si no existía.

    Raises:
      ValueError: Si la entidad está en uso por otra entidad.
    """
    self._validar_eliminacion(identificador)
    return self._repositorio.eliminar(identificador)

  def _validar(self, entidad: T) -> None:
    """Aplica las reglas de negocio previas a crear o actualizar.

    Args:
      entidad: Entidad a validar.
    """

  def _validar_eliminacion(self, identificador: Hashable) -> None:
    """Aplica las reglas de negocio previas a eliminar.

    Args:
      identificador: Clave de la entidad a eliminar.
    """


class ServicioGenero(ServicioCrud[Genero]):
  """Lógica de negocio de los géneros literarios.

  Args:
    repositorio: Repositorio de géneros.
    libros: Repositorio de libros, para controlar referencias.
  """

  def __init__(
    self, repositorio: IRepositorio[Genero], libros: IRepositorio[Libro]
  ) -> None:
    super().__init__(repositorio)
    self._libros = libros

  def _validar_eliminacion(self, identificador: Hashable) -> None:
    """Impide eliminar un género asignado a algún libro."""
    if any(libro.genero.id == identificador
           for libro in self._libros.leer_todos()):
      raise ValueError("El género está asignado a uno o más libros.")


class ServicioEditorial(ServicioCrud[Editorial]):
  """Lógica de negocio de las editoriales.

  Args:
    repositorio: Repositorio de editoriales.
    libros: Repositorio de libros, para controlar referencias.
  """

  def __init__(
    self, repositorio: IRepositorio[Editorial], libros: IRepositorio[Libro]
  ) -> None:
    super().__init__(repositorio)
    self._libros = libros

  def _validar_eliminacion(self, identificador: Hashable) -> None:
    """Impide eliminar una editorial asignada a algún libro."""
    if any(libro.editorial.id == identificador
           for libro in self._libros.leer_todos()):
      raise ValueError("La editorial está asignada a uno o más libros.")


class ServicioMoneda(ServicioCrud[Moneda]):
  """Lógica de negocio de las monedas.

  Args:
    repositorio: Repositorio de monedas.
    precios: Repositorio de precios, para controlar referencias.
  """

  def __init__(
    self, repositorio: IRepositorio[Moneda], precios: IRepositorio[Precio]
  ) -> None:
    super().__init__(repositorio)
    self._precios = precios

  def _validar(self, moneda: Moneda) -> None:
    """Impide registrar dos monedas con el mismo código ISO."""
    if any(existente.codigo == moneda.codigo and existente.id != moneda.id
           for existente in self._repositorio.leer_todos()):
      raise ValueError(f"Ya existe una moneda con código {moneda.codigo}.")

  def _validar_eliminacion(self, identificador: Hashable) -> None:
    """Impide eliminar una moneda utilizada en algún precio."""
    if any(precio.moneda.id == identificador
           for precio in self._precios.leer_todos()):
      raise ValueError("La moneda está utilizada en uno o más precios.")


class ServicioTipoCotizacion(ServicioCrud[TipoCotizacion]):
  """Lógica de negocio de los tipos de cotización.

  Args:
    repositorio: Repositorio de tipos de cotización.
    cotizaciones: Repositorio de cotizaciones, para controlar referencias.
  """

  def __init__(
    self,
    repositorio: IRepositorio[TipoCotizacion],
    cotizaciones: IRepositorioCotizacionDolar,
  ) -> None:
    super().__init__(repositorio)
    self._cotizaciones = cotizaciones

  def _validar_eliminacion(self, identificador: Hashable) -> None:
    """Impide eliminar un tipo que posee cotizaciones históricas."""
    if self._cotizaciones.leer_historico_por_tipo(identificador):
      raise ValueError("El tipo de cotización posee cotizaciones cargadas.")


class ServicioLibro(ServicioCrud[Libro]):
  """Lógica de negocio de los libros del catálogo.

  Args:
    repositorio: Repositorio de libros.
    editoriales: Repositorio de editoriales.
    generos: Repositorio de géneros.
    precios: Repositorio de precios, para controlar referencias.
    stocks: Repositorio de stock, para controlar referencias.
  """

  def __init__(
    self,
    repositorio: IRepositorio[Libro],
    editoriales: IRepositorio[Editorial],
    generos: IRepositorio[Genero],
    precios: IRepositorio[Precio],
    stocks: IRepositorioStock,
  ) -> None:
    super().__init__(repositorio)
    self._editoriales = editoriales
    self._generos = generos
    self._precios = precios
    self._stocks = stocks

  def _validar(self, libro: Libro) -> None:
    """Verifica que la editorial y el género del libro existan."""
    if self._editoriales.leer_por_id(libro.editorial.id) is None:
      raise ValueError("La editorial del libro no existe.")
    if self._generos.leer_por_id(libro.genero.id) is None:
      raise ValueError("El género del libro no existe.")

  def _validar_eliminacion(self, identificador: Hashable) -> None:
    """Impide eliminar un libro que aún tiene precio o stock."""
    if self._precios.leer_por_id(identificador) is not None:
      raise ValueError("El libro tiene un precio asignado; elimínelo antes.")
    if self._stocks.leer_por_libro(str(identificador)) is not None:
      raise ValueError("El libro tiene stock registrado; elimínelo antes.")


class ServicioPrecio(ServicioCrud[Precio]):
  """Lógica de negocio de los precios de los libros.

  Args:
    repositorio: Repositorio de precios.
    libros: Repositorio de libros.
    monedas: Repositorio de monedas.
  """

  def __init__(
    self,
    repositorio: IRepositorio[Precio],
    libros: IRepositorio[Libro],
    monedas: IRepositorio[Moneda],
  ) -> None:
    super().__init__(repositorio)
    self._libros = libros
    self._monedas = monedas

  def _validar(self, precio: Precio) -> None:
    """Verifica que el libro y la moneda del precio existan."""
    if self._libros.leer_por_id(precio.libro_isbn) is None:
      raise ValueError("No existe el libro del precio.")
    if self._monedas.leer_por_id(precio.moneda.id) is None:
      raise ValueError("No existe la moneda del precio.")


class ServicioStock:
  """Lógica de negocio del inventario de libros.

  Args:
    repositorio: Repositorio de stock.
    libros: Repositorio de libros.
  """

  def __init__(
    self, repositorio: IRepositorioStock, libros: IRepositorio[Libro]
  ) -> None:
    self._repositorio = repositorio
    self._libros = libros

  def crear(self, stock: Stock) -> Stock:
    """Registra el stock inicial de un libro existente.

    Args:
      stock: Stock a registrar.

    Returns:
      Stock: El stock registrado.

    Raises:
      ValueError: Si el libro no existe o ya tiene stock.
    """
    self._validar_libro(stock.libro_isbn)
    return self._repositorio.crear(stock)

  def leer_por_libro(self, libro_isbn: str) -> Optional[Stock]:
    """Obtiene el stock de un libro.

    Args:
      libro_isbn: ISBN del libro.

    Returns:
      Optional[Stock]: El stock encontrado o None.
    """
    return self._repositorio.leer_por_libro(libro_isbn)

  def leer_todos(self) -> list[Stock]:
    """Obtiene todos los registros de stock.

    Returns:
      list[Stock]: Lista de registros de stock.
    """
    return self._repositorio.leer_todos()

  def actualizar(self, stock: Stock) -> Stock:
    """Actualiza la cantidad exacta de stock de un libro.

    Args:
      stock: Stock con la cantidad nueva.

    Returns:
      Stock: El stock actualizado.

    Raises:
      ValueError: Si el libro no existe o no tiene stock registrado.
    """
    self._validar_libro(stock.libro_isbn)
    return self._repositorio.actualizar(stock)

  def eliminar(self, libro_isbn: str) -> bool:
    """Elimina el registro de stock de un libro.

    Args:
      libro_isbn: ISBN del libro.

    Returns:
      bool: True si se eliminó, False si no existía.
    """
    return self._repositorio.eliminar(libro_isbn)

  def ingresar(self, libro_isbn: str, cantidad: int) -> Stock:
    """Suma unidades al stock de un libro, creándolo si no existe.

    Args:
      libro_isbn: ISBN del libro.
      cantidad: Unidades a ingresar, mayor a cero.

    Returns:
      Stock: El stock resultante.

    Raises:
      ValueError: Si la cantidad no es positiva o el libro no existe.
    """
    if cantidad <= 0:
      raise ValueError("La cantidad a ingresar debe ser positiva.")
    stock = self.leer_por_libro(libro_isbn)
    if stock is None:
      return self.crear(Stock(libro_isbn, cantidad))
    return self.actualizar(Stock(libro_isbn, stock.cantidad + cantidad))

  def retirar(self, libro_isbn: str, cantidad: int) -> Stock:
    """Descuenta unidades del stock de un libro.

    Args:
      libro_isbn: ISBN del libro.
      cantidad: Unidades a retirar, mayor a cero.

    Returns:
      Stock: El stock resultante.

    Raises:
      ValueError: Si la cantidad no es positiva o el stock no alcanza.
    """
    if cantidad <= 0:
      raise ValueError("La cantidad a retirar debe ser positiva.")
    stock = self.leer_por_libro(libro_isbn)
    if stock is None or stock.cantidad < cantidad:
      raise ValueError("Stock insuficiente.")
    return self.actualizar(Stock(libro_isbn, stock.cantidad - cantidad))

  def _validar_libro(self, libro_isbn: str) -> None:
    """Verifica que el libro asociado al stock exista.

    Args:
      libro_isbn: ISBN del libro.

    Raises:
      ValueError: Si el libro no existe.
    """
    if self._libros.leer_por_id(libro_isbn) is None:
      raise ValueError("No existe el libro para el stock.")


class ServicioCotizacionDolar:
  """Lógica de negocio del histórico de cotizaciones del dólar.

  Args:
    repositorio: Repositorio de cotizaciones.
    tipos: Repositorio de tipos de cotización.
    api_url: URL de la API de cotizaciones; por defecto, API_URL del .env.
    timeout: Segundos máximos de espera de la respuesta de la API.
  """

  def __init__(
    self,
    repositorio: IRepositorioCotizacionDolar,
    tipos: IRepositorio[TipoCotizacion],
    api_url: Optional[str] = None,
    timeout: float = 10.0,
  ) -> None:
    self._repositorio = repositorio
    self._tipos = tipos
    self._api_url = api_url
    self._timeout = timeout

  @property
  def api_url(self) -> str:
    """str: URL de la API; si no se indicó, se toma de API_URL (.env).

    Raises:
      ValueError: Si la URL no está configurada.
    """
    url = self._api_url or os.getenv("API_URL")
    if not url:
      raise ValueError("No está configurada la variable API_URL en el .env.")
    return url

  def obtener_cotizaciones(self) -> list[CotizacionDolar]:
    """Busca, descarga y registra en la base las cotizaciones del dólar.

    Por cada cotización de la API se busca su tipo (creándolo si no
    existe) y se registra el valor de venta para la fecha de
    actualización. Si ya había una cotización de ese tipo y fecha, se
    actualiza su valor; si no, se crea.

    Returns:
      list[CotizacionDolar]: Cotizaciones registradas o actualizadas.

    Raises:
      ValueError: Si la API no responde o devuelve datos inválidos.
    """
    registradas: list[CotizacionDolar] = []
    for dato in self._descargar():
      cotizacion = CotizacionDolar(
        self._obtener_o_crear_tipo(dato["casa"], dato["nombre"]),
        self._fecha_local(dato["fechaActualizacion"]),
        float(dato["venta"]),
      )
      existente = self.leer_por_tipo_y_fecha(
        cotizacion.tipo_cotizacion.id, cotizacion.fecha
      )
      if existente is None:
        registradas.append(self.crear(cotizacion))
      else:
        registradas.append(self.actualizar(cotizacion))
    return registradas

  def _descargar(self) -> list[dict[str, Any]]:
    """Descarga las cotizaciones de la API y valida su estructura.

    Returns:
      list[dict[str, Any]]: Cotizaciones tal como las devuelve la API.

    Raises:
      ValueError: Si la petición falla o la respuesta no es válida.
    """
    url = self.api_url
    try:
      respuesta = requests.get(url, timeout=self._timeout)
      respuesta.raise_for_status()
      datos = respuesta.json()
    except requests.RequestException as error:
      raise ValueError(f"No se pudo consultar la API: {error}") from error
    except ValueError as error:
      raise ValueError("La API no devolvió un JSON válido.") from error

    if not isinstance(datos, list):
      raise ValueError("La API devolvió un formato inesperado.")
    for dato in datos:
      faltantes = [c for c in CAMPOS_API if c not in dato]
      if faltantes:
        raise ValueError(f"La API no informó los campos {faltantes}.")
    return datos

  def _obtener_o_crear_tipo(self, casa: str, nombre: str) -> TipoCotizacion:
    """Busca el tipo de cotización de la API o lo registra si no existe.

    Args:
      casa: Identificador de la cotización en la API (ej. "blue").
      nombre: Nombre de la cotización en la API (ej. "Blue").

    Returns:
      TipoCotizacion: El tipo existente o el recién creado.
    """
    buscados = {normalizar(casa), normalizar(nombre)}
    buscados |= {ALIAS_TIPOS[b] for b in buscados if b in ALIAS_TIPOS}
    tipos = self._tipos.leer_todos()
    for tipo in tipos:
      if normalizar(tipo.nombre) in buscados:
        return tipo
    nuevo_id = max((tipo.id for tipo in tipos), default=0) + 1
    return self._tipos.crear(TipoCotizacion(nuevo_id, nombre))

  @staticmethod
  def _fecha_local(fecha_iso: str) -> date:
    """Convierte la fecha de la API (UTC) a la fecha de Argentina.

    Args:
      fecha_iso: Fecha y hora en formato ISO 8601 (ej. 2026-10-12T20:56Z).

    Returns:
      date: Fecha correspondiente en la zona horaria de Buenos Aires.
    """
    instante = datetime.fromisoformat(fecha_iso.replace("Z", "+00:00"))
    return instante.astimezone(ZONA_HORARIA).date()

  def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    """Registra una cotización nueva.

    Args:
      cotizacion: Cotización a registrar.

    Returns:
      CotizacionDolar: La cotización registrada.

    Raises:
      ValueError: Si el tipo no existe o ya hay cotización ese día.
    """
    self._validar(cotizacion)
    return self._repositorio.crear(cotizacion)

  def leer_por_tipo_y_fecha(
    self, tipo_id: int, fecha: date
  ) -> Optional[CotizacionDolar]:
    """Obtiene la cotización de un tipo en una fecha.

    Args:
      tipo_id: ID del tipo de cotización.
      fecha: Fecha de la cotización.

    Returns:
      Optional[CotizacionDolar]: La cotización encontrada o None.
    """
    return self._repositorio.leer_por_tipo_y_fecha(tipo_id, fecha)

  def leer_historico_por_tipo(self, tipo_id: int) -> list[CotizacionDolar]:
    """Obtiene el histórico de cotizaciones de un tipo.

    Args:
      tipo_id: ID del tipo de cotización.

    Returns:
      list[CotizacionDolar]: Cotizaciones del tipo ordenadas por fecha.
    """
    return self._repositorio.leer_historico_por_tipo(tipo_id)

  def leer_todos(self) -> list[CotizacionDolar]:
    """Obtiene todas las cotizaciones registradas.

    Returns:
      list[CotizacionDolar]: Cotizaciones ordenadas por fecha y tipo.
    """
    return self._repositorio.leer_todos()

  def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    """Actualiza el valor de una cotización existente.

    Args:
      cotizacion: Cotización con el valor nuevo.

    Returns:
      CotizacionDolar: La cotización actualizada.

    Raises:
      ValueError: Si el tipo no existe o la cotización no existe.
    """
    self._validar(cotizacion)
    return self._repositorio.actualizar(cotizacion)

  def eliminar(self, tipo_id: int, fecha: date) -> bool:
    """Elimina la cotización de un tipo en una fecha.

    Args:
      tipo_id: ID del tipo de cotización.
      fecha: Fecha de la cotización.

    Returns:
      bool: True si se eliminó, False si no existía.
    """
    return self._repositorio.eliminar(tipo_id, fecha)

  def _validar(self, cotizacion: CotizacionDolar) -> None:
    """Verifica que el tipo de la cotización exista.

    Args:
      cotizacion: Cotización a validar.

    Raises:
      ValueError: Si el tipo de cotización no existe.
    """
    if self._tipos.leer_por_id(cotizacion.tipo_cotizacion.id) is None:
      raise ValueError("No existe el tipo de cotización.")
