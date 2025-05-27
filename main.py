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
    QGridLayout, QLineEdit, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QIcon


class AnimationCreator(QThread):
    """动画创建线程"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    # Store first image's properties for desc.txt and consistent output
    first_image_width = 0
    first_image_height = 0
    
    def __init__(self, images_data, output_path, fps, loop_count):
        super().__init__()
        self.images_data = images_data # Now expects a list of dicts with path, size, format
        self.output_path = output_path
        self.fps = fps
        self.loop_count = loop_count
        # image_format is now determined per file or a global override if we re-add that feature
    
    def run(self):
        try:
            # 创建临时目录
            temp_dir = Path(self.output_path).parent / "temp_bootanimation"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir()
            
            # 创建part0目录
            part0_dir = temp_dir / "part0"
            part0_dir.mkdir()
            
            # 处理图片
            total_images = len(self.images_data)
            if total_images == 0:
                self.error.emit("没有图片可处理。")
                return

            # Get resolution from the first image
            first_image_info = self.images_data[0]
            with Image.open(first_image_info['path']) as img_for_size:
                self.first_image_width, self.first_image_height = img_for_size.size

            for i, image_info in enumerate(self.images_data):
                image_path = image_info['path']
                original_format = image_info['format'].upper()
                
                with Image.open(image_path) as img:
                    # No resizing, use original size
                    # img = img.resize((720, 1280), Image.Resampling.LANCZOS) # Removed
                    
                    # Determine output format and extension
                    # For now, stick to original format if common (PNG, JPG/JPEG)
                    # Otherwise, default to PNG to preserve quality/transparency
                    if original_format in ["PNG", "JPEG", "JPG"]:
                        output_extension = original_format.lower()
                        if output_extension == "jpeg":
                            output_extension = "jpg" # Standardize to .jpg
                        save_format = original_format
                        if save_format == "JPG":
                            save_format = "JPEG" # PIL uses JPEG for saving JPGs
                    else:
                        output_extension = "png"
                        save_format = "PNG"

                    output_name = f"{i:05d}.{output_extension}"
                    save_path = part0_dir / output_name

                    if save_format == "PNG":
                        # For PNG, if original image has Alpha channel, it's preserved by default
                        # If not, converting to RGBA or RGB before saving might be needed based on specific needs
                        # For simplicity, save directly. PIL handles modes well for PNG.
                        img.save(save_path, save_format)
                    elif save_format == "JPEG":
                        if img.mode == 'RGBA' or img.mode == 'LA' or (img.mode == 'P' and 'transparency' in img.info):
                            # If image has alpha, convert to RGB by pasting on white background
                            # or just convert to RGB, which might discard alpha or blend with black
                            img_rgb = Image.new("RGB", img.size, (255, 255, 255))
                            img_rgb.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' or img.mode == 'LA' else None)
                            img = img_rgb
                        elif img.mode != 'RGB':
                             img = img.convert('RGB')
                        img.save(save_path, "JPEG", quality=95)
                    else:
                        # Fallback for other formats, attempt to save as PNG
                        img.save(save_path, "PNG")
                
                # 更新进度
                progress_value = int((i + 1) / total_images * 80)
                self.progress.emit(progress_value)
            
            # 创建desc.txt文件 using first image's dimensions
            desc_content = f"{self.first_image_width} {self.first_image_height} {self.fps}\np {self.loop_count} 0 part0\n"
            with open(temp_dir / "desc.txt", "w") as f:
                f.write(desc_content)
            
            self.progress.emit(90)
            
            # 创建ZIP文件
            with zipfile.ZipFile(self.output_path, 'w', zipfile.ZIP_STORED) as zipf:
                # 添加desc.txt
                zipf.write(temp_dir / "desc.txt", "desc.txt")
                
                # 添加part0目录下的所有文件 (scan for all .png, .jpg, .jpeg)
                for img_file in part0_dir.iterdir():
                    if img_file.is_file() and img_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                        zipf.write(img_file, f"part0/{img_file.name}")
            
            self.progress.emit(100)
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            self.finished.emit("动画创建成功！")
            
        except Exception as e:
            self.error.emit(f"创建动画时出错: {str(e)}")


class BootAnimationCreator(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("开关机动画制作工具") # Removed "Android"
        self.setGeometry(100, 100, 800, 600)
        self.images_data = [] # Store dicts: {'path': str, 'size': tuple, 'format': str, 'filename': str}
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("开关机动画制作工具") # Removed "Android"
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("开关机动画制作工具") # Removed "Android"
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 图片导入区域
        import_group = QGroupBox("图片导入")
        import_layout = QVBoxLayout(import_group)
        
        # 导入按钮布局
        import_btn_layout = QHBoxLayout()
        self.import_btn = QPushButton("导入图片")
        self.import_btn.clicked.connect(self.import_images)
        self.clear_btn = QPushButton("清空列表")
        self.clear_btn.clicked.connect(self.clear_images)
        import_btn_layout.addWidget(self.import_btn)
        import_btn_layout.addWidget(self.clear_btn)
        import_btn_layout.addStretch()
        import_layout.addLayout(import_btn_layout)
        
        # 图片列表
        self.image_list = QListWidget()
        self.image_list.setMaximumHeight(150)
        import_layout.addWidget(self.image_list)
        
        main_layout.addWidget(import_group)
        
        # 设置区域
        settings_group = QGroupBox("动画设置")
        settings_layout = QGridLayout(settings_group)
        
        # FPS设置
        settings_layout.addWidget(QLabel("帧率 (FPS):"), 0, 0)
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 60)
        self.fps_spinbox.setValue(30)
        settings_layout.addWidget(self.fps_spinbox, 0, 1)
        
        # 循环次数设置
        settings_layout.addWidget(QLabel("循环次数:"), 0, 2)
        self.loop_spinbox = QSpinBox()
        self.loop_spinbox.setRange(0, 100)
        self.loop_spinbox.setValue(1)
        self.loop_spinbox.setSpecialValueText("无限循环") # Index 0 for value 0
        settings_layout.addWidget(self.loop_spinbox, 0, 3)

        # 图片格式设置 - Removed as per new requirement (use original format)
        # settings_layout.addWidget(QLabel("图片格式:"), 2, 0)
        # self.format_combo = QComboBox()
        # self.format_combo.addItems(["JPG (推荐)", "PNG (支持透明)"])
        # settings_layout.addWidget(self.format_combo, 2, 1)
        
        # 输出路径
        settings_layout.addWidget(QLabel("输出路径:"), 1, 0) # Adjusted row index
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("选择输出文件路径...")
        settings_layout.addWidget(self.output_path_edit, 1, 1, 1, 2) # Adjusted row index
        
        self.browse_btn = QPushButton("浏览")
        self.browse_btn.clicked.connect(self.browse_output_path)
        settings_layout.addWidget(self.browse_btn, 1, 3) # Adjusted row index
        
        main_layout.addWidget(settings_group)
        
        # 预览区域
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel("选择图片后显示预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet("border: 1px solid gray;")
        preview_layout.addWidget(self.preview_label)
        
        main_layout.addWidget(preview_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 创建按钮
        self.create_btn = QPushButton("创建动画")
        self.create_btn.clicked.connect(self.create_animation)
        self.create_btn.setMinimumHeight(40)
        main_layout.addWidget(self.create_btn)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        main_layout.addWidget(self.status_label)

        # Add a label to display current image info
        self.image_info_label = QLabel("图片信息: 未选择")
        self.image_info_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.image_info_label) # Add to preview group
        
        # 连接信号
        self.image_list.currentRowChanged.connect(self.preview_image)
    
    def import_images(self):
        """导入图片"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if files:
            for f_path in files:
                try:
                    with Image.open(f_path) as img:
                        self.images_data.append({
                            'path': f_path,
                            'size': img.size,
                            'format': img.format,
                            'filename': os.path.basename(f_path)
                        })
                except Exception as e:
                    QMessageBox.warning(self, "图片导入错误", f"无法加载图片 {os.path.basename(f_path)}: {e}")
            
            self.update_image_list()
            self.status_label.setText(f"已导入 {len(self.images_data)} 张图片")
    
    def clear_images(self):
        """清空图片列表"""
        self.images_data.clear()
        self.image_list.clear()
        self.preview_label.setText("选择图片后显示预览")
        self.image_info_label.setText("图片信息: 未选择")
        self.status_label.setText("已清空图片列表")
    
    def update_image_list(self):
        """更新图片列表显示"""
        self.image_list.clear()
        for i, img_data in enumerate(self.images_data):
            # Display filename, resolution, and format
            item_text = f"{i+1:03d}. {img_data['filename']} ({img_data['size'][0]}x{img_data['size'][1]}, {img_data['format']})"
            self.image_list.addItem(item_text)
    
    def preview_image(self, row):
        """预览选中的图片并显示信息"""
        if 0 <= row < len(self.images_data):
            image_data = self.images_data[row]
            pixmap = QPixmap(image_data['path'])
            if not pixmap.isNull():
                # 缩放图片以适应预览区域
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
        else:
            self.preview_label.setText("选择图片后显示预览")
            self.image_info_label.setText("图片信息: 未选择")
    
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
        if not self.images_data: # Changed self.images to self.images_data
            QMessageBox.warning(self, "警告", "请先导入图片！")
            return
        
        output_path = self.output_path_edit.text().strip()
        if not output_path:
            QMessageBox.warning(self, "警告", "请选择输出路径！")
            return
        
        # 禁用创建按钮
        self.create_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 创建动画线程
        # image_format_str = self.format_combo.currentText().split(" ")[0] # Removed format combo
        self.animation_thread = AnimationCreator(
            self.images_data, # Pass the list of dicts
            output_path,
            self.fps_spinbox.value(),
            self.loop_spinbox.value() # Removed image_format_str
        )
        
        # 连接信号
        self.animation_thread.progress.connect(self.progress_bar.setValue)
        self.animation_thread.finished.connect(self.on_animation_finished)
        self.animation_thread.error.connect(self.on_animation_error)
        
        # 启动线程
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
    creator.setWindowTitle("开关机动画制作工具") # Removed "Android"
    creator.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
