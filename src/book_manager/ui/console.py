from datetime import date
from typing import Callable, Hashable, Iterable, Optional, TypeVar

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
from book_manager.services.services import (
  ServicioCotizacionDolar,
  ServicioCrud,
  ServicioEditorial,
  ServicioGenero,
  ServicioLibro,
  ServicioMoneda,
  ServicioPrecio,
  ServicioStock,
  ServicioTipoCotizacion,
)

T = TypeVar("T", bound=EntidadBase)
Acciones = dict[str, tuple[str, Callable[[], None]]]


class ConsoleUI:
  """Interfaz de consola (CLI) que opera el CRUD de cada entidad.

  Args:
    svc_genero: Servicio de géneros.
    svc_editorial: Servicio de editoriales.
    svc_moneda: Servicio de monedas.
    svc_tipo_cotizacion: Servicio de tipos de cotización.
    svc_libro: Servicio de libros.
    svc_precio: Servicio de precios.
    svc_stock: Servicio de stock.
    svc_cotizacion: Servicio de cotizaciones del dólar.
    guardar: Función que persiste los datos luego de cada operación.
  """

  ANCHO_SEPARADOR = 40

  def __init__(
    self,
    svc_genero: ServicioGenero,
    svc_editorial: ServicioEditorial,
    svc_moneda: ServicioMoneda,
    svc_tipo_cotizacion: ServicioTipoCotizacion,
    svc_libro: ServicioLibro,
    svc_precio: ServicioPrecio,
    svc_stock: ServicioStock,
    svc_cotizacion: ServicioCotizacionDolar,
    guardar: Callable[[], None] = lambda: None,
  ) -> None:
    self._svc_genero = svc_genero
    self._svc_editorial = svc_editorial
    self._svc_moneda = svc_moneda
    self._svc_tipo_cotizacion = svc_tipo_cotizacion
    self._svc_libro = svc_libro
    self._svc_precio = svc_precio
    self._svc_stock = svc_stock
    self._svc_cotizacion = svc_cotizacion
    self._guardar = guardar

  def iniciar(self) -> None:
    """Muestra el menú principal hasta que el usuario elige salir."""
    self._ejecutar_menu("BOOK MANAGER - Menú Principal", {
      "1": ("Gestionar Libros", self._menu_libros),
      "2": ("Gestionar Géneros", self._menu_generos),
      "3": ("Gestionar Editoriales", self._menu_editoriales),
      "4": ("Gestionar Monedas", self._menu_monedas),
      "5": ("Gestionar Tipos de Cotización", self._menu_tipos_cotizacion),
      "6": ("Gestionar Precios", self._menu_precios),
      "7": ("Gestionar Stock", self._menu_stock),
      "8": ("Gestionar Cotizaciones del Dólar", self._menu_cotizaciones),
    }, texto_salida="Salir")
    print("Saliendo del sistema...")

  def _ejecutar_menu(
    self, titulo: str, acciones: Acciones, texto_salida: str = "Volver"
  ) -> None:
    """Muestra un menú de opciones y ejecuta la acción elegida.

    Los errores de validación se informan sin interrumpir el programa y,
    si la acción termina bien, los datos se persisten en disco.

    Args:
      titulo: Título del menú.
      acciones: Opciones del menú: clave -> (descripción, acción).
      texto_salida: Descripción de la opción 0.
    """
    while True:
      print("\n" + "=" * self.ANCHO_SEPARADOR)
      print(titulo)
      print("=" * self.ANCHO_SEPARADOR)
      for clave, (descripcion, _) in acciones.items():
        print(f"{clave}. {descripcion}")
      print(f"0. {texto_salida}")
      opcion = input("Seleccione una opción: ").strip()
      if opcion == "0":
        return
      if opcion not in acciones:
        print("Opción inválida.")
        continue
      try:
        acciones[opcion][1]()
        self._guardar()
      except ValueError as error:
        print(f"Error: {error}")

  @staticmethod
  def _pedir_texto(mensaje: str, actual: Optional[str] = None) -> str:
    """Solicita un texto; si hay valor actual, Enter lo conserva.

    Args:
      mensaje: Texto a mostrar al usuario.
      actual: Valor vigente que se conserva si no se ingresa nada.

    Returns:
      str: Texto ingresado o el valor actual.
    """
    sufijo = f" [{actual}]" if actual is not None else ""
    valor = input(f"{mensaje}{sufijo}: ").strip()
    return valor if valor or actual is None else actual

  def _pedir_entero(self, mensaje: str, actual: Optional[int] = None) -> int:
    """Solicita un número entero hasta que el ingreso sea válido.

    Args:
      mensaje: Texto a mostrar al usuario.
      actual: Valor vigente que se conserva si no se ingresa nada.

    Returns:
      int: Número ingresado o el valor actual.
    """
    while True:
      valor = self._pedir_texto(
        mensaje, None if actual is None else str(actual)
      )
      try:
        return int(valor)
      except ValueError:
        print("Debe ingresar un número entero válido.")

  def _pedir_decimal(
    self, mensaje: str, actual: Optional[float] = None
  ) -> float:
    """Solicita un número decimal hasta que el ingreso sea válido.

    Args:
      mensaje: Texto a mostrar al usuario.
      actual: Valor vigente que se conserva si no se ingresa nada.

    Returns:
      float: Número ingresado o el valor actual.
    """
    while True:
      valor = self._pedir_texto(
        mensaje, None if actual is None else str(actual)
      )
      try:
        return float(valor.replace(",", "."))
      except ValueError:
        print("Debe ingresar un número decimal válido.")

  def _pedir_fecha(self, mensaje: str) -> date:
    """Solicita una fecha en formato AAAA-MM-DD hasta que sea válida.

    Args:
      mensaje: Texto a mostrar al usuario.

    Returns:
      date: Fecha ingresada.
    """
    while True:
      try:
        return date.fromisoformat(self._pedir_texto(f"{mensaje} (AAAA-MM-DD)"))
      except ValueError:
        print("Debe ingresar una fecha válida con formato AAAA-MM-DD.")

  @staticmethod
  def _mostrar(registros: Iterable[object]) -> None:
    """Imprime un listado de registros o un aviso si está vacío.

    Args:
      registros: Registros a imprimir.
    """
    lista = list(registros)
    for registro in lista:
      print(f"  {registro}")
    print(f"Total: {len(lista)} registro(s).")

  @staticmethod
  def _mostrar_uno(registro: Optional[object]) -> None:
    """Imprime un registro o un aviso si no se encontró.

    Args:
      registro: Registro a imprimir.
    """
    print(f"  {registro}" if registro is not None else "No encontrado.")

  @staticmethod
  def _informar_eliminacion(eliminado: bool) -> None:
    """Informa el resultado de una eliminación.

    Args:
      eliminado: True si el registro fue eliminado.
    """
    print("Registro eliminado." if eliminado else "No encontrado.")

  @staticmethod
  def _obtener(servicio: ServicioCrud[T], identificador: Hashable) -> T:
    """Obtiene una entidad existente o informa que no existe.

    Args:
      servicio: Servicio donde se busca la entidad.
      identificador: Clave de la entidad.

    Returns:
      T: La entidad encontrada.

    Raises:
      ValueError: Si la entidad no existe.
    """
    entidad = servicio.leer_por_id(identificador)
    if entidad is None:
      raise ValueError(f"No existe un registro con clave {identificador!r}.")
    return entidad

  def _menu_generos(self) -> None:
    """Menú CRUD de géneros."""
    self._ejecutar_menu("GESTIÓN DE GÉNEROS", {
      "1": ("Listar", lambda: self._mostrar(self._svc_genero.leer_todos())),
      "2": ("Buscar por ID", lambda: self._mostrar_uno(
        self._svc_genero.leer_por_id(self._pedir_entero("ID")))),
      "3": ("Crear", self._crear_genero),
      "4": ("Modificar", self._modificar_genero),
      "5": ("Eliminar", lambda: self._informar_eliminacion(
        self._svc_genero.eliminar(self._pedir_entero("ID a eliminar")))),
    })

  def _crear_genero(self) -> None:
    """Solicita los datos de un género y lo crea."""
    genero = Genero(self._pedir_entero("ID"), self._pedir_texto("Nombre"))
    print(f"Creado: {self._svc_genero.crear(genero)}")

  def _modificar_genero(self) -> None:
    """Solicita los datos nuevos de un género y lo actualiza."""
    actual = self._obtener(self._svc_genero, self._pedir_entero("ID"))
    genero = Genero(actual.id, self._pedir_texto("Nombre", actual.nombre))
    print(f"Modificado: {self._svc_genero.actualizar(genero)}")

  def _menu_editoriales(self) -> None:
    """Menú CRUD de editoriales."""
    self._ejecutar_menu("GESTIÓN DE EDITORIALES", {
      "1": ("Listar", lambda: self._mostrar(self._svc_editorial.leer_todos())),
      "2": ("Buscar por ID", lambda: self._mostrar_uno(
        self._svc_editorial.leer_por_id(self._pedir_entero("ID")))),
      "3": ("Crear", self._crear_editorial),
      "4": ("Modificar", self._modificar_editorial),
      "5": ("Eliminar", lambda: self._informar_eliminacion(
        self._svc_editorial.eliminar(self._pedir_entero("ID a eliminar")))),
    })

  def _crear_editorial(self) -> None:
    """Solicita los datos de una editorial y la crea."""
    editorial = Editorial(
      self._pedir_entero("ID"),
      self._pedir_texto("Nombre"),
      self._pedir_texto("Contacto (opcional)"),
    )
    print(f"Creada: {self._svc_editorial.crear(editorial)}")

  def _modificar_editorial(self) -> None:
    """Solicita los datos nuevos de una editorial y la actualiza."""
    actual = self._obtener(self._svc_editorial, self._pedir_entero("ID"))
    editorial = Editorial(
      actual.id,
      self._pedir_texto("Nombre", actual.nombre),
      self._pedir_texto("Contacto", actual.contacto or ""),
    )
    print(f"Modificada: {self._svc_editorial.actualizar(editorial)}")

  def _menu_monedas(self) -> None:
    """Menú CRUD de monedas."""
    self._ejecutar_menu("GESTIÓN DE MONEDAS", {
      "1": ("Listar", lambda: self._mostrar(self._svc_moneda.leer_todos())),
      "2": ("Buscar por ID", lambda: self._mostrar_uno(
        self._svc_moneda.leer_por_id(self._pedir_entero("ID")))),
      "3": ("Crear", self._crear_moneda),
      "4": ("Modificar", self._modificar_moneda),
      "5": ("Eliminar", lambda: self._informar_eliminacion(
        self._svc_moneda.eliminar(self._pedir_entero("ID a eliminar")))),
    })

  def _crear_moneda(self) -> None:
    """Solicita los datos de una moneda y la crea."""
    moneda = Moneda(
      self._pedir_entero("ID"),
      self._pedir_texto("Código ISO (ej. ARS)"),
      self._pedir_texto("Símbolo (ej. $)"),
    )
    print(f"Creada: {self._svc_moneda.crear(moneda)}")

  def _modificar_moneda(self) -> None:
    """Solicita los datos nuevos de una moneda y la actualiza."""
    actual = self._obtener(self._svc_moneda, self._pedir_entero("ID"))
    moneda = Moneda(
      actual.id,
      self._pedir_texto("Código ISO", actual.codigo),
      self._pedir_texto("Símbolo", actual.simbolo),
    )
    print(f"Modificada: {self._svc_moneda.actualizar(moneda)}")

  def _menu_tipos_cotizacion(self) -> None:
    """Menú CRUD de tipos de cotización."""
    svc = self._svc_tipo_cotizacion
    self._ejecutar_menu("GESTIÓN DE TIPOS DE COTIZACIÓN", {
      "1": ("Listar", lambda: self._mostrar(svc.leer_todos())),
      "2": ("Buscar por ID", lambda: self._mostrar_uno(
        svc.leer_por_id(self._pedir_entero("ID")))),
      "3": ("Crear", self._crear_tipo_cotizacion),
      "4": ("Modificar", self._modificar_tipo_cotizacion),
      "5": ("Eliminar", lambda: self._informar_eliminacion(
        svc.eliminar(self._pedir_entero("ID a eliminar")))),
    })

  def _crear_tipo_cotizacion(self) -> None:
    """Solicita los datos de un tipo de cotización y lo crea."""
    tipo = TipoCotizacion(
      self._pedir_entero("ID"), self._pedir_texto("Nombre")
    )
    print(f"Creado: {self._svc_tipo_cotizacion.crear(tipo)}")

  def _modificar_tipo_cotizacion(self) -> None:
    """Solicita los datos nuevos de un tipo de cotización y lo actualiza."""
    actual = self._obtener(
      self._svc_tipo_cotizacion, self._pedir_entero("ID")
    )
    tipo = TipoCotizacion(actual.id, self._pedir_texto("Nombre", actual.nombre))
    print(f"Modificado: {self._svc_tipo_cotizacion.actualizar(tipo)}")

  def _menu_libros(self) -> None:
    """Menú CRUD de libros."""
    self._ejecutar_menu("GESTIÓN DE LIBROS", {
      "1": ("Listar", lambda: self._mostrar(self._svc_libro.leer_todos())),
      "2": ("Buscar por ISBN", lambda: self._mostrar_uno(
        self._svc_libro.leer_por_id(self._pedir_texto("ISBN")))),
      "3": ("Crear", self._crear_libro),
      "4": ("Modificar", self._modificar_libro),
      "5": ("Eliminar", lambda: self._informar_eliminacion(
        self._svc_libro.eliminar(self._pedir_texto("ISBN a eliminar")))),
    })

  def _crear_libro(self) -> None:
    """Solicita los datos de un libro y lo crea."""
    libro = Libro(
      self._pedir_texto("ISBN (10 o 13 dígitos)"),
      self._pedir_texto("Título"),
      self._pedir_texto("Autor"),
      self._obtener(self._svc_editorial, self._pedir_entero("ID Editorial")),
      self._obtener(self._svc_genero, self._pedir_entero("ID Género")),
    )
    print(f"Creado: {self._svc_libro.crear(libro)}")

  def _modificar_libro(self) -> None:
    """Solicita los datos nuevos de un libro y lo actualiza."""
    actual = self._obtener(self._svc_libro, self._pedir_texto("ISBN"))
    libro = Libro(
      actual.isbn,
      self._pedir_texto("Título", actual.titulo),
      self._pedir_texto("Autor", actual.autor),
      self._obtener(
        self._svc_editorial,
        self._pedir_entero("ID Editorial", actual.editorial.id),
      ),
      self._obtener(
        self._svc_genero, self._pedir_entero("ID Género", actual.genero.id)
      ),
    )
    print(f"Modificado: {self._svc_libro.actualizar(libro)}")

  def _menu_precios(self) -> None:
    """Menú CRUD de precios."""
    self._ejecutar_menu("GESTIÓN DE PRECIOS", {
      "1": ("Listar", lambda: self._mostrar(self._svc_precio.leer_todos())),
      "2": ("Buscar por ISBN", lambda: self._mostrar_uno(
        self._svc_precio.leer_por_id(self._pedir_texto("ISBN")))),
      "3": ("Crear", self._crear_precio),
      "4": ("Modificar", self._modificar_precio),
      "5": ("Eliminar", lambda: self._informar_eliminacion(
        self._svc_precio.eliminar(self._pedir_texto("ISBN a eliminar")))),
    })

  def _crear_precio(self) -> None:
    """Solicita los datos de un precio y lo crea."""
    precio = Precio(
      self._pedir_texto("ISBN del libro"),
      self._pedir_decimal("Valor"),
      self._obtener(self._svc_moneda, self._pedir_entero("ID Moneda")),
    )
    print(f"Creado: {self._svc_precio.crear(precio)}")

  def _modificar_precio(self) -> None:
    """Solicita los datos nuevos de un precio y lo actualiza."""
    actual = self._obtener(self._svc_precio, self._pedir_texto("ISBN"))
    precio = Precio(
      actual.libro_isbn,
      self._pedir_decimal("Valor", actual.valor),
      self._obtener(
        self._svc_moneda, self._pedir_entero("ID Moneda", actual.moneda.id)
      ),
    )
    print(f"Modificado: {self._svc_precio.actualizar(precio)}")

  def _menu_stock(self) -> None:
    """Menú CRUD de stock con ingreso y retiro de unidades."""
    self._ejecutar_menu("GESTIÓN DE STOCK", {
      "1": ("Listar", lambda: self._mostrar(self._svc_stock.leer_todos())),
      "2": ("Buscar por ISBN", lambda: self._mostrar_uno(
        self._svc_stock.leer_por_libro(self._pedir_texto("ISBN")))),
      "3": ("Crear", self._crear_stock),
      "4": ("Modificar cantidad exacta", self._modificar_stock),
      "5": ("Ingresar unidades", self._ingresar_stock),
      "6": ("Retirar unidades", self._retirar_stock),
      "7": ("Eliminar", lambda: self._informar_eliminacion(
        self._svc_stock.eliminar(self._pedir_texto("ISBN a eliminar")))),
    })

  def _crear_stock(self) -> None:
    """Solicita los datos de un stock inicial y lo crea."""
    stock = Stock(
      self._pedir_texto("ISBN del libro"), self._pedir_entero("Cantidad")
    )
    print(f"Creado: {self._svc_stock.crear(stock)}")

  def _modificar_stock(self) -> None:
    """Solicita la cantidad exacta de un stock y lo actualiza."""
    isbn = self._pedir_texto("ISBN del libro")
    actual = self._svc_stock.leer_por_libro(isbn)
    if actual is None:
      raise ValueError("No existe stock para el libro indicado.")
    stock = Stock(isbn, self._pedir_entero("Cantidad", actual.cantidad))
    print(f"Modificado: {self._svc_stock.actualizar(stock)}")

  def _ingresar_stock(self) -> None:
    """Suma unidades al stock de un libro."""
    stock = self._svc_stock.ingresar(
      self._pedir_texto("ISBN del libro"),
      self._pedir_entero("Cantidad a ingresar"),
    )
    print(f"Ingreso registrado: {stock}")

  def _retirar_stock(self) -> None:
    """Descuenta unidades del stock de un libro."""
    stock = self._svc_stock.retirar(
      self._pedir_texto("ISBN del libro"),
      self._pedir_entero("Cantidad a retirar"),
    )
    print(f"Retiro registrado: {stock}")

  def _menu_cotizaciones(self) -> None:
    """Menú CRUD de cotizaciones del dólar."""
    svc = self._svc_cotizacion
    self._ejecutar_menu("GESTIÓN DE COTIZACIONES DEL DÓLAR", {
      "1": ("Listar", lambda: self._mostrar(svc.leer_todos())),
      "2": ("Histórico por tipo", lambda: self._mostrar(
        svc.leer_historico_por_tipo(self._pedir_entero("ID Tipo")))),
      "3": ("Buscar por tipo y fecha", lambda: self._mostrar_uno(
        svc.leer_por_tipo_y_fecha(
          self._pedir_entero("ID Tipo"), self._pedir_fecha("Fecha")))),
      "4": ("Crear", self._crear_cotizacion),
      "5": ("Modificar", self._modificar_cotizacion),
      "6": ("Eliminar", lambda: self._informar_eliminacion(
        svc.eliminar(
          self._pedir_entero("ID Tipo"), self._pedir_fecha("Fecha")))),
    })

  def _crear_cotizacion(self) -> None:
    """Solicita los datos de una cotización y la crea."""
    cotizacion = CotizacionDolar(
      self._obtener(self._svc_tipo_cotizacion, self._pedir_entero("ID Tipo")),
      self._pedir_fecha("Fecha"),
      self._pedir_decimal("Valor en ARS"),
    )
    print(f"Creada: {self._svc_cotizacion.crear(cotizacion)}")

  def _modificar_cotizacion(self) -> None:
    """Solicita el valor nuevo de una cotización y la actualiza."""
    tipo_id = self._pedir_entero("ID Tipo")
    fecha = self._pedir_fecha("Fecha")
    actual = self._svc_cotizacion.leer_por_tipo_y_fecha(tipo_id, fecha)
    if actual is None:
      raise ValueError("No existe la cotización indicada.")
    cotizacion = CotizacionDolar(
      actual.tipo_cotizacion,
      actual.fecha,
      self._pedir_decimal("Valor en ARS", actual.valor),
    )
    print(f"Modificada: {self._svc_cotizacion.actualizar(cotizacion)}")
