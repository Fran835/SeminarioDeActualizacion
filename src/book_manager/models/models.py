"""Modelos ORM (tablas) del sistema Book Manager definidos con SQLAlchemy."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
  CheckConstraint,
  Date,
  DateTime,
  ForeignKey,
  Integer,
  Numeric,
  String,
  Text,
  UniqueConstraint,
)
from sqlalchemy.orm import (
  DeclarativeBase,
  Mapped,
  mapped_column,
  relationship,
)


class Base(DeclarativeBase):
  """Base declarativa de la que heredan todos los modelos."""


class GeneroModel(Base):
  """Tabla de géneros literarios."""

  __tablename__ = "generos"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  nombre: Mapped[str] = mapped_column(String(100), unique=True)

  libros: Mapped[list["LibroModel"]] = relationship(
    back_populates="genero"
  )

  def __repr__(self) -> str:
    """Representación legible del registro."""
    return f"GeneroModel(id={self.id}, nombre={self.nombre!r})"


class EditorialModel(Base):
  """Tabla de editoriales / distribuidoras."""

  __tablename__ = "editoriales"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  nombre: Mapped[str] = mapped_column(String(150), unique=True)
  contacto: Mapped[str | None] = mapped_column(String(150))

  libros: Mapped[list["LibroModel"]] = relationship(
    back_populates="editorial"
  )

  def __repr__(self) -> str:
    """Representación legible del registro."""
    return f"EditorialModel(id={self.id}, nombre={self.nombre!r})"


class MonedaModel(Base):
  """Tabla de monedas en las que se expresan los precios."""

  __tablename__ = "monedas"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  codigo: Mapped[str] = mapped_column(String(3), unique=True)
  simbolo: Mapped[str] = mapped_column(String(5))

  precios: Mapped[list["PrecioModel"]] = relationship(
    back_populates="moneda"
  )

  def __repr__(self) -> str:
    """Representación legible del registro."""
    return f"MonedaModel(id={self.id}, codigo={self.codigo!r})"


class TipoCotizacionModel(Base):
  """Tabla de tipos de cotización del dólar (Oficial, Blue, MEP...)."""

  __tablename__ = "tipos_cotizacion"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  nombre: Mapped[str] = mapped_column(String(50), unique=True)

  cotizaciones: Mapped[list["CotizacionDolarModel"]] = relationship(
    back_populates="tipo_cotizacion"
  )

  def __repr__(self) -> str:
    """Representación legible del registro."""
    return f"TipoCotizacionModel(id={self.id}, nombre={self.nombre!r})"


class LibroModel(Base):
  """Tabla del catálogo de libros."""

  __tablename__ = "libros"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  isbn: Mapped[str] = mapped_column(String(13), unique=True, index=True)
  titulo: Mapped[str] = mapped_column(String(200))
  autor: Mapped[str] = mapped_column(String(150))
  editorial_id: Mapped[int] = mapped_column(
    ForeignKey("editoriales.id", ondelete="RESTRICT")
  )
  genero_id: Mapped[int] = mapped_column(
    ForeignKey("generos.id", ondelete="RESTRICT")
  )

  editorial: Mapped["EditorialModel"] = relationship(
    back_populates="libros"
  )
  genero: Mapped["GeneroModel"] = relationship(back_populates="libros")
  precios: Mapped[list["PrecioModel"]] = relationship(
    back_populates="libro", cascade="all, delete-orphan"
  )
  stock: Mapped[Optional["StockModel"]] = relationship(
    back_populates="libro", cascade="all, delete-orphan"
  )

  def __repr__(self) -> str:
    """Representación legible del registro."""
    return (
      f"LibroModel(id={self.id}, isbn={self.isbn!r}, "
      f"titulo={self.titulo!r})"
    )


class PrecioModel(Base):
  """Tabla de precios: un libro tiene a lo sumo un precio por moneda."""

  __tablename__ = "precios"
  __table_args__ = (
    UniqueConstraint("libro_id", "moneda_id", name="uq_precio_libro"),
    CheckConstraint("valor >= 0", name="ck_precio_valor_positivo"),
  )

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  libro_id: Mapped[int] = mapped_column(
    ForeignKey("libros.id", ondelete="CASCADE")
  )
  moneda_id: Mapped[int] = mapped_column(
    ForeignKey("monedas.id", ondelete="RESTRICT")
  )
  valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))

  libro: Mapped["LibroModel"] = relationship(back_populates="precios")
  moneda: Mapped["MonedaModel"] = relationship(back_populates="precios")

  def __repr__(self) -> str:
    """Representación legible del registro."""
    return (
      f"PrecioModel(libro_id={self.libro_id}, "
      f"valor={self.valor}, moneda_id={self.moneda_id})"
    )


class StockModel(Base):
  """Tabla de stock: relación uno a uno con el libro."""

  __tablename__ = "stocks"
  __table_args__ = (
    CheckConstraint("cantidad >= 0", name="ck_stock_cantidad_positiva"),
  )

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  libro_id: Mapped[int] = mapped_column(
    ForeignKey("libros.id", ondelete="CASCADE"), unique=True
  )
  cantidad: Mapped[int] = mapped_column(Integer, default=0)

  libro: Mapped["LibroModel"] = relationship(back_populates="stock")

  def __repr__(self) -> str:
    """Representación legible del registro."""
    return (
      f"StockModel(libro_id={self.libro_id}, "
      f"cantidad={self.cantidad})"
    )


class CotizacionDolarModel(Base):
  """Tabla histórica de cotizaciones: una por tipo y fecha."""

  __tablename__ = "cotizaciones_dolar"
  __table_args__ = (
    UniqueConstraint(
      "tipo_cotizacion_id", "fecha", name="uq_cotizacion_tipo_fecha"
    ),
    CheckConstraint("valor > 0", name="ck_cotizacion_valor_positivo"),
  )

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  tipo_cotizacion_id: Mapped[int] = mapped_column(
    ForeignKey("tipos_cotizacion.id", ondelete="RESTRICT")
  )
  fecha: Mapped[date] = mapped_column(Date, index=True)
  valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))

  tipo_cotizacion: Mapped["TipoCotizacionModel"] = relationship(
    back_populates="cotizaciones"
  )

  def __repr__(self) -> str:
    """Representación legible del registro."""
    return (
      f"CotizacionDolarModel(tipo_id={self.tipo_cotizacion_id}, "
      f"fecha={self.fecha}, valor={self.valor})"
    )


class AuditoriaModel(Base):
  """Tabla de auditoría: una fila por operación auditada."""

  __tablename__ = "auditorias"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  accion: Mapped[str] = mapped_column(String(100), index=True)
  fecha: Mapped[datetime] = mapped_column(DateTime, index=True)
  detalles: Mapped[str] = mapped_column(Text, default="")

  def __repr__(self) -> str:
    """Representación legible del registro."""
    return (
      f"AuditoriaModel(id={self.id}, accion={self.accion!r}, "
      f"fecha={self.fecha!r})"
    )
