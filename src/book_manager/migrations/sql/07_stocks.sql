-- Migración generada automáticamente desde stocks.csv
-- Registros: 10

INSERT INTO stocks (libro_id, cantidad) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000001'), 50);
INSERT INTO stocks (libro_id, cantidad) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000002'), 20);
INSERT INTO stocks (libro_id, cantidad) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000003'), 15);
INSERT INTO stocks (libro_id, cantidad) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000004'), 10);
INSERT INTO stocks (libro_id, cantidad) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000005'), 60);
INSERT INTO stocks (libro_id, cantidad) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000006'), 25);
INSERT INTO stocks (libro_id, cantidad) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000007'), 30);
INSERT INTO stocks (libro_id, cantidad) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000008'), 40);
INSERT INTO stocks (libro_id, cantidad) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000009'), 12);
INSERT INTO stocks (libro_id, cantidad) VALUES ((SELECT id FROM libros WHERE isbn = '9789870000010'), 8);
