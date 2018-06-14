import sqlite3

class Sqlite(_Base):
    """
        Namespace for sqlite connection
        """
    def __init__(self, db):
        super().__init__(sqlite3)
        self. db = db

    def get_connection(self):
        return self.db_api_driver.connect(self.db, check_same_thread=False)

    @property
    def url(self):
        return "sqlite://{}".format(self.db)