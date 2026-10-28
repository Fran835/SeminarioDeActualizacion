"""Ejecución del scraper y generación automática de alertas."""

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from book_manager.services.comparacion import (
  ResultadoAlertas,
  ServicioComparacion,
)


@dataclass(frozen=True)
class ResultadoScraping:
  """Resultado de una ejecución completa del scraping.

  Args:
    ruta_jsonl: JSONL generado por el spider.
    total_extracciones: Cantidad de fichas extraídas.
    alertas: Resultado de la comparación y de los CSV de alertas.
    salida: Últimas líneas de la salida estándar y de errores del scraper.
  """

  ruta_jsonl: Path
  total_extracciones: int
  alertas: ResultadoAlertas
  salida: str


class ServicioScraping:
  """Ejecuta el spider y genera las alertas en cada ejecución.

  Args:
    comparacion: Servicio que compara los precios y genera los CSV.
    raiz_repo: Raíz del repositorio; por defecto se deduce del módulo.
    timeout: Segundos máximos de espera del scraper.
  """

  def __init__(
    self,
    comparacion: ServicioComparacion,
    raiz_repo: Optional[Path] = None,
    timeout: int = 1800,
  ) -> None:
    self._comparacion = comparacion
    self._raiz_repo = raiz_repo or Path(__file__).resolve().parents[3]
    self._timeout = timeout

  def ejecutar(
    self, titulos: Optional[str] = None, umbral: float = 10.0
  ) -> ResultadoScraping:
    """Ejecuta el scraper y genera los CSV de comparación y alertas.

    Args:
      titulos: Títulos separados por '|'. Si es None, se usa el catálogo.
      umbral: Diferencia porcentual mínima para considerar una alerta.

    Returns:
      ResultadoScraping: Rutas, totales y salida del scraper.

    Raises:
      ValueError: Si el umbral es negativo o el scraper falla.
    """
    if umbral < 0:
      raise ValueError("El umbral de diferencia no puede ser negativo.")
    carpeta = self._comparacion.carpeta_reportes
    carpeta.mkdir(parents=True, exist_ok=True)
    antes = set(carpeta.glob("scraping_*.jsonl"))
    comando = [sys.executable, "-m", "book_manager.scraper.runner"]
    if titulos:
      comando.append(titulos)
    entorno = os.environ.copy()
    ruta_src = str(self._raiz_repo / "src")
    rutas = [ruta_src, entorno.get("PYTHONPATH")]
    entorno["PYTHONPATH"] = os.pathsep.join(
      [ruta for ruta in rutas if ruta]
    )
    try:
      proceso = subprocess.run(
        comando,
        cwd=str(self._raiz_repo / "src"),
        env=entorno,
        capture_output=True,
        text=True,
        timeout=self._timeout,
      )
    except subprocess.TimeoutExpired as error:
      raise ValueError(
        f"El scraper superó el tiempo máximo de {self._timeout} segundos."
      ) from error
    salida = "\n".join(
      parte for parte in (proceso.stdout, proceso.stderr) if parte
    ).strip()
    if proceso.returncode != 0:
      raise ValueError(
        "El scraper terminó con errores:\n"
        f"{salida[-4000:]}"
      )
    despues = set(carpeta.glob("scraping_*.jsonl"))
    nuevos = sorted(
      despues - antes,
      key=lambda ruta: ruta.stat().st_mtime,
    )
    if not nuevos:
      raise ValueError(
        "El scraper no generó un archivo JSONL nuevo. Revisá la salida:\n"
        f"{salida[-4000:]}"
      )
    ruta_jsonl = nuevos[-1]
    total = self._comparacion.contar_extracciones(ruta_jsonl)
    alertas = self._comparacion.generar_alertas(umbral, ruta_jsonl)
    return ResultadoScraping(
      ruta_jsonl=ruta_jsonl,
      total_extracciones=total,
      alertas=alertas,
      salida=salida[-6000:],
    )
