from sqlalchemy import create_engine
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
        return cls._instance

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