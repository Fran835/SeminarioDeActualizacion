# Book Manager

## Sprint actual: Sprint 3

## Objetivo

Obtener datos de la web para comparar los precios de nuestro catálogo con los de un competidor (la librería online Cúspide) y competir de forma más informada.

## Introducción y contexto

En el Sprint 1 se modelaron las entidades con POO y persistencia en archivos; en el Sprint 2 se migró la persistencia a una base relacional (Supabase/PostgreSQL) con SQLAlchemy. En este Sprint 3, partiendo de la rama `Sprint_2`, se incorpora:

- Una función para cargar los datos desde los archivos `.sql` de `migrations/sql`.
- Un scraper con Scrapy (`CuspideSpider`, con Item Loaders y Pipelines) que busca **solo los títulos del catálogo** y toma los 10 primeros resultados de cada búsqueda: precio, URL de la imagen, formas de pago y descripción detallada.
- La comparación del precio interno con el precio web y un CSV de alertas por cada ejecución, según la diferencia porcentual que ingresa el usuario.
- Un reporte Excel (`reportes/`) con Libro, Precio interno, Precio web, Diferencia y Fecha de extracción.
- Un decorador `@auditar` que registra cada operación (acción, fecha y detalles) en la tabla `auditorias`.
- Las opciones de menú "Ejecutar scraping", "Generar reporte" y "Ver historial de auditoría".

## Ejecución

```bash
pip install -r requirements.txt
cd src
python -c "from book_manager.main import main; main()"
```

La conexión se toma de la variable de entorno o secret de Colab `DATABASE_URL`.
