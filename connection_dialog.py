from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QDialogButtonBox
from PyQt5.QtCore import Qt


class ConnectionDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        self.connection_edit = QLineEdit()
        connection_label = QLabel('Connect to')
        layout = QVBoxLayout(self)
        layout.addWidget(connection_label)
        layout.addWidget(self.connection_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def get_connection_string(parent=None):
        dialog = ConnectionDialog(parent)
        result = dialog.exec_()
        return (dialog.connection_edit.text(), result == QDialog.Accepted)
