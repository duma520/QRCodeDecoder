import sys
import sqlite3
import os
import csv
import json
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QLabel, QPushButton, QTextEdit, QFileDialog, 
                            QMessageBox, QListWidget, QSplitter, QStatusBar,QListWidgetItem)
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPalette, QImage
from PyQt5.QtCore import Qt, QSize,QTimer
import cv2
from pyzbar.pyzbar import decode
import numpy as np


class ProjectInfo:
    """项目信息元数据（集中管理所有项目相关信息）"""
    VERSION = "1.5.0"
    BUILD_DATE = "2025-05-20"
    AUTHOR = "杜玛"
    LICENSE = "MIT"
    COPYRIGHT = "© 永久 杜玛"
    URL = "https://github.com/duma520"
    MAINTAINER_EMAIL = "不提供"
    NAME = "二维码/条形码解码工具"
    DESCRIPTION = "二维码/条形码解码工具，支持多种格式的二维码和条形码解码，提供历史记录功能。"


    @classmethod
    def get_metadata(cls) -> dict:
        """获取主要元数据字典"""
        return {
            'version': cls.VERSION,
            'author': cls.AUTHOR,
            'license': cls.LICENSE,
            'url': cls.URL
        }


    @classmethod
    def get_header(cls) -> str:
        """生成标准化的项目头信息"""
        return f"{cls.NAME} {cls.VERSION} | {cls.LICENSE} License | {cls.URL}"

# 马卡龙色系定义
class MacaronColors:
    # 粉色系
    SAKURA_PINK = QColor(255, 183, 206)  # 樱花粉
    ROSE_PINK = QColor(255, 154, 162)    # 玫瑰粉
    
    # 蓝色系
    SKY_BLUE = QColor(162, 225, 246)    # 天空蓝
    LILAC_MIST = QColor(230, 230, 250)   # 淡丁香
    
    # 绿色系
    MINT_GREEN = QColor(181, 234, 215)   # 薄荷绿
    APPLE_GREEN = QColor(212, 241, 199)  # 苹果绿
    
    # 黄色/橙色系
    LEMON_YELLOW = QColor(255, 234, 165) # 柠檬黄
    BUTTER_CREAM = QColor(255, 248, 184) # 奶油黄
    PEACH_ORANGE = QColor(255, 218, 193) # 蜜桃橙
    
    # 紫色系
    LAVENDER = QColor(199, 206, 234)     # 薰衣草紫
    TARO_PURPLE = QColor(216, 191, 216)  # 香芋紫
    
    # 中性色
    CARAMEL_CREAM = QColor(240, 230, 221) # 焦糖奶霜

class QRCodeDecoder(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 初始化数据库
        self.init_db()
        
        # 设置窗口属性
        self.setWindowTitle(f"{ProjectInfo.NAME} {ProjectInfo.VERSION}")
        self.setWindowIcon(QIcon("icon.ico"))
        self.resize(1000, 700)
        
        # 设置马克龙色系
        self.set_macron_style()
        
        # 创建主界面
        self.create_main_ui()
        
        # 高DPI支持
        self.setAttribute(Qt.WA_AlwaysStackOnTop)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        
    def init_db(self):
        """初始化SQLite数据库"""
        self.conn = sqlite3.connect('qrcode_history.db')
        self.cursor = self.conn.cursor()
        
        # 检查表是否存在
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='history'")
        table_exists = self.cursor.fetchone()
        
        if table_exists:
            # 检查现有表结构
            self.cursor.execute("PRAGMA table_info(history)")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            # 添加缺失的列
            if 'code_type' not in columns:
                self.cursor.execute("ALTER TABLE history ADD COLUMN code_type TEXT")
            if 'is_favorite' not in columns:
                self.cursor.execute("ALTER TABLE history ADD COLUMN is_favorite BOOLEAN DEFAULT 0")
        else:
            # 创建新表
            self.cursor.execute('''
                CREATE TABLE history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    content TEXT,
                    image_path TEXT,
                    code_type TEXT,
                    is_favorite BOOLEAN DEFAULT 0
                )
            ''')
        
        # 创建数据库信息表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS db_info (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # 检查是否需要初始化数据库信息
        self.cursor.execute("SELECT value FROM db_info WHERE key='version'")
        if not self.cursor.fetchone():
            self.cursor.execute(
                "INSERT INTO db_info (key, value) VALUES (?, ?)",
                ('version', '1.0.0')
            )
            self.cursor.execute(
                "INSERT INTO db_info (key, value) VALUES (?, ?)",
                ('created_at', datetime.datetime.now().isoformat())
            )
        
        self.conn.commit()

    
    def set_macron_style(self):
        """设置马克龙色系样式"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 245))  # 浅灰蓝背景
        palette.setColor(QPalette.WindowText, QColor(60, 60, 60))  # 深灰文字
        palette.setColor(QPalette.Base, QColor(255, 255, 255))  # 白色背景
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(60, 60, 60))
        palette.setColor(QPalette.Text, QColor(60, 60, 60))
        palette.setColor(QPalette.Button, QColor(230, 230, 235))  # 浅灰蓝按钮
        palette.setColor(QPalette.ButtonText, QColor(60, 60, 60))
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(100, 149, 237))  # 马克龙蓝
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        self.setPalette(palette)
        
        self.setStyleSheet('''
            QPushButton {
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e0e0e5;
            }
            QPushButton:pressed {
                background-color: #d0d0d5;
            }
            QTextEdit, QListWidget {
                border: 1px solid #c0c0c0;
                border-radius: 4px;
            }
            QSplitter::handle {
                background-color: #d0d0d0;
                width: 4px;
            }
        ''')
    
    def create_main_ui(self):
        """创建主界面"""
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧区域 - 图片和操作
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # 图片显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setStyleSheet("background-color: #ffffff; border: 1px solid #c0c0c0;")
        left_layout.addWidget(self.image_label)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.load_button = QPushButton("加载图片")
        self.load_button.setIcon(QIcon.fromTheme("document-open"))
        self.load_button.clicked.connect(self.load_image)
        button_layout.addWidget(self.load_button)

        # 新增粘贴按钮
        self.paste_button = QPushButton("从剪贴板粘贴")
        self.paste_button.setIcon(QIcon.fromTheme("edit-paste"))
        self.paste_button.clicked.connect(self.paste_from_clipboard)
        button_layout.addWidget(self.paste_button)

        self.decode_button = QPushButton("解码二维码/条形码")
        self.decode_button.setIcon(QIcon.fromTheme("edit-find"))
        self.decode_button.clicked.connect(self.decode_qrcode)
        self.decode_button.setEnabled(False)
        button_layout.addWidget(self.decode_button)
        
        self.clear_button = QPushButton("清除")
        self.clear_button.setIcon(QIcon.fromTheme("edit-clear"))
        self.clear_button.clicked.connect(self.clear_all)
        button_layout.addWidget(self.clear_button)
        
        left_layout.addLayout(button_layout)
        
        # 右侧区域 - 结果和历史
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # 解码结果
        result_label = QLabel("解码结果:")
        right_layout.addWidget(result_label)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(200)
        right_layout.addWidget(self.result_text)
        
        # 复制按钮
        self.copy_button = QPushButton("复制结果")
        self.copy_button.setIcon(QIcon.fromTheme("edit-copy"))
        self.copy_button.clicked.connect(self.copy_result)
        self.copy_button.setEnabled(False)
        right_layout.addWidget(self.copy_button)
        
        # 历史记录
        history_label = QLabel("历史记录:")
        right_layout.addWidget(history_label)
        
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.load_history_item)
        right_layout.addWidget(self.history_list)

        # 数据库操作按钮
        db_button_layout = QHBoxLayout()
        db_button_layout.setSpacing(5)

        self.backup_button = QPushButton("备份数据库")
        self.backup_button.setIcon(QIcon.fromTheme("document-save-as"))
        self.backup_button.clicked.connect(self.backup_database)
        db_button_layout.addWidget(self.backup_button)

        self.optimize_button = QPushButton("优化数据库")
        self.optimize_button.setIcon(QIcon.fromTheme("system-run"))
        self.optimize_button.clicked.connect(self.optimize_database)
        db_button_layout.addWidget(self.optimize_button)

        self.export_csv_button = QPushButton("导出CSV")
        self.export_csv_button.setIcon(QIcon.fromTheme("x-office-spreadsheet"))
        self.export_csv_button.clicked.connect(lambda: self.export_history('csv'))
        db_button_layout.addWidget(self.export_csv_button)

        self.export_json_button = QPushButton("导出JSON")
        self.export_json_button.setIcon(QIcon.fromTheme("text-x-json"))
        self.export_json_button.clicked.connect(lambda: self.export_history('json'))
        db_button_layout.addWidget(self.export_json_button)

        right_layout.addLayout(db_button_layout)

        # 历史记录操作按钮
        history_button_layout = QHBoxLayout()
        history_button_layout.setSpacing(5)

        self.delete_button = QPushButton("删除选中")
        self.delete_button.setIcon(QIcon.fromTheme("edit-delete"))
        self.delete_button.clicked.connect(self.delete_history_item)
        history_button_layout.addWidget(self.delete_button)

        self.favorite_button = QPushButton("收藏/取消收藏")
        self.favorite_button.setIcon(QIcon.fromTheme("emblem-favorite"))
        self.favorite_button.clicked.connect(self.toggle_favorite)
        history_button_layout.addWidget(self.favorite_button)

        right_layout.addLayout(history_button_layout)

        
        # 添加部件到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 加载历史记录
        self.load_history()
    
    def load_image(self):
        """加载图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            self.current_image_path = file_path
            pixmap = QPixmap(file_path)
            
            # 缩放图片以适应显示区域
            scaled_pixmap = pixmap.scaled(
                self.image_label.size() - QSize(20, 20), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            self.decode_button.setEnabled(True)
            self.status_bar.showMessage(f"已加载图片: {file_path}", 3000)
    
    def decode_qrcode(self):
        """解码二维码和条形码"""
        if not hasattr(self, 'current_image_path'):
            QMessageBox.warning(self, "警告", "请先加载图片")
            return
        
        try:
            # 处理剪贴板图片
            if self.current_image_path == "clipboard":
                # 检查剪贴板图片是否有效
                if not hasattr(self, 'image_label') or not self.image_label.pixmap():
                    raise ValueError("剪贴板中没有有效的图片")
                
                pixmap = self.image_label.pixmap()
                if pixmap.isNull():
                    raise ValueError("剪贴板图片无效")
                
                # 转换为QImage
                qimage = pixmap.toImage()
                if qimage.isNull():
                    raise ValueError("图片转换失败")
                
                # 转换为RGB888格式
                qimage = qimage.convertToFormat(QImage.Format_RGB888)
                if qimage.isNull():
                    raise ValueError("图片格式转换失败")
                
                # 获取图片尺寸和数据
                width = qimage.width()
                height = qimage.height()
                bytes_per_line = qimage.bytesPerLine()
                
                if width <= 0 or height <= 0:
                    raise ValueError("无效的图片尺寸")
                
                # 获取图片数据
                buffer = qimage.constBits()
                if buffer is None:
                    raise ValueError("无法获取图片数据")
                
                buffer.setsize(qimage.byteCount())
                
                # 转换为numpy数组
                try:
                    arr = np.frombuffer(buffer, np.uint8)
                    
                    # 处理不同情况的行填充
                    if bytes_per_line == width * 3:  # 无填充
                        img = arr.reshape((height, width, 3))
                    else:  # 有行填充
                        # 计算实际每行像素数据大小
                        img = arr.reshape((height, bytes_per_line))
                        img = img[:, :width*3]  # 去除填充部分
                        img = img.reshape((height, width, 3))
                    
                    # 转换颜色空间
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                    
                except Exception as e:
                    raise ValueError(f"图片数据转换失败: {str(e)}")
            else:
                # 使用OpenCV读取图片文件
                img = cv2.imread(self.current_image_path)
                if img is None:
                    raise ValueError(f"无法加载图片文件: {self.current_image_path}")
            
            # 检查图片是否有效
            if img is None or img.size == 0:
                raise ValueError("无效的图片数据")
            
            # 解码二维码和条形码
            decoded_objects = decode(img)
            
            if not decoded_objects:
                QMessageBox.information(self, "提示", "未检测到二维码或条形码")
                return
            
            # 支持的类型映射表
            type_mapping = {
                'AZTEC': 'Aztec码',
                'CODE128': 'Code 128条形码',
                'CODE39': 'Code 39条形码',
                'CODE93': 'Code 93条形码',
                'DATA MATRIX': 'Data Matrix码',
                'EAN13': 'EAN-13条形码',
                'EAN8': 'EAN-8条形码',
                'ITF': 'ITF条形码',
                'PDF417': 'PDF417码',
                'QRCODE': '二维码',
                'UPC-A': 'UPC-A条形码',
                'UPC-E': 'UPC-E条形码'
            }
            
            # 拼接所有解码结果，包含类型信息
            results = []
            print(f"[DEBUG] 解码结果数量: {len(decoded_objects)}")
            for obj in decoded_objects:
                code_type = type_mapping.get(obj.type, obj.type)
                try:
                    content = obj.data.decode('utf-8')
                except UnicodeDecodeError:
                    content = str(obj.data)
                results.append(f"[{code_type}]\n{content}")
            
            result = "\n\n".join(results)
            self.result_text.setPlainText(result)
            self.copy_button.setEnabled(True)
            print(f"[DEBUG] 解码结果: {result}")

            # 保存到历史记录（如果是文件则保存路径，剪贴板图片则不保存路径）
            image_path = self.current_image_path if self.current_image_path != "clipboard" else ""
            self.save_to_history(result, image_path)
            self.load_history()
            
            self.status_bar.showMessage("解码成功", 3000)
            
        except Exception as e:
            error_msg = f"解码失败: {str(e)}"
            print(f"[DEBUG] {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
            self.status_bar.showMessage(error_msg, 3000)

    
    def copy_result(self):
        """复制解码结果"""
        result = self.result_text.toPlainText()
        if result:
            clipboard = QApplication.clipboard()
            clipboard.setText(result)
            self.status_bar.showMessage("已复制到剪贴板", 2000)
    
    def clear_all(self):
        """清除所有内容"""
        self.image_label.clear()
        self.result_text.clear()
        self.decode_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        
        if hasattr(self, 'current_image_path'):
            del self.current_image_path
            
        self.status_bar.showMessage("已清除", 2000)
    
    def save_to_history(self, content, image_path):
        """保存到历史记录数据库"""
        # 提取第一个二维码的类型
        code_type = "未知"
        if content.startswith("["):
            code_type = content.split("]")[0][1:]
        
        self.cursor.execute(
            "INSERT INTO history (content, image_path, code_type) VALUES (?, ?, ?)",
            (content, image_path, code_type)
        )
        self.conn.commit()

    
    def load_history(self):
        """加载历史记录"""
        self.history_list.clear()
        self.cursor.execute("""
            SELECT id, timestamp, content, image_path, code_type, is_favorite 
            FROM history 
            ORDER BY is_favorite DESC, timestamp DESC
        """)
        records = self.cursor.fetchall()
        
        for record in records:
            id, timestamp, content, image_path, code_type, is_favorite = record
            item_text = f"{timestamp}: {content[:100]}{'...' if len(content) > 100 else ''}"
            item = QListWidgetItem(item_text)
            
            # 设置收藏项的背景色
            if is_favorite:
                item.setBackground(MacaronColors.LEMON_YELLOW)
            
            self.history_list.addItem(item)
            item.setData(Qt.UserRole, record)

    
    def load_history_item(self, item):
        """加载历史记录项"""
        record = item.data(Qt.UserRole)
        # 新结构包含6个字段
        if len(record) == 6:
            id, timestamp, content, image_path, code_type, is_favorite = record
        else:  # 兼容旧结构
            id, timestamp, content, image_path = record
        
        # 显示解码内容
        self.result_text.setPlainText(content)
        self.copy_button.setEnabled(True)
        
        # 显示图片
        if image_path:
            try:
                self.current_image_path = image_path
                pixmap = QPixmap(image_path)
                
                # 缩放图片以适应显示区域
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size() - QSize(20, 20), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                
                self.image_label.setPixmap(scaled_pixmap)
                self.decode_button.setEnabled(True)
                self.status_bar.showMessage(f"已加载历史记录: {timestamp}", 3000)
            except:
                self.status_bar.showMessage("无法加载历史图片", 3000)



    def paste_from_clipboard(self):
        """从剪贴板粘贴图片并显示"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            # 从剪贴板获取图片
            qimage = clipboard.image()
            if not qimage.isNull():
                # 转换为QPixmap显示
                pixmap = QPixmap.fromImage(qimage)
                
                # 缩放图片以适应显示区域
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size() - QSize(20, 20), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                
                self.image_label.setPixmap(scaled_pixmap)
                self.decode_button.setEnabled(True)
                
                # 标记为剪贴板来源
                self.current_image_path = "clipboard"
                self.status_bar.showMessage("已从剪贴板粘贴图片", 3000)
                return
        
        QMessageBox.warning(self, "警告", "剪贴板中没有图片数据")

    def keyPressEvent(self, event):
        """处理键盘快捷键"""
        # Ctrl+V 粘贴
        if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            self.paste_from_clipboard()
        else:
            super().keyPressEvent(event)

    def backup_database(self):
        """备份数据库"""
        backup_path = os.path.join(os.path.dirname(__file__), 'backups')
        os.makedirs(backup_path, exist_ok=True)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_path, f'qrcode_history_{timestamp}.db')
        
        try:
            # 使用SQLite的备份API
            new_conn = sqlite3.connect(backup_file)
            self.conn.backup(new_conn)
            new_conn.close()
            self.status_bar.showMessage(f"数据库已备份到: {backup_file}", 5000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "备份失败", f"数据库备份失败: {str(e)}")
            return False

    def optimize_database(self):
        """优化数据库"""
        try:
            self.cursor.execute("VACUUM")
            self.cursor.execute("ANALYZE")
            self.conn.commit()
            self.status_bar.showMessage("数据库优化完成", 3000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "优化失败", f"数据库优化失败: {str(e)}")
            return False

    def export_history(self, format='csv'):
        """导出历史记录"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出历史记录", "", 
            f"{format.upper()} 文件 (*.{format})"
        )
        
        if not file_path:
            return
        
        try:
            self.cursor.execute("SELECT timestamp, content, code_type FROM history ORDER BY timestamp")
            records = self.cursor.fetchall()
            
            if format == 'csv':
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['时间戳', '内容', '类型'])
                    writer.writerows(records)
            elif format == 'json':
                data = [{
                    'timestamp': record[0],
                    'content': record[1],
                    'code_type': record[2]
                } for record in records]
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
            self.status_bar.showMessage(f"历史记录已导出到: {file_path}", 5000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"历史记录导出失败: {str(e)}")
            return False

    def delete_history_item(self):
        """删除选中的历史记录项"""
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要删除的历史记录")
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除选中的历史记录吗？此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for item in selected_items:
                record = item.data(Qt.UserRole)
                self.cursor.execute("DELETE FROM history WHERE id=?", (record[0],))
                self.history_list.takeItem(self.history_list.row(item))
            
            self.conn.commit()
            self.status_bar.showMessage("已删除选中的历史记录", 3000)
            
    def toggle_favorite(self):
        """切换历史记录的收藏状态"""
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择历史记录")
            return
        
        for item in selected_items:
            record = item.data(Qt.UserRole)
            new_state = not bool(record[5]) if len(record) > 5 else True
            
            self.cursor.execute(
                "UPDATE history SET is_favorite=? WHERE id=?",
                (int(new_state), record[0])
            )
            
            # 更新显示
            if new_state:
                item.setBackground(MacaronColors.LEMON_YELLOW)
            else:
                item.setBackground(QColor(255, 255, 255))
        
        self.conn.commit()
        self.status_bar.showMessage("已更新收藏状态", 3000)

    def closeEvent(self, event):
        """关闭窗口事件"""
        self.conn.close()
        event.accept()

if __name__ == "__main__":
    # 必须在QApplication创建前设置高DPI
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion样式以获得更好的跨平台体验
    
    decoder = QRCodeDecoder()
    decoder.show()
    sys.exit(app.exec_())
