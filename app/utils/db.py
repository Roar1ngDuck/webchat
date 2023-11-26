from sqlalchemy import create_engine, text
from os import getenv
from threading import Lock
from ..utils import helpers

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
                cls._instance._create_admin_user()
        return cls._instance
    
    def _drop_tables(self):
        drop_tables_sql = """
        DROP TABLE IF EXISTS messages, threads, areas, users, secret_area_privileges CASCADE;
        """
        with self.engine.connect() as connection:
            with connection.begin():
                connection.execute(text(drop_tables_sql))

    def _initialize_tables(self):
        table_creation_sql = """
        CREATE TABLE IF NOT EXISTS areas (
            id SERIAL PRIMARY KEY,
            topic TEXT NOT NULL,
            is_secret boolean NOT NULL
        );
        CREATE TABLE IF NOT EXISTS threads (
            id SERIAL PRIMARY KEY,
            area integer NOT NULL REFERENCES areas(id),
            title TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password bytea NOT NULL,
            is_admin boolean NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            thread integer NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
            sender integer NOT NULL REFERENCES users(id),
            text TEXT NOT NULL,
            sent_time TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
        );
        CREATE TABLE IF NOT EXISTS secret_area_privileges (
            id SERIAL PRIMARY KEY,
            area_id integer NOT NULL REFERENCES areas(id),
            user_id integer NOT NULL REFERENCES users(id)
        );
        """
        with self.engine.connect() as connection:
            with connection.begin():
                connection.execute(text(table_creation_sql))

    def _create_admin_user(self):
        admin_creation_sql = text("""INSERT INTO users (username, password, is_admin) VALUES (:username, :password, :is_admin) ON CONFLICT (username) DO NOTHING""")
        with self.engine.connect() as connection:
            with connection.begin():
                connection.execute(admin_creation_sql, {"username" : "admin", "password" : helpers.hash_password(getenv("ADMIN_PASSWORD")), "is_admin" : True})


    def fetch_all(self, sql, params=None):
        with self.engine.connect() as connection:
            return connection.execute(sql, params).mappings()
        
    def fetch_one(self, sql, params=None):
        with self.engine.connect() as connection:
            return next(connection.execute(sql, params).mappings())
        
    def execute(self, sql, params=None, return_result = True):
        with self.engine.connect() as connection:
            with connection.begin():
                result = connection.execute(sql, params)
                if return_result:
                    return next(result.mappings())