########################################################################
## IMPORTS
########################################################################
import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import QApplication

########################################################################
# IMPORT GUI FILE
from ui_interface import *
########################################################################
import os
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QT_OPENGL"] = "software"
import sys

########################################################################
## MAIN WINDOW CLASS
########################################################################
class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        ########################################################################
        ## Frameless Window (custom title bar)
        ########################################################################
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)

        # Optional: smoother scaling on high DPI
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)

        ########################################################################
        ## Shadow Effect (lighter, avoids Windows API bug)
        ########################################################################
        self.shadow = QGraphicsDropShadowEffect(self.ui.centralwidget)
        self.shadow.setBlurRadius(25)  # reduce blur (was 50 → safer)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(2)
        self.shadow.setColor(QColor(0, 0, 0, 150))

        self.ui.centralwidget.setGraphicsEffect(self.shadow)



        #######################################################################
        # Set window Icon
        #######################################################################
        self.setWindowIcon(QIcon(":/icons/icons/github.svg"))
        self.setWindowTitle("MODERN UI")

        #######################################################################
        # Window Size grip to resize window
        #######################################################################
        QSizeGrip(self.ui.size_grip)

        #######################################################################
        # Minimize, Close, Exit
        #######################################################################
        self.ui.minimize_window_button.clicked.connect(lambda: self.showMinimized())
        self.ui.close_window_button.clicked.connect(lambda: self.close())
        self.ui.exit_button.clicked.connect(lambda: self.close())
        # In Ui_MainWindow.setupUi, inside header_frame layout:
       


        #######################################################################
        # Restore/Maximize
        #######################################################################
        self.ui.restore_window_button.clicked.connect(lambda: self.restore_or_maximize_window())

        #######################################################################
        # Move window on mouse drag
        #######################################################################
        def moveWindow(e):
            if not self.isMaximized():
                if e.buttons() == Qt.LeftButton:
                    self.move(self.pos() + e.globalPos() - self.clickPosition)
                    self.clickPosition = e.globalPos()
                    e.accept()
        self.ui.header_frame.mouseMoveEvent = moveWindow

        #######################################################################
        # Left Menu toggle
        #######################################################################
        self.ui.open_close_side_bar_btn.clicked.connect(lambda: self.slideLeftMenu())

        self.show()

    ########################################################################
    # Slide left menu
    ########################################################################
    def slideLeftMenu(self):
        width = self.ui.slide_menu_container.width()
        if width == 0:
            newWidth = 450
            self.ui.open_close_side_bar_btn.setIcon(QIcon(u":/icons/icons/chevron-left.svg"))
        else:
            newWidth = 0
            self.ui.open_close_side_bar_btn.setIcon(QIcon(u":/icons/icons/align-left.svg"))

        self.animation = QPropertyAnimation(self.ui.slide_menu_container, b"maximumWidth")
        self.animation.setDuration(250)
        self.animation.setStartValue(width)
        self.animation.setEndValue(newWidth)
        self.animation.setEasingCurve(QEasingCurve.InOutQuart)
        self.animation.start()

    ########################################################################
    # Mouse press
    ########################################################################
    def mousePressEvent(self, event):
        self.clickPosition = event.globalPos()

    ########################################################################
    # Update restore button icon
    ########################################################################
    def restore_or_maximize_window(self):
        if self.isMaximized():
            self.showNormal()
            self.ui.restore_window_button.setIcon(QIcon(u":/icons/icons/maximize-2.svg"))
        else:
            self.showMaximized()
            self.ui.restore_window_button.setIcon(QIcon(u":/icons/icons/minimize-2.svg"))

########################################################################
## EXECUTE APP
########################################################################
if __name__ == "__main__":
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    # Correct way: use the enum, not int
    if hasattr(QApplication, "setHighDpiScaleFactorRoundingPolicy"):
    	QApplication.setHighDpiScaleFactorRoundingPolicy(
        	Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    	)
    window = MainWindow()
    sys.exit(app.exec_())
