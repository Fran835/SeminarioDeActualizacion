"""Repositorios con persistencia en base de datos mediante SQLAlchemy.

Cada repositorio traduce entre las entidades del dominio (entities.py)
y los modelos ORM (models.py), y ejecuta cada operación dentro de una
transacción del GestorTransaccion.
"""

import abc
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from typing import Generic, Optional, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.models.models import (
    Base,
    CotizacionDolarModel,
    EditorialModel,
    GeneroModel,
    LibroModel,
    MonedaModel,
    PrecioModel,
    StockModel,
    TipoCotizacionModel,
)

T = TypeVar("T")
M = TypeVar("M", bound=Base)


# ---------------------------------------------------------------------------
# Interfaces (contratos del Sprint 1)
# ---------------------------------------------------------------------------

class IRepositorio(abc.ABC, Generic[T]):
    """Interfaz para repositorios con operaciones CRUD básicas."""

    @abc.abstractmethod
    def crear(self, entidad: T) -> T:
        """Crea la entidad; ValueError si ya existe."""

    @abc.abstractmethod
    def leer_por_id(self, identificador: object) -> Optional[T]:
        """Devuelve la entidad con esa clave o None."""

    @abc.abstractmethod
    def leer_todos(self) -> list[T]:
        """Devuelve todas las entidades."""

    @abc.abstractmethod
    def actualizar(self, entidad: T) -> T:
        """Actualiza la entidad; ValueError si no existe."""

    @abc.abstractmethod
    def eliminar(self, identificador: object) -> bool:
        """Elimina la entidad; False si no existe."""


class IRepositorioStock(abc.ABC):
    """Interfaz para repositorios del tipo Stock."""

    @abc.abstractmethod
    def crear(self, stock: Stock) -> Stock:
        """Crea el stock de un libro; ValueError si ya existe."""

    @abc.abstractmethod
    def leer_por_libro(self, libro_isbn: str) -> Optional[Stock]:
        """Devuelve el stock del libro o None."""

    @abc.abstractmethod
    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza el stock; ValueError si no existe."""

    @abc.abstractmethod
    def eliminar(self, libro_isbn: str) -> bool:
        """Elimina el stock del libro; False si no existe."""


class IRepositorioCotizacionDolar(abc.ABC):
    """Interfaz para repositorios de cotizaciones del dólar."""

    @abc.abstractmethod
    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea la cotización; ValueError si ya existe para tipo y fecha."""

    @abc.abstractmethod
    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: date
    ) -> Optional[CotizacionDolar]:
        """Devuelve la cotización de ese tipo y fecha o None."""

    @abc.abstractmethod
    def leer_historico_por_tipo(self, tipo_id: int) -> list[CotizacionDolar]:
        """Devuelve las cotizaciones de un tipo ordenadas por fecha."""

    @abc.abstractmethod
    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza la cotización; ValueError si no existe."""

    @abc.abstractmethod
    def eliminar(self, tipo_id: int, fecha: date) -> bool:
        """Elimina la cotización; False si no existe."""


# ---------------------------------------------------------------------------
# Conversión de modelos ORM a entidades
# ---------------------------------------------------------------------------

def _a_genero(modelo: GeneroModel) -> Genero:
    """Convierte un GeneroModel en la entidad Genero."""
    return Genero(modelo.id, modelo.nombre)


def _a_editorial(modelo: EditorialModel) -> Editorial:
    """Convierte un EditorialModel en la entidad Editorial."""
    return Editorial(modelo.id, modelo.nombre, modelo.contacto)


def _a_moneda(modelo: MonedaModel) -> Moneda:
    """Convierte un MonedaModel en la entidad Moneda."""
    return Moneda(modelo.id, modelo.codigo, modelo.simbolo)


def _a_tipo_cotizacion(modelo: TipoCotizacionModel) -> TipoCotizacion:
    """Convierte un TipoCotizacionModel en la entidad TipoCotizacion."""
    return TipoCotizacion(modelo.id, modelo.nombre)


def _id_libro(sesion: Session, isbn: str) -> int:
    """Obtiene el id interno de un libro a partir de su ISBN."""
    libro_id = sesion.scalar(
        select(LibroModel.id).where(LibroModel.isbn == isbn)
    )
    if libro_id is None:
        raise ValueError(f"No existe un libro con ISBN {isbn!r}.")
    return libro_id


# ---------------------------------------------------------------------------
# Repositorio base genérico
# ---------------------------------------------------------------------------

class RepositorioBase(IRepositorio[T], Generic[T, M]):
    """CRUD genérico sobre una tabla de la base de datos.

    Las subclases indican el modelo ORM y cómo convertir entre entidad
    y modelo; la lógica de las transacciones queda centralizada aquí.
    """

    modelo: type[M]

    def __init__(self, conexion: ConexionDB | None = None) -> None:
        """Recibe la conexión o usa la instancia única de ConexionDB."""
        self._conexion: ConexionDB = conexion or ConexionDB()

    @contextmanager
    def _transaccion(self) -> Iterator[Session]:
        """Abre una transacción y traduce errores de integridad."""
        try:
            with self._conexion.transaccion() as sesion:
                yield sesion
        except IntegrityError as error:
            raise ValueError(
                "La base de datos rechazó la operación (registro duplicado "
                f"o con datos relacionados): {error.orig}"
            ) from error

    def _clave(self, entidad: T) -> object:
        """Devuelve la clave de la entidad (propiedad clave de EntidadBase)."""
        return entidad.clave

    @abc.abstractmethod
    def _a_entidad(self, modelo: M) -> T:
        """Convierte un modelo ORM en una entidad del dominio."""

    @abc.abstractmethod
    def _cargar(self, sesion: Session, entidad: T, modelo: M) -> None:
        """Copia los datos de la entidad al modelo ORM."""

    def _consulta(self, clave: object) -> Select:
        """Consulta que busca los registros asociados a una clave."""
        return select(self.modelo).where(self.modelo.id == clave)

    def _buscar(self, sesion: Session, clave: object) -> Optional[M]:
        """Devuelve el primer registro asociado a la clave o None."""
        return sesion.scalars(self._consulta(clave)).first()

    def crear(self, entidad: T) -> T:
        """Inserta la entidad si su clave no existe."""
        clave = self._clave(entidad)
        with self._transaccion() as sesion:
            if self._buscar(sesion, clave) is not None:
                raise ValueError(f"Ya existe un registro con clave {clave!r}.")
            modelo = self.modelo()
            self._cargar(sesion, entidad, modelo)
            sesion.add(modelo)
            sesion.flush()
            sesion.refresh(modelo)
            return self._a_entidad(modelo)

    def leer_por_id(self, identificador: object) -> Optional[T]:
        """Busca una entidad por su clave."""
        with self._transaccion() as sesion:
            modelo = self._buscar(sesion, identificador)
            return None if modelo is None else self._a_entidad(modelo)

    def leer_todos(self) -> list[T]:
        """Devuelve todas las entidades ordenadas por id."""
        with self._transaccion() as sesion:
            consulta = select(self.modelo).order_by(self.modelo.id)
            return [self._a_entidad(m) for m in sesion.scalars(consulta)]

    def actualizar(self, entidad: T) -> T:
        """Modifica el registro existente con la clave de la entidad."""
        clave = self._clave(entidad)
        with self._transaccion() as sesion:
            modelo = self._buscar(sesion, clave)
            if modelo is None:
                raise ValueError(f"No existe un registro con clave {clave!r}.")
            self._cargar(sesion, entidad, modelo)
            sesion.flush()
            sesion.refresh(modelo)
            return self._a_entidad(modelo)

    def eliminar(self, identificador: object) -> bool:
        """Borra los registros asociados a la clave."""
        with self._transaccion() as sesion:
            modelos = sesion.scalars(self._consulta(identificador)).all()
            for modelo in modelos:
                sesion.delete(modelo)
            return bool(modelos)


# ---------------------------------------------------------------------------
# Repositorios de tablas maestras (clave: id)
# ---------------------------------------------------------------------------

class RepositorioGenero(RepositorioBase[Genero, GeneroModel]):
    """Persistencia de géneros literarios."""

    modelo = GeneroModel

    def _a_entidad(self, modelo: GeneroModel) -> Genero:
        """Convierte el modelo en entidad."""
        return _a_genero(modelo)

    def _cargar(
        self, sesion: Session, entidad: Genero, modelo: GeneroModel
    ) -> None:
        """Copia los datos de la entidad al modelo."""
        modelo.id = entidad.id
        modelo.nombre = entidad.nombre


class RepositorioEditorial(RepositorioBase[Editorial, EditorialModel]):
    """Persistencia de editoriales."""

    modelo = EditorialModel

    def _a_entidad(self, modelo: EditorialModel) -> Editorial:
        """Convierte el modelo en entidad."""
        return _a_editorial(modelo)

    def _cargar(
        self, sesion: Session, entidad: Editorial, modelo: EditorialModel
    ) -> None:
        """Copia los datos de la entidad al modelo."""
        modelo.id = entidad.id
        modelo.nombre = entidad.nombre
        modelo.contacto = entidad.contacto


class RepositorioMoneda(RepositorioBase[Moneda, MonedaModel]):
    """Persistencia de monedas."""

    modelo = MonedaModel

    def _a_entidad(self, modelo: MonedaModel) -> Moneda:
        """Convierte el modelo en entidad."""
        return _a_moneda(modelo)

    def _cargar(
        self, sesion: Session, entidad: Moneda, modelo: MonedaModel
    ) -> None:
        """Copia los datos de la entidad al modelo."""
        modelo.id = entidad.id
        modelo.codigo = entidad.codigo
        modelo.simbolo = entidad.simbolo


class RepositorioTipoCotizacion(
    RepositorioBase[TipoCotizacion, TipoCotizacionModel]
):
    """Persistencia de tipos de cotización del dólar."""

    modelo = TipoCotizacionModel

    def _a_entidad(self, modelo: TipoCotizacionModel) -> TipoCotizacion:
        """Convierte el modelo en entidad."""
        return _a_tipo_cotizacion(modelo)

    def _cargar(
        self,
        sesion: Session,
        entidad: TipoCotizacion,
        modelo: TipoCotizacionModel,
    ) -> None:
        """Copia los datos de la entidad al modelo."""
        modelo.id = entidad.id
        modelo.nombre = entidad.nombre


# ---------------------------------------------------------------------------
# Repositorios de libros, precios, stock y cotizaciones
# ---------------------------------------------------------------------------

class RepositorioLibro(RepositorioBase[Libro, LibroModel]):
    """Persistencia de libros (clave de negocio: ISBN)."""

    modelo = LibroModel

    def _consulta(self, clave: object) -> Select:
        """Busca el libro por ISBN."""
        return select(LibroModel).where(LibroModel.isbn == clave)

    def _a_entidad(self, modelo: LibroModel) -> Libro:
        """Convierte el modelo en entidad, incluyendo sus relaciones."""
        return Libro(
            modelo.isbn,
            modelo.titulo,
            modelo.autor,
            _a_editorial(modelo.editorial),
            _a_genero(modelo.genero),
        )

    def _cargar(
        self, sesion: Session, entidad: Libro, modelo: LibroModel
    ) -> None:
        """Copia los datos y las claves foráneas al modelo."""
        modelo.isbn = entidad.isbn
        modelo.titulo = entidad.titulo
        modelo.autor = entidad.autor
        modelo.editorial_id = entidad.editorial.id
        modelo.genero_id = entidad.genero.id


class RepositorioPrecio(RepositorioBase[Precio, PrecioModel]):
    """Persistencia de precios: un precio por libro (clave: ISBN).

    Al actualizar se puede cambiar tanto el valor como la moneda.
    """

    modelo = PrecioModel

    def _consulta(self, clave: object) -> Select:
        """Busca el precio por ISBN del libro."""
        return (
            select(PrecioModel)
            .join(PrecioModel.libro)
            .where(LibroModel.isbn == clave)
        )

    def _a_entidad(self, modelo: PrecioModel) -> Precio:
        """Convierte el modelo en entidad."""
        return Precio(
            modelo.libro.isbn, float(modelo.valor), _a_moneda(modelo.moneda)
        )

    def _cargar(
        self, sesion: Session, entidad: Precio, modelo: PrecioModel
    ) -> None:
        """Copia los datos al modelo resolviendo el libro por ISBN."""
        modelo.libro_id = _id_libro(sesion, entidad.libro_isbn)
        modelo.moneda_id = entidad.moneda.id
        modelo.valor = Decimal(str(entidad.valor))


class RepositorioStock(RepositorioBase[Stock, StockModel], IRepositorioStock):
    """Persistencia del stock: un registro por libro."""

    modelo = StockModel

    def _clave(self, entidad: Stock) -> str:
        """El stock se identifica por el ISBN del libro."""
        return entidad.libro_isbn

    def _consulta(self, clave: object) -> Select:
        """Busca el stock por ISBN del libro."""
        return (
            select(StockModel)
            .join(StockModel.libro)
            .where(LibroModel.isbn == clave)
        )

    def _a_entidad(self, modelo: StockModel) -> Stock:
        """Convierte el modelo en entidad."""
        return Stock(modelo.libro.isbn, modelo.cantidad)

    def _cargar(
        self, sesion: Session, entidad: Stock, modelo: StockModel
    ) -> None:
        """Copia los datos al modelo resolviendo el libro por ISBN."""
        modelo.libro_id = _id_libro(sesion, entidad.libro_isbn)
        modelo.cantidad = entidad.cantidad

    def leer_por_libro(self, libro_isbn: str) -> Optional[Stock]:
        """Devuelve el stock del libro o None."""
        return self.leer_por_id(libro_isbn)


class RepositorioCotizacionDolar(
    RepositorioBase[CotizacionDolar, CotizacionDolarModel],
    IRepositorioCotizacionDolar,
):
    """Persistencia del histórico de cotizaciones (clave: tipo y fecha)."""

    modelo = CotizacionDolarModel

    def _clave(self, entidad: CotizacionDolar) -> tuple[int, date]:
        """La cotización se identifica por tipo y fecha."""
        return entidad.tipo_cotizacion.id, entidad.fecha

    def _consulta(self, clave: object) -> Select:
        """Busca la cotización por (tipo_id, fecha)."""
        tipo_id, fecha = clave
        return select(CotizacionDolarModel).where(
            CotizacionDolarModel.tipo_cotizacion_id == tipo_id,
            CotizacionDolarModel.fecha == fecha,
        )

    def _a_entidad(self, modelo: CotizacionDolarModel) -> CotizacionDolar:
        """Convierte el modelo en entidad."""
        return CotizacionDolar(
            _a_tipo_cotizacion(modelo.tipo_cotizacion),
            modelo.fecha,
            float(modelo.valor),
        )

    def _cargar(
        self,
        sesion: Session,
        entidad: CotizacionDolar,
        modelo: CotizacionDolarModel,
    ) -> None:
        """Copia los datos de la entidad al modelo."""
        modelo.tipo_cotizacion_id = entidad.tipo_cotizacion.id
        modelo.fecha = entidad.fecha
        modelo.valor = Decimal(str(entidad.valor))

    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: date
    ) -> Optional[CotizacionDolar]:
        """Devuelve la cotización de ese tipo y fecha o None."""
        return self.leer_por_id((tipo_id, fecha))

    def leer_todos(self) -> list[CotizacionDolar]:
        """Devuelve todas las cotizaciones ordenadas por fecha y tipo."""
        with self._transaccion() as sesion:
            consulta = select(CotizacionDolarModel).order_by(
                CotizacionDolarModel.fecha,
                CotizacionDolarModel.tipo_cotizacion_id,
            )
            return [self._a_entidad(m) for m in sesion.scalars(consulta)]

    def leer_historico_por_tipo(self, tipo_id: int) -> list[CotizacionDolar]:
        """Devuelve las cotizaciones de un tipo ordenadas por fecha."""
        with self._transaccion() as sesion:
            consulta = (
                select(CotizacionDolarModel)
                .where(CotizacionDolarModel.tipo_cotizacion_id == tipo_id)
                .order_by(CotizacionDolarModel.fecha)
            )
            return [self._a_entidad(m) for m in sesion.scalars(consulta)]

    def eliminar(self, tipo_id: int, fecha: date) -> bool:
        """Elimina la cotización de ese tipo y fecha."""
        return super().eliminar((tipo_id, fecha))
