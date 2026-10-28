"""Punto de entrada de Book Manager con persistencia en base de datos."""

from pathlib import Path

from dotenv import load_dotenv

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import migrar_datos
from book_manager.models.models import Base
from book_manager.repositories.repositories import (
  RepositorioAuditoria,
  RepositorioCotizacionDolar,
  RepositorioEditorial,
  RepositorioGenero,
  RepositorioLibro,
  RepositorioMoneda,
  RepositorioPrecio,
  RepositorioStock,
  RepositorioTipoCotizacion,
)
from book_manager.services.auditoria import (
  ServicioAuditoria,
  configurar_auditoria,
)
from book_manager.services.comparacion import ServicioComparacion
from book_manager.services.reportes import ServicioReportes
from book_manager.services.scraping import ServicioScraping
from book_manager.services.services import (
  ServicioCotizacionDolar,
  ServicioEditorial,
  ServicioGenero,
  ServicioLibro,
  ServicioListaPrecios,
  ServicioMoneda,
  ServicioPrecio,
  ServicioStock,
  ServicioTipoCotizacion,
)
from book_manager.ui.console import ConsoleUI

RUTA_PAQUETE: Path = Path(__file__).resolve().parent
RUTA_MIGRACIONES: Path = RUTA_PAQUETE / "migrations"
RUTA_EXPORTACIONES: Path = RUTA_PAQUETE / "exports"
RUTA_REPORTES: Path = RUTA_PAQUETE / "reportes"
RUTA_ENV: Path = RUTA_PAQUETE.parents[1] / ".env"


def inicializar_base(conexion: ConexionDB, importar_datos: bool) -> None:
  """Crea las tablas y, si se solicita, migra los datos de los CSV."""
  conexion.crear_tablas(Base)
  if importar_datos:
    migrar_datos(
      str(RUTA_MIGRACIONES / "csv"),
      str(RUTA_MIGRACIONES / "sql"),
      conexion,
    )


def crear_aplicacion(import_default_data: bool = False) -> ConsoleUI:
  """Inicializa la base, arma las capas del sistema y devuelve la consola.

  Args:
    import_default_data (bool): Si es True, vuelve a cargar los datos
      iniciales desde los CSV (reemplaza los datos existentes).

  Returns:
    ConsoleUI: La consola configurada, sin iniciar el bucle de menú.
  """
  load_dotenv(RUTA_ENV)
  conexion = ConexionDB()
  inicializar_base(conexion, import_default_data)

  repo_genero = RepositorioGenero(conexion)
  repo_editorial = RepositorioEditorial(conexion)
  repo_moneda = RepositorioMoneda(conexion)
  repo_tipo_cot = RepositorioTipoCotizacion(conexion)
  repo_libro = RepositorioLibro(conexion)
  repo_precio = RepositorioPrecio(conexion)
  repo_stock = RepositorioStock(conexion)
  repo_cotizacion = RepositorioCotizacionDolar(conexion)
  repo_auditoria = RepositorioAuditoria(conexion)

  servicio_auditoria = ServicioAuditoria(repo_auditoria)
  configurar_auditoria(servicio_auditoria)

  servicio_comparacion = ServicioComparacion(
    repo_libro,
    repo_precio,
    repo_cotizacion,
    repo_tipo_cot,
    RUTA_REPORTES,
  )
  servicio_scraping = ServicioScraping(
    servicio_comparacion,
    RUTA_PAQUETE.parents[1],
  )
  servicio_reportes = ServicioReportes(
    servicio_comparacion,
    RUTA_REPORTES,
  )

  return ConsoleUI(
    ServicioGenero(repo_genero, repo_libro),
    ServicioEditorial(repo_editorial, repo_libro),
    ServicioMoneda(repo_moneda, repo_precio),
    ServicioTipoCotizacion(repo_tipo_cot, repo_cotizacion),
    ServicioLibro(
      repo_libro, repo_editorial, repo_genero, repo_precio, repo_stock
    ),
    ServicioPrecio(repo_precio, repo_libro, repo_moneda),
    ServicioStock(repo_stock, repo_libro),
    ServicioCotizacionDolar(repo_cotizacion, repo_tipo_cot),
    ServicioListaPrecios(
      repo_precio,
      repo_cotizacion,
      repo_tipo_cot,
      RUTA_EXPORTACIONES,
    ),
    servicio_scraping,
    servicio_reportes,
    servicio_auditoria,
  )


def main(import_default_data: bool = False) -> None:
  """Inicializa la aplicación y lanza la consola interactiva.

  Args:
    import_default_data (bool): Si es True, vuelve a cargar los datos
      iniciales desde los CSV.
  """
  ui = crear_aplicacion(import_default_data)
  ui.iniciar()


if __name__ == "__main__":
  main()
