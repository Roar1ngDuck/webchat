from datetime import datetime
from sqlalchemy import text
from ..utils.db import Database
from ..utils import helpers


class Message:
    """
    Represents a message in the discussion platform.

    A message is a user's post in a thread. It can contain text and optionally an image URL.

    Attributes:
        db (Database): An instance of the Database class for database operations.
        thread (int): The ID of the thread to which the message belongs.
        sender (int): The ID of the user who sent the message.
        text (str): The text content of the message.
        image_url (str, optional): The URL of the image attached to the message, if any.
        id (int, optional): The unique identifier of the message in the database.
        thread_title (str, optional): The title of the thread to which the message belongs.
        sender_name (str, optional): The name of the user who sent the message.
        sent_time (datetime, optional): The timestamp when the message was sent.
    """

    def __init__(self, thread, sender, text, image_url=None, message_id=None, thread_title=None, sender_name=None, sent_time=None):
        """
        Initializes a Message object.

        Args:
            thread (int): The ID of the thread to which the message belongs.
            sender (int): The ID of the user who sent the message.
            text (str): The text content of the message.
            image_url (str, optional): The URL of the image attached to the message, if any. Defaults to None.
            message_id (int, optional): The unique identifier of the message in the database. Defaults to None.
            thread_title (str, optional): The title of the thread to which the message belongs. Defaults to None.
            sender_name (str, optional): The name of the user who sent the message. Defaults to None.
            sent_time (datetime, optional): The timestamp when the message was sent. Defaults to the current time.
        """

        self.db = Database()
        self.thread = thread
        self.sender = sender
        self.text = text
        self.image_url = image_url
        if sent_time:
            self.sent_time = sent_time
        else:
            self.sent_time = datetime.now()
        self.id = message_id
        self.thread_title = thread_title
        self.sender_name = sender_name

    @classmethod
    def create_from_db(cls, message_id):
        """
        Retrieves a message from the database based on the message ID.

        Args:
            message_id (int): The ID of the message to be fetched.

        Returns:
            Message or None: An instance of Message if found, otherwise None.
        """
        sql = text("""
        SELECT m.id, m.thread, m.sender, m.text, m.image_url, m.sent_time, 
            t.title as thread_title, u.username as sender_name
        FROM messages m
        JOIN threads t ON m.thread = t.id
        JOIN users u ON m.sender = u.id
        WHERE m.id = :message_id
        """)

        try:
            result = Database().fetch_one(sql, {"message_id": message_id})
            if result:
                return cls(
                    thread=result["thread"],
                    sender=result["sender"],
                    text=result["text"],
                    image_url=result["image_url"],
                    message_id=result["id"],
                    thread_title=result["thread_title"],
                    sender_name=result["sender_name"],
                    sent_time=result["sent_time"]
                )
            return None
        except Exception:
            return None

    @property
    def sent_time_ago(self):
        """
        Calculates how much time has passed since the message was sent.

        Returns:
            str: A human-readable string representing the time elapsed since the message was sent.
        """

        return helpers.time_ago(self.sent_time)

    def insert(self):
        """
        Inserts the message into the database.

        Returns:
            Message: The instance of the Message with its ID updated from the database.
        """

        sql = text("""INSERT INTO messages (thread, sender, text, image_url, sent_time) VALUES (:thread, :sender, :text, :image_url, :sent_time) RETURNING id""")
        self.id = self.db.execute(sql, {"thread": self.thread, "sender": self.sender, "text": self.text, "image_url": self.image_url, "sent_time": self.sent_time})["id"]
        return self

    def update(self, new_text, new_image_url=None):
        """
        Updates the text and optionally the image URL of the message in the database.

        Args:
            new_text (str): The new text content of the message.
            new_image_url (str, optional): The new URL of the image attached to the message, if any. Defaults to None.
        """
        sql = text("""UPDATE messages SET text = :new_text, image_url = :new_image_url WHERE id = :message_id""")
        self.db.execute(sql, {"new_text": new_text, "new_image_url": new_image_url, "message_id": self.id}, False)
        self.text = new_text
        self.image_url = new_image_url
