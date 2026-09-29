import abc
from datetime import date
from typing import Hashable, Optional


def validar_texto(valor: str, campo: str) -> str:
  """Valida que un texto no esté vacío y lo devuelve sin espacios extremos.

  Args:
    valor: Texto a validar.
    campo: Nombre descriptivo del campo, usado en el mensaje de error.

  Returns:
    str: El texto validado sin espacios al inicio ni al final.

  Raises:
    ValueError: Si el texto está vacío.
  """
  texto = str(valor).strip()
  if not texto:
    raise ValueError(f"El campo '{campo}' no puede estar vacío.")
  return texto


def validar_id(valor: int, campo: str) -> int:
  """Valida que un identificador numérico sea un entero positivo.

  Args:
    valor: Identificador a validar.
    campo: Nombre descriptivo del campo, usado en el mensaje de error.

  Returns:
    int: El identificador validado.

  Raises:
    ValueError: Si el identificador no es un entero mayor a cero.
  """
  if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
    raise ValueError(f"El campo '{campo}' debe ser un entero positivo.")
  return valor


class EntidadBase(abc.ABC):
  """Clase base abstracta para las entidades persistibles por clave."""

  @property
  @abc.abstractmethod
  def clave(self) -> Hashable:
    """Hashable: Identificador único de la entidad en su repositorio."""


class Genero(EntidadBase):
  """Categoría literaria a la que pertenece un libro.

  Args:
    id_genero: Identificador numérico del género.
    nombre: Nombre del género literario.
  """

  def __init__(self, id_genero: int, nombre: str) -> None:
    self._id = validar_id(id_genero, "id del género")
    self.nombre = nombre

  @property
  def id(self) -> int:
    """int: Identificador numérico del género."""
    return self._id

  @property
  def clave(self) -> int:
    """int: Clave del género en el repositorio."""
    return self._id

  @property
  def nombre(self) -> str:
    """str: Nombre del género literario."""
    return self._nombre

  @nombre.setter
  def nombre(self, valor: str) -> None:
    self._nombre = validar_texto(valor, "nombre del género")

  def __repr__(self) -> str:
    """Devuelve una representación legible del género."""
    return f"Genero(id={self._id}, nombre='{self._nombre}')"


class Editorial(EntidadBase):
  """Proveedor o distribuidora que abastece de libros a la librería.

  Args:
    id_editorial: Identificador numérico de la editorial.
    nombre: Nombre comercial de la editorial.
    contacto: Dato de contacto opcional (correo, teléfono, etc.).
  """

  def __init__(
    self, id_editorial: int, nombre: str, contacto: Optional[str] = None
  ) -> None:
    self._id = validar_id(id_editorial, "id de la editorial")
    self.nombre = nombre
    self.contacto = contacto

  @property
  def id(self) -> int:
    """int: Identificador numérico de la editorial."""
    return self._id

  @property
  def clave(self) -> int:
    """int: Clave de la editorial en el repositorio."""
    return self._id

  @property
  def nombre(self) -> str:
    """str: Nombre comercial de la editorial."""
    return self._nombre

  @nombre.setter
  def nombre(self, valor: str) -> None:
    self._nombre = validar_texto(valor, "nombre de la editorial")

  @property
  def contacto(self) -> Optional[str]:
    """Optional[str]: Dato de contacto de la editorial."""
    return self._contacto

  @contacto.setter
  def contacto(self, valor: Optional[str]) -> None:
    self._contacto = valor.strip() if valor and valor.strip() else None

  def __repr__(self) -> str:
    """Devuelve una representación legible de la editorial."""
    return (
      f"Editorial(id={self._id}, nombre='{self._nombre}', "
      f"contacto='{self._contacto or '-'}')"
    )


class Moneda(EntidadBase):
  """Moneda en la que puede expresarse un precio.

  Args:
    id_moneda: Identificador numérico de la moneda.
    codigo: Código ISO 4217 de tres letras (ARS, USD, etc.).
    simbolo: Símbolo de la moneda ($, U$S, etc.).
  """

  def __init__(self, id_moneda: int, codigo: str, simbolo: str) -> None:
    self._id = validar_id(id_moneda, "id de la moneda")
    self.codigo = codigo
    self.simbolo = simbolo

  @property
  def id(self) -> int:
    """int: Identificador numérico de la moneda."""
    return self._id

  @property
  def clave(self) -> int:
    """int: Clave de la moneda en el repositorio."""
    return self._id

  @property
  def codigo(self) -> str:
    """str: Código ISO 4217 de la moneda en mayúsculas."""
    return self._codigo

  @codigo.setter
  def codigo(self, valor: str) -> None:
    codigo = validar_texto(valor, "código de la moneda").upper()
    if len(codigo) != 3 or not codigo.isalpha():
      raise ValueError("El código de la moneda debe tener 3 letras.")
    self._codigo = codigo

  @property
  def simbolo(self) -> str:
    """str: Símbolo de la moneda."""
    return self._simbolo

  @simbolo.setter
  def simbolo(self, valor: str) -> None:
    self._simbolo = validar_texto(valor, "símbolo de la moneda")

  def __repr__(self) -> str:
    """Devuelve una representación legible de la moneda."""
    return (
      f"Moneda(id={self._id}, codigo='{self._codigo}', "
      f"simbolo='{self._simbolo}')"
    )


class TipoCotizacion(EntidadBase):
  """Tipo de cotización del dólar (Oficial, Blue, MEP, etc.).

  Args:
    id_tipo: Identificador numérico del tipo de cotización.
    nombre: Nombre del tipo de cotización.
  """

  def __init__(self, id_tipo: int, nombre: str) -> None:
    self._id = validar_id(id_tipo, "id del tipo de cotización")
    self.nombre = nombre

  @property
  def id(self) -> int:
    """int: Identificador numérico del tipo de cotización."""
    return self._id

  @property
  def clave(self) -> int:
    """int: Clave del tipo de cotización en el repositorio."""
    return self._id

  @property
  def nombre(self) -> str:
    """str: Nombre del tipo de cotización."""
    return self._nombre

  @nombre.setter
  def nombre(self, valor: str) -> None:
    self._nombre = validar_texto(valor, "nombre del tipo de cotización")

  def __repr__(self) -> str:
    """Devuelve una representación legible del tipo de cotización."""
    return f"TipoCotizacion(id={self._id}, nombre='{self._nombre}')"


class Libro(EntidadBase):
  """Título del catálogo de la librería.

  Args:
    isbn: Código ISBN de 10 o 13 dígitos que identifica al libro.
    titulo: Título del libro.
    autor: Autor o autores del libro.
    editorial: Editorial que provee el libro.
    genero: Género literario del libro.
  """

  def __init__(
    self,
    isbn: str,
    titulo: str,
    autor: str,
    editorial: Editorial,
    genero: Genero,
  ) -> None:
    self._isbn = self._validar_isbn(isbn)
    self.titulo = titulo
    self.autor = autor
    self.editorial = editorial
    self.genero = genero

  @staticmethod
  def _validar_isbn(valor: str) -> str:
    """Normaliza y valida un ISBN.

    Args:
      valor: ISBN ingresado, con o sin guiones.

    Returns:
      str: ISBN compuesto solo por dígitos.

    Raises:
      ValueError: Si el ISBN no tiene 10 o 13 dígitos.
    """
    isbn = str(valor).replace("-", "").strip()
    if not isbn.isdigit() or len(isbn) not in (10, 13):
      raise ValueError("El ISBN debe tener 10 o 13 dígitos.")
    return isbn

  @property
  def isbn(self) -> str:
    """str: Código ISBN del libro (inmutable)."""
    return self._isbn

  @property
  def clave(self) -> str:
    """str: Clave del libro en el repositorio (su ISBN)."""
    return self._isbn

  @property
  def titulo(self) -> str:
    """str: Título del libro."""
    return self._titulo

  @titulo.setter
  def titulo(self, valor: str) -> None:
    self._titulo = validar_texto(valor, "título")

  @property
  def autor(self) -> str:
    """str: Autor o autores del libro."""
    return self._autor

  @autor.setter
  def autor(self, valor: str) -> None:
    self._autor = validar_texto(valor, "autor")

  @property
  def editorial(self) -> Editorial:
    """Editorial: Editorial que provee el libro."""
    return self._editorial

  @editorial.setter
  def editorial(self, valor: Editorial) -> None:
    if not isinstance(valor, Editorial):
      raise ValueError("La editorial del libro no es válida.")
    self._editorial = valor

  @property
  def genero(self) -> Genero:
    """Genero: Género literario del libro."""
    return self._genero

  @genero.setter
  def genero(self, valor: Genero) -> None:
    if not isinstance(valor, Genero):
      raise ValueError("El género del libro no es válido.")
    self._genero = valor

  def __repr__(self) -> str:
    """Devuelve una representación legible del libro."""
    return (
      f"Libro(isbn='{self._isbn}', titulo='{self._titulo}', "
      f"autor='{self._autor}', editorial='{self._editorial.nombre}', "
      f"genero='{self._genero.nombre}')"
    )


class Precio(EntidadBase):
  """Valor monetario de un libro expresado en una moneda.

  Args:
    libro_isbn: ISBN del libro al que corresponde el precio.
    valor: Importe del precio, mayor o igual a cero.
    moneda: Moneda en la que se expresa el importe.
  """

  def __init__(self, libro_isbn: str, valor: float, moneda: Moneda) -> None:
    self._libro_isbn = validar_texto(libro_isbn, "ISBN del libro")
    self.valor = valor
    self.moneda = moneda

  @property
  def libro_isbn(self) -> str:
    """str: ISBN del libro al que corresponde el precio."""
    return self._libro_isbn

  @property
  def clave(self) -> str:
    """str: Clave del precio en el repositorio (ISBN del libro)."""
    return self._libro_isbn

  @property
  def valor(self) -> float:
    """float: Importe del precio."""
    return self._valor

  @valor.setter
  def valor(self, importe: float) -> None:
    if importe < 0:
      raise ValueError("El valor del precio no puede ser negativo.")
    self._valor = float(importe)

  @property
  def moneda(self) -> Moneda:
    """Moneda: Moneda en la que se expresa el precio."""
    return self._moneda

  @moneda.setter
  def moneda(self, valor: Moneda) -> None:
    if not isinstance(valor, Moneda):
      raise ValueError("La moneda del precio no es válida.")
    self._moneda = valor

  def __repr__(self) -> str:
    """Devuelve una representación legible del precio."""
    return (
      f"Precio(libro_isbn='{self._libro_isbn}', "
      f"valor={self._moneda.simbolo} {self._valor:,.2f} "
      f"{self._moneda.codigo})"
    )


class Stock:
  """Cantidad disponible de un libro en el inventario.

  Args:
    libro_isbn: ISBN del libro inventariado.
    cantidad: Unidades disponibles, mayor o igual a cero.
  """

  def __init__(self, libro_isbn: str, cantidad: int) -> None:
    self._libro_isbn = validar_texto(libro_isbn, "ISBN del libro")
    self.cantidad = cantidad

  @property
  def libro_isbn(self) -> str:
    """str: ISBN del libro inventariado."""
    return self._libro_isbn

  @property
  def cantidad(self) -> int:
    """int: Unidades disponibles del libro."""
    return self._cantidad

  @cantidad.setter
  def cantidad(self, valor: int) -> None:
    if valor < 0:
      raise ValueError("La cantidad de stock no puede ser negativa.")
    self._cantidad = int(valor)

  def __repr__(self) -> str:
    """Devuelve una representación legible del stock."""
    return (
      f"Stock(libro_isbn='{self._libro_isbn}', cantidad={self._cantidad})"
    )


class CotizacionDolar:
  """Registro histórico del valor del dólar para un tipo y una fecha.

  Args:
    tipo_cotizacion: Tipo de cotización (Oficial, Blue, MEP, etc.).
    fecha: Fecha de la cotización.
    valor: Valor en pesos de un dólar, mayor a cero.
  """

  def __init__(
    self, tipo_cotizacion: TipoCotizacion, fecha: date, valor: float
  ) -> None:
    if not isinstance(tipo_cotizacion, TipoCotizacion):
      raise ValueError("El tipo de cotización no es válido.")
    if not isinstance(fecha, date):
      raise ValueError("La fecha de la cotización no es válida.")
    self._tipo_cotizacion = tipo_cotizacion
    self._fecha = fecha
    self.valor = valor

  @property
  def tipo_cotizacion(self) -> TipoCotizacion:
    """TipoCotizacion: Tipo de la cotización (inmutable)."""
    return self._tipo_cotizacion

  @property
  def fecha(self) -> date:
    """date: Fecha de la cotización (inmutable)."""
    return self._fecha

  @property
  def valor(self) -> float:
    """float: Valor en pesos de un dólar."""
    return self._valor

  @valor.setter
  def valor(self, importe: float) -> None:
    if importe <= 0:
      raise ValueError("El valor de la cotización debe ser mayor a cero.")
    self._valor = float(importe)

  def __repr__(self) -> str:
    """Devuelve una representación legible de la cotización."""
    return (
      f"CotizacionDolar(tipo='{self._tipo_cotizacion.nombre}', "
      f"fecha={self._fecha.isoformat()}, valor={self._valor:,.2f})"
    )
