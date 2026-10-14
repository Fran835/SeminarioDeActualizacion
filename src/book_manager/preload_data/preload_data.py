import csv
from pathlib import Path

RUTA_CSV = Path(__file__).resolve().parent.parent / "migrations" / "csv"

DATOS_INICIALES: dict[str, tuple[list[str], list[list[object]]]] = {
  "generos.csv": (
    ["id", "nombre"],
    [
      [1, "Desarrollo Personal"], [2, "Psicología"],
      [3, "Ciencia Ficción"], [4, "Ensayo"], [5, "Fantasía"],
      [6, "Misterio"], [7, "Historia"], [8, "Filosofía"],
      [9, "Tecnología"], [10, "Novela Clásica"],
    ],
  ),
  "editoriales.csv": (
    ["id", "nombre", "contacto"],
    [
      [1, "Paidós", "contacto@paidos.com"],
      [2, "Editorial Planeta", "contacto@planeta.com"],
      [3, "Sudamericana", "info@sudamericana.com"],
      [4, "Siruela", "ediciones@siruela.com"],
      [5, "Siglo XXI", "ventas@siglo21.com"],
      [6, "Debate", "contacto@debate.com"],
      [7, "SM", "sm@ediciones-sm.com"],
      [8, "Urano", "urano@edicionesurano.com"],
      [9, "Anagrama", "info@anagrama.com"],
      [10, "Alianza", "alianza@alianza.com"],
    ],
  ),
  "monedas.csv": (
    ["id", "codigo", "simbolo"],
    [
      [1, "ARS", "$"], [2, "USD", "U$S"], [3, "EUR", "€"],
      [4, "GBP", "£"], [5, "BRL", "R$"], [6, "CLP", "CLP$"],
      [7, "UYU", "$U"], [8, "MXN", "MX$"], [9, "JPY", "¥"],
      [10, "CAD", "C$"],
    ],
  ),
  "tipos_cotizacion.csv": (
    ["id", "nombre"],
    [
      [1, "Oficial"], [2, "Blue"], [3, "MEP"], [4, "CCL"],
      [5, "Tarjeta"], [6, "Mayorista"], [7, "Minorista"],
      [8, "Cripto"], [9, "Solidario"], [10, "Turista"],
    ],
  ),
  "libros.csv": (
    ["isbn", "titulo", "autor", "editorial_id", "genero_id"],
    [
      ["9789870000001", "Hábitos atómicos", "James Clear", 1, 1],
      ["9789870000002", "Pensar rápido, pensar despacio",
       "Daniel Kahneman", 6, 2],
      ["9789870000003", "Flores para Algernon", "Daniel Keyes", 7, 3],
      ["9789870000004", "El elogio de la sombra",
       "Jun'ichirō Tanizaki", 4, 4],
      ["9789870000005", "Padre rico, padre pobre",
       "Robert Kiyosaki", 2, 1],
      ["9789870000006", "La llamada del coraje", "Ryan Holiday", 2, 8],
      ["9789870000007", "Céntrate", "Cal Newport", 1, 9],
      ["9789870000008", "Tus zonas erróneas", "Wayne Dyer", 8, 2],
      ["9789870000009", "Fahrenheit 451", "Ray Bradbury", 3, 3],
      ["9789870000010", "El Aleph", "Jorge Luis Borges", 3, 5],
    ],
  ),
  "precios.csv": (
    ["libro_isbn", "valor", "moneda_id"],
    [
      ["9789870000001", 15000.0, 1], ["9789870000002", 18.5, 2],
      ["9789870000003", 12000.0, 1], ["9789870000004", 15.0, 2],
      ["9789870000005", 14000.0, 1], ["9789870000006", 13500.0, 1],
      ["9789870000007", 16000.0, 1], ["9789870000008", 11000.0, 1],
      ["9789870000009", 14.0, 2], ["9789870000010", 9000.0, 1],
    ],
  ),
  "stocks.csv": (
    ["libro_isbn", "cantidad"],
    [
      ["9789870000001", 50], ["9789870000002", 20],
      ["9789870000003", 15], ["9789870000004", 10],
      ["9789870000005", 60], ["9789870000006", 25],
      ["9789870000007", 30], ["9789870000008", 40],
      ["9789870000009", 12], ["9789870000010", 8],
    ],
  ),
  "cotizaciones_dolar.csv": (
    ["tipo_cotizacion_id", "fecha", "valor"],
    [
      [1, "2026-09-21", 1000.50], [2, "2026-09-21", 1300.00],
      [3, "2026-09-21", 1250.75], [4, "2026-09-21", 1280.20],
      [5, "2026-09-21", 1600.80], [1, "2026-09-22", 1001.00],
      [2, "2026-09-22", 1295.00], [3, "2026-09-22", 1248.50],
      [4, "2026-09-22", 1275.00], [5, "2026-09-22", 1601.60],
    ],
  ),
}


def crear_archivos_csv(
  ruta_csv: Path = RUTA_CSV, sobrescribir: bool = False
) -> list[Path]:
  """Genera los archivos CSV de migración con los datos iniciales.

  Args:
    ruta_csv: Carpeta donde se escriben los archivos.
    sobrescribir: Si es True reemplaza los archivos existentes.

  Returns:
    list[Path]: Rutas de los archivos CSV disponibles.
  """
  ruta_csv.mkdir(parents=True, exist_ok=True)
  archivos: list[Path] = []
  for nombre_archivo, (cabeceras, filas) in DATOS_INICIALES.items():
    ruta_archivo = ruta_csv / nombre_archivo
    if sobrescribir or not ruta_archivo.exists():
      escribir_csv(ruta_archivo, cabeceras, filas)
    archivos.append(ruta_archivo)
  return archivos


def escribir_csv(
  ruta_archivo: Path, cabeceras: list[str], filas: list[list[object]]
) -> None:
  """Escribe un archivo CSV con cabecera, reemplazando su contenido.

  Args:
    ruta_archivo: Ruta del archivo a escribir.
    cabeceras: Nombres de las columnas.
    filas: Registros a escribir, uno por fila.
  """
  with open(ruta_archivo, "w", newline="", encoding="utf-8") as archivo:
    escritor = csv.writer(archivo)
    escritor.writerow(cabeceras)
    escritor.writerows(filas)


if __name__ == "__main__":
  for ruta in crear_archivos_csv(sobrescribir=True):
    print(f"[CSV] Archivo generado: {ruta}")
