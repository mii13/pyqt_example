from PyQt5 import QtCore


class QueryResultTableModel(QtCore.QAbstractTableModel):
    has_prev = QtCore.pyqtSignal(bool)
    has_next = QtCore.pyqtSignal(bool)
    changed_page = QtCore.pyqtSignal(int)

    def __init__(self, query=None, parent=None):
        super(QueryResultTableModel, self).__init__(parent)
        self._query = None
        self._pagination = None
        self.set_query(query)

    def set_query(self, query):
        if query is not None:
            self._query = query
            self._pagination = query.paginate()

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._pagination) if self._query else 0

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self._query.keys) if self.rowCount() else 0

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            row, column = index.row(), index.column()
            if 0 <= row < self.rowCount() and 0 <= column < self.columnCount():
                return self._pagination.data[row][column]

    def headerData(self, p_int, Qt_Orientation, role=None):  # real signature unknown; restored from __doc__
        """ headerData(self, int, Qt.Orientation, role: int = Qt.DisplayRole) -> Any """
        if role == QtCore.Qt.DisplayRole and Qt_Orientation == QtCore.Qt.Horizontal:
            return self._query.keys[p_int]
        return super().headerData(p_int, Qt_Orientation, role)

    @QtCore.pyqtSlot()
    def next_page(self):
        self.beginResetModel()
        self._pagination.next_page()
        self.has_next.emit(self._pagination.has_next)
        self.has_prev.emit(self._pagination.has_prev)
        self.changed_page.emit(self._pagination.page)
        self.endResetModel()

    @QtCore.pyqtSlot()
    def prev_page(self):
        self.beginResetModel()
        self._pagination.prev_page()
        self.has_next.emit(self._pagination.has_next)
        self.has_prev.emit(self._pagination.has_prev)
        self.changed_page.emit(self._pagination.page)
        self.endResetModel()
