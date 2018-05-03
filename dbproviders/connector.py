try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


class _Base:
    def __init__(self, driver):
        self.db_api_driver = driver
        self.connection = None

    def __del__(self):
        try:
            self.connection.close()
        except self.db_api_driver.DatabaseError:
            pass

    def do_query(self, query):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            self.connection.commit()
            if "SELECT" in query.upper():
                header = [description[0] for description in cursor.description]
                return header, cursor.fetchall()
            else:
                return ["result", ], [("ok",), ]
        except self.db_api_driver.DatabaseError as e:
            return ["error", ], [(str(e),), ]
        finally:
            cursor.close()

    def connect(self):
        self.connection = self.get_connection()

    def get_connection(self):
        raise NotImplementedError


class Sqlite(_Base):
    def __init__(self, db):
        import sqlite3
        super().__init__(sqlite3)
        self. db = db

    def get_connection(self):
        return self.db_api_driver.connect(self.db)

    @property
    def url(self):
        return "sqlite://{}".format(self.db)


class Mysql(_Base):
    def __init__(self, hostname, port, user, password, db):
        import pymysql
        super().__init__(pymysql)
        self.db = db
        self.hostname = hostname
        self.port = port
        self.user = user
        self.password = password

    def get_connection(self):
        return self.db_api_driver.connect(self.hostname, self.user, self.password, self.db, self.port)

    @property
    def url(self):
        return "mysql://{}/{}".format(self.hostname, self.db)


class Pgsql(_Base):
    def __init__(self, hostname, port, user, password, db):
        import psycopg2
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

    @property
    def url(self):
        return "postgress://{}/{}".format(self.hostname, self.db)


_DRIVER_MAP = {
    'sqlite': Sqlite,
    'postgres': Pgsql,
    'pgsql': Pgsql,
    'postgresql': Pgsql,
    'mysql': Mysql,
}

urlparse.uses_netloc.append('sqlite')
urlparse.uses_netloc.append('postgres')
urlparse.uses_netloc.append('postgresql')
urlparse.uses_netloc.append('pgsql')
urlparse.uses_netloc.append('mysql')


def parse(connection_string):
    url = urlparse.urlparse(connection_string)
    kwargs = {}
    if url.scheme == 'sqlite':
        kwargs["db"] = url.hostname or ":memory:"
    else:
        kwargs["hostname"] = url.hostname
        kwargs["user"] = url.username
        kwargs["password"] = url.password
        kwargs["port"] = url.port
        kwargs["db"] = url.path[1:]

    return url.scheme, kwargs


def get_driver(connection_string):
    driver, kwargs = parse(connection_string)
    if driver not in _DRIVER_MAP.keys():
        raise KeyError("unexpected db: {}".format(driver))
    return _DRIVER_MAP[driver](**kwargs)
