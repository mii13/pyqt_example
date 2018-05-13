import os
import re
import sqlparse
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


class DbProviderException(Exception):
    pass


class Pagination:
    """ Class for pagination sql query result"""
    MAX_ROW = 1000

    def __init__(self, query):
        self.query = query
        self._data = []
        self.last = False
        self.page = 0

    def __len__(self):
        return len(self._data)

    @property
    def data(self):
        return self._data

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.last

    def next_page(self):
        """ get next page """
        self._data = self.query.fetch_data(Pagination.MAX_ROW)
        self.page += 1
        if not self._data:
            self._data = []
            self.last = True
        if len(self._data) == Pagination.MAX_ROW:
            self.last = True

    def prev_page(self):
        """ get prev page """
        if not self.has_prev:
            raise DbProviderException("prev page not exist")
        # it is very bad solution
        self.query.execute_query()
        self.page -= 2
        self.query.scroll(Pagination.MAX_ROW*self.page)
        self.next_page()


class Query:
    """
    The class is parse sql query and do the query in the database
    """

    def __init__(self, db_driver, query):
        self.cursor = None
        self.db_driver = db_driver
        self._result = [("ok",), ]
        try:
            self.query = sqlparse.parse(query)[0]  # this version do only one query
        except IndexError:
            raise DbProviderException("Bad query")

    @property
    def keys(self):
        """ return header """
        if "SELECT" == self.query.get_type().upper():
            return [description[0] for description in self.cursor.description]
        return ["result", ]

    def scroll(self, value):
        self.db_driver.scroll(self.cursor, value)

    def fetch_data(self, size):
        if "SELECT" == self.query.get_type().upper():
            return self.cursor.fetchmany(size)
        else:
            return self._result

    def execute_query(self):
        """ Do query """
        self._close_cursor()
        try:
            self.cursor = self.db_driver.do_query(str(self.query))
        except Exception as e:
            self.db_driver.connection.rollback()
            self._result = [(str(e),), ]

    def _close_cursor(self):
        try:
            self.cursor.close()
        except Exception:
            pass

    def __del__(self):
        self._close_cursor()

    def paginate(self):
        self.execute_query()
        return Pagination(self)


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
        cursor = self.connection.cursor()
        cursor.execute(query)
        self.connection.commit()
        # self.connection.rollback()
        # return ["error", ], [(str(e),), ]
        return cursor

    @staticmethod
    def scroll(cursor, value):
        if not value:
            return
        max_row = 10000  # некое предельное число, что бы можно было листать без учерба к опер. памяти
        if value > max_row:
            counter = value // max_row
            appendix = value % max_row
            if appendix:
                cursor.fetchmany(appendix)
            for _ in range(counter):
                cursor.fetchmany(max_row)  # небольшое утечка памяти, надо разобраться
        else:
            cursor.fetchmany(value)

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

    @staticmethod
    def scroll(cursor, value):
        cursor.scroll(value)

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
