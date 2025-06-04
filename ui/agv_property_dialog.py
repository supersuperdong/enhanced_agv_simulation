"""
AGV属性对话框模块
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
                             QGroupBox, QDialogButtonBox, QGridLayout,
                             QPushButton, QColorDialog, QMessageBox,
                             QCheckBox, QSlider, QFrame)
from PyQt5.QtGui import QColor, QPalette, QFont
from PyQt5.QtCore import Qt


class AGVPropertyDialog(QDialog):
    """AGV属性编辑对话框"""

    def __init__(self, agv, parent=None):
        super().__init__(parent)
        self.agv = agv

        # 验证AGV对象
        if not agv or not hasattr(agv, 'id'):
            raise ValueError("无效的AGV对象")

        self.original_properties = self._backup_agv_properties()

        try:
            self._setup_ui()
            self._load_agv_properties()
            self._connect_signals()
        except Exception as e:
            print(f"初始化AGV属性对话框时发生错误: {e}")
            raise

    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle(f"AGV #{self.agv.id} 属性设置")
        self.setModal(True)
        self.resize(400, 550)

        layout = QVBoxLayout(self)

        # 基本信息组
        layout.addWidget(self._create_basic_info_group())

        # 位置信息组
        layout.addWidget(self._create_position_group())

        # 运动参数组
        layout.addWidget(self._create_motion_group())

        # 外观设置组
        layout.addWidget(self._create_appearance_group())

        # 状态信息组
        layout.addWidget(self._create_status_group())

        # 按钮组 - 使用addLayout而不是addWidget
        layout.addLayout(self._create_button_group())

    def _create_basic_info_group(self):
        """创建基本信息组"""
        group = QGroupBox("基本信息")
        layout = QGridLayout(group)

        # AGV ID (只读)
        layout.addWidget(QLabel("AGV ID:"), 0, 0)
        self.id_label = QLabel(str(self.agv.id))
        self.id_label.setStyleSheet("font-weight: bold; color: blue;")
        layout.addWidget(self.id_label, 0, 1)

        # AGV名称 (可编辑)
        layout.addWidget(QLabel("名称:"), 1, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(f"AGV-{self.agv.id}")
        layout.addWidget(self.name_edit, 1, 1)

        # 当前节点 (只读)
        layout.addWidget(QLabel("当前节点:"), 2, 0)
        self.current_node_label = QLabel(str(self.agv.current_node.id))
        self.current_node_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.current_node_label, 2, 1)

        # 目标节点 (只读)
        layout.addWidget(QLabel("目标节点:"), 3, 0)
        self.target_node_label = QLabel("无" if not self.agv.target_node
                                       else str(self.agv.target_node.id))
        layout.addWidget(self.target_node_label, 3, 1)

        return group

    def _create_position_group(self):
        """创建位置信息组"""
        group = QGroupBox("位置与朝向")
        layout = QGridLayout(group)

        # X坐标
        layout.addWidget(QLabel("X坐标:"), 0, 0)
        self.x_spinbox = QDoubleSpinBox()
        self.x_spinbox.setRange(-9999, 9999)
        self.x_spinbox.setDecimals(1)
        self.x_spinbox.setSuffix(" px")
        layout.addWidget(self.x_spinbox, 0, 1)

        # Y坐标
        layout.addWidget(QLabel("Y坐标:"), 1, 0)
        self.y_spinbox = QDoubleSpinBox()
        self.y_spinbox.setRange(-9999, 9999)
        self.y_spinbox.setDecimals(1)
        self.y_spinbox.setSuffix(" px")
        layout.addWidget(self.y_spinbox, 1, 1)

        # 朝向角度
        layout.addWidget(QLabel("朝向角度:"), 2, 0)
        self.angle_spinbox = QDoubleSpinBox()
        self.angle_spinbox.setRange(0, 360)
        self.angle_spinbox.setDecimals(1)
        self.angle_spinbox.setSuffix("°")
        self.angle_spinbox.setWrapping(True)
        layout.addWidget(self.angle_spinbox, 2, 1)

        return group

    def _create_motion_group(self):
        """创建运动参数组"""
        group = QGroupBox("运动参数")
        layout = QGridLayout(group)

        # 移动速度
        layout.addWidget(QLabel("移动速度:"), 0, 0)
        self.speed_spinbox = QDoubleSpinBox()
        self.speed_spinbox.setRange(0.1, 10.0)
        self.speed_spinbox.setDecimals(1)
        self.speed_spinbox.setSuffix(" px/frame")
        layout.addWidget(self.speed_spinbox, 0, 1)

        # 碰撞缓冲区
        layout.addWidget(QLabel("碰撞缓冲区:"), 1, 0)
        self.collision_buffer_spinbox = QSpinBox()
        self.collision_buffer_spinbox.setRange(0, 100)
        self.collision_buffer_spinbox.setSuffix(" px")
        layout.addWidget(self.collision_buffer_spinbox, 1, 1)

        # 优先级
        layout.addWidget(QLabel("优先级:"), 2, 0)
        self.priority_spinbox = QSpinBox()
        self.priority_spinbox.setRange(1, 10)
        self.priority_spinbox.setToolTip("数值越大优先级越高，影响路径冲突时的处理")
        layout.addWidget(self.priority_spinbox, 2, 1)

        return group

    def _create_appearance_group(self):
        """创建外观设置组"""
        group = QGroupBox("外观设置")
        layout = QGridLayout(group)

        # AGV颜色
        layout.addWidget(QLabel("AGV颜色:"), 0, 0)
        color_layout = QHBoxLayout()

        self.color_preview = QFrame()
        self.color_preview.setFixedSize(30, 20)
        self.color_preview.setFrameStyle(QFrame.Box)
        color_layout.addWidget(self.color_preview)

        self.color_button = QPushButton("选择颜色")
        self.color_button.clicked.connect(self._choose_color)
        color_layout.addWidget(self.color_button)

        color_layout.addStretch()
        layout.addLayout(color_layout, 0, 1)

        # 尺寸设置
        layout.addWidget(QLabel("宽度:"), 1, 0)
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(10, 50)
        self.width_spinbox.setSuffix(" px")
        layout.addWidget(self.width_spinbox, 1, 1)

        layout.addWidget(QLabel("高度:"), 2, 0)
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(10, 50)
        self.height_spinbox.setSuffix(" px")
        layout.addWidget(self.height_spinbox, 2, 1)

        return group

    def _create_status_group(self):
        """创建状态信息组"""
        group = QGroupBox("状态信息")
        layout = QGridLayout(group)

        # 当前状态 (只读)
        layout.addWidget(QLabel("当前状态:"), 0, 0)
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label, 0, 1)

        # 是否移动中 (只读)
        layout.addWidget(QLabel("移动状态:"), 1, 0)
        self.moving_label = QLabel()
        layout.addWidget(self.moving_label, 1, 1)

        # 是否等待中 (只读)
        layout.addWidget(QLabel("等待状态:"), 2, 0)
        self.waiting_label = QLabel()
        layout.addWidget(self.waiting_label, 2, 1)

        # 路径长度 (只读)
        layout.addWidget(QLabel("剩余路径:"), 3, 0)
        self.path_length_label = QLabel()
        layout.addWidget(self.path_length_label, 3, 1)

        return group

    def _create_button_group(self):
        """创建按钮组"""
        button_layout = QHBoxLayout()

        # 编辑模式切换
        self.edit_mode_checkbox = QCheckBox("编辑模式")
        self.edit_mode_checkbox.setToolTip("选中时可以编辑AGV属性，取消选中时为只读查看模式")
        self.edit_mode_checkbox.stateChanged.connect(self._toggle_edit_mode)
        button_layout.addWidget(self.edit_mode_checkbox)

        button_layout.addStretch()

        # 删除AGV按钮
        self.delete_button = QPushButton("删除AGV")
        self.delete_button.setStyleSheet("QPushButton { background-color: #ff4444; color: white; font-weight: bold; }")
        self.delete_button.clicked.connect(self._delete_agv)
        button_layout.addWidget(self.delete_button)

        button_layout.addStretch()

        # 标准对话框按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_changes)

        # 保存按钮引用，用于启用/禁用
        self.ok_button = button_box.button(QDialogButtonBox.Ok)
        self.apply_button = button_box.button(QDialogButtonBox.Apply)

        button_layout.addWidget(button_box)

        return button_layout

    def _toggle_edit_mode(self, state):
        """切换编辑模式"""
        edit_enabled = (state == Qt.Checked)

        # 启用/禁用编辑控件
        self.name_edit.setEnabled(edit_enabled)
        self.x_spinbox.setEnabled(edit_enabled)
        self.y_spinbox.setEnabled(edit_enabled)
        self.angle_spinbox.setEnabled(edit_enabled)
        self.speed_spinbox.setEnabled(edit_enabled)
        self.collision_buffer_spinbox.setEnabled(edit_enabled)
        self.priority_spinbox.setEnabled(edit_enabled)
        self.color_button.setEnabled(edit_enabled)
        self.width_spinbox.setEnabled(edit_enabled)
        self.height_spinbox.setEnabled(edit_enabled)

        # 启用/禁用按钮
        self.ok_button.setEnabled(edit_enabled)
        self.apply_button.setEnabled(edit_enabled)

        # 控制预览模式
        self._preview_mode = edit_enabled

        if edit_enabled:
            self.setWindowTitle(f"AGV #{self.agv.id} 属性设置 - 编辑模式")
        else:
            self.setWindowTitle(f"AGV #{self.agv.id} 属性查看 - 只读模式")
            # 在只读模式下恢复原始状态
            self._restore_to_original()

    def _connect_signals(self):
        """连接信号和槽"""
        # 实时预览位置变化 - 添加防护机制
        self.x_spinbox.valueChanged.connect(self._preview_position)
        self.y_spinbox.valueChanged.connect(self._preview_position)
        self.angle_spinbox.valueChanged.connect(self._preview_angle)

        # 初始化预览标志
        self._preview_enabled = True
        self._preview_mode = True  # 是否为预览模式（不影响实际运动）

    def _backup_agv_properties(self):
        """备份AGV原始属性"""
        return {
            # 基本属性
            'x': self.agv.x,
            'y': self.agv.y,
            'angle': self.agv.angle,
            'speed': self.agv.speed,
            'collision_buffer': self.agv.collision_buffer,
            'color': QColor(self.agv.color),
            'width': self.agv.width,
            'height': self.agv.height,
            'name': getattr(self.agv, 'name', f"AGV-{self.agv.id}"),
            'priority': getattr(self.agv, 'priority', 5),

            # 运动状态 - 关键！
            'moving': self.agv.moving,
            'waiting': self.agv.waiting,
            'status': self.agv.status,
            'target_node': self.agv.target_node,
            'task_target': self.agv.task_target,
            'path': self.agv.path.copy() if self.agv.path else [],
            'path_index': self.agv.path_index,
            'wait_counter': self.agv.wait_counter,
            'target_angle': self.agv.target_angle,

            # 节点关系
            'current_node': self.agv.current_node
        }

    def _backup_agv_properties(self):
        """备份AGV原始属性"""
        return {
            # 基本属性
            'x': self.agv.x,
            'y': self.agv.y,
            'angle': self.agv.angle,
            'speed': self.agv.speed,
            'collision_buffer': self.agv.collision_buffer,
            'color': QColor(self.agv.color),
            'width': self.agv.width,
            'height': self.agv.height,
            'name': getattr(self.agv, 'name', f"AGV-{self.agv.id}"),
            'priority': getattr(self.agv, 'priority', 5),

            # 运动状态 - 关键！
            'moving': self.agv.moving,
            'waiting': self.agv.waiting,
            'status': self.agv.status,
            'target_node': self.agv.target_node,
            'task_target': self.agv.task_target,
            'path': self.agv.path.copy() if self.agv.path else [],
            'path_index': self.agv.path_index,
            'wait_counter': self.agv.wait_counter,
            'target_angle': self.agv.target_angle,

            # 节点关系
            'current_node': self.agv.current_node
        }

    def _load_agv_properties(self):
        """加载AGV属性到界面"""
        # 临时禁用预览，避免在加载时触发信号
        self._preview_enabled = False

        try:
            # 基本信息
            self.name_edit.setText(getattr(self.agv, 'name', f"AGV-{self.agv.id}"))

            # 位置信息
            self.x_spinbox.setValue(self.agv.x)
            self.y_spinbox.setValue(self.agv.y)
            self.angle_spinbox.setValue(self.agv.angle)

            # 运动参数
            self.speed_spinbox.setValue(self.agv.speed)
            self.collision_buffer_spinbox.setValue(self.agv.collision_buffer)
            self.priority_spinbox.setValue(getattr(self.agv, 'priority', 5))

            # 外观设置
            self._update_color_preview()
            self.width_spinbox.setValue(self.agv.width)
            self.height_spinbox.setValue(self.agv.height)

            # 状态信息
            self._update_status_info()

            # 设置默认模式 - 如果AGV正在移动，默认为只读模式
            if self.agv.moving or self.agv.waiting:
                self.edit_mode_checkbox.setChecked(False)
                self._toggle_edit_mode(Qt.Unchecked)
                print(f"AGV #{self.agv.id} 正在运行中，启用只读模式以避免干扰")
            else:
                self.edit_mode_checkbox.setChecked(True)
                self._toggle_edit_mode(Qt.Checked)

        finally:
            # 重新启用预览
            self._preview_enabled = True

    def _restore_to_original(self):
        """恢复到原始状态（用于只读模式切换）"""
        try:
            # 恢复所有原始属性
            for attr, value in self.original_properties.items():
                if attr == 'path':
                    self.agv.path = value.copy() if value else []
                elif attr == 'current_node':
                    if value and hasattr(value, 'id'):
                        self.agv.current_node = value
                elif attr == 'target_node':
                    self.agv.target_node = value
                else:
                    setattr(self.agv, attr, value)

            # 重新加载界面显示
            self._preview_enabled = False
            try:
                self.x_spinbox.setValue(self.agv.x)
                self.y_spinbox.setValue(self.agv.y)
                self.angle_spinbox.setValue(self.agv.angle)
                self._update_status_info()
            finally:
                self._preview_enabled = True

        except Exception as e:
            print(f"恢复原始状态时发生错误: {e}")

    def _update_color_preview(self):
        """更新颜色预览"""
        try:
            color = self.agv.color
            if color and color.isValid():
                self.color_preview.setStyleSheet(
                    f"background-color: rgb({color.red()}, {color.green()}, {color.blue()});"
                )
            else:
                # 如果颜色无效，使用默认颜色
                self.color_preview.setStyleSheet("background-color: rgb(255, 140, 0);")
        except Exception as e:
            print(f"更新颜色预览时发生错误: {e}")
            self.color_preview.setStyleSheet("background-color: rgb(255, 140, 0);")

    def _update_status_info(self):
        """更新状态信息"""
        try:
            self.status_label.setText(getattr(self.agv, 'status', '未知状态'))
            self.moving_label.setText("是" if getattr(self.agv, 'moving', False) else "否")
            self.waiting_label.setText("是" if getattr(self.agv, 'waiting', False) else "否")

            if hasattr(self.agv, 'path') and self.agv.path:
                remaining = len(self.agv.path) - getattr(self.agv, 'path_index', 0) - 1
                remaining = max(0, remaining)  # 确保不为负数
                self.path_length_label.setText(f"{remaining} 个节点")
            else:
                self.path_length_label.setText("无")
        except Exception as e:
            print(f"更新状态信息时发生错误: {e}")
            self.status_label.setText("状态获取失败")
            self.moving_label.setText("未知")
            self.waiting_label.setText("未知")
            self.path_length_label.setText("未知")

    def _choose_color(self):
        """选择AGV颜色"""
        try:
            current_color = getattr(self.agv, 'color', QColor(255, 140, 0))
            if not current_color.isValid():
                current_color = QColor(255, 140, 0)

            color = QColorDialog.getColor(current_color, self, "选择AGV颜色")
            if color.isValid():
                self.agv.color = color
                self._update_color_preview()
        except Exception as e:
            print(f"选择颜色时发生错误: {e}")

    def _preview_position(self):
        """实时预览位置变化 - 只在预览模式下生效"""
        # 检查预览是否启用
        if not getattr(self, '_preview_enabled', False):
            return

        # 避免在应用更改时触发预览
        if hasattr(self, '_applying_changes'):
            return

        # 在预览模式下，只更新显示，不影响运动逻辑
        if getattr(self, '_preview_mode', True):
            try:
                # 仅更新视觉位置，不改变节点关系和运动状态
                new_x = self.x_spinbox.value()
                new_y = self.y_spinbox.value()

                # 简单的边界检查
                if -10000 <= new_x <= 10000 and -10000 <= new_y <= 10000:
                    # 临时保存原始状态
                    original_moving = self.agv.moving
                    original_target = self.agv.target_node
                    original_current = self.agv.current_node

                    # 只更新显示位置
                    self.agv.x = new_x
                    self.agv.y = new_y

                    # 确保不破坏运动状态
                    self.agv.moving = original_moving
                    self.agv.target_node = original_target
                    self.agv.current_node = original_current

            except Exception as e:
                print(f"预览位置更新错误: {e}")

    def _preview_angle(self):
        """实时预览角度变化 - 只在预览模式下生效"""
        # 检查预览是否启用
        if not getattr(self, '_preview_enabled', False):
            return

        if hasattr(self, '_applying_changes'):
            return

        # 在预览模式下，只更新显示
        if getattr(self, '_preview_mode', True):
            try:
                new_angle = self.angle_spinbox.value()
                if 0 <= new_angle <= 360:
                    # 保存原始运动状态
                    original_target_angle = self.agv.target_angle
                    original_moving = self.agv.moving

                    # 只更新显示角度
                    self.agv.angle = new_angle

                    # 恢复运动状态
                    if original_moving:
                        self.agv.target_angle = original_target_angle

            except Exception as e:
                print(f"预览角度更新错误: {e}")

    def _apply_changes(self):
        """应用更改"""
        self._applying_changes = True
        try:
            # 保存一些关键的运动状态
            should_resume_movement = (
                self.original_properties.get('moving', False) and
                self.edit_mode_checkbox.isChecked()
            )

            # 应用基本属性
            name_text = self.name_edit.text().strip()
            self.agv.name = name_text if name_text else f"AGV-{self.agv.id}"

            # 应用位置和角度（如果在编辑模式）
            if self.edit_mode_checkbox.isChecked():
                # 检查位置是否改变了
                new_x = self.x_spinbox.value()
                new_y = self.y_spinbox.value()
                position_changed = (abs(new_x - self.original_properties['x']) > 1 or
                                  abs(new_y - self.original_properties['y']) > 1)

                if position_changed:
                    # 位置发生了显著变化，需要重新定位到最近的节点
                    print(f"AGV #{self.agv.id} 位置发生变化，重新定位到最近节点")
                    self._relocate_agv_to_nearest_node(new_x, new_y)
                else:
                    # 位置没有显著变化，保持原有状态
                    self.agv.x = new_x
                    self.agv.y = new_y

                self.agv.angle = self.angle_spinbox.value()

            # 应用运动参数
            self.agv.speed = max(0.1, self.speed_spinbox.value())
            self.agv.collision_buffer = max(0, self.collision_buffer_spinbox.value())
            self.agv.priority = max(1, min(10, self.priority_spinbox.value()))

            # 应用外观设置
            self.agv.width = max(10, min(50, self.width_spinbox.value()))
            self.agv.height = max(10, min(50, self.height_spinbox.value()))

            # 如果没有在编辑模式或位置没有显著变化，尝试恢复运动状态
            if (not self.edit_mode_checkbox.isChecked() or
                not hasattr(self, '_position_significantly_changed')):
                self._restore_movement_state()

            # 更新状态显示
            self._update_status_info()

            # 显示成功消息
            try:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, "成功", "AGV属性已更新")
            except:
                print("AGV属性已更新")

        except Exception as e:
            print(f"应用更改时发生错误: {e}")
            try:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "错误", f"应用更改时发生错误:\n{str(e)}")
            except:
                pass
        finally:
            if hasattr(self, '_applying_changes'):
                del self._applying_changes

    def _relocate_agv_to_nearest_node(self, new_x, new_y):
        """将AGV重新定位到最近的节点"""
        try:
            # 这里需要从父对象获取节点信息
            # 由于我们在对话框中，需要通过parent获取simulation_widget
            parent_widget = self.parent()
            if hasattr(parent_widget, 'nodes'):
                nodes = parent_widget.nodes

                # 找到最近的节点
                min_distance = float('inf')
                nearest_node = None

                for node in nodes.values():
                    distance = ((new_x - node.x) ** 2 + (new_y - node.y) ** 2) ** 0.5
                    if distance < min_distance:
                        min_distance = distance
                        nearest_node = node

                if nearest_node:
                    # 释放原来的节点
                    if (self.agv.current_node and
                        self.agv.current_node.occupied_by == self.agv.id):
                        self.agv.current_node.occupied_by = None

                    # 设置新位置和节点
                    self.agv.x = new_x
                    self.agv.y = new_y
                    self.agv.current_node = nearest_node

                    # 如果新节点没有被占用，标记为占用
                    if nearest_node.occupied_by is None:
                        nearest_node.occupied_by = self.agv.id

                    # 清除运动状态，因为位置改变了
                    self.agv.moving = False
                    self.agv.target_node = None
                    self.agv.path = []
                    self.agv.path_index = 0
                    self.agv.status = "位置已更新"

                    print(f"AGV #{self.agv.id} 已重新定位到节点 {nearest_node.id}")

        except Exception as e:
            print(f"重新定位AGV时发生错误: {e}")
            # 降级处理：至少更新位置
            self.agv.x = new_x
            self.agv.y = new_y

    def _restore_movement_state(self):
        """恢复运动状态"""
        try:
            # 恢复运动相关的状态
            if self.original_properties.get('moving', False):
                self.agv.moving = True
                self.agv.target_node = self.original_properties.get('target_node')
                self.agv.path = self.original_properties.get('path', []).copy()
                self.agv.path_index = self.original_properties.get('path_index', 0)
                self.agv.task_target = self.original_properties.get('task_target')
                self.agv.waiting = self.original_properties.get('waiting', False)
                self.agv.status = self.original_properties.get('status', '运行中')

                print(f"AGV #{self.agv.id} 运动状态已恢复")

        except Exception as e:
            print(f"恢复运动状态时发生错误: {e}")

    def _delete_agv(self):
        """删除AGV"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除AGV #{self.agv.id} 吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.done(2)  # 返回特殊值表示删除

    def reject(self):
        """取消时的处理 - 不影响移动中的AGV"""
        try:
            print(f"取消AGV #{self.agv.id} 属性编辑...")

            # 如果AGV正在移动，不应该恢复任何状态，让它继续移动
            if self.agv.moving or self.agv.waiting:
                print(f"AGV #{self.agv.id} 正在运行中，取消操作不影响其移动状态")
                super().reject()
                return

            # 只有当AGV处于静止状态时，才考虑恢复某些非关键属性
            # 但即使如此，也不恢复位置和移动相关的属性
            try:
                # 只恢复外观和配置相关的属性，不影响位置和移动
                safe_restore_attrs = ['name', 'color', 'width', 'height', 'priority', 'collision_buffer']

                for attr in safe_restore_attrs:
                    if attr in self.original_properties:
                        setattr(self.agv, attr, self.original_properties[attr])

                print(f"AGV #{self.agv.id} 已恢复外观设置，位置和移动状态未受影响")

            except Exception as e:
                print(f"恢复AGV外观设置时发生错误: {e}")

        except Exception as e:
            print(f"处理取消操作时发生错误: {e}")

        super().reject()

    def get_agv(self):
        """获取AGV对象"""
        return self.agv

    @classmethod
    def edit_agv_properties(cls, agv, parent=None):
        """
        静态方法：编辑AGV属性

        Returns:
            tuple: (result_code, agv)
            result_code: 0=取消, 1=确定, 2=删除
        """
        try:
            # 检查AGV对象的有效性
            if not agv or not hasattr(agv, 'id'):
                print("无效的AGV对象")
                return 0, agv

            dialog = cls(agv, parent)
            result = dialog.exec_()

            if result == 2:  # 删除
                return 2, agv
            elif result == dialog.Accepted:  # 确定
                dialog._apply_changes()
                return 1, agv
            else:  # 取消
                return 0, agv

        except Exception as e:
            print(f"编辑AGV属性时发生错误: {e}")
            try:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(parent, "错误", f"无法编辑AGV属性:\n{str(e)}")
            except:
                pass
            return 0, agv

    def showEvent(self, event):
        """显示事件"""
        try:
            super().showEvent(event)
            # 每次显示时刷新状态信息
            self._update_status_info()
        except Exception as e:
            print(f"显示对话框时发生错误: {e}")