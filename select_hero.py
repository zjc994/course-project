import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

class SelectHeroWindow(QMainWindow):
    def __init__(self, main_window, width, height):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("选择英雄")
        self.resize(width, height)
        self.setMinimumSize(1280, 720)
        self.setWindowFlags(
            Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint
        )

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # ---------------- 背景 ----------------
        self.background = QLabel(self.central_widget)
        self.bg_original_pixmap = QPixmap("images/background/background_of_selecting_your_heros.png")

        # ---------------- 左上角蘑菇（完整显示，不拉伸） ----------------
        self.base_mushroom = QLabel(self.central_widget)
        self.mushroom_pix = QPixmap("images/hero/adventurer.png")
        self.base_mushroom.setAttribute(Qt.WA_TranslucentBackground)
        self.base_mushroom.setAlignment(Qt.AlignCenter)

        # ---------------- 3个舞台（完整显示，不拉伸） ----------------
        self.stages = []
        for i in range(3):
            lbl = QLabel(self.central_widget)
            lbl.setPixmap(QPixmap("images/objects/stage_for_mushroom.png"))
            lbl.setAttribute(Qt.WA_TranslucentBackground)
            lbl.setAlignment(Qt.AlignCenter)
            self.stages.append(lbl)

        # ---------------- 左侧装备 ----------------
        self.equipment_icons = [
            "images/ui/icon_of_sword.png",
            "images/ui/icon_of_bow.png",
            "images/ui/icon_of_wand.png"
        ]
        self.equipment_btns = []
        for icon_path in self.equipment_icons:
            btn = QPushButton("", self.central_widget)
            btn.setFlat(True)
            btn.setIcon(QIcon(icon_path))
            btn.setStyleSheet("border:none; background-color:transparent;")
            self.equipment_btns.append(btn)

        # ---------------- 底部UI ----------------
        # 返回按钮
        self.back_btn = QPushButton("", self.central_widget)
        self.back_btn.setFlat(True)
        self.back_btn.setIcon(QIcon("images/ui/icon_of_return.png"))
        self.back_btn.setStyleSheet("border:none; background-color:transparent;")
        self.back_btn.clicked.connect(self.go_back)

        # 镜子（完整显示）
        self.mirror_lbl = QLabel(self.central_widget)
        self.mirror_pix = QPixmap("images/objects/mirror.png")
        self.mirror_lbl.setAttribute(Qt.WA_TranslucentBackground)
        self.mirror_lbl.setAlignment(Qt.AlignCenter)

        # 垃圾桶（完整显示）
        self.bin_lbl = QLabel(self.central_widget)
        self.bin_pix = QPixmap("images/objects/rubbish_bin.png")
        self.bin_lbl.setAttribute(Qt.WA_TranslucentBackground)
        self.bin_lbl.setAlignment(Qt.AlignCenter)

        # 开战按钮
        self.start_battle_btn = QPushButton("", self.central_widget)
        self.start_battle_btn.setFlat(True)
        self.start_battle_btn.setIcon(QIcon("images/ui/icon_of_start_battle.png"))
        self.start_battle_btn.setStyleSheet("border:none; background-color:transparent;")

    # ====================== 核心修复：所有图片保持原图比例，完整显示 ======================
    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        h = self.height()

        # 背景
        self.background.setGeometry(0, 0, w, h)
        scaled_bg = self.bg_original_pixmap.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.background.setPixmap(scaled_bg)
        self.background.lower()

        # 左上角蘑菇 —— 修复：等比例，完整显示
        mushroom_scaled = self.mushroom_pix.scaled(int(w*0.10), int(h*0.15), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.base_mushroom.setPixmap(mushroom_scaled)
        self.base_mushroom.setFixedSize(mushroom_scaled.size())
        self.base_mushroom.move(int(w*0.012), int(h*0.08))

        # 3个舞台 —— 修复：等比例，完整显示
        stage_size = int(w * 0.1)
        for i, lbl in enumerate(self.stages):
            scaled_pix = lbl.pixmap().scaled(
                stage_size, stage_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            lbl.setPixmap(scaled_pix)
            lbl.setFixedSize(scaled_pix.size())
            lbl.move(
                int(w * 0.2) + i * int(w * 0.22),
                int(h * 0.7)
            )
            if i==1:
                lbl.move(int(w * 0.2) + i * int(w * 0.22),
                int(h * 0.64))

        # 左侧装备图标
        equip_size = int(h * 0.12)
        equip_y = int(h * 0.28)
        for i, btn in enumerate(self.equipment_btns):
            btn.setFixedSize(equip_size, equip_size)
            btn.setIconSize(btn.size())
            btn.move(int(w*0.017), equip_y + i * int(h*0.15))

        # ---------------- 底部UI 位置与大小修复 ----------------
        ui_size = int(h * 0.2)

        # 返回按钮（左下）
        self.back_btn.setFixedSize(ui_size, ui_size)
        self.back_btn.setIconSize(self.back_btn.size())
        self.back_btn.move(int(w*0.03), int(h*0.82))

        # 镜子 —— 修复：等比例完整显示
        mirror_scaled = self.mirror_pix.scaled(int(w*0.12), int(h*0.168), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.mirror_lbl.setPixmap(mirror_scaled)
        self.mirror_lbl.setFixedSize(mirror_scaled.size())
        self.mirror_lbl.move(int(w*0.36), int(h*0.80))

        # 垃圾桶 —— 修复：等比例完整显示
        bin_scaled = self.bin_pix.scaled(int(w*0.12), int(h*0.1725), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.bin_lbl.setPixmap(bin_scaled)
        self.bin_lbl.setFixedSize(bin_scaled.size())
        self.bin_lbl.move(int(w*0.52), int(h*0.80))

        # 开战按钮（右下）
        self.start_battle_btn.setFixedSize(ui_size, ui_size)
        self.start_battle_btn.setIconSize(self.start_battle_btn.size())
        self.start_battle_btn.move(int(w*0.88), int(h*0.82))

    # 返回
    def go_back(self):
        # 关键：返回前，把当前窗口的宽高同步给主窗口
        current_w = self.width()
        current_h = self.height()
        self.hide()
        if self.main_window:
            # 让主窗口变成和当前窗口一样大！
            self.main_window.resize(current_w, current_h)
            self.main_window.show()

# 测试
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SelectHeroWindow(None, 1280, 720)
    win.show()
    sys.exit(app.exec_())

