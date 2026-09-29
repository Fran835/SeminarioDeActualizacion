# Book Manager

## Sprint 1

### Objetivo

Aplicar los conocimientos de programación orientada a objetos y de
almacenamiento de datos en archivos para su persistencia, construyendo la
base de un sistema de gestión de inventario de libros.

### Introducción y contexto

Una librería con venta al público necesita modernizar su sistema de gestión
de inventario. Debido a la fluctuación en los costos de importación, el
sistema debe gestionar precios en diferentes monedas y seguir la cotización
del dólar para actualizar sus valores.

En este sprint se desarrolla una aplicación de consola (CLI) en Python que
permite administrar, mediante operaciones CRUD, las entidades del dominio:
Libro, Género, Editorial, Moneda, Tipo de Cotización, Precio, Stock y
Cotización del Dólar. Los datos iniciales se importan desde archivos CSV.

### Arquitectura

- `entities`: clases del dominio con encapsulamiento y validaciones.
- `repositories`: persistencia de las entidades (CRUD).
- `services`: reglas de negocio e integridad referencial.
- `preload_data`: generación e importación de los CSV de `migrations/csv`.
- `ui`: interfaz de consola.
- `main.py`: punto de entrada e inyección de dependencias.

### Ejecución

```bash
cd src
python -m book_manager.main
```
