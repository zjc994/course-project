import sys
import os
qt_plugin_path = os.path.join(
    os.path.expanduser("~"),
    "AppData", "Roaming", "Python", "Python313",
    "site-packages", "PyQt5", "Qt5", "plugins"
)
#os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(qt_plugin_path, "platforms")
#os.environ["QT_PLUGIN_PATH"] = qt_plugin_path

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QMessageBox, QShortcut
from PyQt5.QtGui import QPixmap, QIcon, QKeySequence
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect

class StartGameBackground(QMainWindow):
    def __init__(self, main_window=None, width=1280, height=720):
        super().__init__()
        self.setWindowTitle("英雄试炼")
        self.resize(width, height)
        
        self.setMinimumSize(1280, 720)
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.background = QLabel(self.central_widget)
        self.bg_original_pixmap = QPixmap("images/background/initial_background.jpg")

        self.title = QLabel(self.central_widget)
        self.title_original_pixmap = QPixmap("images/objects/title_of_the_game.png")
        self.title.setAttribute(Qt.WA_TranslucentBackground)

        self.button_original_width = 160
        self.button_original_height = 50

        self.start_btn = QPushButton("", self.central_widget)
        self.start_btn.setFlat(True)
        self.start_btn.setIcon(QIcon("images/ui/start_game_button.png"))
        self.start_btn.setStyleSheet("border:none; background-color:transparent;")
        self.start_btn.clicked.connect(self.on_start_clicked)

        self.help_btn = QPushButton("", self.central_widget)
        self.help_btn.setFlat(True)
        self.help_btn.setIcon(QIcon("images/ui/help_button.png"))
        self.help_btn.setStyleSheet("border:none; background-color:transparent;")
        self.help_btn.clicked.connect(self.on_help_clicked)

        self.exit_btn = QPushButton("", self.central_widget)
        self.exit_btn.setFlat(True)
        self.exit_btn.setIcon(QIcon("images/ui/exit_button.png"))
        self.exit_btn.setStyleSheet("border:none; background-color:transparent;")
        self.exit_btn.clicked.connect(self.on_exit_clicked)

        self.fullscreen_mode = False
        self.fullscreen_shortcut = QShortcut(QKeySequence(Qt.Key_F11), self)
        self.fullscreen_shortcut.activated.connect(self.toggle_fullscreen)
        self.escape_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.escape_shortcut.activated.connect(self.exit_fullscreen)

        from select_hero import SelectHeroWindow
        self.select_window = SelectHeroWindow(self, self.width(), self.height())


    def resizeEvent(self, event):
        super().resizeEvent(event)
        window_width = self.width()
        window_height = self.height()

        self.background.setGeometry(0, 0, window_width, window_height)
        scaled_bg = self.bg_original_pixmap.scaled(
            window_width, window_height,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )
        self.background.setPixmap(scaled_bg)

        title_width = int(window_width * 1)
        scaled_title = self.title_original_pixmap.scaled(
            title_width, int(window_height * 0.3),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.title.setPixmap(scaled_title)
        self.title.setFixedSize(scaled_title.size())
        self.title.move(
            (window_width - self.title.width()) // 2,
            int(window_height * 0.05)
        )

        button_width = int(window_width * 0.25)
        button_height = int(button_width * (self.button_original_height / self.button_original_width))

        button_spacing = int(window_height * 0.15)
        start_y = int(window_height * 0.35)

        buttons = [self.start_btn, self.help_btn, self.exit_btn]
        for i, btn in enumerate(buttons):
            btn.setFixedSize(button_width, button_height)
            btn.setIconSize(btn.size())
            btn.move(
                (window_width - button_width) // 2,
                start_y + i * button_spacing
            )

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_mode = False
        else:
            self.showFullScreen()
            self.fullscreen_mode = True

    def exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_mode = False

    def apply_fullscreen_state(self, fullscreen: bool):
        self.fullscreen_mode = fullscreen
        if fullscreen:
            self.showFullScreen()
        else:
            self.showNormal()

    def button_hover_anim(self, button, scale):
        pass

    def on_start_clicked(self):
        geo=self.geometry()
        self.select_window.setGeometry(geo)
        self.select_window.resize(self.width(),self.height())
        self.select_window.apply_fullscreen_state(self.fullscreen_mode)
        self.select_window.show()
        self.hide()

    def on_help_clicked(self):
        pass

    def on_exit_clicked(self):
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StartGameBackground()
    window.show()
    sys.exit(app.exec_())
