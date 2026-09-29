from book_manager.preload_data.preload_data import (
  RUTA_CSV,
  cargar_datos_desde_csv,
  crear_archivos_csv,
  guardar_datos_en_csv,
)
from book_manager.repositories.repositories import (
  RepositorioCotizacionDolar,
  RepositorioEditorial,
  RepositorioGenero,
  RepositorioLibro,
  RepositorioMoneda,
  RepositorioPrecio,
  RepositorioStock,
  RepositorioTipoCotizacion,
)
from book_manager.services.services import (
  ServicioCotizacionDolar,
  ServicioEditorial,
  ServicioGenero,
  ServicioLibro,
  ServicioMoneda,
  ServicioPrecio,
  ServicioStock,
  ServicioTipoCotizacion,
)
from book_manager.ui.console import ConsoleUI


def main(import_default_data: bool = True) -> None:
  """Punto de entrada de Book Manager.

  Construye los repositorios y servicios, inyecta las dependencias,
  opcionalmente precarga los datos de migración y ejecuta la consola.
  Con datos precargados, cada operación se persiste en los mismos CSV.

  Args:
    import_default_data: Si es True carga y persiste en migrations/csv.
  """
  repo_genero = RepositorioGenero()
  repo_editorial = RepositorioEditorial()
  repo_moneda = RepositorioMoneda()
  repo_tipo_cotizacion = RepositorioTipoCotizacion()
  repo_libro = RepositorioLibro()
  repo_precio = RepositorioPrecio()
  repo_stock = RepositorioStock()
  repo_cotizacion = RepositorioCotizacionDolar()

  svc_genero = ServicioGenero(repo_genero, repo_libro)
  svc_editorial = ServicioEditorial(repo_editorial, repo_libro)
  svc_moneda = ServicioMoneda(repo_moneda, repo_precio)
  svc_tipo_cotizacion = ServicioTipoCotizacion(
    repo_tipo_cotizacion, repo_cotizacion
  )
  svc_libro = ServicioLibro(
    repo_libro, repo_editorial, repo_genero, repo_precio, repo_stock
  )
  svc_precio = ServicioPrecio(repo_precio, repo_libro, repo_moneda)
  svc_stock = ServicioStock(repo_stock, repo_libro)
  svc_cotizacion = ServicioCotizacionDolar(
    repo_cotizacion, repo_tipo_cotizacion
  )

  if import_default_data:
    crear_archivos_csv(RUTA_CSV)
    cargar_datos_desde_csv(
      RUTA_CSV,
      svc_genero,
      svc_editorial,
      svc_moneda,
      svc_tipo_cotizacion,
      svc_libro,
      svc_precio,
      svc_stock,
      svc_cotizacion,
    )
    print(f"[INFO] Datos iniciales precargados desde {RUTA_CSV}.")

  servicios = (
    svc_genero,
    svc_editorial,
    svc_moneda,
    svc_tipo_cotizacion,
    svc_libro,
    svc_precio,
    svc_stock,
    svc_cotizacion,
  )
  guardar = (
    (lambda: guardar_datos_en_csv(RUTA_CSV, *servicios))
    if import_default_data else (lambda: None)
  )
  ConsoleUI(*servicios, guardar=guardar).iniciar()


if __name__ == "__main__":
  main()
