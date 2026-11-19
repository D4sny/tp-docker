-- Exécuté automatiquement par Postgres au PREMIER démarrage (quand le volume est vide).

CREATE TABLE messages (
    id         SERIAL PRIMARY KEY,
    author     VARCHAR(50)  NOT NULL,
    content    VARCHAR(500) NOT NULL,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);

INSERT INTO messages (author, content) VALUES
    ('Le BR', 'Bienvenue sur le livre d''or ! Ce message vient de init.sql.'),
    ('Moby Dock', 'Si tu me vois encore après un docker compose down, c''est grâce au volume');
