# CHANGELOG

## Sprint 2

[Ejercicio 8]
- Nuevas opciones del menú principal: obtener cotizaciones por API, lista de precios bimonetaria y exportar precios a CSV.
- Se crea ServicioListaPrecios en services.py con la lógica de conversión y exportación.
- La conversión usa el peso como puente (ARS = 1, USD = cotización vigente del tipo elegido).
- La lista bimonetaria muestra cada libro en pesos y en la moneda elegida según el tipo de cotización.
- La exportación genera exports/lista_precios.csv con el precio en pesos y en USD por cada tipo de cotización.
- main.py carga el .env con load_dotenv y crea el nuevo servicio.

[Ejercicio 7]
- Se agrega API_URL=https://dolarapi.com/v1/dolares al .env y se carga con python-dotenv.
- Se versiona .env.example con las variables necesarias; el .env real sigue fuera del repositorio.
- Nuevo método ServicioCotizacionDolar.obtener_cotizaciones(): descarga, valida y registra cotizaciones.
- Los tipos de la API se asocian a los existentes (Bolsa -> MEP, Contado con liquidación -> CCL) o se crean.
- Se registra el valor de venta en la fecha de Argentina; si ya existe para tipo y fecha, se actualiza.
- Errores de red, HTTP o formato se informan como ValueError.
- Se agrega requests a requirements.txt.
- Corrección: se versiona .env solo con API_URL, como pide la estructura; DATABASE_URL queda en el secret de Colab.
- Se elimina .env.example y se actualiza .gitignore.
- ServicioStock y ServicioListaPrecios trabajan con el objeto Libro.
- requirements.txt actualizado con versiones mínimas.

[Ejercicio 6]
- Se reemplazan los repositorios en memoria por repositorios con SQLAlchemy.
- RepositorioBase genérico con CRUD transaccional y conversión entidad/modelo.
- La clave de búsqueda se toma de la propiedad clave de EntidadBase.
- Precio: un precio por libro identificado por ISBN; al modificarlo puede cambiar la moneda.
- Los errores de integridad de la base se traducen a ValueError.
- main.py crea las tablas, migra opcionalmente los CSV y arma los servicios con sus dependencias.
- Corrección TP1: Precio y Stock tienen como atributo un objeto Libro en lugar del ISBN (relación entre clases).
- Los repositorios de precios y stock construyen el Libro con su editorial y su género.
- Estilo: indentación de 2 espacios y sin comentarios en línea.

[Ejercicio 5]
- Se crea migrations/migrations.py con la función migrar_datos().
- Lectura de los 8 CSV del Sprint 1 respetando el orden de dependencias.
- Mapeo de columnas CSV -> tabla: libro_isbn se resuelve a libro_id con una subconsulta por ISBN.
- Los ids que no vienen en el CSV (libros, precios, stocks, cotizaciones) los genera la base.
- Validación de encabezados: si falta una columna la migración se detiene con un mensaje claro.
- Generación de un archivo .sql de INSERTs por tabla en migrations/sql.
- Ejecución en una única transacción (todo o nada), re-ejecutable y con escape de comillas.
- Datos migrados a la base PostgreSQL de Supabase.
- preload_data.py queda solo con la generación de los CSV del Sprint 1; se quitan funciones que ya no se usan.
- Estilo: indentación de 2 espacios y sin comentarios en línea.

[Ejercicio 4]
- Se crean los modelos ORM en models/models.py con la Base declarativa.
- Tablas: generos, editoriales, monedas, tipos_cotizacion, libros, precios, stocks y cotizaciones_dolar.
- Relaciones: libro N:1 editorial/género, precio N:1 libro/moneda, stock 1:1 libro, cotización N:1 tipo.
- Restricciones de unicidad (isbn, precio por moneda, cotización por tipo y fecha) y CHECK de valores no negativos.
- Se crean las tablas en la base con ConexionDB.crear_tablas().
- Estilo: indentación de 2 espacios y sin comentarios en línea.

[Ejercicio 3]
- Se crea el context manager GestorTransaccion en database/connection.py.
- Commit automático al finalizar el bloque y rollback ante excepciones.
- ConexionDB expone crear_sesion() y transaccion(); se elimina obtener_sesion().
- Se agrega commit_ejercicio() para evitar commits duplicados al re-ejecutar.

[Ejercicio 2]
- Se crea la clase ConexionDB en database/connection.py con SQLAlchemy.
- La URL de conexión se lee de la variable DATABASE_URL (.env / secret de Colab).
- Se implementa Singleton, sesiones transaccionales y prueba de conexión.
- Se habilitan las claves foráneas en SQLite.
- Se agregan SQLAlchemy, python-dotenv y psycopg2-binary a requirements.txt.
- Corrección: DATABASE_URL se toma del entorno o del secret de Colab (Supabase); la contraseña nunca se guarda en el repositorio.
- Las URL postgres:// de Supabase se adaptan al driver psycopg2.
- Estilo: indentación de 2 espacios, líneas de hasta 80 caracteres y sin comentarios en línea.

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
