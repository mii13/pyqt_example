import sys
from PyQt5.QtWidgets import QApplication
from mainwindow import QueryWindow


if __name__ == '__main__':

    app = QApplication(sys.argv)

    qw = QueryWindow()
    qw.show()
    sys.exit(app.exec_())
