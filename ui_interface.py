# ui_interface.py
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from table2 import DataTablePage   # <-- import your table class
import icons_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 500)
        MainWindow.setStyleSheet("*{ border: none; }")

        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setStyleSheet("background-color: rgb(24, 24, 36);")

        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)   

                # ================= LEFT SIDEBAR =================
        self.slide_menu_container = QFrame(self.centralwidget)
        self.slide_menu_container.setMaximumSize(QSize(450, 16777215))
        self.slide_menu_container.setStyleSheet("background-color: rgb(9, 5, 13);")
        self.verticalLayout_2 = QVBoxLayout(self.slide_menu_container)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)

        # slide_menu frame (will contain top container + exit area)
        self.slide_menu = QFrame(self.slide_menu_container)
        self.verticalLayout_5 = QVBoxLayout(self.slide_menu)
        self.verticalLayout_5.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout_5.setSpacing(6)
        # anchor everything at top
        self.verticalLayout_5.setAlignment(Qt.AlignTop)

        # --- Logo + Title ---
        self.logo_frame = QFrame(self.slide_menu)
        self.logo_layout = QVBoxLayout(self.logo_frame)
        self.logo_layout.setContentsMargins(0, 0, 0, 0)
        self.logo_layout.setSpacing(4)

        self.label_logo = QLabel(self.logo_frame)
        self.label_logo.setPixmap(QPixmap(":/icons/icons/twitter.svg"))
        self.label_logo.setAlignment(Qt.AlignCenter)

        self.label_title = QLabel("APP NAME", self.logo_frame)
        font = QFont(); font.setPointSize(12); font.setBold(True)
        self.label_title.setFont(font)
        self.label_title.setAlignment(Qt.AlignCenter)

        self.logo_layout.addWidget(self.label_logo, 0, Qt.AlignCenter)
        self.logo_layout.addWidget(self.label_title, 0, Qt.AlignCenter)

        # --- Menu (buttons) ---
        self.menu_frame = QFrame(self.slide_menu)
        self.menu_layout = QVBoxLayout(self.menu_frame)
        self.menu_layout.setContentsMargins(0, 0, 0, 0)
        self.menu_layout.setSpacing(6)
        self.menu_layout.setAlignment(Qt.AlignTop)

        # Sidebar buttons
        self.btn_dashboard = QPushButton("Dashboard", self.menu_frame)
        self.btn_dashboard.setIcon(QIcon(":/icons/icons/github.svg"))

        self.btn_clients = QPushButton("Manage Clients", self.menu_frame)
        self.btn_clients.setIcon(QIcon(":/icons/icons/users.svg"))
        

        self.btn_products = QPushButton("Manage Products", self.menu_frame)
        self.btn_products.setIcon(QIcon(":/icons/icons/package.svg"))

        self.btn_suppliers = QPushButton("Manage Suppliers", self.menu_frame)
        self.btn_suppliers.setIcon(QIcon(":/icons/icons/truck.svg"))

        self.btn_reports = QPushButton("Reports", self.menu_frame)
        self.btn_reports.setIcon(QIcon(":/icons/icons/bar-chart-2.svg"))

        self.btn_settings = QPushButton("Settings", self.menu_frame)
        self.btn_settings.setIcon(QIcon(":/icons/icons/key.svg"))

        # style all buttons
        for btn in [
            self.btn_dashboard, self.btn_clients, self.btn_products,
            self.btn_suppliers, self.btn_reports, self.btn_settings
        ]:
            btn.setIconSize(QSize(18, 18))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    color: white;
                    padding: 6px 20px;
                    text-align: left;
                    font-size: 14px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: rgb(40, 40, 60);
                }
            """)
            self.menu_layout.addWidget(btn)


        # --- put logo + menu inside a top_container so they stay together pinned to top ---
        self.top_container = QFrame(self.slide_menu)
        self.top_layout = QVBoxLayout(self.top_container)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setSpacing(8)
        self.top_layout.setAlignment(Qt.AlignTop)
        self.top_layout.addWidget(self.logo_frame, 0, Qt.AlignTop)
        self.top_layout.addWidget(self.menu_frame, 0, Qt.AlignTop)

        # Add the top container to the slide menu, then add a stretch so anything after it is pushed down
        self.verticalLayout_5.addWidget(self.top_container)
        self.verticalLayout_5.addStretch()

        # Exit button at bottom of sidebar
        self.frame_9 = QFrame(self.slide_menu)
        self.horizontalLayout_9 = QHBoxLayout(self.frame_9)
        self.exit_button = QPushButton("Exit", self.frame_9)
        self.exit_button.setStyleSheet("""
                QPushButton {
                    color: white;
                     
                    font-size: 14px;             /* increase font size */
                    border: none;
                    
                }
                
            """)
        self.exit_button.setIcon(QIcon(":/icons/icons/external-link.svg"))
        self.exit_button.setIconSize(QSize(16, 16))
        self.horizontalLayout_9.addWidget(self.exit_button, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.verticalLayout_5.addWidget(self.frame_9, 0, Qt.AlignBottom)

        self.verticalLayout_2.addWidget(self.slide_menu)
        self.horizontalLayout.addWidget(self.slide_menu_container)

        # ================= MAIN BODY =================
        self.main_body = QFrame(self.centralwidget)
        self.verticalLayout = QVBoxLayout(self.main_body)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)

        # --- Header ---
        self.header_frame = QFrame(self.main_body)
        self.header_frame.setStyleSheet("background-color: rgb(9, 5, 13);")
        self.horizontalLayout_2 = QHBoxLayout(self.header_frame)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0,0)
        self.horizontalLayout_2.setSpacing(4)

        # Left: sidebar toggle
        self.frame_6 = QFrame(self.header_frame)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_6)
        self.open_close_side_bar_btn = QPushButton(self.frame_6)
        self.open_close_side_bar_btn.setIcon(QIcon(":/icons/icons/align-left.svg"))
        self.open_close_side_bar_btn.setIconSize(QSize(28, 28))
        self.open_close_side_bar_btn.setCursor(Qt.PointingHandCursor)
        self.horizontalLayout_7.addWidget(self.open_close_side_bar_btn, 0, Qt.AlignLeft)
        self.horizontalLayout_2.addWidget(self.frame_6, 0, Qt.AlignLeft)

        # Center: search bar (keep old size behavior)
        self.frame_search = QFrame(self.header_frame)
        self.h_search = QHBoxLayout(self.frame_search)
        self.lineEdit = QLineEdit(self.frame_search)
        self.lineEdit.setMinimumSize(QSize(135, 0))     # same as earlier
        self.lineEdit.setMaximumWidth(250)              # prevent huge expansion
        self.lineEdit.setPlaceholderText("Search")
        self.lineEdit.setStyleSheet("border-bottom: 3px solid rgb(230, 5, 64); color: white; background: transparent;")
        self.pushButton_6 = QPushButton(self.frame_search)
        self.pushButton_6.setIcon(QIcon(":/icons/icons/search.svg"))
        self.pushButton_6.setCursor(Qt.PointingHandCursor)
        self.h_search.addWidget(self.lineEdit)
        self.h_search.addWidget(self.pushButton_6)
        self.horizontalLayout_2.addWidget(self.frame_search)

        # Stretch to push the next widgets to the right
        self.horizontalLayout_2.addStretch()

        # Right: profile + notification
        self.frame_2 = QFrame(self.header_frame)
        self.horizontalLayout_5 = QHBoxLayout(self.frame_2)
        self.pushButton_5 = QPushButton(self.frame_2)   # profile
        self.pushButton_5.setIcon(QIcon(":/icons/icons/user.svg"))
        self.pushButton_5.setIconSize(QSize(20, 20))
        self.pushButton_5.setCursor(Qt.PointingHandCursor)
        self.pushButton_4 = QPushButton(self.frame_2)   # notification
        self.pushButton_4.setIcon(QIcon(":/icons/icons/bell.svg"))
        self.pushButton_4.setIconSize(QSize(20, 20))
        self.pushButton_4.setCursor(Qt.PointingHandCursor)
        self.horizontalLayout_5.addWidget(self.pushButton_5)
        self.horizontalLayout_5.addWidget(self.pushButton_4)
        self.horizontalLayout_2.addWidget(self.frame_2, 0, Qt.AlignRight)

        # Window controls (minimize / restore / close) — top-rightmost
        self.window_controls = QFrame(self.header_frame)
        self.window_controls_layout = QHBoxLayout(self.window_controls)
        self.window_controls_layout.setContentsMargins(0, 0, 0, 0)
        self.window_controls_layout.setSpacing(4)

        self.minimize_window_button = QPushButton(self.window_controls)
        self.minimize_window_button.setIcon(QIcon(":/icons/icons/arrow-down-left.svg"))
        self.minimize_window_button.setFixedSize(32, 32)
        self.minimize_window_button.setCursor(Qt.PointingHandCursor)

        self.restore_window_button = QPushButton(self.window_controls)
        self.restore_window_button.setIcon(QIcon(":/icons/icons/maximize-2.svg"))
        self.restore_window_button.setFixedSize(32, 32)
        self.restore_window_button.setCursor(Qt.PointingHandCursor)

        self.close_window_button = QPushButton(self.window_controls)
        self.close_window_button.setIcon(QIcon(":/icons/icons/x.svg"))
        self.close_window_button.setFixedSize(32, 32)
        self.close_window_button.setCursor(Qt.PointingHandCursor)

        for btn in [self.minimize_window_button, self.restore_window_button, self.close_window_button]:
            btn.setStyleSheet("QPushButton:hover { background-color: rgb(40,40,60); }")

        self.window_controls_layout.addWidget(self.minimize_window_button)
        self.window_controls_layout.addWidget(self.restore_window_button)
        self.window_controls_layout.addWidget(self.close_window_button)
        self.horizontalLayout_2.addWidget(self.window_controls, 0, Qt.AlignRight)

        self.verticalLayout.addWidget(self.header_frame, 0, Qt.AlignTop)

               # --- Main Pages (stacked) ---
        self.pages = QStackedWidget(self.main_body)

        self.page_dashboard = QLabel("Dashboard Page")
        self.page_dashboard.setAlignment(Qt.AlignCenter)

        self.page_clients = QLabel("Manage Clients Page")
        #self.page_clients.setAlignment(Qt.AlignCenter)
        self.page_clients = DataTablePage()

        self.page_products = QLabel("Manage Products Page")
        self.page_products.setAlignment(Qt.AlignCenter)

        self.page_suppliers = QLabel("Manage Suppliers Page")
        self.page_suppliers.setAlignment(Qt.AlignCenter)

        self.page_reports = QLabel("Reports Page")
        self.page_reports.setAlignment(Qt.AlignCenter)

        self.page_settings = QLabel("Settings Page")
        self.page_settings.setAlignment(Qt.AlignCenter)

        # add to stacked widget
        self.pages.addWidget(self.page_dashboard)   # index 0
        self.pages.addWidget(self.page_clients)     # index 1
        self.pages.addWidget(self.page_products)    # index 2
        self.pages.addWidget(self.page_suppliers)   # index 3
        self.pages.addWidget(self.page_reports)     # index 4
        self.pages.addWidget(self.page_settings)    # index 5
        self.verticalLayout.addWidget(self.pages)


        # --- Footer with size grip ---
        self.footer = QFrame(self.main_body)
        self.horizontalLayout_3 = QHBoxLayout(self.footer)
        self.label = QLabel("Modern UI v 7.7.7", self.footer)
        self.label.setStyleSheet("""
                QLabel {
                    color: white;
                    
                    font-size: 12px;             /* increase font size */
                    border: none;
                    
                }
                
            """)
        self.horizontalLayout_3.addWidget(self.label, 0, Qt.AlignLeft)

        # add QSizeGrip holder
        self.size_grip = QFrame(self.footer)
        self.size_grip.setMinimumSize(QSize(10, 10))
        self.size_grip.setMaximumSize(QSize(10, 10))
        self.horizontalLayout_3.addWidget(self.size_grip, 0, Qt.AlignRight | Qt.AlignBottom)

        self.verticalLayout.addWidget(self.footer, 0, Qt.AlignBottom)

        self.horizontalLayout.addWidget(self.main_body)
        MainWindow.setCentralWidget(self.centralwidget)

        # connections: switching pages
        self.btn_dashboard.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.btn_clients.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        self.btn_products.clicked.connect(lambda: self.pages.setCurrentIndex(2))
        self.btn_suppliers.clicked.connect(lambda: self.pages.setCurrentIndex(3))
        self.btn_reports.clicked.connect(lambda: self.pages.setCurrentIndex(4))
        self.btn_settings.clicked.connect(lambda: self.pages.setCurrentIndex(5))
        self.exit_button.clicked.connect(MainWindow.close)


        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
