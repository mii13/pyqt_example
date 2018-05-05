import os
import re
import sqlparse
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


class Query:
    """
    The class is parse sql query and do the query in the database
    """
    MAX_ROW = 10000

    def __init__(self, connection, query):
        self.cursor = connection.cursor()
        self.connection = connection
        self.query = sqlparse.parse(query)[0]  # this version do only one query

    def do(self):
        """
        Do query and return result
        """
        try:
            self.cursor.execute(str(self.query))
            self.connection.commit()
            if "SELECT" == self.query.get_type().upper():
                header = [description[0] for description in self.cursor.description]
                return header, self
            return ["result", ], [("ok",), ]
        except Exception as e:
            self.connection.rollback()
            return ["error", ], [(str(e),), ]

    def __iter__(self):
        row = 0
        size = 1000
        while True:
            if row*size >= self.MAX_ROW:
                raise MemoryError("Result is very big; Use limit/ofset in query for pagination")
            row += 1
            results = self.cursor.fetchmany(size)
            if not results:
                break
            for result in results:
                yield result

    def __del__(self):
        try:
            self.cursor.close()
        except Exception:
            pass


class _Base:
    """
       interface for query execution
    """
    def __init__(self, driver):
        self.db_api_driver = driver
        self.connection = None

    def __del__(self):
        try:
            self.connection.close()
        except Exception:
            pass

    def do_query(self, query):
        return Query(self.connection, query).do()

    def connect(self):
        self.connection = self.get_connection()

    def get_connection(self):
        raise NotImplementedError


class Sqlite(_Base):
    """
        Namespace for sqlite connection
        """
    def __init__(self, db):
        import sqlite3
        super().__init__(sqlite3)
        self. db = db

    def get_connection(self):
        return self.db_api_driver.connect(self.db, check_same_thread=False)

    @property
    def url(self):
        return "sqlite://{}".format(self.db)


class Mysql(_Base):
    """
    Namespace for mysql connection
    """
    def __init__(self, hostname, port, user, password, db):
        import pymysql
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


class Pgsql(_Base):
    """
    Namespace for postgress connection
    """
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


def parse_sqlite_filename(path):
    filename = os.path.basename(path)
    if re.findall(r'[^A-Za-z0-9_\-\.\\]', filename):
        raise NameError("Bad sqlite database name")
    extension = os.path.splitext(filename)[1].lstrip(".")
    if extension not in ("db", "sdb", "sqlite", "db3", "s3db", "sqlite3", "sl3", "db2", "s2db", "sqlite2", "sl2"):
        raise NameError("Bad sqlite database extension")


def parse(connection_string):
    url = urlparse.urlparse(connection_string)
    kwargs = {}
    if url.scheme == 'sqlite':
        path = url.path[1:] or url.netloc or ""
        if path:
            parse_sqlite_filename(path)
        kwargs["db"] = path or ":memory:"
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
