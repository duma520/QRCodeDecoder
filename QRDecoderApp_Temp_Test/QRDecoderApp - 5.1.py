import os
import sys
import cv2
import numpy as np
from PyQt5.QtCore import Qt, QSettings, QSize, QPoint, QRect, QTranslator, QLibraryInfo
from PyQt5.QtGui import QIcon, QImage, QPixmap, QKeySequence, QClipboard, QPainter, QPen, QPolygon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QMessageBox, QScrollArea,
                             QSizePolicy, QAction, QMenuBar, QStatusBar, QToolBar)


class QRDecoder:
    def __init__(self):
        # 初始化微信解码器需要的模型文件
        self.detect_net = cv2.dnn.readNetFromCaffe("detect.prototxt", "detect.caffemodel")
        self.sr_net = cv2.dnn.readNetFromCaffe("sr.prototxt", "sr.caffemodel")
        
    def decode_wechat_qrcode(self, image):
        """使用微信官方解码器解码"""
        try:
            # 转换为灰度图像
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 检查OpenCV版本并选择正确的API
            if hasattr(cv2, 'wechat_qrcode_WeChatQRCode'):  # 旧版API
                detector = cv2.wechat_qrcode_WeChatQRCode(
                    "detect.prototxt", "detect.caffemodel",
                    "sr.prototxt", "sr.caffemodel"
                )
            elif hasattr(cv2, 'wechat_qrcode'):  # 新版API
                detector = cv2.wechat_qrcode.WeChatQRCode(
                    "detect.prototxt", "detect.caffemodel",
                    "sr.prototxt", "sr.caffemodel"
                )
            else:
                print("当前OpenCV版本不支持微信二维码解码器")
                return None, None
            
            results, points = detector.detectAndDecode(gray)
            
            if len(results) > 0:
                return results[0], points
            return None, None
        except Exception as e:
            print(f"微信解码器错误: {e}")
            return None, None

    
    def decode_opencv(self, image):
        """使用OpenCV解码"""
        try:
            # 转换为灰度图像
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 使用OpenCV QR码解码器
            detector = cv2.QRCodeDetector()
            retval, decoded_info, points, straight_qrcode = detector.detectAndDecodeMulti(gray)
            
            if retval and decoded_info:
                return decoded_info[0], points[0]
            return None, None
        except Exception as e:
            print(f"OpenCV解码错误: {e}")
            return None, None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 初始化设置
        self.settings = QSettings("WeChatQRDecoder", "SunQRDecoder")
        self.decoder = QRDecoder()
        
        # 初始化UI
        self.init_ui()
        
        # 加载上次的窗口状态
        self.load_settings()
        
        # 检查图标文件
        if os.path.exists("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("微信小程序太阳码解码工具")
        
        # 创建主部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # 图像显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setMinimumSize(400, 300)
        
        # 创建滚动区域以便查看大图
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area, 1)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        # 打开文件按钮
        self.open_button = QPushButton("打开文件")
        self.open_button.clicked.connect(self.open_image)
        button_layout.addWidget(self.open_button)
        
        # 粘贴按钮
        self.paste_button = QPushButton("粘贴 (Ctrl+V)")
        self.paste_button.clicked.connect(self.paste_image)
        button_layout.addWidget(self.paste_button)
        
        # 解码按钮
        self.decode_button = QPushButton("解码")
        self.decode_button.clicked.connect(self.decode_image)
        button_layout.addWidget(self.decode_button)
        
        # 结果区域
        self.result_label = QLabel("结果将显示在这里")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setWordWrap(True)
        main_layout.addWidget(self.result_label)
        
        # 创建菜单栏
        self.create_menus()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 设置窗口最小大小
        self.setMinimumSize(600, 500)
        
        # 添加快捷键
        self.setup_shortcuts()
    
    def create_menus(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        open_action = QAction("打开", self)
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)
        
        paste_action = QAction("粘贴", self)
        paste_action.triggered.connect(self.paste_image)
        file_menu.addAction(paste_action)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 解码菜单
        decode_menu = menubar.addMenu("解码")
        
        decode_action = QAction("解码图像", self)
        decode_action.triggered.connect(self.decode_image)
        decode_menu.addAction(decode_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("Main Toolbar")  # 添加明确的名称
        toolbar.setObjectName("MainToolbar")  # 设置objectName
        self.addToolBar(toolbar)
        
        toolbar.addAction("打开", self.open_image)
        toolbar.addAction("粘贴", self.paste_image)
        toolbar.addAction("解码", self.decode_image)

    
    def setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+V 粘贴
        paste_shortcut = QAction(self)
        paste_shortcut.setShortcut(QKeySequence.Paste)
        paste_shortcut.triggered.connect(self.paste_image)
        self.addAction(paste_shortcut)
        
        # Ctrl+O 打开
        open_shortcut = QAction(self)
        open_shortcut.setShortcut(QKeySequence.Open)
        open_shortcut.triggered.connect(self.open_image)
        self.addAction(open_shortcut)
        
        # Ctrl+D 解码
        decode_shortcut = QAction(self)
        decode_shortcut.setShortcut(Qt.CTRL + Qt.Key_D)
        decode_shortcut.triggered.connect(self.decode_image)
        self.addAction(decode_shortcut)
    
    def open_image(self):
        """打开图像文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开图像文件", "",
            "图像文件 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )
        
        if file_path:
            self.load_image(file_path)
    
    def paste_image(self):
        """从剪贴板粘贴图像"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            # 从剪贴板获取图像
            qimage = clipboard.image()
            self.display_qimage(qimage)
        elif mime_data.hasUrls():
            # 处理文件URL
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
                        self.load_image(file_path)
                        break
        else:
            QMessageBox.information(self, "提示", "剪贴板中没有可用的图像")
    
    def load_image(self, file_path):
        """加载图像文件"""
        try:
            # 使用OpenCV读取图像
            cv_image = cv2.imread(file_path)
            if cv_image is None:
                raise ValueError("无法读取图像文件")
            
            # 转换为Qt图像并显示
            height, width, channel = cv_image.shape
            bytes_per_line = 3 * width
            qimage = QImage(cv_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            self.display_qimage(qimage)
            
            # 保存最后打开的路径
            self.settings.setValue("last_directory", os.path.dirname(file_path))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载图像: {str(e)}")
    
    def display_qimage(self, qimage):
        """显示QImage"""
        pixmap = QPixmap.fromImage(qimage)
        self.current_pixmap = pixmap  # 保存当前图像
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        ))
    
    def decode_image(self):
        """解码当前显示的图像"""
        if not hasattr(self, 'current_pixmap'):
            QMessageBox.warning(self, "警告", "没有可解码的图像")
            return
        
        # 将QPixmap转换为OpenCV格式
        qimage = self.current_pixmap.toImage()
        qimage = qimage.convertToFormat(QImage.Format_RGB888)
        width = qimage.width()
        height = qimage.height()
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        arr = np.array(ptr).reshape(height, width, 3)  # 复制数据
        
        # 转换为BGR格式供OpenCV使用
        cv_image = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        
        # 先尝试使用微信解码器
        result, points = self.decoder.decode_wechat_qrcode(cv_image)
        
        # 如果微信解码器失败，尝试OpenCV解码器
        if result is None:
            result, points = self.decoder.decode_opencv(cv_image)
        
        if result:
            self.result_label.setText(f"解码结果: {result}")
            
            # 在图像上绘制检测到的二维码区域
            if points is not None:
                self.draw_qr_region(points)
        else:
            self.result_label.setText("未能识别二维码")
    
    def draw_qr_region(self, points):
        """在图像上绘制二维码区域"""
        try:
            # 将QPixmap转换为QImage以便修改
            qimage = self.current_pixmap.toImage()
            painter = QPainter(qimage)
            painter.setPen(QPen(Qt.red, 3))
            
            # 绘制多边形
            polygon = QPolygon()
            for point in points:
                # 微信解码器返回的点是浮点坐标
                x, y = point[0], point[1] if isinstance(point, (list, np.ndarray)) else point.x(), point.y()
                polygon.append(QPoint(int(x), int(y)))
            
            painter.drawPolygon(polygon)
            painter.end()
            
            # 更新显示
            self.current_pixmap = QPixmap.fromImage(qimage)
            self.image_label.setPixmap(self.current_pixmap.scaled(
                self.image_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            ))
        except Exception as e:
            print(f"绘制二维码区域时出错: {e}")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", 
                         "微信小程序太阳码解码工具\n\n"
                         "用于解码微信小程序非方块形二维码(太阳码)\n"
                         "支持从文件打开或剪贴板粘贴图像\n"
                         "使用微信官方解码器和OpenCV进行解码")
    
    def load_settings(self):
        """加载保存的设置"""
        # 窗口几何状态
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # 窗口状态（最大化等）
        window_state = self.settings.value("window_state")
        if window_state:
            self.restoreState(window_state)
        
        # 其他设置
        self.last_directory = self.settings.value("last_directory", "")
    
    def save_settings(self):
        """保存当前设置"""
        # 窗口几何状态
        self.settings.setValue("geometry", self.saveGeometry())
        
        # 窗口状态
        self.settings.setValue("window_state", self.saveState())
        
        # 其他设置
        if hasattr(self, 'last_directory'):
            self.settings.setValue("last_directory", self.last_directory)
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        
        # 调整图像大小以适应新窗口尺寸
        if hasattr(self, 'current_pixmap'):
            self.image_label.setPixmap(self.current_pixmap.scaled(
                self.image_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            ))
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.save_settings()
        super().closeEvent(event)


if __name__ == "__main__":
    # 检查模型文件是否存在
    required_files = ["detect.prototxt", "detect.caffemodel", "sr.prototxt", "sr.caffemodel"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"错误: 缺少必要的模型文件: {', '.join(missing_files)}")
        print("请确保以下文件存在于程序目录中:")
        print("- detect.prototxt")
        print("- detect.caffemodel")
        print("- sr.prototxt")
        print("- sr.caffemodel")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion风格以获得更好的外观
    
    # 设置中文语言
    translator = QTranslator()
    if translator.load("qt_zh_CN.qm", QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
        app.installTranslator(translator)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())