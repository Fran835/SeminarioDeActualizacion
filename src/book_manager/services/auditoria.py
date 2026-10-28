"""Auditoría de operaciones del sistema y decorador @auditar."""

import functools
from collections.abc import Callable
from typing import Any, Optional, TypeVar, cast

from book_manager.entities.entities import Auditoria
from book_manager.repositories.repositories import RepositorioAuditoria

F = TypeVar("F", bound=Callable[..., Any])
_servicio_global: Optional["ServicioAuditoria"] = None


class ServicioAuditoria:
  """Registra y consulta el historial de operaciones auditadas.

  Args:
    repositorio: Repositorio de auditoría.
  """

  def __init__(self, repositorio: RepositorioAuditoria) -> None:
    self._repositorio = repositorio

  def registrar(self, accion: str, detalles: str = "") -> Auditoria:
    """Registra una operación en la auditoría.

    Args:
      accion: Nombre de la operación.
      detalles: Información adicional de la operación.

    Returns:
      Auditoria: El registro creado.
    """
    return self._repositorio.registrar(accion, detalles)

  def historial(self, limite: int = 50) -> list[Auditoria]:
    """Devuelve las últimas operaciones registradas.

    Args:
      limite: Cantidad máxima de registros.

    Returns:
      list[Auditoria]: Registros, del más nuevo al más viejo.
    """
    return self._repositorio.leer_ultimos(limite)

  def leer_todos(self) -> list[Auditoria]:
    """Devuelve todo el historial de auditoría."""
    return self._repositorio.leer_todos()


def configurar_auditoria(servicio: ServicioAuditoria) -> None:
  """Define el servicio que usan los decoradores @auditar.

  Args:
    servicio: Servicio de auditoría configurado.
  """
  global _servicio_global
  _servicio_global = servicio


def obtener_servicio_auditoria() -> Optional[ServicioAuditoria]:
  """Devuelve el servicio de auditoría configurado, si existe."""
  return _servicio_global


def _resumir(valor: Any, limite: int = 240) -> str:
  """Convierte un valor en un texto corto para la columna detalles."""
  texto = repr(valor)
  if len(texto) <= limite:
    return texto
  return f"{texto[:limite]}..."


def _detallar(
  etiqueta: str,
  args: tuple[Any, ...],
  kwargs: dict[str, Any],
  resultado: Any = None,
) -> str:
  """Arma el texto de detalles de una operación auditada."""
  partes: list[str] = []
  if etiqueta:
    partes.append(etiqueta)
  if args:
    partes.append(type(args[0]).__name__)
    argumentos = args[1:]
    if argumentos:
      partes.append(
        "args=" + ", ".join(_resumir(argumento) for argumento in argumentos)
      )
  if kwargs:
    partes.append(
      "kwargs=" + ", ".join(
        f"{clave}={_resumir(valor)}" for clave, valor in kwargs.items()
      )
    )
  if resultado is not None:
    partes.append(f"resultado={_resumir(resultado)}")
  return " | ".join(partes)[:1000] or "sin detalles"


def _registrar(accion: str, detalles: str) -> None:
  """Registra sin interrumpir la operación si la auditoría falla."""
  if _servicio_global is None:
    return
  try:
    _servicio_global.registrar(accion, detalles)
  except Exception as error:
    print(f"No se pudo registrar la auditoría de {accion!r}: {error}")


def auditar(accion: str, detalle: str = "") -> Callable[[F], F]:
  """Decora una operación para auditar su éxito o su error.

  Args:
    accion: Nombre de la acción que se registra.
    detalle: Texto fijo que se agrega a los detalles.

  Returns:
    Callable[[F], F]: Decorador que envuelve la operación.
  """

  def decorador(func: F) -> F:
    """Envuelve la función y registra el resultado."""

    @functools.wraps(func)
    def envoltura(*args: Any, **kwargs: Any) -> Any:
      """Ejecuta la operación y registra su resultado."""
      try:
        resultado = func(*args, **kwargs)
      except Exception as error:
        detalles = _detallar(detalle, args, kwargs)
        _registrar(
          accion,
          f"{detalles} | error={type(error).__name__}: {error}",
        )
        raise
      _registrar(accion, _detallar(detalle, args, kwargs, resultado))
      return resultado

    return cast(F, envoltura)

  return decorador
