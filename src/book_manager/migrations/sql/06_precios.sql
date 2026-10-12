-- Migración generada automáticamente desde precios.csv
-- Registros: 10

INSERT INTO precios (libro_id, valor, moneda_id) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000001'), 15000.0, 1);
INSERT INTO precios (libro_id, valor, moneda_id) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000002'), 18.5, 2);
INSERT INTO precios (libro_id, valor, moneda_id) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000003'), 12000.0, 1);
INSERT INTO precios (libro_id, valor, moneda_id) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000004'), 15.0, 2);
INSERT INTO precios (libro_id, valor, moneda_id) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000005'), 14000.0, 1);
INSERT INTO precios (libro_id, valor, moneda_id) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000006'), 13500.0, 1);
INSERT INTO precios (libro_id, valor, moneda_id) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000007'), 16000.0, 1);
INSERT INTO precios (libro_id, valor, moneda_id) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000008'), 11000.0, 1);
INSERT INTO precios (libro_id, valor, moneda_id) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000009'), 14.0, 2);
INSERT INTO precios (libro_id, valor, moneda_id) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000010'), 9000.0, 1);
