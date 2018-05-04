from PyQt5 import QtWidgets, QtGui, QtCore
from dbproviders import get_driver
from connection_dialog import ConnectionDialog
from threading import Event


class QueryWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = None
        self.init_ui()
        self.query_stop_event = Event()

    def init_ui(self):
        self.create_menu()
        self.create_table_view()
        self.create_status_bar()
        query_label = QtWidgets.QLabel('Query')
        result_label = QtWidgets.QLabel('Result')
        self.query_edit = QtWidgets.QTextEdit()
        self.query_edit.setEnabled(False)
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
        splitter = QtWidgets.QFrame()
        splitter.setFrameStyle(QtWidgets.QFrame.VLine)

        self.status_query_label = QtWidgets.QLabel('')
        self.statusBar().addPermanentWidget(self.database_label, 0)
        self.statusBar().addPermanentWidget(splitter, 1)
        self.statusBar().addPermanentWidget(self.status_query_label, 2)

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

        # stop query action
        self.stop_queryAction = QtWidgets.QAction(QtGui.QIcon('icons/stop_query.png'), '&Stop Query', self)
        self.stop_queryAction.setDisabled(True)
        self.stop_queryAction.triggered.connect(self.stop_query)

        # connect action
        self.connectAction = QtWidgets.QAction(QtGui.QIcon('icons/ball_green.png'), '&Connect', self)
        self.connectAction.setShortcut('Ctrl+H')
        self.connectAction.triggered.connect(self.connect_to_db)

        # disconnect action
        self.disconnectAction = QtWidgets.QAction(QtGui.QIcon('icons/ball_red.png'), '&Disconnect', self)
        self.disconnectAction.setShortcut('Ctrl+K')
        self.disconnectAction.setEnabled(False)
        self.disconnectAction.triggered.connect(self.disconnect_from_db)

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
        self.toolbar.addAction(self.stop_queryAction)

    def create_table_view(self):
        self.table_view = QtWidgets.QTableView()
        self._table_model = QtGui.QStandardItemModel(self)
        self.table_view.setModel(self._table_model)

    def closeEvent(self, event):

        reply = QtWidgets.QMessageBox.question(self, 'Message', "Are you sure to quit?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
            if self.driver:
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
        self.stop_queryAction.setEnabled(True)
        self.queryAction.setEnabled(False)
        self.disconnectAction.setEnabled(False)
        self.status_query_label.setText("Do query...")
        self.query_stop_event.clear()
        self._do_query()
        self.status_query_label.setText("Ready")
        self.stop_queryAction.setEnabled(False)
        self.queryAction.setEnabled(True)
        self.disconnectAction.setEnabled(True)

    def _do_query(self):
        h, d = self.driver.do_query(self.query_edit.toPlainText().strip())
        self.fill_table(h, d)

    def fill_table(self, headers, data):
        self._table_model.clear()
        self._table_model.beginResetModel()
        self._table_model.setHorizontalHeaderLabels(headers)
        try:
            for r_i, row in enumerate(data):
                for c_i, data in enumerate(row):
                    item = QtGui.QStandardItem(str(data))
                    self._table_model.setItem(r_i, c_i, item)
                QtWidgets.qApp.processEvents()
                if self.query_stop_event.is_set():
                    break
        except MemoryError as e:
            QtWidgets.QMessageBox.warning(self, "query warning ", str(e))

        self._table_model.endResetModel()

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

    @QtCore.pyqtSlot()
    def stop_query(self):
        self.query_stop_event.set()


