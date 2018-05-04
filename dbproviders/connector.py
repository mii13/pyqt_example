import sqlparse
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

"sqlite://Northwind_small.sqlite"
"select * from 'order' o1 join 'order' o2 on o1.Id != o2.Id join 'order' o3 on o2.Id != o3.Id;"


class Query:
    MAX_ROW = 10000
    """
    The class is parse sql query and do the query in the database
    """
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
            else:
                return ["result", ], [("ok",), ]
        except Exception as e:
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
    def __init__(self, driver):
        self.db_api_driver = driver
        self.connection = None

    def __del__(self):
        try:
            self.connection.close()
        except (self.db_api_driver.DatabaseError, AttributeError):
            pass

    def do_query(self, query):
        return Query(self.connection, query).do()

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
        return self.db_api_driver.connect(self.db, check_same_thread=False)

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
        kwargs["db"] = url.path or url.netloc or ":memory:"
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
