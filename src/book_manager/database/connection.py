"""Manejo de la conexión a la base de datos relacional con SQLAlchemy."""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_DATABASE_URL: str = "sqlite:///book_manager.db"


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
        self.__url: str = url or os.getenv(
            "DATABASE_URL", DEFAULT_DATABASE_URL
        )
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

    @contextmanager
    def obtener_sesion(self) -> Iterator[Session]:
        """Sesión transaccional: commit al terminar, rollback ante error."""
        sesion = self.__fabrica_sesiones()
        try:
            yield sesion
            sesion.commit()
        except Exception:
            sesion.rollback()
            raise
        finally:
            sesion.close()

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
