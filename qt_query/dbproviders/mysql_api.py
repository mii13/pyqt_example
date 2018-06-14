import pymysql
from .base_api import Base


class Mysql(Base):
    """
    Namespace for mysql connection
    """
    def __init__(self, hostname, port, user, password, db):
        super().__init__(pymysql)
        self.db = db
        self.hostname = hostname
        self.port = port
        self.user = user
        self.password = password

    def get_connection(self):
        return self.db_api_driver.connect(host=self.hostname, user=self.user, password=self.password,
                                          database=self.db, port=self.port)

    @property
    def url(self):
        return "mysql://{}/{}".format(self.hostname, self.db)