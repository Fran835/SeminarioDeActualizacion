"""Migración de los datos del Sprint 1 (archivos CSV) a la base relacional."""

import csv
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import NamedTuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from book_manager.database.connection import ConexionDB


class ExpresionSQL(str):
  """Fragmento SQL que se escribe tal cual, sin comillas."""


Conversor = Callable[[str], object]


class Columna(NamedTuple):
  """Relaciona una columna del CSV con su columna en la tabla destino."""

  origen: str
  destino: str
  convertir: Conversor


class TablaMigracion(NamedTuple):
  """Describe cómo migrar un archivo CSV a su tabla destino."""

  archivo_csv: str
  tabla: str
  columnas: list[Columna]


def formatear_valor(valor: object) -> str:
  """Convierte un valor de Python en un literal SQL seguro."""
  if valor is None:
    return "NULL"
  if isinstance(valor, ExpresionSQL):
    return str(valor)
  if isinstance(valor, (int, float)):
    return repr(valor)
  texto_escapado = str(valor).replace("'", "''")
  return f"'{texto_escapado}'"


def _texto(valor: str) -> str:
  """Normaliza un valor de texto quitando espacios sobrantes."""
  return valor.strip()


def _fecha(valor: str) -> str:
  """Valida que el valor sea una fecha ISO (AAAA-MM-DD) y la devuelve."""
  return date.fromisoformat(valor.strip()).isoformat()


def _libro_por_isbn(valor: str) -> ExpresionSQL:
  """Resuelve el id del libro a partir de su ISBN con una subconsulta."""
  isbn = formatear_valor(valor.strip())
  return ExpresionSQL(f"(SELECT id FROM libros WHERE isbn = {isbn})")


def _misma(nombre: str, convertir: Conversor) -> Columna:
  """Columna que conserva el mismo nombre en el CSV y en la tabla."""
  return Columna(nombre, nombre, convertir)


TABLAS: list[TablaMigracion] = [
  TablaMigracion(
    "generos.csv",
    "generos",
    [_misma("id", int), _misma("nombre", _texto)],
  ),
  TablaMigracion(
    "editoriales.csv",
    "editoriales",
    [
      _misma("id", int),
      _misma("nombre", _texto),
      _misma("contacto", _texto),
    ],
  ),
  TablaMigracion(
    "monedas.csv",
    "monedas",
    [
      _misma("id", int),
      _misma("codigo", _texto),
      _misma("simbolo", _texto),
    ],
  ),
  TablaMigracion(
    "tipos_cotizacion.csv",
    "tipos_cotizacion",
    [_misma("id", int), _misma("nombre", _texto)],
  ),
  TablaMigracion(
    "libros.csv",
    "libros",
    [
      _misma("isbn", _texto),
      _misma("titulo", _texto),
      _misma("autor", _texto),
      _misma("editorial_id", int),
      _misma("genero_id", int),
    ],
  ),
  TablaMigracion(
    "precios.csv",
    "precios",
    [
      Columna("libro_isbn", "libro_id", _libro_por_isbn),
      _misma("valor", float),
      _misma("moneda_id", int),
    ],
  ),
  TablaMigracion(
    "stocks.csv",
    "stocks",
    [
      Columna("libro_isbn", "libro_id", _libro_por_isbn),
      _misma("cantidad", int),
    ],
  ),
  TablaMigracion(
    "cotizaciones_dolar.csv",
    "cotizaciones_dolar",
    [
      _misma("tipo_cotizacion_id", int),
      _misma("fecha", _fecha),
      _misma("valor", float),
    ],
  ),
]


def leer_csv(ruta: Path, columnas_requeridas: list[str]) -> list[dict]:
  """Lee un CSV validando que tenga todas las columnas requeridas."""
  with ruta.open(newline="", encoding="utf-8") as archivo:
    lector = csv.DictReader(archivo)
    encabezados = lector.fieldnames or []
    faltantes = [c for c in columnas_requeridas if c not in encabezados]
    if faltantes:
      raise ValueError(
        f"{ruta.name}: faltan las columnas {faltantes}. "
        f"Encabezados encontrados: {encabezados}"
      )
    return list(lector)


def generar_inserts(
  tabla: TablaMigracion, filas: list[dict[str, str]]
) -> list[str]:
  """Genera una sentencia INSERT por cada fila del CSV."""
  nombres = ", ".join(columna.destino for columna in tabla.columnas)
  sentencias = []
  for fila in filas:
    valores = []
    for columna in tabla.columnas:
      crudo = fila[columna.origen].strip()
      valores.append(None if crudo == "" else columna.convertir(crudo))
    literales = ", ".join(formatear_valor(valor) for valor in valores)
    sentencias.append(
      f"INSERT INTO {tabla.tabla} ({nombres}) VALUES ({literales});"
    )
  return sentencias


def escribir_sql(
  ruta: Path, archivo_origen: str, sentencias: list[str]
) -> None:
  """Guarda las sentencias en un archivo .sql con un encabezado."""
  encabezado = [
    f"-- Migración generada automáticamente desde {archivo_origen}",
    f"-- Registros: {len(sentencias)}",
    "",
  ]
  ruta.write_text("\n".join(encabezado + sentencias) + "\n", "utf-8")


def _vaciar_tablas(sesion: Session) -> None:
  """Borra los datos existentes en orden inverso a las dependencias."""
  for tabla in reversed(TABLAS):
    sesion.execute(text(f"DELETE FROM {tabla.tabla}"))


def _sincronizar_secuencias(sesion: Session) -> None:
  """En PostgreSQL ajusta las secuencias de id tras insertar ids fijos."""
  for tabla in TABLAS:
    sesion.execute(text(
      f"SELECT setval(pg_get_serial_sequence('{tabla.tabla}', 'id'), "
      f"COALESCE((SELECT MAX(id) FROM {tabla.tabla}), 1))"
    ))


def leer_sentencias_sql(ruta: Path) -> list[str]:
  """Lee las sentencias de un archivo .sql, omitiendo los comentarios.

  Args:
    ruta (Path): Archivo .sql con una sentencia por línea.

  Returns:
    list[str]: Sentencias SQL listas para ejecutar.
  """
  lineas = ruta.read_text(encoding="utf-8").splitlines()
  return [
    linea.strip() for linea in lineas
    if linea.strip() and not linea.strip().startswith("--")
  ]


def cargar_datos_desde_sql(
  ruta_sql: str, conexion: ConexionDB | None = None
) -> dict[str, int]:
  """Carga en la base de datos los datos de archivos .sql.

  Recibe un archivo .sql o una carpeta. Con una carpeta, vacía las
  tablas del sistema y ejecuta todos sus archivos en orden alfabético
  (01_generos.sql, 02_editoriales.sql, ...), que respeta las
  dependencias entre tablas. Todo se ejecuta en una única transacción:
  si una sentencia falla, no se carga nada.

  Args:
    ruta_sql (str): Archivo .sql o carpeta con archivos .sql.
    conexion (ConexionDB | None): Conexión a utilizar. Por defecto se
      usa la instancia única de ConexionDB.

  Returns:
    dict[str, int]: Cantidad de sentencias ejecutadas por tabla.

  Raises:
    FileNotFoundError: Si la ruta no existe o no contiene archivos .sql.
  """
  ruta = Path(ruta_sql)
  if not ruta.exists():
    raise FileNotFoundError(f"No existe la ruta {ruta}.")
  archivos = sorted(ruta.glob("*.sql")) if ruta.is_dir() else [ruta]
  if not archivos:
    raise FileNotFoundError(f"No hay archivos .sql en {ruta}.")
  conexion = conexion or ConexionDB()
  cargadas: dict[str, int] = {}
  with conexion.transaccion() as sesion:
    if ruta.is_dir():
      _vaciar_tablas(sesion)
    conexion_sql = sesion.connection()
    for archivo in archivos:
      sentencias = leer_sentencias_sql(archivo)
      for sentencia in sentencias:
        conexion_sql.exec_driver_sql(sentencia)
      tabla = archivo.stem.split("_", 1)[-1]
      cargadas[tabla] = len(sentencias)
    if conexion.motor == "postgresql":
      _sincronizar_secuencias(sesion)
  return cargadas


def migrar_datos(
  carpeta_csvs: str,
  carpeta_sqls: str,
  conexion: ConexionDB | None = None,
) -> dict[str, int]:
  """Función encargada de la migración de datos de csv a sql.

  Se encarga de leer los archivos csv y crear los archivos sql
  para la inserción en la base de datos. Luego los carga con
  cargar_datos_desde_sql dentro de una única transacción: si alguna
  sentencia falla, no se migra nada.

  Args:
    carpeta_csvs (str): Carpeta donde se encuentran los archivos csv
      de origen.
    carpeta_sqls (str): Carpeta donde se deben guardar los archivos sql
      generados.
    conexion (ConexionDB | None): Conexión a utilizar. Por defecto se
      usa la instancia única de ConexionDB.

  Returns:
    dict[str, int]: Cantidad de registros migrados por tabla.
  """
  origen = Path(carpeta_csvs)
  destino = Path(carpeta_sqls)
  destino.mkdir(parents=True, exist_ok=True)
  for numero, tabla in enumerate(TABLAS, start=1):
    requeridas = [columna.origen for columna in tabla.columnas]
    filas = leer_csv(origen / tabla.archivo_csv, requeridas)
    sentencias = generar_inserts(tabla, filas)
    archivo_sql = destino / f"{numero:02d}_{tabla.tabla}.sql"
    escribir_sql(archivo_sql, tabla.archivo_csv, sentencias)
  return cargar_datos_desde_sql(str(destino), conexion)
