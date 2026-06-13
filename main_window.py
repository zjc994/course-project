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
        QMessageBox.information(
            self,
            "游戏介绍",
            (
                "英雄试炼\n\n"
                "这是一款回合制英雄战斗小游戏。你需要先在选择界面把基础蘑菇拖到舞台上，"
                "再用武器将它派生为不同英雄，组成三人小队挑战熔岩领主。\n\n"
                "英雄派生：\n"
                "剑 -> 战士：生命值高，可以攻击敌人，也能给队友提升攻击力。\n"
                "弓 -> 弓手：擅长群体攻击，可以给队友附加反伤效果。\n"
                "法杖 -> 法师：可以攻击敌人，也能治疗队友。\n\n"
                "战斗规则：\n"
                "英雄回合中，将英雄拖到敌人身上可以发动攻击；拖到队友身上可以释放辅助技能。"
                "每名英雄每回合只能行动一次。所有英雄行动完毕后，进入敌人回合。\n\n"
                "其他玩法：\n"
                "选择界面的镜子可以复制已派生英雄；垃圾桶可以删除英雄。"
                "F11 可切换全屏，Esc 可退出全屏。"
            )
        )

    def on_exit_clicked(self):
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StartGameBackground()
    window.show()
    sys.exit(app.exec_())
