import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel, 
    QMessageBox, QDialog, QVBoxLayout, QShortcut
)
from PyQt5.QtGui import QPixmap, QIcon, QDrag, QMouseEvent, QKeySequence, QFont
from PyQt5.QtCore import Qt, QMimeData, QByteArray, QPoint, QSize

# ==============================
# 英雄数据类体系
# ==============================
class MushroomHero:
    name = "蘑菇基类"
    attack = 10
    hp = 100
    description = "这是基类，拖动武器图标到基类身上可以派生为不同英雄。"
    parent_class = "无"

    def format_info(self):
        return (
            f"名称: {self.name}\n"
            f"继承: {self.parent_class}\n"
            f"基础攻击力: {self.attack}\n"
            f"基础血量: {self.hp}\n"
            f"特性: {self.description}\n"
        )

class Warrior(MushroomHero):
    name = "武士"
    attack = 60
    hp = 600
    description = "对单体造成大伤害，给单个队友加攻击力。"
    parent_class = "蘑菇基类"

class Archer(MushroomHero):
    name = "弓箭手"
    attack = 400
    hp = 30
    description = "造成群体伤害，并给队友提供反伤效果。"
    parent_class = "蘑菇基类"

class Mage(MushroomHero):
    name = "法师"
    attack = 500
    hp = 40
    description = "可以治愈，单体攻击并降低敌人攻击力。"
    parent_class = "蘑菇基类"

EQUIP_TO_HERO = {
    "sword": "warrior.png",
    "bow": "archer.png",
    "wand": "mage.png"
}

HERO_TYPE_TO_CLASS = {
    "adventurer": MushroomHero,
    "warrior": Warrior,
    "archer": Archer,
    "mage": Mage,
}

def get_hero_data_by_type(hero_type):
    cls = HERO_TYPE_TO_CLASS.get(hero_type, MushroomHero)
    return cls()

class CopyDialog(QDialog):
    def __init__(self, hero_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("镜像复制")
        self.setFixedSize(280, 150)
        self.copy_type = None
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel(f"复制 {hero_name}"))
        btn_shallow = QPushButton("📋 浅拷贝（共享资源）")
        btn_shallow.clicked.connect(lambda: self.set_result("shallow"))
        btn_deep = QPushButton("📁 深拷贝（完全独立）")
        btn_deep.clicked.connect(lambda: self.set_result("deep"))
        
        layout.addWidget(btn_shallow)
        layout.addWidget(btn_deep)

    def set_result(self, mode):
        self.copy_type = mode
        self.accept()

# ==============================
# 可拖拽英雄标签
# ==============================
class DraggableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.OpenHandCursor)
        self.hero_type = None
        self.stage_index = -1
        self.base_pixmap = None
        self.hero_data = None
        self.shallow_group_id = -1
        self._click_candidate = False

    def setPixmap(self, pixmap):
        self.base_pixmap = pixmap
        super().setPixmap(pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.base_pixmap:
            super().setPixmap(self.base_pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self._click_candidate = True
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() != Qt.LeftButton:
            return
        distance = (event.pos() - self.drag_start_pos).manhattanLength()
        if distance < QApplication.startDragDistance():
            return
        self._click_candidate = False

        drag = QDrag(self)
        mime_data = QMimeData()
        drag_data = {
            "type": "hero",
            "hero_type": self.hero_type,
            "stage_index": self.stage_index
        }
        mime_data.setData("application/x-hero-data", QByteArray(str(drag_data).encode()))
        drag.setMimeData(mime_data)

        if self.pixmap():
            drag.setPixmap(self.pixmap())
        drag.setHotSpot(event.pos())
        drag.exec_(Qt.MoveAction)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self._click_candidate:
            main_win = self.window()
            if main_win and hasattr(main_win, "show_hero_info"):
                main_win.show_hero_info(self)
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-equip-data") and self.stage_index != -1:
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-equip-data"):
            if self.stage_index == -1:
                QMessageBox.warning(
                    self.window(),
                    "装备失败",
                    "请先将蘑菇拖到舞台上，再拖动武器进行派生。"
                )
                event.ignore()
                return
            equip_data = eval(event.mimeData().data("application/x-equip-data").data().decode())
            equip_type = equip_data["equip_type"]
            hero_img = EQUIP_TO_HERO.get(equip_type)
            
            if hero_img and self.hero_type == "adventurer":
                main_win = self.window()
                if not main_win or not hasattr(main_win, "stages"):
                    return
                stage = main_win.stages[self.stage_index]
                
                new_type = {
                    "sword": "warrior",
                    "bow": "archer",
                    "wand": "mage"
                }[equip_type]
                new_pix = QPixmap(f"images/hero/{hero_img}")
                max_w = int(stage.width() * main_win.hero_scale_factor)
                max_h = int(stage.height() * main_win.hero_scale_factor)
                scaled = new_pix.scaled(max_w, max_h, Qt.KeepAspectRatio)
                self.setFixedSize(scaled.size())
                self.base_pixmap = new_pix
                self.hero_data = get_hero_data_by_type(new_type)
                super().setPixmap(scaled)
                
                pos = stage.mapTo(main_win.central_widget, QPoint(0, 0))
                right_offset, up_offset = main_win.get_stage_hero_offset(stage, new_type)
                self.move(
                    pos.x() + (stage.width() - self.width()) // 2 + right_offset,
                    pos.y() + stage.height() - self.height() + up_offset
                )
                self.raise_()

                self.hero_type = new_type
                self.shallow_group_id = -1
                
                if main_win and hasattr(main_win, "show_hero_info"):
                    main_win.show_hero_info(self)
                
            event.acceptProposedAction()

# ==============================
# 可拖拽装备按钮
# ==============================
class DraggableEquipButton(QPushButton):
    def __init__(self, equip_type, icon_path, parent=None):
        super().__init__(parent)
        self.equip_type = equip_type
        self.setFlat(True)
        self.setIcon(QIcon(icon_path))
        self.setStyleSheet("""
            QPushButton { background-color: #87CEEB; border: none; border-radius: 12px; }
            QPushButton:hover { background-color: #6BB3D9; }
            QPushButton:pressed { background-color: #5A9CC2; }
        """)
        self.setCursor(Qt.OpenHandCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            main_win = self.window()
            if main_win and hasattr(main_win, "show_context_info"):
                main_win.show_context_info(
                    f"武器：拖动此图标到蘑菇基类身上可派生为不同英雄。\n"
                    "剑 -> 武士，弓 -> 弓箭手，魔杖 -> 法师。"
                )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() != Qt.LeftButton:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData("application/x-equip-data", 
            QByteArray(str({"type":"equip","equip_type":self.equip_type}).encode()))
        drag.setMimeData(mime_data)
        
        pix = self.icon().pixmap(self.size())
        drag.setPixmap(pix.scaled(
            int(self.width()*0.8), int(self.height()*0.8), Qt.KeepAspectRatio
        ))
        drag.setHotSpot(event.pos())
        drag.exec_(Qt.CopyAction)

# ==============================
# 舞台标签
# ==============================
class StageLabel(QLabel):
    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.setAcceptDrops(True)
        self.hero_label = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-hero-data"):
            data = eval(event.mimeData().data("application/x-hero-data").data().decode())
            if data["type"] == "hero" and data["hero_type"] == "adventurer" and self.hero_label is None:
                event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-hero-data") and self.hero_label is None:
            data = eval(event.mimeData().data("application/x-hero-data").data().decode())
            if data["hero_type"] == "adventurer":
                main_win = self.window()
                if not main_win:
                    return

                hero = main_win.create_hero_on_stage(
                    self,
                    QPixmap("images/hero/adventurer.png"),
                    "adventurer",
                    self.index
                )
                self.hero_label = hero

            event.acceptProposedAction()

# ==============================
# 垃圾桶
# ==============================
class BinLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            main_win = self.window()
            if main_win and hasattr(main_win, "show_context_info"):
                main_win.show_context_info(
                    "垃圾桶：拖动已有角色到这里可以删除该角色。\n"
                    "如果该角色是浅拷贝组的一员，整个组会一起被删除。"
                )
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-hero-data") and eval(event.mimeData().data("application/x-hero-data").data().decode())["stage_index"] != -1:
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-hero-data"):
            data = eval(event.mimeData().data("application/x-hero-data").data().decode())
            if data["stage_index"] >= 0:
                main_win = self.window()
                if main_win and hasattr(main_win, "stages"):
                    stage = main_win.stages[data["stage_index"]]
                    if stage.hero_label:
                        main_win.delete_hero_with_chain(stage.hero_label)

# ==============================
# 镜子（复制）
# ==============================
class MirrorLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            main_win = self.window()
            if main_win and hasattr(main_win, "show_context_info"):
                main_win.show_context_info(
                    "镜子：拖动已派生的角色（即已经装备武器的蘑菇）到镜子上，可选择深拷贝或浅拷贝。\n"
                    "浅拷贝会共享资源，删除任一会崩溃整组。"
                )
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-hero-data"):
            data = eval(event.mimeData().data("application/x-hero-data").data().decode())
            if data["hero_type"] != "adventurer":
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-hero-data"):
            data = eval(event.mimeData().data("application/x-hero-data").data().decode())
            if data["hero_type"] != "adventurer":
                main_win = self.window()
                if main_win:
                    stage = main_win.stages[data["stage_index"]]
                    main_win.try_copy_hero(stage.hero_label)
                event.acceptProposedAction()
                return
        event.ignore()

# ==============================
# 主窗口
# ==============================
class SelectHeroWindow(QMainWindow):
    def __init__(self, main_window, width, height):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("选择英雄")
        self.resize(width, height)
        self.setMinimumSize(1280, 720)
        self.setWindowFlags(
            Qt.Window | 
            Qt.WindowMinimizeButtonHint | 
            Qt.WindowMaximizeButtonHint | 
            Qt.WindowCloseButtonHint
        )

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.next_group_id = 0
        self.shallow_groups = {}
        self.hero_scale_factor = 2.0
        self.fullscreen_mode = False

        # 背景
        self.background = QLabel(self.central_widget)
        self.bg_pm = QPixmap("images/background/background_of_selecting_your_heros.png")

        # 初始蘑菇
        self.base_mushroom = DraggableLabel(self.central_widget)
        self.base_mushroom.hero_type = "adventurer"
        self.base_mushroom.hero_data = get_hero_data_by_type("adventurer")
        self.mushroom_pm = QPixmap("images/hero/adventurer.png")
        self.base_mushroom.setAttribute(Qt.WA_TranslucentBackground)

        # 舞台
        self.stages = []
        for i in range(3):
            stage = StageLabel(i, self.central_widget)
            stage.setPixmap(QPixmap("images/objects/stage_for_mushroom.png"))
            stage.setAttribute(Qt.WA_TranslucentBackground)
            self.stages.append(stage)

        # 装备
        self.equip_cfg = [
            ("sword", "images/ui/icon_of_sword.png"),
            ("bow", "images/ui/icon_of_bow.png"),
            ("wand", "images/ui/icon_of_wand.png")
        ]
        self.equip_btns = []
        for t, p in self.equip_cfg:
            btn = DraggableEquipButton(t, p, self.central_widget)
            self.equip_btns.append(btn)

        # UI
        self.back_btn = QPushButton("", self.central_widget)
        self.back_btn.setFlat(True)
        self.back_btn.setIcon(QIcon("images/ui/icon_of_return.png"))
        self.back_btn.setStyleSheet("border:none; background:transparent;")
        self.back_btn.clicked.connect(self.go_back)

        self.mirror_lbl = MirrorLabel(self.central_widget)
        self.mirror_pm = QPixmap("images/objects/mirror.png")
        self.mirror_lbl.setAttribute(Qt.WA_TranslucentBackground)

        self.bin_lbl = BinLabel(self.central_widget)
        self.bin_pm = QPixmap("images/objects/rubbish_bin.png")
        self.bin_lbl.setAttribute(Qt.WA_TranslucentBackground)

        self.start_btn = QPushButton("", self.central_widget)
        self.start_btn.setFlat(True)
        self.start_btn.setIcon(QIcon("images/ui/icon_of_start_battle.png"))
        self.start_btn.setStyleSheet("border:none; background:transparent;")
        self.start_btn.clicked.connect(self.on_start_battle)

        self.info_label = QLabel(self.central_widget)
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.info_label.setStyleSheet(
            "background: rgba(0, 0, 0, 0.6); color: white; border-radius: 10px; padding: 10px;"
        )
        self.info_label.setText(
            "点击角色查看详细信息。\n\n"
            "蘑菇基类：基础攻击力/基础血量，可拖动武器图标进行派生。"
        )
        self.info_label.setMinimumSize(200, 150)

        self.fullscreen_shortcut = QShortcut(QKeySequence(Qt.Key_F11), self)
        self.fullscreen_shortcut.activated.connect(self.toggle_fullscreen)
        self.escape_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.escape_shortcut.activated.connect(self.exit_fullscreen)

    def update_info_label(self, w, h):
        info_width = int(w * 0.2)
        info_height = int(h * 0.25)
        self.info_label.resize(info_width, info_height)
        margin = int(w * 0.02)
        self.info_label.move(w - info_width - margin, margin)
        font_size = max(10, int(info_width / 20))
        font = QFont()
        font.setPixelSize(font_size)
        self.info_label.setFont(font)

    def get_stage_hero_offset(self, stage, hero_type):
        if hero_type != "adventurer":
            return int(stage.width() * 0.22), -int(stage.height() * 0.28)
        return 0, -int(stage.height() * 0.5)

    def get_stage_hero_size(self, stage, pixmap):
        max_w = int(stage.width() * self.hero_scale_factor)
        max_h = int(stage.height() * self.hero_scale_factor)
        return pixmap.scaled(max_w, max_h, Qt.KeepAspectRatio).size()

    def create_hero_on_stage(self, stage, pixmap, hero_type, stage_index):
        hero = DraggableLabel(self.central_widget)
        hero.hero_type = hero_type
        hero.hero_data = get_hero_data_by_type(hero_type)
        hero.stage_index = stage_index
        hero.setFixedSize(self.get_stage_hero_size(stage, pixmap))
        hero.setPixmap(pixmap)

        pos = stage.mapTo(self.central_widget, QPoint(0, 0))
        right_offset, up_offset = self.get_stage_hero_offset(stage, hero_type)
        hero.move(
            pos.x() + (stage.width() - hero.width()) // 2 + right_offset,
            pos.y() + stage.height() - hero.height() + up_offset
        )
        hero.show()
        hero.raise_()
        return hero

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()

        self.background.setGeometry(0, 0, w, h)
        self.background.setPixmap(
            self.bg_pm.scaled(w, h, Qt.KeepAspectRatioByExpanding)
        )
        self.background.lower()

        m_size = self.mushroom_pm.scaled(int(w*0.1), int(h*0.15), Qt.KeepAspectRatio).size()
        self.base_mushroom.setFixedSize(m_size)
        self.base_mushroom.setPixmap(self.mushroom_pm)
        self.base_mushroom.move(int(w*0.012), int(h*0.08))

        s_size = int(w * 0.1)
        for i, stage in enumerate(self.stages):
            pm = stage.pixmap().scaled(s_size, s_size, Qt.KeepAspectRatio)
            stage.setPixmap(pm)
            stage.setFixedSize(pm.size())
            y = int(h*0.64) if i == 1 else int(h*0.7)
            stage.move(int(w*0.2) + i*int(w*0.22), y)

            if stage.hero_label and stage.hero_label.base_pixmap:
                max_w = int(stage.width() * self.hero_scale_factor)
                max_h = int(stage.height() * self.hero_scale_factor)
                scaled = stage.hero_label.base_pixmap.scaled(max_w, max_h, Qt.KeepAspectRatio)
                stage.hero_label.setFixedSize(scaled.size())
                pos = stage.mapTo(self.central_widget, QPoint(0,0))
                right_offset, up_offset = self.get_stage_hero_offset(stage, stage.hero_label.hero_type)
                stage.hero_label.move(
                    pos.x() + (stage.width() - stage.hero_label.width())//2 + right_offset,
                    pos.y() + stage.height() - stage.hero_label.height() + up_offset
                )
                stage.hero_label.raise_()

        e_size = int(h * 0.12)
        ey = int(h * 0.28)
        for i, btn in enumerate(self.equip_btns):
            btn.setFixedSize(e_size, e_size)
            btn.setIconSize(btn.size())
            btn.move(int(w*0.017), ey + i*int(h*0.15))

        ui_size = int(h*0.2)
        self.back_btn.setFixedSize(ui_size, ui_size)
        self.back_btn.setIconSize(QSize(ui_size, ui_size))
        self.back_btn.move(int(w*0.03), int(h*0.82))

        m_scaled = self.mirror_pm.scaled(int(w*0.12), int(h*0.168), Qt.KeepAspectRatio)
        self.mirror_lbl.setFixedSize(m_scaled.size())
        self.mirror_lbl.setPixmap(m_scaled)
        self.mirror_lbl.move(int(w*0.36), int(h*0.8))

        b_scaled = self.bin_pm.scaled(int(w*0.12), int(h*0.1725), Qt.KeepAspectRatio)
        self.bin_lbl.setFixedSize(b_scaled.size())
        self.bin_lbl.setPixmap(b_scaled)
        self.bin_lbl.move(int(w*0.52), int(h*0.8))

        self.start_btn.setFixedSize(ui_size, ui_size)
        self.start_btn.setIconSize(QSize(ui_size, ui_size))
        self.start_btn.move(int(w*0.88), int(h*0.82))

        self.update_info_label(w, h)

    def go_back(self):
        full = self.isFullScreen()
        if self.main_window:
            geo=self.geometry()
            self.main_window.setGeometry(geo)
            self.main_window.apply_fullscreen_state(full)
            self.main_window.show()
        self.hide()

    def show_hero_info(self, hero):
        if hero and hero.hero_data:
            self.info_label.setText(hero.hero_data.format_info())
        else:
            self.info_label.setText(
                "当前角色无详细信息。点击蘑菇基类或已派生英雄查看。"
            )

    def show_context_info(self, text):
        self.info_label.setText(text)

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

    def sync_fullscreen_state(self):
        if self.main_window and self.main_window.fullscreen_mode:
            self.apply_fullscreen_state(True)
        else:
            self.apply_fullscreen_state(False)

    def try_copy_hero(self, hero):
        empty = None
        for s in self.stages:
            if s.hero_label is None:
                empty = s
                break
        if not empty:
            QMessageBox.warning(self, "无法复制", "没有空舞台！")
            return

        dlg = CopyDialog(hero.hero_type, self)
        if dlg.exec_() != QDialog.Accepted:
            return

        new_hero = self.create_hero_on_stage(empty, hero.base_pixmap, hero.hero_type, empty.index)
        empty.hero_label = new_hero

        if dlg.copy_type == "shallow":
            g = hero.shallow_group_id
            if g == -1:
                g = self.next_group_id
                self.next_group_id += 1
                hero.shallow_group_id = g
                self.shallow_groups[g] = [hero]
            new_hero.shallow_group_id = g
            self.shallow_groups[g].append(new_hero)
        else:
            new_hero.shallow_group_id = -1

    def delete_hero_with_chain(self, hero):
        gid = hero.shallow_group_id
        if gid != -1 and len(self.shallow_groups.get(gid, [])) > 1:
            group = self.shallow_groups[gid]
            names = [h.hero_type for h in group]
            QMessageBox.warning(self, "💀 浅拷贝崩溃", f"全部崩溃：{', '.join(names)}")
            for h in group[:]:
                self.remove_hero_from_stage(h)
            del self.shallow_groups[gid]
        else:
            self.remove_hero_from_stage(hero)
            if gid != -1 and gid in self.shallow_groups:
                self.shallow_groups[gid].remove(hero)
                if not self.shallow_groups[gid]:
                    del self.shallow_groups[gid]

    def remove_hero_from_stage(self, hero):
        stage = self.stages[hero.stage_index]
        stage.hero_label = None
        hero.deleteLater()

    # ★ 新增加的重置方法
    def reset_battle_state(self):
        from fight_window1 import my_heroes, enemy_list, moveable_hero
        my_heroes.clear()
        enemy_list.clear()
        moveable_hero.clear()
        for stage in self.stages:
            if stage.hero_label:
                stage.hero_label.deleteLater()
                stage.hero_label = None
        self.shallow_groups.clear()
        self.next_group_id = 0
        self.update()

    def on_start_battle(self):
        for s in self.stages:
            if not s.hero_label or s.hero_label.hero_type == "adventurer":
                QMessageBox.warning(self, "无法开始", "需要3个已升级英雄! ")
                return

        hero_list1 = []
        for s in self.stages:
            hero_list1.append([s.hero_label.hero_type, s.hero_label.stage_index, s.hero_label.shallow_group_id])
        shallow_group_list1 = {}
        for key, th in self.shallow_groups.items():
            idx_list = []
            for p in th:
                idx_list.append(p.stage_index)
            shallow_group_list1[key] = idx_list
        
        try:
            from fight_window1 import Fight_Window
            # 传入 self
            self.fight_win = Fight_Window(hero_list1, shallow_group_list1, self.width(), self.height(), self)
            self.fight_win.show()
            self.hide()
        except ImportError:
            QMessageBox.warning(self, "战斗模块缺失", "未找到fight_window1.py文件或Fight_Window类!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SelectHeroWindow(None, 1280, 720)
    win.show()
    sys.exit(app.exec_())
