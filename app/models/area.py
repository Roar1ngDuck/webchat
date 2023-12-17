from sqlalchemy import text
from ..utils import helpers
from ..utils.db import Database
from .thread import Thread

class Area:
    """
    Represents an area on the discussion platform.

    An area is a section or category under which threads can be created. It can be either secret or public.

    Attributes:
        db (Database): An instance of the Database class for database operations.
        topic (str): The topic or title of the area.
        is_secret (bool): Flag indicating if the area is secret.
        id (int, optional): The unique identifier of the area in the database.
    """

    def __init__(self, topic, is_secret = False, id = None):
        """
        Initializes an Area object.

        Args:
            topic (str): The topic or title of the area.
            is_secret (bool, optional): Flag indicating if the area is secret. Defaults to False.
            id (int, optional): The unique identifier of the area in the database. Defaults to None.
        """

        self.db = Database()
        self.topic = topic
        self.is_secret = is_secret
        self.id = id

    @classmethod
    def create_from_db(cls, area_id, user_id):
        """
        Creates an Area instance from the database based on the area ID and user ID.

        Args:
            area_id (int): The ID of the area to be fetched.
            user_id (int): The ID of the user to check access permissions.

        Returns:
            Area or None: An instance of Area if found and accessible by the user, otherwise None.
        """

        sql = text("""
        SELECT a.topic, a.is_secret
        FROM areas a
        LEFT JOIN secret_area_privileges sap ON a.id = sap.area_id AND sap.user_id = :user_id
        INNER JOIN users u ON u.id = :user_id
        WHERE a.id = :area_id AND (u.is_admin = true OR a.is_secret = false OR sap.user_id IS NOT NULL)
        """)

        try:
            result = Database().fetch_one(sql, {"area_id": area_id, "user_id": user_id})
            instance = cls(result["topic"], result["is_secret"], area_id)
            return instance
        except:
            return None

    @property
    def thread_count(self):
        """
        The number of threads in the area.

        Returns:
            int: The count of threads within the area.
        """

        sql = text("""SELECT COUNT(*) FROM threads t WHERE t.area = :area_id""")
        return self.db.fetch_one(sql, {"area_id" : self.id})["count"]
    
    @property
    def message_count(self):
        """
        The number of messages across all threads in the area.

        Returns:
            int: The count of messages within all threads of the area.
        """

        sql = text("""SELECT COUNT(*) FROM messages m WHERE m.thread in (SELECT t.id FROM threads t WHERE t.area = :area_id)""")
        return self.db.fetch_one(sql, {"area_id" : self.id})["count"]

    @property
    def last_message(self):
        """
        The time of the last message sent in the area.

        Returns:
            str or None: A human-readable string of the time since the last message was sent, or None if no messages.
        """

        sql = text("""SELECT MAX(m.sent_time) FROM messages m WHERE m.thread in (SELECT t.id FROM threads t WHERE t.area = :area_id)""")
        last_message_time = self.db.fetch_one(sql, {"area_id" : self.id})["max"]
        if not last_message_time:
            return helpers.time_ago(last_message_time)
        return None

    @property
    def threads(self):
        """
        A list of threads in the area.

        Returns:
            list[Thread]: A list of Thread objects representing the threads in the area.
        """

        sql = text("""SELECT t.id,t.area,t.title,t.owner_id,a.topic FROM threads t, areas a WHERE t.area = :area_id AND t.area = a.id""")
        threads:list[Thread] = []
        for thread_result in self.db.fetch_all(sql, {"area_id" : self.id}):
            thread = Thread(thread_result["area"], thread_result["title"], thread_result["owner_id"], thread_result["id"], thread_result["topic"])
            threads.append(thread)
        return threads

    def insert(self):
        """
        Inserts the area into the database.

        Returns:
            Area: The instance of the Area with its ID updated from the database.
        """

        sql = text("""INSERT INTO areas (topic, is_secret) VALUES (:topic, :is_secret) RETURNING id""")
        self.id = self.db.execute(sql, {"topic" : self.topic, "is_secret" : self.is_secret})["id"]
        return self
