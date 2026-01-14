import sys
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout
)


class DataTablePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)

        # --- Top Search Bar ---
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search records...")
        self.search_bar.setStyleSheet(
            "padding: 6px; border: 1px solid #e60540; color: white; background: #181824;"
        )
        main_layout.addWidget(self.search_bar)

        # --- Data Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Email", "Mobile", "Created",
            "Insert", "View", "Delete"
        ])

        # ✅ Hide extra index (row numbers)
        self.table.verticalHeader().setVisible(False)

        self.table.setStyleSheet("""
        QTableWidget::item:selected {
            background-color: transparent;
        }
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

        # Demo rows
        self.add_row("1", "John Doe", "johndoe@example.com", "+91-9999999999", "2025-09-08")
        self.add_row("2", "John", "john@example.com", "+91-9999999999", "2025-09-08")
        self.add_row("3", "Doe", "doe@example.com", "+91-9999999999", "2025-09-08")

        main_layout.addWidget(self.table)

    def styled_button(self, icon_path, tooltip=""):
        btn = QPushButton()
        btn.setIcon(QIcon(icon_path))
        btn.setToolTip(tooltip)
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
        btn.setFixedSize(32, 28)
        return btn

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
        btn_insert.clicked.connect(lambda _, r=row_position: self.insert_row_below(r))
        self.set_centered_widget(row_position, 5, btn_insert)

        # View Button
        btn_view = self.styled_button(":/icons/icons/eye.svg", "View row details")
        btn_view.clicked.connect(lambda _, r=row_position: self.view_row(r))
        self.set_centered_widget(row_position, 6, btn_view)

        # Delete Button
        btn_delete = self.styled_button(":/icons/icons/trash.svg", "Delete row")
        btn_delete.clicked.connect(lambda _, r=row_position: self.delete_row(r))
        self.set_centered_widget(row_position, 7, btn_delete)

    def set_centered_widget(self, row, column, widget):
        """Wrap widget in a layout to center it inside the cell"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(widget, alignment=Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(layout)
        self.table.setCellWidget(row, column, container)

    def insert_row_below(self, row):
        print(f"Insert below row {row}")
        self.add_row("NEW", "New Name", "new@example.com", "+91-0000000000", "2025-09-08")

    def view_row(self, row):
        values = [self.table.item(row, col).text() for col in range(5)]
        print(f"Viewing row {row}: {values}")

    def delete_row(self, row):
        print(f"Deleting row {row}")
        self.table.removeRow(row)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    table_page = DataTablePage()
    window.setCentralWidget(table_page)
    window.resize(950, 500)
    window.setWindowTitle("DataTable with Centered Action Buttons")
    window.show()
    sys.exit(app.exec_())
