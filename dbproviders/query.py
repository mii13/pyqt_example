import sqlparse
from .exceptions import DbProviderException


class Query:
    """
    The class is parse sql query and do the query in the database
    """

    def __init__(self, db_driver, query):
        self.cursor = None
        self.db_driver = db_driver
        self._error = ""
        try:
            self.query = sqlparse.parse(query)[0]  # this version do only one query
        except IndexError:
            raise DbProviderException("Bad query")

    @property
    def keys(self):
        """ return header """
        header = ["result", ]
        try:
            header = [description[0] for description in self.cursor.description]
        except AttributeError:
            header = ["error", ]
        except TypeError:
            pass  # update, insert statements description is None
        return header

    def scroll(self, value):
        self.db_driver.scroll(self.cursor, value)

    def fetch_data(self, size):
        if self._error:
            return [(self._error,), ]
        elif "SELECT" == self.query.get_type().upper():
            return self.cursor.fetchmany(size)

        return [("ok", ), ]

    def execute_query(self):
        """ Do query """
        self._close_cursor()
        try:
            self.cursor = self.db_driver.do_query(str(self.query))
        except self.db_driver.db_api_driver.DatabaseError as e:
            self.db_driver.connection.rollback()
            self._error = str(e)

    def _close_cursor(self):
        try:
            self.cursor.close()
        except (AttributeError, self.db_driver.db_api_driver.DatabaseError):
            pass

    def __del__(self):
        self._close_cursor()

    def paginate(self):
        self.execute_query()
        return Pagination(self)


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
