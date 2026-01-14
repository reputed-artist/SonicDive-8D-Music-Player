import sys, sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout,
    QPushButton, QDialog, QFormLayout, QLabel, QDialogButtonBox, QLineEdit
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox

DB_FILE = "message.db"


class DataTablePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)

        # --- Top Search Bar ---
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search records...")
        self.search_bar.textChanged.connect(self.search_records)
        main_layout.addWidget(self.search_bar)

        # --- Data Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Email", "Mobile", "Created",
            "Insert", "View", "Delete"
        ])
        self.table.verticalHeader().setVisible(False)

        self.table.setStyleSheet("""
        QTableWidget::item:selected { background-color: transparent; }
        QTableWidget {
            background-color: #181824;
            alternate-background-color: #1e1e2e;
            color: white;
            gridline-color: #333;
            border: 1px solid #444;
        }
        QHeaderView::section {
            background-color: #09050d;
            color: #e60540;
            padding: 6px;
            border: none;
        }
        """)

        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        main_layout.addWidget(self.table)

        # Load data from DB
        self.load_data_from_db()

    def db_connection(self):
        return sqlite3.connect(DB_FILE)

    def styled_button(self, icon_path, tooltip=""):
        btn = QPushButton()
        btn.setIcon(QIcon(icon_path))
        btn.setToolTip(tooltip)
        btn.setFixedSize(32, 28)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        return btn

    def set_centered_widget(self, row, column, widget):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(widget, alignment=Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(layout)
        self.table.setCellWidget(row, column, container)

    def load_data_from_db(self):
        """Load all rows from DB into the table"""
        self.table.setRowCount(0)
        conn = self.db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, mobile, created FROM messages")
        for row in cur.fetchall():
            self.add_row(*map(str, row))
        conn.close()

    def add_row(self, id_, name, email, mobile, created):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        # Fill normal data cells
        self.table.setItem(row_position, 0, QTableWidgetItem(id_))
        self.table.setItem(row_position, 1, QTableWidgetItem(name))
        self.table.setItem(row_position, 2, QTableWidgetItem(email))
        self.table.setItem(row_position, 3, QTableWidgetItem(mobile))
        self.table.setItem(row_position, 4, QTableWidgetItem(created))

        # Insert Button
        btn_insert = self.styled_button(":/icons/icons/edit.svg", "Insert new row")
        btn_insert.clicked.connect(lambda _, r=row_position: self.insert_row_dialog(r))
        self.set_centered_widget(row_position, 5, btn_insert)

        # View Button
        btn_view = self.styled_button(":/icons/icons/eye.svg", "View row details")
        btn_view.clicked.connect(lambda _, r=row_position: self.view_row_dialog(r))
        self.set_centered_widget(row_position, 6, btn_view)

        # Delete Button
        btn_delete = self.styled_button(":/icons/icons/trash.svg", "Delete row")
        btn_delete.clicked.connect(lambda _, r=row_position: self.delete_row(r))
        self.set_centered_widget(row_position, 7, btn_delete)

    # ------------------ Dialogs ------------------
    def insert_row_dialog(self, row):
        dialog = QDialog(self)
        dialog.setWindowTitle("Insert New Record")
        dialog.setFixedSize(400, 220)  # Slightly taller to accommodate spacing

        # --- Main vertical layout with top margin to shift content down ---
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(20, 20, 20, 20)  # left, top, right, bottom
        main_layout.setSpacing(10)

        # --- Form layout ---
        form = QFormLayout()
        form.setSpacing(10)
        main_layout.addLayout(form)

        # --- Input fields ---
        name_input = QLineEdit()
        email_input = QLineEdit()
        mobile_input = QLineEdit()

        # Reduce textbox height and style
        for widget in [name_input, email_input, mobile_input]:
            widget.setFixedHeight(25)  # smaller textbox height
            widget.setStyleSheet("""
                color: white;
                background-color: white;
                border: 1px solid #e60540;
                padding: 2px 4px;
            """)

        # --- Labels ---
        name_label = QLabel("Name:")
        email_label = QLabel("Email:")
        mobile_label = QLabel("Mobile:")
        for label in [name_label, email_label, mobile_label]:
            label.setStyleSheet("color: white;")

        form.addRow(name_label, name_input)
        form.addRow(email_label, email_input)
        form.addRow(mobile_label, mobile_input)

        # --- Spacer to push buttons slightly down ---
        main_layout.addStretch(1)

        # --- Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #e60540;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        main_layout.addWidget(buttons)

        # --- Execute dialog ---
        if dialog.exec_() == QDialog.Accepted:
            name, email, mobile = name_input.text(), email_input.text(), mobile_input.text()
            conn = self.db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO messages (name, email, mobile, created) VALUES (?, ?, ?, date('now'))",
                (name, email, mobile)
            )
            conn.commit()
            conn.close()
            self.load_data_from_db()


    def view_row_dialog(self, row):
        dialog = QDialog(self)
        dialog.setWindowTitle("View Record")
        dialog.setFixedSize(400, 200)

        main_layout = QVBoxLayout(dialog)
        form = QFormLayout()
        main_layout.addLayout(form)

        # Fetch data
        name = self.table.item(row, 1).text()
        email = self.table.item(row, 2).text()
        mobile = self.table.item(row, 3).text()

        # Right-side labels (data)
        name_label = QLabel(name)
        email_label = QLabel(email)
        mobile_label = QLabel(mobile)
        for label in [name_label, email_label, mobile_label]:
            label.setStyleSheet("color: white;")

        # Left-side labels (field names)
        name_text_label = QLabel("Name:")
        name_text_label.setStyleSheet("color: white;")
        email_text_label = QLabel("Email:")
        email_text_label.setStyleSheet("color: white;")
        mobile_text_label = QLabel("Mobile:")
        mobile_text_label.setStyleSheet("color: white;")

        # Add rows to form
        form.addRow(name_text_label, name_label)
        form.addRow(email_text_label, email_label)
        form.addRow(mobile_text_label, mobile_label)

        # Spacer
        main_layout.addStretch(1)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #e60540;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        buttons.accepted.connect(dialog.accept)
        main_layout.addWidget(buttons)

        dialog.exec_()


    


    def delete_row(self, row):
        # Custom confirmation dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Confirm Deletion")
        dialog.setFixedSize(300, 120)
        
        layout = QVBoxLayout(dialog)
        
        # Message
        msg = QLabel("Are you sure you want to delete this record?")
        msg.setStyleSheet("color: white;")
        layout.addWidget(msg)
        
        # Spacer
        layout.addStretch(1)
        
        # Buttons layout
        btn_layout = QHBoxLayout()
        
        yes_btn = QPushButton("Yes")
        yes_btn.setStyleSheet("""
            background-color: white;
            color: #e60540;
            border-radius: 4px;
            padding: 6px 12px;
        """)
        
        no_btn = QPushButton("No")
        no_btn.setStyleSheet("""
            background-color: white;
            color: #e60540;
            border-radius: 4px;
            padding: 6px 12px;
        """)
        
        btn_layout.addWidget(yes_btn)
        btn_layout.addWidget(no_btn)
        layout.addLayout(btn_layout)
        
        # Connect buttons
        yes_btn.clicked.connect(lambda: dialog.done(1))
        no_btn.clicked.connect(lambda: dialog.done(0))
        
        # Execute dialog
        result = dialog.exec_()
        
        if result == 1:
            # Delete from DB
            id_ = self.table.item(row, 0).text()
            conn = self.db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM messages WHERE id=?", (id_,))
            conn.commit()
            conn.close()
            # Remove row
            self.table.removeRow(row)

    # ------------------ Search ------------------

    def search_records(self, text):
        for row in range(self.table.rowCount()):
            match = False
            for col in range(1, 5):  # skip ID, check other columns
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    table_page = DataTablePage()
    window.setCentralWidget(table_page)
    window.resize(950, 500)
    window.setWindowTitle("DataTable with DB Integration")
    window.show()
    sys.exit(app.exec_())
