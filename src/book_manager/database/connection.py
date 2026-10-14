"""Manejo de la conexión y las transacciones con SQLAlchemy."""

import os
from types import TracebackType
from typing import Any

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

try:
  from google.colab import userdata
except ImportError:
  userdata = None

DEFAULT_DATABASE_URL: str = "sqlite:///book_manager.db"
VARIABLE_URL: str = "DATABASE_URL"


def resolver_url() -> str:
  """Obtiene la URL de conexión sin guardar credenciales en el código.

  Busca DATABASE_URL en las variables de entorno y, si no está, en los
  secrets de Colab. Si no la encuentra, usa una base SQLite local.

  Returns:
    str: URL de conexión compatible con SQLAlchemy.
  """
  url = os.getenv(VARIABLE_URL)
  if not url and userdata is not None:
    try:
      url = userdata.get(VARIABLE_URL)
    except Exception:
      url = None
  if not url or "://" not in url:
    print(f"[BD] Sin {VARIABLE_URL}: se usa {DEFAULT_DATABASE_URL}.")
    return DEFAULT_DATABASE_URL
  for esquema in ("postgres://", "postgresql://"):
    if url.startswith(esquema):
      return url.replace(esquema, "postgresql+psycopg2://", 1)
  return url


class ConexionDB:
  """Encapsula el engine y la fábrica de sesiones de SQLAlchemy.

  Implementa el patrón Singleton: toda la aplicación comparte una
  única conexión, configurada a partir de la variable DATABASE_URL.
  """

  _instancia: "ConexionDB | None" = None

  def __new__(cls, *args: Any, **kwargs: Any) -> "ConexionDB":
    """Devuelve siempre la misma instancia de la clase."""
    if cls._instancia is None:
      cls._instancia = super().__new__(cls)
      cls._instancia._inicializada = False
    return cls._instancia

  def __init__(self, url: str | None = None, echo: bool = False) -> None:
    """Crea el engine a partir de la URL recibida o de DATABASE_URL."""
    if self._inicializada:
      return
    self.__url: str = url or resolver_url()
    self.__engine: Engine = create_engine(
      self.__url, echo=echo, pool_pre_ping=True
    )
    self.__fabrica_sesiones: sessionmaker[Session] = sessionmaker(
      bind=self.__engine, expire_on_commit=False
    )
    if self.__engine.dialect.name == "sqlite":
      event.listen(
        self.__engine, "connect", self._activar_claves_foraneas
      )
    self._inicializada: bool = True

  @staticmethod
  def _activar_claves_foraneas(conexion_dbapi: Any, _registro: Any) -> None:
    """Habilita las claves foráneas en SQLite (vienen desactivadas)."""
    cursor = conexion_dbapi.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

  @property
  def engine(self) -> Engine:
    """Engine de SQLAlchemy asociado a la conexión."""
    return self.__engine

  @property
  def motor(self) -> str:
    """Nombre del motor de base de datos (sqlite, postgresql, etc.)."""
    return self.__engine.dialect.name

  @property
  def url_segura(self) -> str:
    """URL de conexión con la contraseña oculta."""
    return self.__engine.url.render_as_string(hide_password=True)

  def crear_sesion(self) -> Session:
    """Crea una sesión nueva vinculada al engine."""
    return self.__fabrica_sesiones()

  def transaccion(self) -> "GestorTransaccion":
    """Devuelve un context manager que maneja una transacción."""
    return GestorTransaccion(self)

  def probar_conexion(self) -> bool:
    """Ejecuta una consulta mínima para verificar que la base responde."""
    try:
      with self.__engine.connect() as conexion:
        conexion.execute(text("SELECT 1"))
      return True
    except Exception as error:
      print(f"Error al conectar con {self.url_segura}: {error}")
      return False

  def crear_tablas(self, base: type[DeclarativeBase]) -> None:
    """Crea las tablas registradas en la metadata de la base."""
    base.metadata.create_all(self.__engine)

  def eliminar_tablas(self, base: type[DeclarativeBase]) -> None:
    """Elimina las tablas registradas en la metadata de la base."""
    base.metadata.drop_all(self.__engine)

  def cerrar(self) -> None:
    """Libera el pool de conexiones y reinicia el Singleton."""
    self.__engine.dispose()
    ConexionDB._instancia = None

  def __repr__(self) -> str:
    """Representación legible sin exponer credenciales."""
    return f"ConexionDB(motor={self.motor!r}, url={self.url_segura!r})"


class GestorTransaccion:
  """Context manager que delimita una transacción de base de datos.

  Al entrar abre una sesión; al salir hace commit si el bloque terminó
  bien o rollback si se produjo una excepción, y siempre cierra la
  sesión. La excepción no se suprime: se propaga a quien la invocó.

  Uso:
    with GestorTransaccion(ConexionDB()) as sesion:
      sesion.add(objeto)
  """

  def __init__(self, conexion: ConexionDB) -> None:
    """Guarda la conexión desde la que se crearán las sesiones."""
    self.__conexion: ConexionDB = conexion
    self.__sesion: Session | None = None

  @property
  def activa(self) -> bool:
    """Indica si hay una transacción en curso."""
    return self.__sesion is not None

  def __enter__(self) -> Session:
    """Abre la sesión y la entrega al bloque with."""
    self.__sesion = self.__conexion.crear_sesion()
    return self.__sesion

  def __exit__(
    self,
    tipo_error: type[BaseException] | None,
    error: BaseException | None,
    traza: TracebackType | None,
  ) -> bool:
    """Confirma o revierte la transacción y cierra la sesión."""
    if self.__sesion is None:
      return False
    try:
      if tipo_error is None:
        self.__confirmar()
      else:
        self.__sesion.rollback()
    finally:
      self.__sesion.close()
      self.__sesion = None
    return False

  def __confirmar(self) -> None:
    """Hace commit; si el commit falla, revierte y relanza el error."""
    try:
      self.__sesion.commit()
    except Exception:
      self.__sesion.rollback()
      raise
