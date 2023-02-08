import sys

from database import nmlDB

from PyQt5.QtGui import QPalette, QColor, QPixmap
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLabel,
    QLineEdit,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QTabWidget,
    QMenu,
    QAction,
    QComboBox,
    QListWidget,
    QGroupBox,
)


class CreateNewUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.new_user_info = {}

        self.setWindowTitle("Create New User")
        self.setFixedSize(QSize(400, 300))

        # Buttons at the bottom of the form
        QBtn = QDialogButtonBox.Save | QDialogButtonBox.Cancel  # type: ignore
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.return_info)
        self.buttonBox.rejected.connect(self.reject)

        # Create the Form
        self.create_form()

        self.main_layout = QVBoxLayout()
        message = QLabel("Please Enter the Following Information")
        self.main_layout.addWidget(message)
        self.main_layout.addWidget(self.form_group_box)
        self.main_layout.addWidget(self.buttonBox)
        self.setLayout(self.main_layout)

    def return_info(self):
        # printing the form information
        self.new_user_info = {
            "firstName": self.first_name_form.text(),
            "lastName": self.last_name_form.text(),
            "email": self.email_form.text(),
        }
        self.accept()

    def create_form(self):
        form_layout = QFormLayout()

        self.form_group_box = QGroupBox()
        self.first_name_form = QLineEdit()
        self.last_name_form = QLineEdit()
        self.email_form = QLineEdit()

        form_layout.addRow(QLabel("FIRST NAME"), self.first_name_form)
        form_layout.addRow(QLabel("LAST NAME"), self.last_name_form)
        form_layout.addRow(QLabel("EMAIL"), self.email_form)

        self.form_group_box.setLayout(form_layout)


class MainWindow(QMainWindow):
    """
    Main window for gui interface
    """

    def __init__(self, database: nmlDB) -> None:
        super().__init__()

        self.database = database
        self.USER_UUID = None
        self.USER_EMAIL = None

        # Window Setup
        self.setWindowTitle("nml.ai")
        self.setFixedSize(QSize(1080, 720))

        self.user_selector = QListWidget()
        self.user_selector.setFixedSize(250, 300)
        self.user_selector.addItems(self.database.get_all_users_emails())
        self.user_selector.setCurrentRow(0)
        self.user_selector.currentItemChanged.connect(self.user_selector_index_changed)

        self.add_new_user_btn = QPushButton("Create User")
        self.add_new_user_btn.clicked.connect(self.create_new_user)
        self.add_new_user_btn.setStyleSheet(
            "border-radius: 10px; "
            'font: 25 13pt "Bahnschrift Light"; '
            "background-color: rgb(209, 170, 170)"
        )

        self.set_user_btn = QPushButton("Set User")
        self.set_user_btn.clicked.connect(self.set_user)
        self.set_user_btn.setStyleSheet(
            "border-radius: 10px; "
            'font: 25 13pt "Bahnschrift Light"; '
            "background-color: rgb(209, 170, 170)"
        )

        self.placeholder_vid = QLabel()
        grey = QPixmap(750, 500)
        grey.fill(QColor("darkGray"))
        self.placeholder_vid.setPixmap(grey)

        # Set the Layout
        main_layout = QHBoxLayout()
        left_panel_layout = QVBoxLayout()
        user_btn_layout = QHBoxLayout()
        right_panel_layout = QVBoxLayout()

        # Left Panel Layout
        left_panel_layout.addWidget(self.user_selector)
        user_btn_layout.addWidget(self.add_new_user_btn)
        user_btn_layout.addWidget(self.set_user_btn)
        left_panel_layout.addLayout(user_btn_layout)

        # Right Panel Layout
        right_panel_layout.addWidget(self.placeholder_vid)

        # Add other layouts to main layout
        main_layout.addLayout(left_panel_layout)
        main_layout.addLayout(right_panel_layout)

        # Set the central widget of the Window.
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.setStyleSheet(
            "background-color: qlineargradient(spread:pad, x1:0.056, y1:0.119318, x2:1, y2:1, stop:0 rgba(255, 229, 222, 255), stop:1 rgba(229, 235, 255, 255));"
        )

        self.label = QLabel("NML.ai", self)
        self.label.setStyleSheet(
            'font: 25 58pt "Bahnschrift Light";'
            " color: rgb(79, 79, 79);"
            "background-color: transparent;"
        )
        # TODO MOVE INSIDE LAYOUT
        self.label.setFixedSize(250, 80)
        self.label.move(int(self.width() / 2 - 100), 30)

    def user_selector_index_changed(self, i):
        print(f"cb index = {i.text()}")
        self.USER_EMAIL = i.text()

    def create_new_user(self):
        # Create a pop up with form
        print("Creating new user")
        user_create_dialog = CreateNewUserDialog(self)

        dialog_action = user_create_dialog.exec()
        if dialog_action:
            # Check if all info is present
            user_first_name = user_create_dialog.new_user_info.get("firstName", None)
            user_last_name = user_create_dialog.new_user_info.get("lastName", None)
            user_email = user_create_dialog.new_user_info.get("email", None)

            if user_first_name and user_last_name and user_email:
                # Add new user
                self.USER_UUID = self.database.insert_new_user(
                    user_email, user_first_name, user_last_name
                )
                self.user_selector.addItem(user_email)
                print("Successfully Created new user")

            else:
                # If missing fields, alert
                missing_field_text = "Missing Field(s): "
                if not user_first_name:
                    missing_field_text += "First Name | "
                if not user_last_name:
                    missing_field_text += "Last Name | "
                if not user_email:
                    missing_field_text += "Email"

                missing_fields_alert = QMessageBox(self)
                missing_fields_alert.setStandardButtons(QMessageBox.Ok)  # type: ignore
                missing_fields_alert.setWindowTitle("Error")
                missing_fields_alert.setText(missing_field_text)
                missing_fields_alert.exec()

        else:
            print("Cancel")

    def set_user(self):
        if not self.USER_EMAIL:
            not_selected_alert = QMessageBox(self)
            not_selected_alert.setStandardButtons(QMessageBox.Ok)  # type: ignore
            not_selected_alert.setWindowTitle("Error")
            not_selected_alert.setText("Please Select a User")
            not_selected_alert.exec()
        else:
            self.USER_UUID = self.database.get_uuid_by_email(self.USER_EMAIL)
            self.user_selector.setEnabled(False)
            self.set_user_btn.setEnabled(False)
            self.add_new_user_btn.setEnabled(False)


def run_gui():
    app = QApplication(sys.argv)
    user_db = nmlDB("nml.db")

    window = MainWindow(user_db)
    window.show()
    app.exec()


if __name__ == "__main__":
    run_gui()
