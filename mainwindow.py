import time
from PyQt5 import QtWidgets, QtGui, QtCore
from dbproviders import get_driver, Query
from connection_dialog import ConnectionDialog
from table_model import QueryResultTableModel


class QueryWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = None
        self.init_ui()

    def init_ui(self):
        self.create_status_bar()
        self.create_table_view()
        self.create_menu()
        query_label = QtWidgets.QLabel('Query')
        result_label = QtWidgets.QLabel('Result')
        self.query_edit = QtWidgets.QTextEdit()
        self.query_edit.setEnabled(False)
        self.query_edit.setText("")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(query_label)
        layout.addWidget(self.query_edit)
        layout.addWidget(result_label)
        layout.addWidget(self.table_view)
        wid = QtWidgets.QWidget(self)
        self.setCentralWidget(wid)
        wid.setLayout(layout)

        self.center()
        self.setWindowTitle('Query Window')

    def create_status_bar(self):
        self.database_label = QtWidgets.QLabel('Disconnect')
        splitter1 = QtWidgets.QFrame()
        splitter1.setFrameStyle(QtWidgets.QFrame.VLine)
        splitter2 = QtWidgets.QFrame()
        splitter2.setFrameStyle(QtWidgets.QFrame.VLine)

        self.status_query_label = QtWidgets.QLabel('')
        self.page_query_label = QtWidgets.QLabel('')
        self.statusBar().addPermanentWidget(self.database_label, 0)
        self.statusBar().addPermanentWidget(splitter1, 1)
        self.statusBar().addPermanentWidget(self.status_query_label, 2)
        self.statusBar().addPermanentWidget(splitter2, 3)
        self.statusBar().addPermanentWidget(self.page_query_label, 4)

    def create_menu(self):
        # exit action
        exitAction = QtWidgets.QAction(QtGui.QIcon('icons/exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)

        # do query action
        self.queryAction = QtWidgets.QAction(QtGui.QIcon('icons/query.png'), '&Query', self)
        self.queryAction.setShortcut('F5')
        self.queryAction.setDisabled(True)
        self.queryAction.triggered.connect(self.do_query)

        # connect action
        self.connectAction = QtWidgets.QAction(QtGui.QIcon('icons/ball_green.png'), '&Connect', self)
        self.connectAction.setShortcut('Ctrl+H')
        self.connectAction.triggered.connect(self.connect_to_db)

        # disconnect action
        self.disconnectAction = QtWidgets.QAction(QtGui.QIcon('icons/ball_red.png'), '&Disconnect', self)
        self.disconnectAction.setShortcut('Ctrl+K')
        self.disconnectAction.setEnabled(False)
        self.disconnectAction.triggered.connect(self.disconnect_from_db)

        # next page action
        self.next_page_action = QtWidgets.QAction(QtGui.QIcon('icons/next.png'), '&Next page', self)
        self.next_page_action.setEnabled(False)
        self.next_page_action.triggered.connect(self.next_page)

        # prev page action
        self.prev_page_action = QtWidgets.QAction(QtGui.QIcon('icons/prev.png'), '&Gren page', self)
        self.prev_page_action.setEnabled(False)
        self.prev_page_action.triggered.connect(self.prev_page)

        # menu

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        # toolbar

        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(exitAction)
        self.toolbar.addAction(self.connectAction)
        self.toolbar.addAction(self.disconnectAction)
        self.toolbar.addAction(self.queryAction)
        self.toolbar.addAction(self.prev_page_action)
        self.toolbar.addAction(self.next_page_action)

    def create_table_view(self):
        self.table_view = QtWidgets.QTableView()
        self._table_model = QueryResultTableModel(parent=self) # QtGui.QStandardItemModel(self)
        self._table_model.has_next.connect(self.has_next)
        self._table_model.has_prev.connect(self.has_prev)
        self._table_model.changed_page.connect(self.change_page)
        self.table_view.resizeColumnsToContents()
        self.table_view.setModel(self._table_model)

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Message', "Are you sure to quit?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
            if self.driver:
                time.sleep(0.5)
                self._disconnect_from_db()
        else:
            event.ignore()

    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    @QtCore.pyqtSlot()
    def do_query(self):
        self.queryAction.setEnabled(False)
        self.disconnectAction.setEnabled(False)
        self.status_query_label.setText("Do query...")

        self._do_query()

        self.status_query_label.setText("Ready")
        self.queryAction.setEnabled(True)
        self.disconnectAction.setEnabled(True)

    def _do_query(self):
        try:
            self._table_model.set_query(Query(self.driver, self.query_edit.toPlainText().strip()))
            self._table_model.next_page()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "query error ", str(e))

    @QtCore.pyqtSlot()
    def connect_to_db(self):
        connection_string, ok = ConnectionDialog.get_connection_string(self)
        if not ok:
            return

        connection_string = connection_string or "sqlite://:memory:"
        try:
            self.driver = get_driver(connection_string)
            self.driver.connect()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "db connect error ", str(e))
            return

        self.database_label.setText(self.driver.url)
        self.queryAction.setEnabled(True)
        self.query_edit.setEnabled(True)
        self.disconnectAction.setEnabled(True)
        self.connectAction.setEnabled(False)

    def _disconnect_from_db(self):
        self.driver = None

    @QtCore.pyqtSlot()
    def disconnect_from_db(self):
        self._disconnect_from_db()
        self.database_label.setText('Disconnect')
        self.status_query_label.setText("")
        self.queryAction.setEnabled(False)
        self.query_edit.setEnabled(False)
        self.disconnectAction.setEnabled(False)
        self.connectAction.setEnabled(True)

    @QtCore.pyqtSlot(bool)
    def has_next(self, value):
        self.next_page_action.setEnabled(value)

    @QtCore.pyqtSlot(bool)
    def has_prev(self, value):
        self.prev_page_action.setEnabled(value)

    @QtCore.pyqtSlot(int)
    def change_page(self, value):
        self.page_query_label.setText(str(value))

    @QtCore.pyqtSlot()
    def next_page(self):
        self.queryAction.setEnabled(False)
        self.disconnectAction.setEnabled(False)
        self.next_page_action.setEnabled(False)
        self.prev_page_action.setEnabled(False)
        self._table_model.next_page()
        self.queryAction.setEnabled(True)
        self.disconnectAction.setEnabled(True)

    @QtCore.pyqtSlot()
    def prev_page(self):
        self.queryAction.setEnabled(False)
        self.disconnectAction.setEnabled(False)
        self.next_page_action.setEnabled(False)
        self.prev_page_action.setEnabled(False)
        self._table_model.prev_page()
        self.queryAction.setEnabled(True)
        self.disconnectAction.setEnabled(True)

