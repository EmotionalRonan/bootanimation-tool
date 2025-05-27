#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android Boot Animation Creator
一个用于创建Android开关机动画的PyQt工具
"""

import sys
import os
import zipfile
import shutil
from pathlib import Path
from PIL import Image
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QSpinBox, QTextEdit,
    QFileDialog, QMessageBox, QProgressBar, QGroupBox,
    QGridLayout, QLineEdit, QComboBox, QCheckBox, QTabWidget, QListWidgetItem,
    QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QIcon


class AnimationCreator(QThread):
    """动画创建线程"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    first_image_width = 0
    first_image_height = 0
    
    def __init__(self, images_data, output_path, fps, segment_params_list):
        super().__init__()
        self.images_data = images_data
        self.output_path = output_path
        self.fps = fps
        self.segment_params_list = segment_params_list # 列表，每个元素是{'loop': count, 'pause': time}
    
    def run(self):
        temp_dir = Path(self.output_path).parent / "temp_bootanimation"
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir()

            if not self.images_data:
                self.error.emit("没有图片可处理。")
                return

            first_valid_image_path = None
            for img_d in self.images_data:
                if Path(img_d['path']).exists():
                    first_valid_image_path = img_d['path']
                    break
            if not first_valid_image_path:
                self.error.emit("没有有效的图片文件路径。")
                return
                
            with Image.open(first_valid_image_path) as img_for_size:
                self.first_image_width, self.first_image_height = img_for_size.size

            segment_processing_info = {}
            active_segments = sorted(list(set(img.get('segment', 0) for img in self.images_data)))
            
            for img_d in self.images_data:
                if 'segment' not in img_d or img_d['segment'] is None:
                    img_d['segment'] = 0 
            active_segments = sorted(list(set(img['segment'] for img in self.images_data)))
            
            if not active_segments and self.images_data: 
                self.error.emit("图片数据存在但无法确定活动段落。")
                return

            for seg_idx in active_segments:
                seg_path = temp_dir / f"processed_part{seg_idx}"
                seg_path.mkdir(exist_ok=True)
                segment_processing_info[seg_idx] = {
                    'path': seg_path,
                    'image_count': 0
                }

            total_images_to_process = len(self.images_data)
            for i, image_info in enumerate(self.images_data):
                segment_idx = image_info['segment']
                
                if segment_idx not in segment_processing_info:
                    print(f"警告: 图片 {image_info.get('filename', '未知文件名')} 的段落索引 {segment_idx} 未在预处理信息中找到，跳过。")
                    continue 

                current_segment_info = segment_processing_info[segment_idx]
                image_path_str = image_info['path']
                original_format = image_info.get('format','').upper()
                
                try:
                    with Image.open(image_path_str) as img:
                        if original_format in ["PNG", "JPEG", "JPG"]:
                            output_extension = original_format.lower()
                            if output_extension == "jpeg": output_extension = "jpg"
                            save_format = original_format
                            if save_format == "JPG": save_format = "JPEG"
                        else:
                            output_extension = "png"
                            save_format = "PNG"

                        output_name = f"{current_segment_info['image_count']:05d}.{output_extension}"
                        save_path = current_segment_info['path'] / output_name
                        current_segment_info['image_count'] += 1

                        if save_format == "PNG":
                            img.save(save_path, save_format)
                        elif save_format == "JPEG":
                            if img.mode == 'RGBA' or img.mode == 'LA' or (img.mode == 'P' and 'transparency' in img.info):
                                img_rgb = Image.new("RGB", img.size, (255, 255, 255))
                                img_rgb.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' or img.mode == 'LA' else None)
                                img = img_rgb
                            elif img.mode != 'RGB':
                                img = img.convert('RGB')
                            img.save(save_path, "JPEG", quality=95)
                        else:
                            img.save(save_path, "PNG")
                except FileNotFoundError:
                    print(f"错误: 无法找到图片文件 {image_path_str}，跳过。")
                    total_images_to_process -=1 
                    continue 
                except Exception as img_e:
                    print(f"错误: 处理图片 {image_path_str} 时发生错误: {img_e}，跳过。")
                    total_images_to_process -=1 
                    continue 
                
                if total_images_to_process > 0: 
                    progress_value = int((i + 1) / total_images_to_process * 80)
                    self.progress.emit(progress_value)
            
            desc_content_lines = []
            desc_content_lines.append(f"{self.first_image_width} {self.first_image_height} {self.fps}")
            
            valid_segments_for_desc = 0
            for seg_idx in active_segments:
                if seg_idx in segment_processing_info and segment_processing_info[seg_idx]['image_count'] > 0:
                    params = self.segment_params_list[seg_idx] if seg_idx < len(self.segment_params_list) else {'loop': 0, 'pause': 0}
                    loop_count = params.get('loop', 0)
                    pause_time = params.get('pause', 0)
                    desc_content_lines.append(f"p {loop_count} {pause_time} part{seg_idx}")
                    valid_segments_for_desc +=1
            
            if valid_segments_for_desc == 0:
                self.error.emit("没有成功处理任何图片段落以生成动画。")
                return

            with open(temp_dir / "desc.txt", "w") as f:
                f.write("\n".join(desc_content_lines) + "\n")
            
            self.progress.emit(90)
            
            with zipfile.ZipFile(self.output_path, 'w', zipfile.ZIP_STORED) as zipf:
                zipf.write(temp_dir / "desc.txt", "desc.txt")
                
                for seg_idx in active_segments:
                    if seg_idx in segment_processing_info and segment_processing_info[seg_idx]['image_count'] > 0:
                        source_image_dir = segment_processing_info[seg_idx]['path']
                        zip_target_dir = f"part{seg_idx}"
                        for img_file in source_image_dir.iterdir():
                            if img_file.is_file():
                                zipf.write(img_file, f"{zip_target_dir}/{img_file.name}")
            
            self.progress.emit(100)
            self.finished.emit("动画创建成功！")

        except Exception as e:
            import traceback
            print(f"创建动画线程 'run' 方法内部发生严重错误: {str(e)}")
            print(traceback.format_exc())
            self.error.emit(f"创建动画时发生严重错误: {str(e)}")
        finally:
            if temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e_clean:
                    print(f"清理临时目录 {temp_dir} 时出错: {e_clean}")


class BootAnimationCreator(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("开关机动画制作工具")
        self.setGeometry(100, 100, 950, 700) # 增大默认窗口尺寸
        self.images_data = [] 
        self.segment_widgets_list = [] # 存储每个段落的UI控件
        self.init_ui()
        self._add_new_segment_ui() # 启动时至少创建一个段落 (part0)
    
    def _add_new_segment_ui(self):
        """动态添加一个新的动画段落到UI"""
        if len(self.segment_widgets_list) >= 8:
            QMessageBox.information(self, "提示", "最多只能添加8个动画段落。")
            return

        segment_index = len(self.segment_widgets_list)
        segment_name = f"Part {segment_index}"

        new_tab_content_widget = QWidget()
        tab_layout = QVBoxLayout(new_tab_content_widget)

        buttons_layout = QHBoxLayout()
        import_btn = QPushButton(f"导入图片到 {segment_name}")
        import_btn.clicked.connect(lambda checked, s_idx=segment_index: self.import_images(s_idx))
        buttons_layout.addWidget(import_btn)

        clear_btn = QPushButton(f"清空 {segment_name}")
        clear_btn.clicked.connect(lambda checked, s_idx=segment_index: self.clear_images(s_idx))
        buttons_layout.addWidget(clear_btn)
        tab_layout.addLayout(buttons_layout)

        image_list_widget = QListWidget()
        image_list_widget.setMaximumHeight(150)
        image_list_widget.itemClicked.connect(self.preview_image_from_item)
        image_list_widget.currentItemChanged.connect(self.preview_image_from_item)
        tab_layout.addWidget(image_list_widget)

        params_layout = QGridLayout()
        loop_label = QLabel("循环次数:")
        loop_spinbox = QSpinBox()
        loop_spinbox.setRange(0, 100)
        loop_spinbox.setSpecialValueText("无限 (0)")
        
        # 新逻辑：新添加的（即当前最后的）段落默认无限循环 (0)
        loop_spinbox.setValue(0) 

        params_layout.addWidget(loop_label, 0, 0)
        params_layout.addWidget(loop_spinbox, 0, 1)

        pause_label = QLabel("此段暂停 (ms):")
        pause_spinbox = QSpinBox()
        pause_spinbox.setRange(0, 60000)
        pause_spinbox.setValue(0)
        params_layout.addWidget(pause_label, 0, 2)
        params_layout.addWidget(pause_spinbox, 0, 3)
        tab_layout.addLayout(params_layout)

        self.segments_tab_widget.addTab(new_tab_content_widget, segment_name)

        # 将新段落的控件添加到列表中
        current_segment_info = {
            'tab_widget': new_tab_content_widget,
            'image_list': image_list_widget,
            'loop_spinbox': loop_spinbox,
            'pause_spinbox': pause_spinbox,
            'import_btn': import_btn,
            'clear_btn': clear_btn
        }
        self.segment_widgets_list.append(current_segment_info)

        # 如果这不是第一个段落 (Part 0)，则将前一个段落（现在是中间段落）的循环次数设为1
        if segment_index > 0:
            previous_segment_info = self.segment_widgets_list[segment_index - 1]
            # 只有当它之前是0（无限循环）时才改为1，避免覆盖用户设置的其他值
            if previous_segment_info['loop_spinbox'].value() == 0:
                 previous_segment_info['loop_spinbox'].setValue(1)
        elif segment_index == 0 and len(self.segment_widgets_list) == 1: 
            # 如果这是添加的第一个段落(Part 0)，且它是当前唯一的段落，它应该无限循环
            # loop_spinbox.setValue(0) 已经处理了此情况
            pass 

        if len(self.segment_widgets_list) > 1:
            self.remove_segment_btn.show()
        else:
            self.remove_segment_btn.hide()
        
        if len(self.segment_widgets_list) >= 8:
            self.add_segment_btn.setEnabled(False)
            self.status_label.setText(f"已添加 Part {segment_index}. 已达到最大段落数 (8).")
        else:
            self.status_label.setText(f"已添加 Part {segment_index}")


    def _remove_last_segment_ui(self):
        """移除最后一个动画段落"""
        if len(self.segment_widgets_list) > 1: # 至少保留一个段落
            segment_to_remove_index = len(self.segment_widgets_list) - 1
            
            self.segments_tab_widget.removeTab(segment_to_remove_index)
            self.segment_widgets_list.pop() # 移除最后一个段落的控件信息
            
            # 清理与该段落相关的图片数据
            self.images_data = [img for img in self.images_data if img.get('segment') != segment_to_remove_index]
            self.update_image_list() 

            # 更新新成为"最后段落"的循环次数（如果存在）
            if self.segment_widgets_list: # 确保移除后列表不为空
                new_last_segment_info = self.segment_widgets_list[-1]
                # 如果它当前的循环次数是1（之前作为中间段落的默认值），则设为0（无限）
                # 如果用户已设置了其他特定值（非0也非1），则保留用户设置
                if new_last_segment_info['loop_spinbox'].value() == 1:
                    new_last_segment_info['loop_spinbox'].setValue(0)
            
            if len(self.segment_widgets_list) <= 1:
                self.remove_segment_btn.hide()
            self.status_label.setText(f"已移除 Part {segment_to_remove_index}")

            # Re-enable add button if below max and it was disabled
            if len(self.segment_widgets_list) < 8 and not self.add_segment_btn.isEnabled():
                self.add_segment_btn.setEnabled(True)

        else:
            QMessageBox.information(self, "提示", "至少需要保留一个动画段落。")


    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("开关机动画制作工具")
        self.setGeometry(100, 100, 950, 700) # 增大默认窗口尺寸
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) # 主垂直布局
        
        title_label = QLabel("开关机动画制作工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # --- 创建 QSplitter --- 
        splitter = QSplitter(Qt.Horizontal)

        # --- 左侧面板 (段落管理和TabWidget) ---
        left_panel_widget = QWidget()
        left_panel_layout = QVBoxLayout(left_panel_widget)
        
        # 段落管理按钮
        segment_management_layout = QHBoxLayout()
        self.add_segment_btn = QPushButton("添加新段落")
        self.add_segment_btn.clicked.connect(self._add_new_segment_ui)
        segment_management_layout.addWidget(self.add_segment_btn)

        self.remove_segment_btn = QPushButton("移除最后段落")
        self.remove_segment_btn.clicked.connect(self._remove_last_segment_ui)
        self.remove_segment_btn.hide() # 初始隐藏
        segment_management_layout.addWidget(self.remove_segment_btn)
        left_panel_layout.addLayout(segment_management_layout)

        # 动态段落的TabWidget
        self.segments_tab_widget = QTabWidget()
        left_panel_layout.addWidget(self.segments_tab_widget)
        
        splitter.addWidget(left_panel_widget)

        # --- 右侧面板 (全局设置和预览) ---
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        
        # 全局动画设置
        settings_group = QGroupBox("全局动画设置")
        settings_layout = QGridLayout(settings_group)
        
        settings_layout.addWidget(QLabel("帧率 (FPS):"), 0, 0)
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 60)
        self.fps_spinbox.setValue(30)
        settings_layout.addWidget(self.fps_spinbox, 0, 1)
        
        settings_layout.addWidget(QLabel("输出路径:"), 1, 0)
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("选择输出文件路径...")
        settings_layout.addWidget(self.output_path_edit, 1, 1, 1, 2)
        
        self.browse_btn = QPushButton("浏览")
        self.browse_btn.clicked.connect(self.browse_output_path)
        settings_layout.addWidget(self.browse_btn, 1, 3)
        right_panel_layout.addWidget(settings_group)
        
        # 预览区域
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_label = QLabel("选择图片后显示预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet("border: 1px solid gray;")
        preview_layout.addWidget(self.preview_label)
        self.image_info_label = QLabel("图片信息: 未选择")
        self.image_info_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.image_info_label)
        right_panel_layout.addWidget(preview_group)
        right_panel_layout.addStretch() # 添加伸缩，使预览区域不会过大

        splitter.addWidget(right_panel_widget)
        
        # 设置splitter的初始大小比例 (例如，左边占60%，右边占40%)
        splitter.setSizes([500, 400]) 
        
        main_layout.addWidget(splitter) # 将splitter添加到主布局
        
        # --- 底部控件 (进度条, 创建按钮, 状态标签) ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        self.create_btn = QPushButton("创建动画")
        self.create_btn.setObjectName("create_btn") # Set object name for QSS
        self.create_btn.clicked.connect(self.create_animation)
        self.create_btn.setMinimumHeight(40)
        main_layout.addWidget(self.create_btn)
        
        self.status_label = QLabel("就绪")
        main_layout.addWidget(self.status_label)

    def import_images(self, segment_index):
        """导入图片到指定的段落"""
        if not (0 <= segment_index < len(self.segment_widgets_list)):
            QMessageBox.warning(self, "错误", f"无效的段落索引: {segment_index}")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self, f"选择图片文件 (Part {segment_index})", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if files:
            # Flag to process default output path only for the first file of the first import to Part 0
            processed_default_path_for_part0_batch = False 
            is_first_import_to_empty_part0 = segment_index == 0 and not any(img_d.get('segment') == 0 for img_d in self.images_data)

            for f_path in files:
                try:
                    with Image.open(f_path) as img:
                        # 设置默认输出路径逻辑
                        if self.output_path_edit.text().strip() == "" and \
                           is_first_import_to_empty_part0 and \
                           not processed_default_path_for_part0_batch:
                            
                            first_image_path_for_part0 = Path(f_path)
                            parent_dir = first_image_path_for_part0.parent
                            default_output_name = "bootanimation.zip"
                            self.output_path_edit.setText(str(parent_dir / default_output_name))
                            processed_default_path_for_part0_batch = True #确保此批次只设置一次

                        # 检查这是否是整个应用程序中添加的第一张图片（用于初始预览）
                        is_first_image_overall = not self.images_data

                        self.images_data.append({
                            'path': f_path,
                            'size': img.size,
                            'format': img.format,
                            'filename': os.path.basename(f_path),
                            'segment': segment_index 
                        })
                        
                        self.status_label.setText(f"已导入到 Part {segment_index}: {os.path.basename(f_path)}")
                        
                        if is_first_image_overall: # 如果是整个应用的第一张图
                           self._display_preview(self.images_data[0])
                except Exception as e:
                    QMessageBox.warning(self, "图片导入错误", f"无法加载图片 {os.path.basename(f_path)}: {e}")
            
            self.update_image_list() # 更新所有列表的显示
    
    def clear_images(self, segment_index=None):
        """清空指定段落或所有段落的图片列表"""
        if segment_index is not None:
            if not (0 <= segment_index < len(self.segment_widgets_list)):
                QMessageBox.warning(self, "错误", f"无效的段落索引: {segment_index}")
                return
            
            # 从 self.images_data 中移除属于该段落的图片
            self.images_data = [img for img in self.images_data if img.get('segment') != segment_index]
            # self.segment_widgets_list[segment_index]['image_list'].clear() # 由 update_image_list 处理
            self.status_label.setText(f"已清空 Part {segment_index} 的图片列表")
        else:
            # 清空所有
            self.images_data.clear()
            # for seg_widget_info in self.segment_widgets_list: # 由 update_image_list 处理
            #     seg_widget_info['image_list'].clear()
            self.status_label.setText("已清空所有图片列表")

        self.update_image_list() # 更新所有列表

        if not self.images_data:
            self._display_preview(None) # 重置预览
    
    def update_image_list(self):
        """更新所有动态段落的图片列表显示"""
        # 首先清空所有当前显示的列表项
        for seg_widget_info in self.segment_widgets_list:
            seg_widget_info['image_list'].clear()

        # 然后根据 self.images_data 重新填充
        for global_idx, img_data_item in enumerate(self.images_data):
            segment_idx = img_data_item.get('segment')
            if segment_idx is not None and 0 <= segment_idx < len(self.segment_widgets_list):
                target_list_widget = self.segment_widgets_list[segment_idx]['image_list']
                
                item_text = f"{target_list_widget.count() + 1:03d}. {img_data_item['filename']} ({img_data_item['size'][0]}x{img_data_item['size'][1]}, {img_data_item['format']})"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.UserRole, global_idx) # 存储的是在 self.images_data 中的全局索引
                target_list_widget.addItem(list_item)
    
    def _display_preview(self, image_data):
        """根据给定的image_data显示预览"""
        if image_data is None:
            self.preview_label.setText("选择图片后显示预览")
            self.image_info_label.setText("图片信息: 未选择")
            return

        pixmap = QPixmap(image_data['path'])
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)
            info_text = f"图片信息: {image_data['filename']} | {image_data['size'][0]}x{image_data['size'][1]} | {image_data['format']}"
            self.image_info_label.setText(info_text)
        else:
            self.preview_label.setText("无法预览此图片")
            self.image_info_label.setText(f"图片信息: {image_data['filename']} (加载失败)")

    def preview_image_from_item(self, item: QListWidgetItem):
        """预览选中的列表项中的图片并显示信息"""
        if item is None: # QListWidget.currentItemChanged can pass None if list becomes empty
            active_list_widget = self.sender() # QListWidget that emitted the signal
            if active_list_widget and isinstance(active_list_widget, QListWidget) and active_list_widget.count() == 0 : # if list is empty
                 # Check if any other list has items to preview or reset
                all_empty = True
                for seg_info in self.segment_widgets_list:
                    if seg_info['image_list'].count() > 0:
                        all_empty = False
                        # Optionally, select and preview first item of first non-empty list
                        # For now, just don't reset if another list might be active
                        break
                if all_empty:
                     self._display_preview(None)
            # If item is None but other items exist (e.g. focus changed away), do nothing or handle as needed
            return

        data_idx = item.data(Qt.UserRole)
        if data_idx is not None and 0 <= data_idx < len(self.images_data):
            image_data = self.images_data[data_idx]
            self._display_preview(image_data)
        else:
            # This case means item exists, but its stored data_idx is invalid or None.
            # This indicates an issue with how setData was called or if the item is unexpected.
            print(f"Error in preview_image_from_item: Item has invalid data_idx '{data_idx}'. Resetting preview.")
            self._display_preview(None) # Reset preview
    
    def browse_output_path(self):
        """浏览输出路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存动画文件", "bootanimation.zip",
            "ZIP文件 (*.zip)"
        )
        
        if file_path:
            self.output_path_edit.setText(file_path)
    
    def create_animation(self):
        """创建动画"""
        if not self.images_data:
            QMessageBox.warning(self, "警告", "请先导入图片！")
            return
        
        output_path = self.output_path_edit.text().strip()
        if not output_path:
            QMessageBox.warning(self, "警告", "请选择输出路径！")
            return
        
        self.create_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # --- 收集所有段落的参数 (循环次数和暂停时间) ---
        segment_params_list = [] # 将存储每个段落的 {'loop': count, 'pause': time} 字典
        
        if not self.segment_widgets_list: 
            # 如果没有任何UI段落（理论上不应发生，因为总有Part 0）
            # 提供一个默认参数给 AnimationCreator，以防万一
            segment_params_list.append({'loop': 0, 'pause': 0}) 
        else:
            for seg_widget_info in self.segment_widgets_list:
                loop_count = seg_widget_info['loop_spinbox'].value()
                pause_time = seg_widget_info['pause_spinbox'].value()
                segment_params_list.append({'loop': loop_count, 'pause': pause_time})

        self.animation_thread = AnimationCreator(
            self.images_data, 
            output_path,
            self.fps_spinbox.value(),
            segment_params_list # 传递包含所有段落参数的列表
        )
        
        self.animation_thread.progress.connect(self.progress_bar.setValue)
        self.animation_thread.finished.connect(self.on_animation_finished)
        self.animation_thread.error.connect(self.on_animation_error)
        
        self.animation_thread.start()
        self.status_label.setText("正在创建动画...")
    
    def on_animation_finished(self, message):
        """动画创建完成"""
        self.create_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        QMessageBox.information(self, "成功", message)
    
    def on_animation_error(self, error_message):
        """动画创建出错"""
        self.create_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("创建失败")
        QMessageBox.critical(self, "错误", error_message)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    # 设置全局样式
    style_file = Path(__file__).parent / "style.qss"
    if style_file.exists():
        with open(style_file, "r") as f:
            app.setStyleSheet(f.read())
    creator = BootAnimationCreator()
    creator.setWindowTitle("开关机动画制作工具")
    creator.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
