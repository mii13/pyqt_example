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
