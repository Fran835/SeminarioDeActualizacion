# CHANGELOG

## Sprint 2

[Ejercicio 6]
- Se reemplazan los repositorios en memoria por repositorios con SQLAlchemy.
- RepositorioBase genérico con CRUD transaccional y conversión entidad/modelo.
- La clave de búsqueda se toma de la propiedad clave de EntidadBase.
- Precio: un precio por libro identificado por ISBN; al modificarlo puede cambiar la moneda.
- Los errores de integridad de la base se traducen a ValueError.
- main.py crea las tablas, migra opcionalmente los CSV y arma los servicios con sus dependencias.

[Ejercicio 5]
- Se crea migrations/migrations.py con la función migrar_datos().
- Lectura de los 8 CSV del Sprint 1 respetando el orden de dependencias.
- Mapeo de columnas CSV -> tabla: libro_isbn se resuelve a libro_id con una subconsulta por ISBN.
- Los ids que no vienen en el CSV (libros, precios, stocks, cotizaciones) los genera la base.
- Validación de encabezados: si falta una columna la migración se detiene con un mensaje claro.
- Generación de un archivo .sql de INSERTs por tabla en migrations/sql.
- Ejecución en una única transacción (todo o nada), re-ejecutable y con escape de comillas.

## Sprint 1

## [Ejercicio 07]

- Archivo main.py con la inyección de dependencias entre capas.
- Parámetro import_default_data para precargar los datos CSV.
- Conexión de la consola con la persistencia en migrations/csv.

## [Ejercicio 06]

- Clase ConsoleUI con menú principal y submenús por entidad.
- Operaciones listar, buscar, crear, modificar y eliminar para las 8 entidades, más ingreso/retiro de stock e histórico de cotizaciones.
- Validación de ingresos por teclado y manejo de errores de negocio.
- Guardado automático de los datos luego de cada operación exitosa.

## [Ejercicio 05]

- Módulo preload_data.py con la generación de los CSV de migración.
- Archivos CSV con 10 registros por entidad en migrations/csv.
- Carga de los CSV respetando el orden de dependencias entre entidades.
- Persistencia: guardar_datos_en_csv vuelca el estado actual a los CSV.

## [Ejercicio 04]

- Servicio genérico ServicioCrud con hooks de validación.
- Validación de relaciones: editorial y género del libro, libro y moneda del precio, libro del stock y tipo de la cotización.
- Integridad referencial al eliminar entidades en uso.
- Operaciones de ingreso y retiro de stock.

## [Ejercicio 03]

- Interfaces IRepositorio, IRepositorioStock e IRepositorioCotizacionDolar según el código base.
- Repositorio genérico en memoria RepositorioMemoria indexado por clave.
- Repositorios concretos con CRUD completo para las 8 entidades.

## [Ejercicio 02]

- Clase abstracta EntidadBase con la clave de cada entidad.
- Entidades Libro, Genero, Editorial, Moneda, TipoCotizacion, Precio, Stock y CotizacionDolar con atributos encapsulados.
- Validaciones en setters (textos vacíos, ISBN, código ISO, valores negativos) aplicadas también desde los constructores.

## [Ejercicio 01]

- Configuración del repositorio y creación de la rama Sprint_1.
- Creación de la estructura de directorios src/book_manager.
- Creación de README.md con objetivo e introducción del Sprint 1.
- Creación de requirements.txt, .gitignore y CHANGELOG.md.
