# CHANGELOG

[Ejercicio 2]
- Se crea la clase ConexionDB en database/connection.py con SQLAlchemy.
- La URL de conexión se lee de la variable DATABASE_URL (.env / secret de Colab).
- Se implementa Singleton, sesiones transaccionales y prueba de conexión.
- Se habilitan las claves foráneas en SQLite.
- Se agregan SQLAlchemy, python-dotenv y psycopg2-binary a requirements.txt.

[Ejercicio 1]
- Sprint 2: se crea la rama Sprint_2 a partir de la rama Sprint_1.
- Se configura Git en Colab usando el secret GITHUB_TOKEN.
- Se crea la estructura de directorios del proyecto (database, entities, models, preload_data, repositories, services, migrations, ui).
- Se agrega .gitignore para excluir .env y archivos generados.
- Se actualiza el README.md con el objetivo y contexto del Sprint 2.

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
