from sqlalchemy import text
from ..utils import helpers
from ..utils.db import Database
from .message import Message


class Thread:
    """
    Represents a discussion thread in a forum or discussion platform.

    A thread is a sequence of messages under a specific topic within an area.

    Attributes:
        db (Database): An instance of the Database class for database operations.
        area (int): The ID of the area to which the thread belongs.
        title (str): The title of the thread.
        id (int, optional): The unique identifier of the thread in the database.
        area_name (str, optional): The name of the area to which the thread belongs.
        owner_id (int): The ID of the user who created the thread.
        messages (list[Message]): A list of Message objects in the thread.
    """

    def __init__(self, area, title, owner_id, id=None, area_name=None):
        """
        Initializes a Thread object.

        Args:
            area (int): The ID of the area to which the thread belongs.
            title (str): The title of the thread.
            owner_id (int): The ID of the user who created the thread.
            id (int, optional): The unique identifier of the thread in the database. Defaults to None.
            area_name (str, optional): The name of the area to which the thread belongs. Defaults to None.
        """

        self.db = Database()
        self.area = area
        self.title = title
        self.id = id
        self.area_name = area_name
        self.owner_id = owner_id
        self.messages: list[Thread] = []

    @classmethod
    def create_from_db(cls, id):
        """
        Creates a Thread instance from the database based on the thread ID.

        Args:
            id (int): The ID of the thread to be fetched.

        Returns:
            Thread or None: An instance of Thread if found in the database, otherwise None.
        """

        sql = text("""
SELECT m.id, t.title, t.owner_id, u.id as sender_id, u.username, m.text, m.image_url, m.sent_time, t.area, a.topic FROM messages m
JOIN users u ON m.sender = u.id
JOIN threads t ON m.thread = t.id
JOIN areas a on t.area = a.id WHERE m.thread = :thread_id ORDER BY m.sent_time""")
        instance = None
        for row in Database().fetch_all(sql, {"thread_id": id}):
            if not instance:
                instance = cls(row["area"], row["title"], row["owner_id"], id, row["topic"])
            instance.messages.append(Message(id, row["sender_id"], row["text"], image_url=row["image_url"], message_id=row["id"], thread_title=row["title"], sender_name=row["username"], sent_time=row["sent_time"]))
        return instance

    @property
    def message_count(self):
        """
        The number of messages in the thread.

        Returns:
            int: The count of messages within the thread.
        """

        sql = text("""SELECT COUNT(*) FROM messages m WHERE m.thread = :thread_id""")
        return self.db.fetch_one(sql, {"thread_id": self.id})["count"]

    @property
    def last_message(self):
        """
        The time of the last message sent in the thread.

        Returns:
            str or None: A human-readable string of the time since the last message was sent, or None if no messages.
        """

        sql = text("""SELECT MAX(m.sent_time) FROM messages m WHERE m.thread = :thread_id""")
        result = self.db.fetch_one(sql, {"thread_id": self.id})["max"]
        if result:
            return helpers.time_ago(result)
        return result

    def insert(self):
        """
        Inserts the thread into the database.

        The method inserts the thread's information into the database and sets the `id` attribute with the database-generated ID.

        Returns:
            Thread: The instance of the Thread with its ID updated from the database.
        """

        sql = text("""INSERT INTO threads (area, title, owner_id) VALUES (:area, :title, :owner_id) RETURNING id""")
        self.id = self.db.execute(sql, {"area": self.area, "title": self.title, "owner_id": self.owner_id})["id"]
        return self
