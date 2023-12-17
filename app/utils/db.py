from os import getenv
from threading import Lock
from sqlalchemy import create_engine, text
from ..utils import helpers


class Database:
    """
    A singleton class that represents the database connection.

    This class ensures that only one instance of the database connection is created
    (singleton pattern). It handles the creation, initialization, and management of
    database tables and provides methods for executing and fetching data from the database.

    Attributes:
        _instance (Database): A static instance of the Database class.
        _lock (Lock): A threading lock to ensure thread-safe singleton instantiation.
        _engine (Engine): An SQLAlchemy engine instance for database connections.
    """

    _instance = None
    _lock = Lock()
    _engine = None

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance._engine = create_engine(getenv("DB_URL"))
                if getenv("ENV") == "TEST":
                    cls._instance._drop_tables()  # Drop tables if in test environment
                cls._instance._initialize_tables()
                cls._instance._create_admin_user()
        return cls._instance

    def _drop_tables(self):
        drop_tables_sql = """
        DROP TABLE IF EXISTS messages, threads, areas, users, secret_area_privileges CASCADE;
        """
        with self._engine.connect() as connection:
            with connection.begin():
                connection.execute(text(drop_tables_sql))

    def _initialize_tables(self):
        table_creation_sql = """
        CREATE TABLE IF NOT EXISTS areas (
            id SERIAL PRIMARY KEY,
            topic TEXT NOT NULL,
            is_secret boolean NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password bytea NOT NULL,
            is_admin boolean NOT NULL
        );
        CREATE TABLE IF NOT EXISTS threads (
            id SERIAL PRIMARY KEY,
            area integer NOT NULL REFERENCES areas(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            owner_id integer NOT NULL REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            thread integer NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
            sender integer NOT NULL REFERENCES users(id),
            text TEXT NOT NULL,
            image_url TEXT,
            sent_time TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
        );
        CREATE TABLE IF NOT EXISTS secret_area_privileges (
            id SERIAL PRIMARY KEY,
            area_id integer NOT NULL REFERENCES areas(id) ON DELETE CASCADE,
            user_id integer NOT NULL REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS thread_subscriptions (
            id SERIAL PRIMARY KEY,
            thread_id integer NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
            user_id integer NOT NULL REFERENCES users(id),
            UNIQUE (thread_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id integer NOT NULL REFERENCES users(id),
            thread_id integer NOT NULL REFERENCES threads(id),
            sender_id integer NOT NULL REFERENCES users(id),
            message TEXT NOT NULL,
            sent_time TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
        );
        """
        with self._engine.connect() as connection:
            with connection.begin():
                connection.execute(text(table_creation_sql))

    def _create_admin_user(self):
        admin_creation_sql = text("""INSERT INTO users (username, password, is_admin) VALUES (:username, :password, :is_admin) ON CONFLICT (username) DO NOTHING""")
        with self._engine.connect() as connection:
            with connection.begin():
                connection.execute(admin_creation_sql, {"username": "admin", "password": helpers.hash_password(getenv("ADMIN_PASSWORD")), "is_admin": True})

    def fetch_all(self, sql, params=None):
        """
        Executes a SQL query and returns all results.

        Args:
            sql (str): The SQL query to be executed.
            params (dict, optional): Parameters to be used in the SQL query.

        Returns:
            ResultProxy: A list of dictionaries containing the query results.
        """
        with self._engine.connect() as connection:
            return connection.execute(sql, params).mappings()

    def fetch_one(self, sql, params=None):
        """
        Executes a SQL query and returns the first result.

        Args:
            sql (str): The SQL query to be executed.
            params (dict, optional): Parameters to be used in the SQL query.

        Returns:
            dict: A dictionary containing the first row of the query results.
        """
        with self._engine.connect() as connection:
            try:
                return next(connection.execute(sql, params).mappings())
            except Exception:
                return None

    def execute(self, sql, params=None, return_result=True):
        """
        Executes a SQL query and optionally returns the result.

        Args:
            sql (str): The SQL query to be executed.
            params (dict, optional): Parameters to be used in the SQL query.
            return_result (bool, optional): If true, returns the first result of the query.

        Returns:
            dict or None: A dictionary containing the first row of the query results if return_result is True, else None.
        """
        with self._engine.connect() as connection:
            with connection.begin():
                try:
                    result = connection.execute(sql, params)
                    if return_result:
                        return next(result.mappings())
                except Exception:
                    return None
