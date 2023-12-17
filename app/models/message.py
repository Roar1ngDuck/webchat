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
