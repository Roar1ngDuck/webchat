from sqlalchemy import create_engine, text
from os import getenv
from threading import Lock

class Database:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance.engine = create_engine(getenv("DB_URL"))
                if getenv("ENV") == "TEST":
                    cls._instance._drop_tables()  # Drop tables if in test environment
                cls._instance._initialize_tables()
        return cls._instance
    
    def _drop_tables(self):
        drop_tables_sql = """
        DROP TABLE IF EXISTS messages, threads, areas, users CASCADE;
        """
        with self.engine.connect() as connection:
            with connection.begin():
                connection.execute(text(drop_tables_sql))

    def _initialize_tables(self):
        table_creation_sql = """
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            thread integer NOT NULL,
            sender integer NOT NULL,
            text TEXT NOT NULL,
            sent_time TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
        );
        CREATE TABLE IF NOT EXISTS threads (
            id SERIAL PRIMARY KEY,
            area integer NOT NULL,
            title TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS areas (
            id SERIAL PRIMARY KEY,
            topic TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            password bytea NOT NULL
        );
        """
        with self.engine.connect() as connection:
            with connection.begin():
                connection.execute(text(table_creation_sql))

    def fetch_all(self, sql, params=None):
        with self.engine.connect() as connection:
            return connection.execute(sql, params).mappings()
        
    def fetch_one(self, sql, params=None):
        with self.engine.connect() as connection:
            return next(connection.execute(sql, params).mappings())
        
    def insert_one(self, sql, params=None):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(sql, params)
                return next(result.mappings())