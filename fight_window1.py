import random
import sys
import os
import math
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QMessageBox, QShortcut
from PyQt5.QtGui import QPixmap, QIcon, QKeySequence, QMouseEvent, QDrag, QTransform
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QPoint, QSize, QEasingCurve, QTimer, QMimeData, QByteArray

# ==================== 全局数值 ====================
ini_attacks = {"mage": 40, "archer": 30, "warrior": 60, "lava_minion": 40, "lavaloard": 100}
ini_elements = {"mage": 500, "archer": 400, "warrior": 600, "lavaloard": 1000, "lava_minion": 200}
add_elements = 100
reflect_damage = 30
my_heroes = []
enemy_list = []
hero_turn = True
moveable_hero = []

# ==================== 箭矢类 ====================
class arrow(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_size = 0.1
        self.original_pixmap = QPixmap(os.path.join("images", "objects", "arrow.png"))
        self.rotation = 0.0
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignCenter)
        if not self.original_pixmap.isNull():
            self.setPixmap(self.original_pixmap)

    def rotate_self(self, angle):
        trans = QTransform().rotate(angle)
        new_pic = self.original_pixmap.transformed(trans, Qt.SmoothTransformation)
        main_win = self.window()
        if main_win:
            w = main_win.width()
        else:
            w = 1280
        tar_w = int(w * self.scale_size)
        tar_h = int(w * self.scale_size * (self.original_pixmap.height() / max(1, self.original_pixmap.width())))
        scale_pic = new_pic.scaled(tar_w, tar_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scale_pic)

    def move_to(self, final_x, final_y, finished_callback=None):
        curr_cx = self.x() + self.width() // 2
        curr_cy = self.y() + self.height() // 2
        dx = final_x - curr_cx
        dy = final_y - curr_cy
        rad = math.atan2(dy, dx)
        my_angle = math.degrees(rad)
        self.rotate_self(my_angle)
        self.show()

        end_x = int(final_x - self.width() // 2)
        end_y = int(final_y - self.height() // 2)
        start_x = self.x()
        start_y = self.y()

        parent_obj = self.parent() if self.parent() is not None else self
        self._anim = QPropertyAnimation(self, b"pos", parent_obj)
        self._anim.setStartValue(QPoint(start_x, start_y))
        self._anim.setEndValue(QPoint(end_x, end_y))
        self._anim.setDuration(400)
        self._anim.setEasingCurve(QEasingCurve.Linear)
        if finished_callback is not None:
            self._anim.finished.connect(finished_callback)

        def _cleanup_anim():
            try:
                pass
            finally:
                self._anim = None

        self._anim.finished.connect(_cleanup_anim)
        self._anim.finished.connect(self.deleteLater)
        self._anim.start()

    def start_from(self, start_x, start_y, my_angle=75):
        main_win = self.window()
        if main_win:
            w = main_win.width()
        else:
            w = 1280
        src_w = self.original_pixmap.width()
        src_h = self.original_pixmap.height()
        real_w = int(w * self.scale_size)
        real_h = int(real_w * (src_h / src_w))
        top_left_x = int(start_x) + self.width() * 2
        top_left_y = int(start_y) + self.height() * 2
        self.setGeometry(top_left_x, top_left_y, real_w, real_h)
        self.rotate_self(-my_angle)
        self.show()
        rad = math.radians(my_angle)
        dis = int(w * 0.15)
        end_cx = start_x + dis / math.tan(rad)
        end_cy = start_y - dis

        parent_obj = self.parent() if self.parent() is not None else self
        self._anim = QPropertyAnimation(self, b"pos", parent_obj)
        self._anim.setStartValue(QPoint(top_left_x, top_left_y))
        self._anim.setEndValue(QPoint(int(end_cx - real_w // 2), int(end_cy - real_h // 2)))
        self._anim.setDuration(400)
        self._anim.setEasingCurve(QEasingCurve.Linear)
        self._anim.finished.connect(lambda: setattr(self, "_anim", None))
        self._anim.start()

# ==================== 火球类 ====================
class Fireball(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_pixmap = QPixmap(os.path.join("images", "enemy", "lavaball.png"))
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(10, 10)

    def set_size_from_window(self):
        main_win = self.window()
        if main_win:
            w = main_win.width()
            size = int(w * 0.06)
        else:
            size = 100
        self.setFixedSize(size, size)
        if not self.original_pixmap.isNull():
            self.setPixmap(self.original_pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def fly_to(self, start_x, start_y, final_x, final_y, finished_callback=None):
        self.set_size_from_window()
        self.move(start_x, start_y)
        self.show()
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(500)
        anim.setStartValue(QPoint(start_x, start_y))
        anim.setEndValue(QPoint(final_x, final_y))
        anim.setEasingCurve(QEasingCurve.Linear)
        if finished_callback is not None:
            anim.finished.connect(finished_callback)
        anim.finished.connect(self.deleteLater)
        anim.start()

# ==================== 闪电球类 ====================
class LightningBall(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_pixmap = QPixmap(os.path.join("images", "objects", "lightening_ball.png"))
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(10, 10)

    def set_size_from_window(self):
        main_win = self.window()
        if main_win:
            w = main_win.width()
            size = int(w * 0.06)
        else:
            size = 100
        self.setFixedSize(size, size)
        if not self.original_pixmap.isNull():
            self.setPixmap(self.original_pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def fly_to(self, start_x, start_y, final_x, final_y, finished_callback=None):
        self.set_size_from_window()
        self.move(start_x, start_y)
        self.show()
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(500)
        anim.setStartValue(QPoint(start_x, start_y))
        anim.setEndValue(QPoint(final_x, final_y))
        anim.setEasingCurve(QEasingCurve.Linear)
        if finished_callback is not None:
            anim.finished.connect(finished_callback)
        anim.finished.connect(self.deleteLater)
        anim.start()

# ==================== 英雄类 ====================
class fighting_hero(QLabel):
    def __init__(self, hero_type: str, shallow_group_id: int, id: int, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.hero_type = hero_type
        self.reflect_damage = 0
        self.shallow_group_id = shallow_group_id
        self.id = id
        self.alive = True
        self.attack = ini_attacks.get(self.hero_type, 0)
        self.attack_multiplier = 1
        self.elements = ini_elements.get(self.hero_type, 0)
        img_path = os.path.join("images", "hero", f"{self.hero_type}.png")
        self.bg_original_pixmap = QPixmap(img_path)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignCenter)
        self.home_pos = QPoint(0, 0)

        self.drag_start_pos = QPoint()

        self._hp_bg = QLabel(self)
        self._hp_fg = QLabel(self)
        self._hp_bg.setStyleSheet("""
            background-color: #2d2d2d;
            border: 1px solid #111111;
            border-radius: 3px;
        """)
        self._hp_fg.setStyleSheet("""
            background-color: #e53935;
            border-radius: 2px;
        """)
        self._hp_bg.hide()
        self._hp_fg.hide()
        self._hp_bg.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._hp_fg.setAttribute(Qt.WA_TransparentForMouseEvents)

    def shake(self, duration: int = 200, amplitude: int = 5):
        original_pos = self.pos()
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(duration)
        anim.setKeyValueAt(0.25, QPoint(original_pos.x() - amplitude, original_pos.y()))
        anim.setKeyValueAt(0.5, QPoint(original_pos.x() + amplitude, original_pos.y()))
        anim.setKeyValueAt(0.75, QPoint(original_pos.x() - amplitude, original_pos.y()))
        anim.setKeyValueAt(1.0, original_pos)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.start()

    def update_hp_bar(self):
        self.hp_width = int(self.width() * 0.65)
        self.hp_height = int(self.height() * 0.07)
        self.hp_x = int((self.width() - self.hp_width) / 2)
        self.hp_y = int(0.93 * self.height())
        self.hp_ratio = (self.elements / ini_elements[self.hero_type])
        self.hp_ratio = 0 if self.hp_ratio <= 0 else self.hp_ratio
        self._hp_bg.setGeometry(self.hp_x, self.hp_y, self.hp_width, self.hp_height)
        self._hp_fg.setGeometry(self.hp_x, self.hp_y, int(self.hp_ratio * self.hp_width), self.hp_height)
        self._hp_bg.show()
        self._hp_fg.show()
        self._hp_fg.lower()
        self._hp_bg.lower()

    def set_sprite_size(self, max_w: int, max_h: int):
        if self.bg_original_pixmap and not self.bg_original_pixmap.isNull():
            scaled = self.bg_original_pixmap.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled)
            self.setFixedSize(scaled.size())
        else:
            self.setFixedSize(max_w, max_h)
        self.update_hp_bar()

    def animate_move_to(self, x: int, y: int, duration: int = 450, delay: int = 0):
        start = QPoint(-self.width() - 80, y)
        end = QPoint(x, y)
        self.move(start)
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.Linear)
        if delay <= 0:
            anim.start()
        else:
            QTimer.singleShot(delay, anim.start)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        global hero_turn, moveable_hero
        if event.buttons() != Qt.LeftButton or not moveable_hero[self.id] or not hero_turn:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData("application/fighting_hero",
                          QByteArray(str({"attack": int(self.attack * self.attack_multiplier),
                                          "hero_type": self.hero_type,
                                          "hero_id": self.id,
                                          "shallow_group_id": self.shallow_group_id,
                                          "x": self.x(),
                                          "y": self.y()}).encode())
                          )
        drag.setMimeData(mime_data)
        drag_icon_path = os.path.join("images", "objects", "target.png")
        drag_icon = QPixmap(drag_icon_path)

        if drag_icon.isNull():
            drag_icon = self.pixmap().scaled(
                int(self.width() * 0.4), int(self.height() * 0.4),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        else:
            drag_icon = drag_icon.scaled(
                int(self.width() * 0.4), int(self.height() * 0.4),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

        drag.setPixmap(drag_icon)
        drag.setHotSpot(QPoint(drag_icon.width() // 2, drag_icon.height() // 2))

        result = drag.exec_(Qt.CopyAction)
        if result == Qt.CopyAction:
            moveable_hero[self.id] = False
            print(f"[英雄行动] {self.hero_type} (id={self.id}) 已完成行动")
            main_win = self.window()
            if main_win:
                main_win.check_and_switch_turn()
                main_win.update_status()
        else:
            print(f"[提示] {self.hero_type} (id={self.id}) 拖放无效，行动未消耗")

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/fighting_hero"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        global my_heroes
        if event.mimeData().hasFormat("application/fighting_hero"):
            data = eval(event.mimeData().data("application/fighting_hero").data().decode())
            source_id = data.get("hero_id")
            source_type = data.get("hero_type")
            print(f"[辅助] {source_type} (id={source_id}) 对 {self.hero_type} (id={self.id}) 使用了技能")
            main_win = self.window()
            if source_type == "mage":
                self.elements = min(add_elements + self.elements, ini_elements[self.hero_type])
                self.update_hp_bar()
                self.shake()
                for h in my_heroes:
                    if h.shallow_group_id == self.shallow_group_id and h.shallow_group_id != -1 and h.id != self.id and h.alive:
                        h.elements = min(add_elements + h.elements, ini_elements[h.hero_type])
                        h.update_hp_bar()
                        h.shake()
            elif source_type == "warrior":
                self.attack_multiplier = 1.2
                self.shake()
            elif source_type == "archer":
                self.reflect_damage = reflect_damage
                self.shake()
            event.setDropAction(Qt.CopyAction)
            event.acceptProposedAction()

## 敌人类
class Enemy(QLabel):
    def __init__(self, enemy_type: str = "lavaloard", slot: str = "boss", parent=None):
        super().__init__(parent)
        self.attack_multiplier = 1
        self.summon_minion = 0
        self.area_damage = 0
        self.enemy_type = enemy_type
        self.slot = slot
        self.hero_type = enemy_type
        self.elements = ini_elements[self.enemy_type]
        img_path = os.path.join("images", "enemy", f"{self.enemy_type}.png")
        self.bg_original_pixmap = QPixmap(img_path)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.home_pos = QPoint(0, 0)

        self._hp_bg = QLabel(self)
        self._hp_fg = QLabel(self)
        self._hp_bg.setStyleSheet("""
            background-color: #2d2d2d;
            border: 1px solid #111111;
            border-radius: 3px;
        """)
        self._hp_fg.setStyleSheet("""
            background-color: #e53935;
            border-radius: 2px;
        """)
        self._hp_bg.hide()
        self._hp_fg.hide()
        self._hp_bg.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._hp_fg.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.attack_icon_label = QLabel(self)
        attack_icon_pix = QPixmap("images/objects/attack_hero_icon.png")
        if not attack_icon_pix.isNull():
            self.attack_icon_label.setPixmap(attack_icon_pix)
        self.attack_icon_label.setFixedSize(10, 10)
        self.attack_icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.attack_icon_label.hide()

        self.summon_icon_label = QLabel(self)
        summon_icon_pix = QPixmap("images/objects/summon_minion_icon.png")
        if not summon_icon_pix.isNull():
            self.summon_icon_label.setPixmap(summon_icon_pix)
        self.summon_icon_label.setFixedSize(10, 10)
        self.summon_icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.summon_icon_label.hide()

    def update_icons_scale(self):
        w = self.width() or 1280
        h = self.height() or 720
        if self.attack_icon_label.isVisible():
            icon_size = max(6, int(0.3 * w))
            self.attack_icon_label.setFixedSize(icon_size, icon_size)
            pix = self.attack_icon_label.pixmap()
            if pix and not pix.isNull():
                self.attack_icon_label.setPixmap(pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            offset_x = max(10, int(w * 0.05))
            offset_y = max(10, int(h * 0.05))
            self.attack_icon_label.move(offset_x, offset_y)
            self.attack_icon_label.raise_()
        if self.summon_icon_label.isVisible():
            icon_size = max(6, int(0.3 * w))
            self.summon_icon_label.setFixedSize(icon_size, icon_size)
            pix = self.summon_icon_label.pixmap()
            if pix and not pix.isNull():
                self.summon_icon_label.setPixmap(pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            offset_x = max(10, int(w * 0.05))
            offset_y = max(10, int(h * 0.05))
            self.summon_icon_label.move(offset_x, offset_y)
            self.summon_icon_label.raise_()

    def show_attack_icon(self):
        if self.enemy_type == "lavaloard":
            w = self.width() or 1280
            h = self.height() or 720
            icon_size = max(6, int(0.3 * w))
            self.attack_icon_label.setFixedSize(icon_size, icon_size)
            pix = self.attack_icon_label.pixmap()
            if pix and not pix.isNull():
                self.attack_icon_label.setPixmap(pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            offset_x = max(10, int(w * 0.05))
            offset_y = max(10, int(h * 0.05))
            self.attack_icon_label.move(offset_x, offset_y)
            self.attack_icon_label.show()
            self.attack_icon_label.raise_()

    def hide_attack_icon(self):
        self.attack_icon_label.hide()

    def show_summon_icon(self):
        if self.enemy_type == "lavaloard":
            w = self.width() or 1280
            h = self.height() or 720
            icon_size = max(6, int(0.3 * w))
            self.summon_icon_label.setFixedSize(icon_size, icon_size)
            pix = self.summon_icon_label.pixmap()
            if pix and not pix.isNull():
                self.summon_icon_label.setPixmap(pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            offset_x = max(10, int(w * 0.05))
            offset_y = max(10, int(h * 0.05))
            self.summon_icon_label.move(offset_x, offset_y)
            self.summon_icon_label.show()
            self.summon_icon_label.raise_()

    def hide_summon_icon(self):
        self.summon_icon_label.hide()

    def shake(self, duration: int = 200, amplitude: int = 5):
        original_pos = self.pos()
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(duration)
        anim.setKeyValueAt(0.25, QPoint(original_pos.x() - amplitude, original_pos.y()))
        anim.setKeyValueAt(0.5, QPoint(original_pos.x() + amplitude, original_pos.y()))
        anim.setKeyValueAt(0.75, QPoint(original_pos.x() - amplitude, original_pos.y()))
        anim.setKeyValueAt(1.0, original_pos)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.start()

    def update_hp_bar(self):
        self.hp_width = int(self.width() * 0.65)
        self.hp_height = int(self.height() * 0.07)
        self.hp_x = int((self.width() - self.hp_width) / 2)
        self.hp_y = int(0.93 * self.height())
        self.hp_ratio = (self.elements / ini_elements[self.hero_type])
        self.hp_ratio = 0 if self.hp_ratio <= 0 else self.hp_ratio
        self._hp_bg.setGeometry(self.hp_x, self.hp_y, self.hp_width, self.hp_height)
        self._hp_fg.setGeometry(self.hp_x, self.hp_y, int(self.hp_ratio * self.hp_width), self.hp_height)
        self._hp_bg.show()
        self._hp_fg.show()
        self._hp_fg.lower()
        self._hp_bg.lower()

    def set_sprite_size(self, max_w: int, max_h: int):
        scale = 1.3 if self.enemy_type == "lavaloard" else 1.0
        max_w = int(scale * max_w)
        max_h = int(scale * max_h)
        if self.bg_original_pixmap and not self.bg_original_pixmap.isNull():
            scaled = self.bg_original_pixmap.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled)
            self.setFixedSize(scaled.size())
        else:
            self.setFixedSize(max_w, max_h)
        self.update_hp_bar()
        self.update_icons_scale()

    def animate_move_from_right(self, final_x: int, final_y: int, duration: int = 600, delay: int = 0):
        parent = self.parent() if self.parent() is not None else self
        start_x = parent.width() + 80
        start_rect = QRect(start_x, final_y, self.width(), self.height())
        final_rect = QRect(final_x, final_y, self.width(), self.height())
        anim = QPropertyAnimation(self, b"geometry", self)
        anim.setStartValue(start_rect)
        anim.setEndValue(final_rect)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.Linear)
        if delay <= 0:
            anim.start()
        else:
            QTimer.singleShot(delay, anim.start)
        return anim

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/fighting_hero"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        global my_heroes, moveable_hero, enemy_list
        if not event.mimeData().hasFormat("application/fighting_hero"):
            return

        data = eval(event.mimeData().data("application/fighting_hero").data().decode())
        base_damage = data["attack"]
        hero_id = data.get("hero_id")
        hero_type = data.get("hero_type")
        main_win = self.window()
        if not main_win:
            return

        print(f"[攻击] {hero_type} (id={hero_id}) 攻击 {self.enemy_type} ({self.slot})")

        if hero_type == "archer":
            sx = data["x"]
            sy = data["y"]
            targets = []
            for enemy in enemy_list[:]:
                if enemy.elements <= 0:
                    continue
                tx = enemy.x() + enemy.width() // 2
                ty = enemy.y() + enemy.height() // 2
                targets.append((enemy, tx, ty))

            if not targets:
                event.setDropAction(Qt.CopyAction)
                event.acceptProposedAction()
                main_win.check_and_switch_turn()
                main_win.update_status()
                return

            main_win._pending_arrows = len(targets)
            main_win._defer_enemy_turn = True

            def _on_single_arrow_land():
                main_win._pending_arrows -= 1
                if main_win._pending_arrows <= 0:
                    for enemy in enemy_list[:]:
                        if enemy.elements <= 0:
                            continue
                        enemy.elements -= base_damage
                        enemy.update_hp_bar()
                        enemy.shake()
                        print(f"  -> 箭矢命中 {enemy.enemy_type} ({enemy.slot}), 剩余血量 {enemy.elements}")
                        if enemy.elements <= 0:
                            print(f"  -> {enemy.enemy_type} ({enemy.slot}) 死亡")
                            if enemy.slot in ["top", "bottom"]:
                                main_win.enemy_slots[enemy.slot] = None
                                enemy_list.remove(enemy)
                            enemy.hide()
                            enemy.deleteLater()
                            if enemy.slot == "boss":
                                QMessageBox.information(main_win, "胜利！", "你击败了熔岩领主！")
                                main_win._end_battle()
                                return
                    main_win._defer_enemy_turn = False
                    main_win.check_and_switch_turn()
                    main_win.update_status()

            for idx, (enemy, tx, ty) in enumerate(targets):
                arr = arrow(main_win.central_widget)
                arr.start_from(sx, sy)
                QTimer.singleShot(idx * 90, lambda tx=tx, ty=ty, a=arr: a.move_to(tx, ty, finished_callback=_on_single_arrow_land))

            total_ms = (len(targets) - 1) * 90 + 400 + 500
            def _archer_fallback():
                if getattr(main_win, '_pending_arrows', 0) > 0:
                    print("[调试] 弓箭手动画超时，强制结束")
                    main_win._pending_arrows = 0
                    main_win._defer_enemy_turn = False
                    main_win.check_and_switch_turn()
                    main_win.update_status()
            QTimer.singleShot(total_ms, _archer_fallback)

        elif hero_type == "warrior":
            attacker = next((h for h in my_heroes if h.id == hero_id), None)
            if attacker is None:
                self.elements -= base_damage
                self.update_hp_bar()
                self.shake()
                print(f"  -> 造成伤害 {base_damage}, 剩余血量 {self.elements}")
                self._check_death_and_switch(main_win)
            else:
                orig_x, orig_y = attacker.home_pos.x(), attacker.home_pos.y()
                dest_cx = self.x() + self.width() // 2
                dest_cy = self.y() + self.height() // 2
                dest_x = int(dest_cx - attacker.width() // 2)
                dest_y = int(dest_cy - attacker.height() // 2)
                attacker.raise_()
                main_win._defer_enemy_turn = True

                fwd_anim = QPropertyAnimation(attacker, b"pos", main_win)
                fwd_anim.setStartValue(QPoint(orig_x, orig_y))
                fwd_anim.setEndValue(QPoint(dest_x, dest_y))
                fwd_anim.setDuration(260)
                fwd_anim.setEasingCurve(QEasingCurve.OutQuad)
                main_win._animations.append(fwd_anim)

                def _on_reach():
                    final_damage = base_damage
                    for h in my_heroes:
                        if h.id == hero_id and h.reflect_damage > 0:
                            final_damage += h.reflect_damage
                            break
                    self.elements -= final_damage
                    self.update_hp_bar()
                    self.shake()
                    print(f"  -> 战士冲锋造成 {final_damage} 伤害, 剩余血量 {self.elements}")

                    if self.elements <= 0:
                        if self.slot == "boss":
                            self._handle_death(main_win)
                            main_win._defer_enemy_turn = False
                            main_win.check_and_switch_turn()
                            main_win.update_status()
                            return
                        else:
                            self._handle_death(main_win)

                    back_anim = QPropertyAnimation(attacker, b"pos", main_win)
                    back_anim.setStartValue(QPoint(dest_x, dest_y))
                    back_anim.setEndValue(QPoint(orig_x, orig_y))
                    back_anim.setDuration(260)
                    back_anim.setEasingCurve(QEasingCurve.InQuad)
                    main_win._animations.append(back_anim)

                    def _on_back():
                        try:
                            main_win._animations.remove(fwd_anim)
                        except ValueError:
                            pass
                        try:
                            main_win._animations.remove(back_anim)
                        except ValueError:
                            pass
                        main_win._defer_enemy_turn = False
                        main_win.check_and_switch_turn()
                        main_win.update_status()

                    back_anim.finished.connect(_on_back)
                    back_anim.start()

                fwd_anim.finished.connect(_on_reach)
                fwd_anim.start()

                QTimer.singleShot(1200, lambda: self._warrior_fallback(main_win))

        elif hero_type == "mage":
            attacker = next((h for h in my_heroes if h.id == hero_id), None)
            if attacker is None:
                self.elements -= base_damage
                self.update_hp_bar()
                self.shake()
                self._check_death_and_switch(main_win)
            else:
                src_x = attacker.x() + attacker.width() // 2
                src_y = attacker.y() - attacker.height()//7
                target_x = self.x() + self.width() // 2
                target_y = self.y() + self.height() // 2
                main_win._defer_enemy_turn = True

                def _on_lightning_hit():
                    final_damage = base_damage
                    for h in my_heroes:
                        if h.id == hero_id and h.reflect_damage > 0:
                            final_damage += h.reflect_damage
                            break
                    self.elements -= final_damage
                    self.update_hp_bar()
                    self.shake()
                    print(f"  -> 闪电命中，造成 {final_damage} 伤害, 剩余血量 {self.elements}")
                    self._check_death_and_switch(main_win)

                ball = LightningBall(main_win.central_widget)
                ball.fly_to(src_x, src_y, target_x, target_y, finished_callback=_on_lightning_hit)

        else:
            self.elements -= base_damage
            self.update_hp_bar()
            self.shake()
            self._check_death_and_switch(main_win)

        event.setDropAction(Qt.CopyAction)
        event.acceptProposedAction()
        main_win.update_status()

    def _check_death_and_switch(self, main_win):
        if self.elements <= 0:
            self._handle_death(main_win)
        main_win._defer_enemy_turn = False
        main_win.check_and_switch_turn()
        main_win.update_status()

    def _handle_death(self, main_win):
        print(f"[死亡] {self.enemy_type} ({self.slot}) 被击败")
        self.hide_attack_icon()
        self.hide_summon_icon()
        if self.slot in ["top", "bottom"]:
            main_win.enemy_slots[self.slot] = None
            enemy_list.remove(self)
        self.hide()
        self.deleteLater()
        if self.slot == "boss":
            QMessageBox.information(main_win, "胜利！", "你击败了熔岩领主！")
            main_win._end_battle()

    def _warrior_fallback(self, main_win):
        if getattr(main_win, '_defer_enemy_turn', False):
            print("[调试] 战士动画超时，强制结束")
            main_win._defer_enemy_turn = False
            main_win.check_and_switch_turn()
            main_win.update_status()

    def animate_attack_hero(self, target_hero, on_finished):
        orig_x, orig_y = self.home_pos.x(), self.home_pos.y()
        target_cx = target_hero.x() + target_hero.width() // 2
        target_cy = target_hero.y() + target_hero.height() // 2
        dest_x = target_cx - self.width() // 2
        dest_y = target_cy - self.height() // 2

        fwd = QPropertyAnimation(self, b"pos", self)
        fwd.setDuration(250)
        fwd.setStartValue(QPoint(orig_x, orig_y))
        fwd.setEndValue(QPoint(dest_x, dest_y))
        fwd.setEasingCurve(QEasingCurve.OutQuad)

        back = QPropertyAnimation(self, b"pos", self)
        back.setDuration(250)
        back.setStartValue(QPoint(dest_x, dest_y))
        back.setEndValue(QPoint(orig_x, orig_y))
        back.setEasingCurve(QEasingCurve.InQuad)

        fwd.finished.connect(back.start)
        back.finished.connect(on_finished)
        fwd.start()

    def attack_hero(self, on_finished=None):
        global my_heroes
        main_win = self.window()
        if not main_win:
            if on_finished:
                on_finished()
            return
        print(f"[敌人行动] {self.enemy_type} ({self.slot}) 开始行动")

        if self.enemy_type == "lava_minion":
            alive_heroes = [h for h in my_heroes if h.alive and h.elements > 0]
            if not alive_heroes:
                print("  -> 没有存活英雄")
                if on_finished:
                    on_finished()
                return
            target = random.choice(alive_heroes)
            damage = int(ini_attacks[self.enemy_type] * self.attack_multiplier)
            print(f"  -> 攻击 {target.hero_type} (id={target.id}), 造成 {damage} 伤害")

            def on_animation_done():
                if target.reflect_damage > 0:
                    self.elements -= target.reflect_damage
                    self.update_hp_bar()
                    self.shake()
                    print(f"  -> 反伤 {target.reflect_damage}, 自己剩余血量 {self.elements}")
                    if self.elements <= 0:
                        self._handle_death(main_win)
                        if on_finished:
                            on_finished()
                        return

                target.elements = max(0, target.elements - damage)
                target.update_hp_bar()
                target.shake()
                for h in my_heroes:
                    if h.shallow_group_id == target.shallow_group_id and h.shallow_group_id != -1 and h.id != target.id and h.alive:
                        h.elements = target.elements
                        h.update_hp_bar()
                if target.elements <= 0:
                    print(f"  -> 英雄 {target.hero_type} 死亡")
                    target.alive = False
                    target.hide()
                    for h in my_heroes:
                        if h.shallow_group_id == target.shallow_group_id and h.shallow_group_id != -1 and h.id != target.id and h.alive:
                            h.elements = 0
                            h.update_hp_bar()
                            h.alive = False
                            h.hide()
                            print(f"  -> 浅拷贝连锁: {h.hero_type} 死亡")
                if on_finished:
                    on_finished()

            self.animate_attack_hero(target, on_animation_done)
            return

        # Boss 逻辑
        if self.summon_minion == 1:
            print("  -> 释放召唤技能")
            self.shake()
            self.summon_minion = 0
            self.hide_summon_icon()
            if not main_win.enemy_slots["top"]:
                main_win.create_minion("top")
                print("  -> 召唤小兵到上方")
            elif not main_win.enemy_slots["bottom"]:
                main_win.create_minion("bottom")
                print("  -> 召唤小兵到下方")
            else:
                self.elements = min(self.elements + ini_elements["lava_minion"], ini_elements[self.enemy_type])
                self.update_hp_bar()
                self.shake()
                print(f"  -> 恢复血量至 {self.elements}")
            if on_finished:
                QTimer.singleShot(600, on_finished)

        elif self.area_damage == 1:
            print("  -> 释放群体攻击")
            self.shake()
            self.area_damage = 0
            self.hide_attack_icon()
            damage = 2 * int(ini_attacks[self.enemy_type] * self.attack_multiplier)

            alive_targets = [h for h in my_heroes if h.alive and h.elements > 0]
            if not alive_targets:
                if on_finished:
                    on_finished()
                return

            pending = len(alive_targets)
            boss_cx = self.x() + self.width() // 2
            boss_cy = self.y() + self.height() // 2

            def _aoe_fireball_done():
                nonlocal pending
                pending -= 1
                if pending <= 0:
                    for h in my_heroes:
                        if h.alive and h.elements > 0:
                            if h.reflect_damage > 0:
                                self.elements -= h.reflect_damage
                                self.update_hp_bar()
                                self.shake()
                                print(f"  -> 反伤 {h.reflect_damage} 来自 {h.hero_type}")
                            h.elements = max(0, h.elements - damage)
                            h.update_hp_bar()
                            h.shake()
                            print(f"  -> {h.hero_type} 受到 {damage} 伤害, 剩余血量 {h.elements}")
                            for p in my_heroes:
                                if h.shallow_group_id == -1:
                                    break
                                if p.shallow_group_id == h.shallow_group_id and p.id != h.id and p.alive:
                                    p.elements = max(0, p.elements - damage)
                                    p.update_hp_bar()
                                    p.shake()
                                    if p.elements <= 0:
                                        p.alive = False
                                        p.hide()
                                        print(f"  -> 浅拷贝连锁: {p.hero_type} 死亡")
                            if h.elements <= 0:
                                h.alive = False
                                h.hide()
                                print(f"  -> {h.hero_type} 死亡")
                    if self.elements <= 0:
                        self._handle_death(main_win)
                    if on_finished:
                        on_finished()

            for h in alive_targets:
                target_cx = h.x() + h.width() // 2
                target_cy = h.y() + h.height() // 2
                fireball = Fireball(main_win.central_widget)
                fireball.fly_to(boss_cx, boss_cy, target_cx, target_cy, finished_callback=_aoe_fireball_done)

        else:
            skill = random.randint(0, 4)
            if skill <= 1:          # 召唤
                self.summon_minion = 1
                print("  -> 准备下回合召唤")
                self.show_summon_icon()
                self.shake()
                if on_finished:
                    QTimer.singleShot(300, on_finished)
            elif skill <= 3:        # 群攻
                self.area_damage = 1
                print("  -> 准备下回合群体攻击")
                self.show_attack_icon()
                self.shake()
                if on_finished:
                    QTimer.singleShot(300, on_finished)
            else:                   # 普通攻击
                alive_heroes = [h for h in my_heroes if h.alive and h.elements > 0]
                if not alive_heroes:
                    if on_finished:
                        on_finished()
                    return
                target = random.choice(alive_heroes)
                damage = int(ini_attacks[self.enemy_type] * self.attack_multiplier)
                print(f"  -> 普通攻击 {target.hero_type}, 造成 {damage} 伤害")

                boss_cx = self.x() + self.width() // 2
                boss_cy = self.y() + self.height() // 2
                target_cx = target.x() + target.width() // 2
                target_cy = target.y() + target.height() // 2

                def _on_fireball_hit():
                    if target.reflect_damage > 0:
                        self.elements -= target.reflect_damage
                        self.update_hp_bar()
                        self.shake()
                        print(f"  -> 反伤 {target.reflect_damage}")
                        if self.elements <= 0:
                            self._handle_death(main_win)
                            if on_finished:
                                on_finished()
                            return

                    target.elements = max(0, target.elements - damage)
                    target.update_hp_bar()
                    target.shake()
                    for h in my_heroes:
                        if target.shallow_group_id == -1:
                            break
                        if h.shallow_group_id == target.shallow_group_id and h.id != target.id and h.alive:
                            h.elements = target.elements
                            h.update_hp_bar()

                    if target.elements <= 0:
                        print(f"  -> 英雄 {target.hero_type} 死亡")
                        target.alive = False
                        target.hide()
                        for h in my_heroes:
                            if target.shallow_group_id == -1:
                                break
                            if h.shallow_group_id == target.shallow_group_id and h.id != target.id and h.alive:
                                h.elements = 0
                                h.update_hp_bar()
                                h.alive = False
                                h.hide()
                                print(f"  -> 浅拷贝连锁: {h.hero_type} 死亡")
                    if on_finished:
                        on_finished()

                fireball = Fireball(main_win.central_widget)
                fireball.fly_to(boss_cx, boss_cy, target_cx, target_cy, finished_callback=_on_fireball_hit)

# ==================== 战斗窗口 ====================
class Fight_Window(QMainWindow):
    def __init__(self, hero_list, shallow_group_list, width1, height1, select_hero_window=None):
        global my_heroes, enemy_list, moveable_hero
        super().__init__()
        self.setWindowTitle("战斗")
        self.resize(width1, height1)
        self.hero_list = hero_list
        self.shallow_group_list = shallow_group_list
        self.select_hero_window = select_hero_window

        self.setMinimumSize(1280, 720)
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.background = QLabel(self.central_widget)
        self.bg_original_pixmap = QPixmap(os.path.join("images", "background", "battle_background.jpg"))

        self.hero_scale_factor = 1.3
        self._animations = []
        self._entered = False
        self._pending_arrows = 0
        self._defer_enemy_turn = False
        self.enemy_slots = {"top": None, "bottom": None}
        self.round_counter = 0

        my_heroes.clear()
        enemy_list.clear()
        moveable_hero.clear()

        for idx, entry in enumerate(self.hero_list):
            if isinstance(entry, (list, tuple)) and len(entry) > 0:
                hero_type = entry[0]
                shallow_id = entry[2] if len(entry) > 2 else -1
            else:
                hero_type = entry
                shallow_id = -1
            h = fighting_hero(hero_type, shallow_id, idx, parent=self.central_widget)
            h.hide()
            my_heroes.append(h)
            moveable_hero.append(True)

        self.enemy = Enemy("lavaloard", "boss", parent=self.central_widget)
        self.enemy.hide()
        self.enemy.raise_()
        enemy_list.append(self.enemy)

        self.status_label = QLabel("", self.central_widget)
        self.status_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.status_label.show()

        self._turn_timeout_timer = QTimer()
        self._turn_timeout_timer.setSingleShot(True)
        self._turn_timeout_timer.timeout.connect(self._force_enemy_turn)

        self.force_end_btn = QPushButton("强制结束回合", self.central_widget)
        self.force_end_btn.clicked.connect(self.force_end_player_turn)
        self.force_end_btn.setStyleSheet("background: orange; color: white; padding: 5px;")
        self.force_end_btn.hide()

        self.update_status()

    def _end_battle(self):
        if self.select_hero_window:
            self.select_hero_window.reset_battle_state()
            self.select_hero_window.show()
        self.close()

    def update_status(self):
        global hero_turn, my_heroes, moveable_hero
        main_win = self
        w = main_win.width()
        h = main_win.height()
        font_size = int(h * 0.02)
        if hero_turn:
            alive_not_acted = [h for h in my_heroes if h.alive and h.elements > 0 and moveable_hero[h.id]]
            text = f"⚔️ 英雄回合 第{self.round_counter}轮\n"
            if alive_not_acted:
                text += "未行动: " + ", ".join([h.hero_type for h in alive_not_acted])
            else:
                text += "所有英雄已行动，等待切换..."
        else:
            text = f"🔥 敌人回合 第{self.round_counter}轮"
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: white; background-color: rgba(0,0,0,0.6); padding: 8px; border-radius: 5px; font-size: {font_size}px;")
        self.status_label.adjustSize()
        self.status_label.move(10, 10)

    def force_end_player_turn(self):
        global hero_turn, moveable_hero
        if not hero_turn:
            return
        print("[强制] 玩家强制结束回合")
        for i in range(len(moveable_hero)):
            moveable_hero[i] = False
        self.check_and_switch_turn()
        self.update_status()

    def check_and_switch_turn(self):
        global hero_turn
        if not hero_turn:
            return
        if not any(moveable_hero):
            if self._defer_enemy_turn:
                if not self._turn_timeout_timer.isActive():
                    self._turn_timeout_timer.start(3000)
                    print("[调试] 动画进行中，等待3秒...")
                return
            self._turn_timeout_timer.stop()
            self.round_counter += 1
            print(f"\n===== 第 {self.round_counter} 轮：英雄回合结束，进入敌人回合 =====")
            self.enemy_turn()

    def _force_enemy_turn(self):
        if not any(moveable_hero) and hero_turn:
            print("[调试] 超时强制进入敌人回合！")
            self._defer_enemy_turn = False
            self.enemy_turn()

    def enemy_turn(self):
        global hero_turn
        hero_turn = False
        self._turn_timeout_timer.stop()
        self.force_end_btn.hide()
        self.update_status()
        QTimer.singleShot(500, self._execute_enemy_turn)

    def _execute_enemy_turn(self):
        global hero_turn, moveable_hero
        alive_enemies = [e for e in enemy_list if e.elements > 0]
        minions = [e for e in alive_enemies if e.enemy_type == "lava_minion"]
        boss = [e for e in alive_enemies if e.enemy_type == "lavaloard"]
        attack_order = minions + boss

        if not attack_order:
            print("没有存活敌人，胜利！")
            QMessageBox.information(self, "胜利！", "你击败了所有敌人！")
            self._end_battle()
            return

        def attack_next(index):
            if index >= len(attack_order):
                print(f"===== 敌人回合结束，回到英雄回合 =====")
                self._finish_enemy_turn()
                return
            enemy = attack_order[index]
            enemy.attack_hero(on_finished=lambda: attack_next(index + 1))

        attack_next(0)

    def _finish_enemy_turn(self):
        global hero_turn, moveable_hero
        moveable_hero.clear()
        for h in my_heroes:
            moveable_hero.append(h.alive and h.elements > 0)
        hero_turn = True
        self._defer_enemy_turn = False
        self._turn_timeout_timer.stop()
        self.update_status()
        alive_heroes = [h for h in my_heroes if h.alive and h.elements > 0]
        if not alive_heroes:
            QMessageBox.critical(self, "失败", "所有英雄都阵亡了！")
            self._end_battle()

    def create_minion(self, slot: str):
        print(f"[召唤] 创建小兵于 {slot}")
        minion = Enemy("lava_minion", slot, parent=self.central_widget)
        s_size = int(self.width() * 0.1)
        max_w = int(s_size * self.hero_scale_factor * 0.8)
        max_h = int(s_size * self.hero_scale_factor * 0.8)
        minion.set_sprite_size(max_w, max_h)

        boss_x = self.enemy.x()
        boss_y = self.enemy.y()
        boss_height = self.enemy.height()
        if slot == "top":
            minion_y = boss_y - minion.height() - 20
            minion_x = boss_x + (self.enemy.width() - minion.width()) // 2
        else:
            minion_y = boss_y + boss_height + 20
            minion_x = boss_x + (self.enemy.width() - minion.width()) // 2

        minion.move(self.width() + 80, minion_y)
        minion.show()
        minion.raise_()
        minion.animate_move_from_right(minion_x, minion_y, duration=600)

        minion.home_pos = QPoint(minion_x, minion_y)
        enemy_list.append(minion)
        self.enemy_slots[slot] = minion

    def update_minions_position(self):
        s_size = int(self.width() * 0.1)
        max_w = int(s_size * self.hero_scale_factor * 0.8)
        max_h = int(s_size * self.hero_scale_factor * 0.8)

        boss_x = self.enemy.x()
        boss_y = self.enemy.y()
        boss_height = self.enemy.height()

        if self.enemy_slots["top"]:
            minion = self.enemy_slots["top"]
            minion.set_sprite_size(max_w, max_h)
            minion_y = boss_y - minion.height() - 20
            minion_x = boss_x + (self.enemy.width() - minion.width()) // 2
            minion.setGeometry(minion_x, minion_y, minion.width(), minion.height())
            minion.home_pos = QPoint(minion_x, minion_y)
            minion.raise_()

        if self.enemy_slots["bottom"]:
            minion = self.enemy_slots["bottom"]
            minion.set_sprite_size(max_w, max_h)
            minion_y = boss_y + boss_height + 20
            minion_x = boss_x + (self.enemy.width() - minion.width()) // 2
            minion.setGeometry(minion_x, minion_y, minion.width(), minion.height())
            minion.home_pos = QPoint(minion_x, minion_y)
            minion.raise_()

    def place_heroes(self):
        global my_heroes
        w = self.width()
        h = self.height()

        self.background.setGeometry(0, 0, w, h)
        if not self.bg_original_pixmap.isNull():
            scaled_bg = self.bg_original_pixmap.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.background.setPixmap(scaled_bg)
            self.background.lower()

        s_size = int(w * 0.1)
        x0 = int(w * 0.15)

        for i, hero in enumerate(my_heroes):
            max_w = int(s_size * self.hero_scale_factor)
            max_h = int(s_size * self.hero_scale_factor)
            hero.set_sprite_size(max_w, max_h)

            stage_x = x0 if i != 1 else x0 + int(w * 0.13)
            stage_y = int(h * (0.3 + 0.2 * i))

            final_x = stage_x + (s_size - hero.width()) // 2
            final_y = stage_y + (s_size - hero.height()) // 2

            hero.setGeometry(final_x, final_y, hero.width(), hero.height())
            hero.home_pos = QPoint(final_x, final_y)
            hero.show()
            hero.raise_()

        if self.enemy and self.enemy.elements > 0:
            enemy_max_w = int(s_size * self.hero_scale_factor)
            enemy_max_h = int(s_size * self.hero_scale_factor)
            self.enemy.set_sprite_size(enemy_max_w, enemy_max_h)
            enemy_stage_y = int(h * 0.6)
            enemy_stage_x = int(w * 0.82)
            enemy_final_x = enemy_stage_x - (self.enemy.width() // 2)
            enemy_final_y = enemy_stage_y - (self.enemy.height() // 2)
            self.enemy.setGeometry(enemy_final_x, enemy_final_y, self.enemy.width(), self.enemy.height())
            self.enemy.home_pos = QPoint(enemy_final_x, enemy_final_y)
            self.enemy.show()
            if self.enemy.area_damage == 1:
                self.enemy.show_attack_icon()
            self.enemy.raise_()

        self.update_minions_position()

    def start_entry_animation(self):
        global my_heroes
        self._animations.clear()
        for i, hero in enumerate(my_heroes):
            final_rect = hero.geometry()
            start_rect = QRect(-final_rect.width() - 80, final_rect.y(), final_rect.width(), final_rect.height())
            anim = QPropertyAnimation(hero, b"geometry", self)
            anim.setDuration(600)
            anim.setStartValue(start_rect)
            anim.setEndValue(final_rect)
            anim.setEasingCurve(QEasingCurve.Linear)
            self._animations.append(anim)
            QTimer.singleShot(i * 150, lambda a=anim: a.start())

        if self.enemy:
            enemy_delay = len(my_heroes) * 150
            anim_e = self.enemy.animate_move_from_right(self.enemy.x(), self.enemy.y(), duration=700, delay=enemy_delay)
            self._animations.append(anim_e)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._entered:
            self.place_heroes()
            self.start_entry_animation()
            self._entered = True
            self.update_status()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.place_heroes()
        self.update_status()
        self.force_end_btn.move(10, self.height() - 40)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_heroes = [["warrior", 0, -1], ["archer", 1, -1], ["mage", 2, -1]]
    win = Fight_Window(test_heroes, {}, 1280, 720)
    win.show()
    sys.exit(app.exec_())
