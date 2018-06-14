import psycopg2


class Pgsql(_Base):
    """
    Namespace for postgress connection
    """
    def __init__(self, hostname, port, user, password, db):
        super().__init__(psycopg2)
        self.db = db
        self.hostname = hostname
        self.port = port
        self.user = user
        self.password = password

    def get_connection(self):
        dsn = ("dbname='{db}' user='{user}' host='{hostname}' port='{port}'"
               "password='{password}'".format(db=self.db, user=self.user, port=self.port,
                                              hostname=self.hostname, password=self.password))
        return self.db_api_driver.connect(dsn)

    @staticmethod
    def scroll(cursor, value):
        cursor.scroll(value)

    @property
    def url(self):
        return "postgress://{}/{}".format(self.hostname, self.db)