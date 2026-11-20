CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(32) UNIQUE NOT NULL,
    password VARCHAR(32) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT false,
    attempts SMALLINT NOT NULL DEFAULT 0 CHECK(attempts >= 0)
);

INSERT INTO users (username, password, is_admin) VALUES
('admin', '123', true),
('user1', '123', false),
('user2', '123', false);
