from PyQt5.QtWidgets import (QMainWindow, QMessageBox, QDesktopWidget, QTableView, QWidget,
                             QTextEdit, QVBoxLayout, QAction, QLabel)
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtCore import pyqtSlot
from dbproviders import get_driver
from connection_dialog import ConnectionDialog


class QueryWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = None
        self.init_ui()

    def init_ui(self):
        self.create_menu()
        self.create_table_view()
        self.statusBar().showMessage('Disconnect')
        query_label = QLabel('Query')
        result_label = QLabel('Result')
        self.query_edit = QTextEdit()
        self.query_edit.setEnabled(False)
        layout = QVBoxLayout()
        layout.addWidget(query_label)
        layout.addWidget(self.query_edit)
        layout.addWidget(result_label)
        layout.addWidget(self.table_view)
        wid = QWidget(self)
        self.setCentralWidget(wid)
        wid.setLayout(layout)

        self.center()
        self.setWindowTitle('Query Window')

    def create_menu(self):
        # exit action
        exitAction = QAction(QIcon('icons/exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)

        # do query action
        self.queryAction = QAction(QIcon('icons/query.png'), '&Query', self)
        self.queryAction.setShortcut('F5')
        self.queryAction.setDisabled(True)
        self.queryAction.triggered.connect(self.do_query)

        # connect action
        self.connectAction = QAction(QIcon('icons/ball_green.png'), '&Connect', self)
        self.connectAction.setShortcut('Ctrl+H')
        self.connectAction.triggered.connect(self.connect_to_db)

        # disconnect action
        self.disconnectAction = QAction(QIcon('icons/ball_red.png'), '&Disconnect', self)
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

    def create_table_view(self):
        self.table_view = QTableView()
        self._table_model = QStandardItemModel(self)
        self.table_view.setModel(self._table_model)

    def closeEvent(self, event):

        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            if self.driver:
                self._disconnect_from_db()
        else:
            event.ignore()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    @pyqtSlot()
    def do_query(self):
        h, d = self.driver.do_query(self.query_edit.toPlainText().strip())
        self.fill_table(h, d)

    def fill_table(self, headers, data):
        self._table_model.clear()
        self._table_model.beginResetModel()
        for r_i, row in enumerate(data):
            for c_i, data in enumerate(row):
                item = QStandardItem(str(data))
                self._table_model.setItem(r_i, c_i, item)
        self._table_model.setHorizontalHeaderLabels(headers)
        self._table_model.endResetModel()

    @pyqtSlot()
    def connect_to_db(self):
        connection_string, ok = ConnectionDialog.get_connection_string(self)
        if not ok:
            return

        connection_string = connection_string or "sqlite://:memory:"

        try:
            self.driver = get_driver(connection_string)
            self.driver.connect()
        except Exception as e:
            QMessageBox.critical(self, "db connect error ", str(e))
            return

        self.statusBar().showMessage(self.driver.url)
        self.queryAction.setEnabled(True)
        self.query_edit.setEnabled(True)
        self.disconnectAction.setEnabled(True)
        self.connectAction.setEnabled(False)

    def _disconnect_from_db(self):
        self.driver = None

    @pyqtSlot()
    def disconnect_from_db(self):
        self._disconnect_from_db()
        self.statusBar().showMessage('Disconnect')
        self.queryAction.setEnabled(False)
        self.query_edit.setEnabled(False)
        self.disconnectAction.setEnabled(False)
        self.connectAction.setEnabled(True)
