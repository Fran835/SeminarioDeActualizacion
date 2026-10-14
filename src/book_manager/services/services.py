import csv
import os
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
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

MONEDA_LOCAL = "ARS"
MONEDA_DOLAR = "USD"
ZONA_HORARIA = ZoneInfo("America/Argentina/Buenos_Aires")
CAMPOS_API = ("casa", "nombre", "venta", "fechaActualizacion")
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
      return self.crear(Stock(self._obtener_libro(libro_isbn), cantidad))
    stock.cantidad += cantidad
    return self.actualizar(stock)

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
    stock.cantidad -= cantidad
    return self.actualizar(stock)

  def _obtener_libro(self, libro_isbn: str) -> Libro:
    """Obtiene el libro asociado a un stock.

    Args:
      libro_isbn: ISBN del libro.

    Returns:
      Libro: El libro encontrado.

    Raises:
      ValueError: Si el libro no existe.
    """
    libro = self._libros.leer_por_id(libro_isbn)
    if libro is None:
      raise ValueError("No existe el libro para el stock.")
    return libro

  def _validar_libro(self, libro_isbn: str) -> None:
    """Verifica que el libro asociado al stock exista.

    Args:
      libro_isbn: ISBN del libro.

    Raises:
      ValueError: Si el libro no existe.
    """
    self._obtener_libro(libro_isbn)


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


@dataclass(frozen=True)
class FilaPrecio:
  """Precio de un libro expresado en pesos y en otra moneda.

  Args:
    isbn: ISBN del libro.
    titulo: Título del libro.
    moneda_original: Código de la moneda en la que está cargado el precio.
    valor_original: Importe cargado en la moneda original.
    valor_pesos: Importe convertido a pesos (None si no hay tasa).
    valor_moneda: Importe en la moneda elegida (None si no hay tasa).
  """

  isbn: str
  titulo: str
  moneda_original: str
  valor_original: float
  valor_pesos: Optional[float]
  valor_moneda: Optional[float]


class ServicioListaPrecios:
  """Lógica de conversión de precios entre monedas y su exportación.

  La conversión usa como puente al peso: cada moneda tiene una tasa en
  pesos por unidad (ARS = 1, USD = cotización vigente del dólar).

  Args:
    precios: Repositorio de precios.
    cotizaciones: Repositorio de cotizaciones del dólar.
    tipos: Repositorio de tipos de cotización.
    carpeta_exportacion: Carpeta donde se guardan los CSV exportados.
  """

  def __init__(
    self,
    precios: IRepositorio[Precio],
    cotizaciones: IRepositorioCotizacionDolar,
    tipos: IRepositorio[TipoCotizacion],
    carpeta_exportacion: Path,
  ) -> None:
    self._precios = precios
    self._cotizaciones = cotizaciones
    self._tipos = tipos
    self._carpeta_exportacion = carpeta_exportacion

  def cotizacion_vigente(self, tipo_id: int) -> CotizacionDolar:
    """Obtiene la cotización más reciente de un tipo.

    Args:
      tipo_id: ID del tipo de cotización.

    Returns:
      CotizacionDolar: Última cotización registrada para el tipo.

    Raises:
      ValueError: Si el tipo no tiene cotizaciones registradas.
    """
    historico = self._cotizaciones.leer_historico_por_tipo(tipo_id)
    if not historico:
      raise ValueError(
        "El tipo de cotización no tiene valores; obtenga las cotizaciones."
      )
    return max(historico, key=lambda cotizacion: cotizacion.fecha)

  def tasas(self, tipo_id: int) -> dict[str, float]:
    """Devuelve cuántos pesos vale una unidad de cada moneda convertible.

    Args:
      tipo_id: ID del tipo de cotización usado para el dólar.

    Returns:
      dict[str, float]: Código de moneda -> pesos por unidad.
    """
    return {
      MONEDA_LOCAL: 1.0,
      MONEDA_DOLAR: self.cotizacion_vigente(tipo_id).valor,
    }

  @staticmethod
  def convertir(
    valor: float, origen: str, destino: str, tasas: dict[str, float]
  ) -> Optional[float]:
    """Convierte un importe entre dos monedas usando el peso como puente.

    Args:
      valor: Importe a convertir.
      origen: Código de la moneda del importe.
      destino: Código de la moneda a la que se convierte.
      tasas: Pesos por unidad de cada moneda.

    Returns:
      Optional[float]: Importe convertido redondeado a 2 decimales, o
        None si alguna de las dos monedas no tiene tasa.
    """
    if origen not in tasas or destino not in tasas:
      return None
    return round(valor * tasas[origen] / tasas[destino], 2)

  def lista_bimonetaria(
    self, codigo_moneda: str, tipo_id: int
  ) -> list[FilaPrecio]:
    """Arma la lista de precios de los libros en pesos y en otra moneda.

    Args:
      codigo_moneda: Código de la moneda elegida (ej. USD).
      tipo_id: ID del tipo de cotización usado para el dólar.

    Returns:
      list[FilaPrecio]: Una fila por cada libro con precio cargado.

    Raises:
      ValueError: Si la moneda elegida no tiene tasa de conversión.
    """
    tasas = self.tasas(tipo_id)
    codigo = codigo_moneda.upper()
    if codigo not in tasas:
      raise ValueError(
        f"No hay cotización para convertir a {codigo}. "
        f"Monedas disponibles: {', '.join(tasas)}."
      )
    filas = []
    for precio in self._precios.leer_todos():
      origen = precio.moneda.codigo
      filas.append(FilaPrecio(
        precio.libro.isbn,
        precio.libro.titulo,
        origen,
        precio.valor,
        self.convertir(precio.valor, origen, MONEDA_LOCAL, tasas),
        self.convertir(precio.valor, origen, codigo, tasas),
      ))
    return filas

  def exportar_csv(self, nombre_archivo: str = "lista_precios.csv") -> Path:
    """Exporta los precios en pesos y en dólares de cada tipo de cotización.

    Genera una columna en pesos (según la cotización oficial si existe,
    o la primera disponible) y una columna en USD por cada tipo de
    cotización con valores registrados.

    Args:
      nombre_archivo: Nombre del archivo CSV a generar.

    Returns:
      Path: Ruta del archivo generado.

    Raises:
      ValueError: Si no hay cotizaciones registradas.
    """
    tipos = [
      tipo for tipo in self._tipos.leer_todos()
      if self._cotizaciones.leer_historico_por_tipo(tipo.id)
    ]
    if not tipos:
      raise ValueError("No hay cotizaciones registradas para exportar.")
    tasas_por_tipo = {tipo.nombre: self.tasas(tipo.id) for tipo in tipos}
    tipo_pesos = next(
      (tipo.nombre for tipo in tipos if normalizar(tipo.nombre) == "oficial"),
      tipos[0].nombre,
    )

    columnas_usd = [f"precio_USD_{nombre}" for nombre in tasas_por_tipo]
    encabezado = [
      "isbn", "titulo", "moneda_original", "precio_original",
      f"precio_ARS_{tipo_pesos}", *columnas_usd,
    ]
    self._carpeta_exportacion.mkdir(parents=True, exist_ok=True)
    ruta = self._carpeta_exportacion / nombre_archivo
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
      escritor = csv.writer(archivo)
      escritor.writerow(encabezado)
      for precio in self._precios.leer_todos():
        origen = precio.moneda.codigo
        fila = [
          precio.libro.isbn,
          precio.libro.titulo,
          origen,
          precio.valor,
          self.convertir(
            precio.valor, origen, MONEDA_LOCAL, tasas_por_tipo[tipo_pesos]
          ),
        ]
        fila += [
          self.convertir(precio.valor, origen, MONEDA_DOLAR, tasas)
          for tasas in tasas_por_tipo.values()
        ]
        escritor.writerow(["" if valor is None else valor for valor in fila])
    return ruta
