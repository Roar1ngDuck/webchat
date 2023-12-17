from sqlalchemy import text
from ..utils import helpers
from ..utils.db import Database

class User:
    """
    Represents a user in the discussion platform.

    This class encapsulates user information, including their username, password (hashed), and administrative status.

    Attributes:
        db (Database): An instance of the Database class for database operations.
        username (str): The username of the user.
        password (str): The hashed password of the user.
        is_admin (bool): Flag indicating whether the user has administrative privileges.
        id (int, optional): The unique identifier of the user in the database, set after insertion.
    """

    def __init__(self, username, password, is_admin = False):
        """
        Initializes a User object.

        Args:
            username (str): The username of the user.
            password (str): The raw password of the user, which will be hashed.
            is_admin (bool, optional): Flag indicating whether the user has administrative privileges. Defaults to False.
        """

        self.db = Database()
        self.username = username
        self.password = helpers.hash_password(password)
        self.is_admin = is_admin

    def insert(self):
        sql = text("""INSERT INTO users (username, password, is_admin) VALUES (:username, :password, :is_admin) RETURNING id""")
        self.id = self.db.execute(sql, {"username" : self.username, "password" : self.password, "is_admin" : self.is_admin})["id"]
