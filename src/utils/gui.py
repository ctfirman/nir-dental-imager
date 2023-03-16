import os
import sys
import cv2
import numpy as np

from PyQt5.QtGui import QColor, QPixmap, QImage, QIcon
from PyQt5.QtCore import QSize, Qt, QThreadPool, pyqtSlot
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
    QGridLayout,
    QTabWidget,
    QStackedLayout,
    QListWidget,
    QGroupBox,
)

from utils.database import nmlDB
from utils.camera import VideoThread
from utils.crack_detect import NMLModel, CrackDetectHighlight
from utils.version import BETA_VERSION


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


class PreviewImageDialog(QDialog):
    def __init__(self, user_uuid, image_session, database, parent=None):
        super().__init__(parent=parent)
        """Create a new dialog as a new pop up window for when the user clicks "capture". This dialog box would show
        them the results of the current image"""
        self.database = database
        self.user_uuid = user_uuid
        self.FILEPATH_OF_PAST_SCAN_IMAGE = ""

        self.setWindowTitle("Image Preview")

        # Buttons at the bottom of the form
        QBtn = QDialogButtonBox.Ok  # type: ignore
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        # Set size
        self.setFixedSize(600, 700)

        # Path for the completed image
        completed_img_path = os.path.join(
            self.database.get_base_filepath(self.user_uuid),
            "complete",
            f"{image_session.session_id}-normal.jpg",
        )
        if self.FILEPATH_OF_PAST_SCAN_IMAGE == "":
            self.FILEPATH_OF_PAST_SCAN_IMAGE = completed_img_path

        # Make the crack status more readable by changing the status code to words
        if image_session.crack_detected == 1:
            crack_status = "CRACK"
            crack_detection_str = "Oh no! Crack detected!"
            background_color_css = "background-color: rgba(255, 0, 0, 0.25)"
        else:
            crack_status = "NOCRACK"
            crack_detection_str = "Good job! No crack detected!"
            background_color_css = "background-color: rgba(0, 255, 0, 0.25)"

        # Final string will be the concatenated fields from the database: session id, crack_status, image name
        final_str = f"Showing current scan result for: {image_session.session_id}_{crack_status}_{image_session.image_name}"

        # Creating the name label
        current_scan_name = QLabel(final_str)
        current_scan_name.setStyleSheet('font: 18 13pt "Fira Code"; ')
        current_scan_name.setContentsMargins(0, 0, 0, 20)
        current_scan_name.setAlignment(Qt.AlignTop)  # type: ignore

        # Creating the signal label, (to notify user in a more visualized way if they have crack or not)
        crack_detection_status = QLabel(crack_detection_str)
        crack_detection_status.setStyleSheet(
            'font: 24 13pt "Fira Code";' + background_color_css
        )
        crack_detection_status.setContentsMargins(0, 15, 0, 15)
        crack_detection_status.setFixedWidth(400)
        crack_detection_status.setAlignment(Qt.AlignCenter)  # type: ignore

        # Creating the image label
        completed_img_path_raw = os.path.join(
            self.database.get_base_filepath(self.user_uuid),
            "complete",
            f"{image_session.session_id}-cropped.jpg",
        )

        self.current_scan_image_label = QLabel()
        if image_session.crack_detected == 1:
            current_scan_pixmap = QPixmap(completed_img_path)
        else:
            current_scan_pixmap = QPixmap(completed_img_path_raw)
        resized_current_scan_pixmap = current_scan_pixmap.scaled(400, 400)
        self.current_scan_image_label.setPixmap(resized_current_scan_pixmap)
        self.current_scan_image_label.setContentsMargins(0, 0, 0, 20)

        # Indicator label
        self.indicator_label = QLabel(
            "The 'normal' image is shown (regular crack detection)"
        )
        self.indicator_label.setStyleSheet('font: 18 13pt "Fira Code"; ')
        self.indicator_label.setContentsMargins(0, 0, 0, 20)

        # Creating the button to swap between images
        # Button for swapping between highlighted and unhighlighted images
        switch_image_button = QPushButton("Change Sensitivity")
        switch_image_button.setStyleSheet(
            "border-radius: 10px; "
            'font: 25 13pt "Fira Code"; '
            "background-color: rgb(56, 182, 255)"
        )
        switch_image_button.clicked.connect(self._swap_current_scan_image)
        switch_image_button.setEnabled(True)
        switch_image_button.setFixedWidth(200)
        if image_session.crack_detected == 0:
            switch_image_button.setEnabled(False)

        # Adding all widgets to the layout, aligning the whole thing
        self.current_scan_result_layout = QVBoxLayout()
        self.current_scan_result_layout.addWidget(current_scan_name)
        self.current_scan_result_layout.addWidget(crack_detection_status)
        self.current_scan_result_layout.addWidget(self.current_scan_image_label)
        self.current_scan_result_layout.addWidget(self.indicator_label)
        self.current_scan_result_layout.addWidget(switch_image_button)
        self.current_scan_result_layout.addWidget(self.buttonBox)

        for widget in [
            current_scan_name,
            crack_detection_status,
            self.current_scan_image_label,
            self.indicator_label,
            switch_image_button,
        ]:
            self.current_scan_result_layout.setAlignment(widget, Qt.AlignHCenter)  # type: ignore

        self.setLayout(self.current_scan_result_layout)

    def _swap_current_scan_image(self):

        """Swap between a highlighted image, a slightly more precise highlighted image (risk associated), and the
        reqular raw image. Checks the filepath to see if it has the '-cropped' suffix. Changes the
        FILEPATH_OF_PAST_SCAN_IMAGE string accordingly"""

        if "-cropped" in self.FILEPATH_OF_PAST_SCAN_IMAGE:
            unhighlighted_file_path = self.FILEPATH_OF_PAST_SCAN_IMAGE.replace(
                "-cropped", "-normal"
            )
            highlighted_output_pixmap = QPixmap(unhighlighted_file_path)
            resized_highlighted_output_pixmap = highlighted_output_pixmap.scaled(
                400, 400
            )
            self.current_scan_image_label.setPixmap(resized_highlighted_output_pixmap)
            self.FILEPATH_OF_PAST_SCAN_IMAGE = unhighlighted_file_path
            self.indicator_label.setText(
                "The 'normal' image is shown (regular crack detection)"
            )
        elif "-normal" in self.FILEPATH_OF_PAST_SCAN_IMAGE:
            highlighted_file_path = self.FILEPATH_OF_PAST_SCAN_IMAGE.replace(
                "-normal", "-precise"
            )
            unhighlighted_output_pixmap = QPixmap(highlighted_file_path)
            resized_unhighlighted_output_pixmap = unhighlighted_output_pixmap.scaled(
                400, 400
            )
            self.current_scan_image_label.setPixmap(resized_unhighlighted_output_pixmap)
            self.FILEPATH_OF_PAST_SCAN_IMAGE = highlighted_file_path
            self.indicator_label.setText(
                "The 'precise' image is shown (precise crack detection)"
            )
        elif "-precise" in self.FILEPATH_OF_PAST_SCAN_IMAGE:
            precise_highlighted_file_path = self.FILEPATH_OF_PAST_SCAN_IMAGE.replace(
                "-precise", "-cropped"
            )
            unhighlighted_output_pixmap = QPixmap(precise_highlighted_file_path)
            resized_unhighlighted_output_pixmap = unhighlighted_output_pixmap.scaled(
                400, 400
            )
            self.current_scan_image_label.setPixmap(resized_unhighlighted_output_pixmap)
            self.FILEPATH_OF_PAST_SCAN_IMAGE = precise_highlighted_file_path
            self.indicator_label.setText("The original image is displayed")
        else:
            print(
                "There was a problem in reading the file name of the image. Make sure that the image "
                "file path has the specified keywords in it. The keywords were specified in the "
                "function call for the crack_detect_method_1"
            )


class MainWindow(QMainWindow):
    """
    Main window for gui interface
    """

    def __init__(self, database: nmlDB) -> None:
        super().__init__()

        self.database = database
        self.USER_UUID = ""
        self.SELECTED_DATE = None
        self.SELECTED_SESSION_ID = None
        self.USER_EMAIL = None
        self.MOST_RECENT_IMAGE_SESSION = 0
        self.FILEPATH_OF_PAST_SCAN_IMAGE = ""
        self.image_session_dict = {}
        self.session_id_to_thread_worker = {}

        # Window Setup
        self.setWindowTitle("NML.ai")
        self.setMinimumSize(QSize(1080, 720))
        self.setWindowIcon(QIcon("assets/logo.png"))

        # Create all Widgets and layouts
        self.init_widgets()
        self.init_layouts()

        self.crack_detection_thread_pool = QThreadPool()

    def init_widgets(self):
        self.user_selector = QListWidget()
        self.user_selector.setFixedSize(250, 300)
        self.user_selector.addItems(self.database.get_all_users_emails())
        self.user_selector.currentItemChanged.connect(self.user_selector_index_changed)

        self.past_scan_date_selector = QListWidget()
        self.past_scan_date_selector.setFixedSize(236, 250)
        self.past_scan_date_selector.currentItemChanged.connect(
            self.past_scan_date_selector_index_changed
        )

        self.past_scan_image_session_selector = QListWidget()
        self.past_scan_image_session_selector.setFixedSize(236, 250)
        self.past_scan_image_session_selector.currentItemChanged.connect(
            self.past_scan_image_session_selector_index_changed
        )

        # Button for swapping between highlighted and unhighlighted images
        self.switch_image_button = QPushButton("Change Sensitivity")
        self.switch_image_button.setStyleSheet(
            "border-radius: 10px; "
            'font: 25 13pt "Fira Code"; '
            "background-color: rgb(56, 182, 255)"
        )
        self.switch_image_button.clicked.connect(self.swap_past_scan_image)
        self.switch_image_button.setEnabled(False)

        # Default to first item if exists
        if self.user_selector.count():
            self.user_selector.setCurrentRow(0)
            self.USER_EMAIL = self.user_selector.item(0).text()

        self.add_new_user_btn = QPushButton("Create User")
        self.add_new_user_btn.clicked.connect(self.create_new_user)
        self.add_new_user_btn.setStyleSheet(
            "border-radius: 10px; "
            'font: 25 13pt "Fira Code"; '
            "background-color: rgb(56, 182, 255)"
        )

        self.set_user_btn = QPushButton("Set User")
        self.set_user_btn.clicked.connect(self.set_user)
        self.set_user_btn.setStyleSheet(
            "border-radius: 10px; "
            'font: 25 13pt "Fira Code"; '
            "background-color: rgb(56, 182, 255)"
        )

        self.title_label = QLabel("NML.ai", self)
        self.title_label.setStyleSheet(
            'font: 25 58pt "Fira Code";'
            " color: rgb(79, 79, 79);"
            "background-color: transparent;"
        )

        # Initialize Video
        self.video_label = QLabel()
        if BETA_VERSION:
            grey = QPixmap(450, 800)
        else:
            grey = QPixmap(480, 640)
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

        # Initialize the past scan image
        self.past_scan_image_label = QLabel()
        filler_pixmap = QPixmap(400, 400)
        filler_pixmap.fill(QColor(0, 0, 0, 25))
        self.past_scan_image_label.setPixmap(filler_pixmap)

        self.current_scan_image_label = QLabel()

        # Capture image button
        self.capture_image_button = QPushButton("Capture Image")
        self.capture_image_button.setCheckable(False)
        self.capture_image_button.clicked.connect(self.capture_image_handler)
        self.capture_image_button.setEnabled(False)
        self.capture_image_button.setStyleSheet(
            "border-radius: 10px; "
            'font: 25 13pt "Fira Code"; '
            "background-color: rgb(56, 182, 255)"
        )

        # Capture image textbox for image name
        self.image_name_text = QLabel("Enter the Image Name:")
        self.image_name_box = QLineEdit()

        # Label for indicator showing which sensitivity image is being displayed
        self.indicator_label = QLabel(
            "The 'normal' image is shown (regular crack detection)"
        )
        self.indicator_label.setStyleSheet('font: 18 13pt "Fira Code"; ')
        self.indicator_label.setContentsMargins(0, 0, 0, 20)

        # Label for crack status (better visualization for whether or not a crack is detected)
        # Creating the signal label, (to notify user in a more visualized way if they have crack or not)
        self.crack_detection_status = QLabel()
        self.crack_detection_status.setContentsMargins(0, 15, 0, 15)
        self.crack_detection_status.setFixedWidth(400)
        self.crack_detection_status.setAlignment(Qt.AlignCenter)  # type: ignore

    def init_layouts(self):
        # Set the Layout
        main_layout = QVBoxLayout()
        self.stacked_layout = QStackedLayout()
        user_selector_layout = QVBoxLayout()
        past_scan_layout = QHBoxLayout()
        past_scan_left_lists = QVBoxLayout()
        past_scan_results = QVBoxLayout()
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
        self.capture_image_button.setFixedWidth(460)
        new_scan_layout.addWidget(self.capture_image_button)
        new_scan_layout.setAlignment(self.capture_image_button, Qt.AlignHCenter)  # type: ignore

        new_scan_container = QWidget()
        new_scan_container.setLayout(new_scan_layout)

        # Previous Scan Layout

        # Organizing the list widgets on a vertical layout (left side)
        past_scan_left_lists.addWidget(self.past_scan_date_selector)
        past_scan_left_lists.addWidget(self.past_scan_image_session_selector)

        # Organizing the results widgets on a vertical layout as well, (right side)
        past_scan_results.addWidget(self.crack_detection_status)
        past_scan_results.addWidget(self.past_scan_image_label)
        past_scan_results.addWidget(self.indicator_label)
        past_scan_results.addWidget(self.switch_image_button)

        for widget in [
            self.crack_detection_status,
            self.past_scan_image_label,
            self.indicator_label,
            self.switch_image_button,
        ]:
            past_scan_results.setAlignment(widget, Qt.AlignHCenter)  # type: ignore

        past_scan_layout.addLayout(past_scan_left_lists)
        past_scan_layout.addLayout(past_scan_results)

        # Centers each widget into its respective allocated square in the grid
        past_scan_layout.setAlignment(Qt.AlignCenter)  # type: ignore
        self.past_scan_image_label.setAlignment(Qt.AlignCenter)  # type: ignore

        # Set width of the swap images button, set left margin (lists were too close to left border), center the button
        self.switch_image_button.setFixedWidth(460)
        past_scan_layout.setContentsMargins(50, 0, 0, 0)
        past_scan_layout.setAlignment(self.switch_image_button, Qt.AlignHCenter)  # type: ignore

        past_scan_container = QWidget()
        past_scan_container.setLayout(past_scan_layout)

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
            "background-color: #d1e5e6;"
            # "background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0.2, y2:0.2, stop:0 rgba(56, 182, 255,1), stop:1 rgba(255,244,228,1));"
        )

    def user_selector_index_changed(self, i):
        print(f"user_selector index = {i.text()}")
        self.USER_EMAIL = i.text()

    def past_scan_date_selector_index_changed(self, i):
        date = i.text()
        print(f"past_scan_date_selector index = {date}")
        self.SELECTED_DATE = date
        result = []

        # Assigning names to the crack_status for readability in the second list widget
        for image_session in self.image_session_dict[date]:
            crack_status = ""
            if image_session.crack_detected == 1:
                crack_status = "CRACK"
            elif image_session.crack_detected == 0:
                crack_status = "NOCRACK"

            # Final string will be the concatenated fields from the database: session id, crack_status, image name
            final_str = (
                f"{image_session.session_id}_{crack_status}_{image_session.image_name}"
            )

            # Result is the list of all the final strings (concatenated fields) to pass into the second list widget
            result.append(final_str)

        # Reset the filepath of the displayed image
        self.FILEPATH_OF_PAST_SCAN_IMAGE = ""

        # Remove the current image from the pixmap and put a filler, in the case user wants to select a different date
        filler_pixmap = QPixmap(400, 400)
        filler_pixmap.fill(QColor(0, 0, 0, 25))
        self.past_scan_image_label.setPixmap(filler_pixmap)

        self.switch_image_button.setEnabled(False)

        # Blocks the .clear() signal, since .clear() triggers the .connect of the second list widget, causing a crash
        self.past_scan_image_session_selector.blockSignals(True)
        self.past_scan_image_session_selector.clear()
        self.past_scan_image_session_selector.blockSignals(False)

        self.past_scan_image_session_selector.addItems(result)

    def past_scan_image_session_selector_index_changed(self, i):
        # session_info contains the session_id, crack_status, and image_name all concatenated to be displayed on the list
        session_info = i.text()
        print(f"past_scan_date_selector index = {session_info}")

        # Gets the actual session id from the name
        session_id, crack_status, img_name = session_info.split("_")
        completed_img_path = os.path.join(
            self.database.get_base_filepath(self.USER_UUID),  # type: ignore
            "complete",  # type: ignore
            f"{session_id}-normal.jpg",  # type: ignore
        )

        if crack_status == "CRACK":
            completed_img_path = os.path.join(
                self.database.get_base_filepath(self.USER_UUID),  # type: ignore
                "complete",  # type: ignore
                f"{session_id}-normal.jpg",  # type: ignore
            )
            crack_detection_str = "Oh no! Crack detected!"
            background_color_css = "background-color: rgba(255, 0, 0, 0.25);"
        else:
            completed_img_path = os.path.join(
                self.database.get_base_filepath(self.USER_UUID),  # type: ignore
                "complete",  # type: ignore
                f"{session_id}-cropped.jpg",  # type: ignore
            )
            crack_detection_str = "Good job! No crack detected!"
            background_color_css = "background-color: rgba(0, 255, 0, 0.25);"

        self.crack_detection_status.setText(crack_detection_str)
        self.crack_detection_status.setStyleSheet(
            'font: 24 13pt "Fira Code";' + background_color_css
        )

        # Sets the filepath of the image, then displays it
        self.FILEPATH_OF_PAST_SCAN_IMAGE = completed_img_path
        highlighted_output_pixmap = QPixmap(completed_img_path)
        resized_highlighted_output_pixmap = highlighted_output_pixmap.scaled(400, 400)
        self.past_scan_image_label.setPixmap(resized_highlighted_output_pixmap)
        self.switch_image_button.setEnabled(True)

    def swap_past_scan_image(self):

        """Swap between a highlighted image, a slightly more precise highlighted image (risk associated), and the
        reqgular raw image. Checks the filepath to see if it has the '-cropped' suffix. Changes the
        FILEPATH_OF_PAST_SCAN_IMAGE string accordingly"""

        if "-cropped" in self.FILEPATH_OF_PAST_SCAN_IMAGE:
            highlighted_file_path = self.FILEPATH_OF_PAST_SCAN_IMAGE.replace(
                "-cropped", "-normal"
            )
            highlighted_output_pixmap = QPixmap(highlighted_file_path)
            resized_highlighted_output_pixmap = highlighted_output_pixmap.scaled(
                400, 400
            )
            self.past_scan_image_label.setPixmap(resized_highlighted_output_pixmap)
            self.FILEPATH_OF_PAST_SCAN_IMAGE = highlighted_file_path
            self.indicator_label.setText(
                "The 'normal' image is shown (regular crack detection)"
            )
        elif "-normal" in self.FILEPATH_OF_PAST_SCAN_IMAGE:
            highlighted_file_path = self.FILEPATH_OF_PAST_SCAN_IMAGE.replace(
                "-normal", "-precise"
            )
            unhighlighted_output_pixmap = QPixmap(highlighted_file_path)
            resized_unhighlighted_output_pixmap = unhighlighted_output_pixmap.scaled(
                400, 400
            )
            self.past_scan_image_label.setPixmap(resized_unhighlighted_output_pixmap)
            self.FILEPATH_OF_PAST_SCAN_IMAGE = highlighted_file_path
            self.indicator_label.setText(
                "The 'precise' image is shown (regular crack detection)"
            )
        elif "-precise" in self.FILEPATH_OF_PAST_SCAN_IMAGE:
            highlighted_file_path = self.FILEPATH_OF_PAST_SCAN_IMAGE.replace(
                "-precise", "-cropped"
            )
            unhighlighted_output_pixmap = QPixmap(highlighted_file_path)
            resized_unhighlighted_output_pixmap = unhighlighted_output_pixmap.scaled(
                400, 400
            )
            self.past_scan_image_label.setPixmap(resized_unhighlighted_output_pixmap)
            self.FILEPATH_OF_PAST_SCAN_IMAGE = highlighted_file_path
            self.indicator_label.setText("The original image is displayed")

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

            # Populate past scans initially
            all_image_session = self.database.get_all_img_sessions_for_uuid(
                self.USER_UUID  # type: ignore
            )

            for image_session in all_image_session:
                date = str(image_session.date.date())
                if self.image_session_dict.get(date, None) is None:
                    self.image_session_dict[date] = []
                self.image_session_dict[date].append(image_session)
            self.past_scan_date_selector.addItems(self.image_session_dict.keys())

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
        if BETA_VERSION:
            # qt_image = qt_image.scaled(720, 1280)
            qt_image = qt_image.scaled(450, 800)
        self.video_label.setPixmap(qt_image)

    # @pyqtSlot(bool)
    def enable_initial_capture_toggle(self, toggle_state: bool) -> None:
        self.capture_image_button.setEnabled(toggle_state)

    # @pyqtSlot(bool)
    def completed_capture_handler(self, capture_status: bool) -> None:
        """Handler after an image is captured"""
        if self.USER_UUID:
            image_crack_detection_worker = CrackDetectHighlight(
                self.database, self.MOST_RECENT_IMAGE_SESSION, self.USER_UUID
            )
            image_crack_detection_worker.signals.finished.connect(
                self.update_past_scans_list
            )
            self.session_id_to_thread_worker[
                self.MOST_RECENT_IMAGE_SESSION
            ] = image_crack_detection_worker
            self.crack_detection_thread_pool.start(image_crack_detection_worker)

        self.capture_image_button.setEnabled(capture_status)

    # @pyqtSlot(int)
    def update_past_scans_list(self, image_session_id):
        """Updates the list of past scans after an image session computation is completed"""
        image_session_id = int(image_session_id)
        image_session = self.database.get_img_session_for_uuid(
            self.USER_UUID, image_session_id  # type: ignore
        )
        self.session_id_to_thread_worker[image_session_id].stop_thread()

        crack_status = ""
        if image_session.crack_detected == 1:
            crack_status = "CRACK"
        elif image_session.crack_detected == 0:
            crack_status = "NOCRACK"

        final_str = (
            f"{image_session.session_id}_{crack_status}_{image_session.image_name}"
        )

        date = str(image_session.date.date())
        # If no dates in date list, add date
        current_list_widget_dates = [
            self.past_scan_date_selector.item(x).text()
            for x in range(self.past_scan_date_selector.count())
        ]
        if not date in current_list_widget_dates:
            self.past_scan_date_selector.addItem(date)

        if self.image_session_dict.get(date, None) is None:
            self.image_session_dict[date] = []
        self.image_session_dict[date].append(image_session)

        if self.SELECTED_DATE == date:
            self.past_scan_image_session_selector.addItem(final_str)  # type: ignore

        print("Crack detection is done")
        show_current_scan_result = PreviewImageDialog(
            self.USER_UUID,
            image_session,
            self.database,
            parent=self,
        )

        dialog_action = show_current_scan_result.exec()
        if dialog_action:
            print("Closed!")

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
