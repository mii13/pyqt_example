import os
import re
import importlib
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


def import_class(module, obj):
    m = importlib.import_module(module)
    return getattr(m, obj)


_DRIVER_MAP = {
    'sqlite': "qt_query.dbproviders.sqlite_api.Sqlite",
    'postgres': "qt_query.dbproviders.postgres_api.Pgsql",
    'pgsql': "qt_query.dbproviders.postgres_api.Pgsql",
    'postgresql': "qt_query.dbproviders.postgres_api.Pgsql",
    'mysql': "qt_query.dbproviders.mysql_api.Mysql",
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
    mod = _DRIVER_MAP[driver].split(".")
    cl = import_class(".".join(mod[:-1]), mod[-1])
    return cl(**kwargs)
