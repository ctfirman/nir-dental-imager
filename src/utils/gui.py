import sys
import cv2
import numpy as np

from PyQt5.QtGui import QColor, QPixmap, QImage
from PyQt5.QtCore import QSize, Qt, QThreadPool
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
    QFormLayout,
    QTabWidget,
    QStackedLayout,
    QListWidget,
    QGroupBox,
)

# TODO import errors
from utils.database import nmlDB
from utils.camera import VideoThread
from utils.crack_detect import crack_detect_method_1, NMLModel, CrackDetectHighlight


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
        self.MOST_RECENT_IMAGE_SESSION = 0

        # Window Setup
        self.setWindowTitle("nml.ai")
        self.setFixedSize(QSize(1080, 720))

        # Create all Widgets and layouts
        self.init_widgets()
        self.init_layouts()

        self.crack_detection_thread_pool = QThreadPool()

    def init_widgets(self):
        self.user_selector = QListWidget()
        self.user_selector.setFixedSize(250, 300)
        self.user_selector.addItems(self.database.get_all_users_emails())
        self.user_selector.currentItemChanged.connect(self.user_selector_index_changed)

        # Default to first item if exists
        if self.user_selector.count():
            self.user_selector.setCurrentRow(0)
            self.USER_EMAIL = self.user_selector.item(0).text()

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

        self.title_label = QLabel("NML.ai", self)
        self.title_label.setStyleSheet(
            'font: 25 58pt "Bahnschrift Light";'
            " color: rgb(79, 79, 79);"
            "background-color: transparent;"
        )
        self.title_label.setFixedSize(250, 80)

        # Initialize Video
        self.video_label = QLabel()
        grey = QPixmap(750, 500)
        grey.fill(QColor("darkGray"))
        self.video_label.setPixmap(grey)

        # Placeholder for video thread, Will be initialized in set_user with complete info
        self.video_thread = VideoThread(
            self.USER_UUID if self.USER_UUID else "empty-uuid", self.database
        )
        self.video_thread.change_image_signal.connect(self.update_image)
        self.video_thread.error_image_signal.connect(self.error_video_handler)
        self.video_thread.camera_available_signal.connect(
            self.enable_initial_capture_toggle
        )
        self.video_thread.capture_complete_signal.connect(
            self.completed_capture_handler
        )

        # Capture image button
        self.capture_image_button = QPushButton("Capture Image")
        self.capture_image_button.setCheckable(False)
        self.capture_image_button.clicked.connect(self.capture_image_handler)
        self.capture_image_button.setEnabled(False)

        # Capture image textbox for image name
        self.image_name_text = QLabel("Enter the Image Name:")
        self.image_name_box = QLineEdit()

    def init_layouts(self):
        # Set the Layout
        main_layout = QVBoxLayout()
        self.stacked_layout = QStackedLayout()
        user_selector_layout = QVBoxLayout()
        user_btn_layout = QHBoxLayout()
        new_scan_layout = QVBoxLayout()
        image_name_layout = QHBoxLayout()

        # Main Layout
        main_layout.addWidget(self.title_label)
        main_layout.setAlignment(self.title_label, Qt.AlignHCenter)  # type: ignore

        # User Selector Layout
        user_selector_layout.addWidget(self.user_selector)
        user_btn_layout.addWidget(self.add_new_user_btn)
        user_btn_layout.addWidget(self.set_user_btn)
        user_selector_layout.addLayout(user_btn_layout)
        user_selector_layout.setAlignment(self.user_selector, Qt.AlignHCenter)  # type: ignore

        user_selector_container = QWidget()
        user_selector_container.setLayout(user_selector_layout)

        # New Scan Layout
        new_scan_layout.addWidget(self.video_label)
        new_scan_layout.setAlignment(self.video_label, Qt.AlignCenter)  # type: ignore
        image_name_layout.addWidget(self.image_name_text)
        image_name_layout.addWidget(self.image_name_box)
        new_scan_layout.addLayout(image_name_layout)
        new_scan_layout.addWidget(self.capture_image_button)

        new_scan_container = QWidget()
        new_scan_container.setLayout(new_scan_layout)

        # Previous Scan Layout
        past_scan_container = QWidget()

        # Tab Widget for new scan and past scan
        content_tab = QTabWidget()
        content_tab.addTab(new_scan_container, "New Scan")
        content_tab.addTab(past_scan_container, "Past Scan")

        # Stacked layout for swapping between login and content
        self.stacked_layout.addWidget(user_selector_container)
        self.stacked_layout.addWidget(content_tab)

        # Add other layouts to main layout
        main_layout.addLayout(self.stacked_layout)

        # Set the central widget of the Window.
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.setStyleSheet(
            "background-color: qlineargradient(spread:pad, x1:0.056, y1:0.119318, x2:1, y2:1, stop:0 rgba(255, 229, 222, 255), stop:1 rgba(229, 235, 255, 255));"
        )

    def user_selector_index_changed(self, i):
        print(f"user_selector index = {i.text()}")
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

            # Start video thread
            self.video_thread.set_user(self.USER_UUID)
            self.video_thread.start()  # TODO restart thread if changed user. Maybe? -> https://stackoverflow.com/questions/44006024/restart-qthread-with-gui

            # Swap layouts
            self.stacked_layout.setCurrentIndex(1)

    def capture_image_handler(self, checked):
        self.capture_image_button.setEnabled(False)
        print("Capturing an Image!")

        image_name = self.image_name_box.text()
        self.image_name_box.clear()
        self.MOST_RECENT_IMAGE_SESSION = self.video_thread.init_capture_image(
            image_name
        )

    # @pyqtSlot(str)
    def error_video_handler(self, msg: str) -> None:
        print(msg)

    # @pyqtSlot(np.ndarray)
    def update_image(self, cv_img: np.ndarray) -> None:
        qt_image = self._convert_cv_to_qt(cv_img)
        self.video_label.setPixmap(qt_image)

    # @pyqtSlot(bool)
    def enable_initial_capture_toggle(self, toggle_state: bool) -> None:
        self.capture_image_button.setEnabled(toggle_state)

    # @pyqtSlot(bool)
    def completed_capture_handler(self, capture_status: bool) -> None:
        """Handler after an image is captured"""
        # self.MOST_RECENT_IMAGE_SESSION

        if self.USER_UUID:
            image_crack_detection_worker = CrackDetectHighlight(
                self.database, self.MOST_RECENT_IMAGE_SESSION, self.USER_UUID
            )
            image_crack_detection_worker.signals.finished.connect(
                self.update_past_scans_list
            )
            self.crack_detection_thread_pool.start(image_crack_detection_worker)

        # for crack detect, pass in LATEST_SESSION_ID
        # crack_detect_method_1(self.MOST_RECENT_IMAGE_SESSION, True)
        # NMLModel.get_data_for_ml(self.USER_UUID, self.MOST_RECENT_IMAGE_SESSION, self.database)

        # TODO: CALL CRACK DETECTION IF BLOCKING DO BEFORE ENABLING BUTTON
        self.capture_image_button.setEnabled(capture_status)

    # @pyqtSlot(int)
    def update_past_scans_list(self, image_session_id):
        """Updates the list of past scans after an image session computation is completed"""
        print("Crack detection is done")
        pass

    def _convert_cv_to_qt(self, cv_img) -> QPixmap:
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(
            rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888  # type: ignore
        )
        return QPixmap.fromImage(convert_to_Qt_format)

    def closeEvent(self, event):
        if self.video_thread:
            self.video_thread.stop()
        event.accept()


def run_gui():
    app = QApplication(sys.argv)
    user_db = nmlDB("nml.db")

    window = MainWindow(user_db)
    window.show()
    app.exec()


if __name__ == "__main__":
    run_gui()
