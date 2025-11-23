CREATE TABLE forms (
    id SERIAL PRIMARY KEY,
    columns JSONB NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT NOT NULL,
    chat_link TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    creator_id INTEGER NOT NULL
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_url TEXT NOT NULL,
    client_id TEXT NOT NULL,
    client_secret TEXT NOT NULL,
    scopes TEXT NOT NULL,
    email TEXT NOT NULL
);
