"""
视频转MP3主窗口UI
"""
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QProgressBar, QPlainTextEdit, QFileDialog, QMessageBox,
    QGroupBox, QCheckBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.converter import VideoConverter, scan_video_files, check_ffmpeg


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频转MP3工具")
        self.setMinimumSize(800, 600)

        self.input_dir = "./Input/"
        self.output_dir = "./Output/"
        self.converter = None
        self.video_files = []

        self._setup_ui()
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        """检查ffmpeg是否已安装"""
        if not check_ffmpeg():
            QMessageBox.warning(
                self,
                "警告",
                "未检测到FFmpeg！请确保FFmpeg已安装并添加到系统PATH中。\n\n"
                "下载地址: https://ffmpeg.org/download.html"
            )

    def _setup_ui(self):
        """设置UI界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ========== 输入区域 ==========
        input_group = QGroupBox("输入设置")
        input_layout = QHBoxLayout(input_group)

        self.input_path_label = QLineEdit(self.input_dir)
        self.input_path_label.setReadOnly(True)

        btn_select_input = QPushButton("选择输入目录")
        btn_select_input.clicked.connect(self._on_select_input)

        btn_scan = QPushButton("扫描文件")
        btn_scan.clicked.connect(self._on_scan_files)

        input_layout.addWidget(QLabel("输入目录:"))
        input_layout.addWidget(self.input_path_label, 1)
        input_layout.addWidget(btn_select_input)
        input_layout.addWidget(btn_scan)

        main_layout.addWidget(input_group)

        # ========== 输出区域 ==========
        output_group = QGroupBox("输出设置")
        output_layout = QHBoxLayout(output_group)

        self.output_path_label = QLineEdit(self.output_dir)
        self.output_path_label.setReadOnly(True)

        btn_select_output = QPushButton("选择输出目录")
        btn_select_output.clicked.connect(self._on_select_output)

        output_layout.addWidget(QLabel("输出目录:"))
        output_layout.addWidget(self.output_path_label, 1)
        output_layout.addWidget(btn_select_output)

        main_layout.addWidget(output_group)

        # ========== 文件列表区域 ==========
        files_group = QGroupBox("视频文件列表")
        files_layout = QVBoxLayout(files_group)

        # 全选/反选按钮
        select_layout = QHBoxLayout()
        self.chk_select_all = QCheckBox("全选")
        self.chk_select_all.stateChanged.connect(self._on_select_all_changed)

        lbl_file_count = QLabel("文件数量: 0")
        self.lbl_file_count = lbl_file_count

        select_layout.addWidget(self.chk_select_all)
        select_layout.addStretch()
        select_layout.addWidget(lbl_file_count)

        files_layout.addLayout(select_layout)

        # 文件列表
        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        files_layout.addWidget(self.file_list_widget)

        main_layout.addWidget(files_group, 1)

        # ========== 操作区域 ==========
        operation_group = QGroupBox("操作")
        operation_layout = QVBoxLayout(operation_group)

        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("总体进度:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar, 1)

        operation_layout.addLayout(progress_layout)

        # 开始按钮
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("开始转换")
        self.btn_start.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.btn_start.setMinimumHeight(40)
        self.btn_start.clicked.connect(self._on_start_convert)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop_convert)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)

        operation_layout.addLayout(btn_layout)

        main_layout.addWidget(operation_group)

        # ========== 日志区域 ==========
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(100)
        log_layout.addWidget(self.log_text)

        # 清空日志按钮
        btn_clear_log = QPushButton("清空日志")
        btn_clear_log.clicked.connect(self._on_clear_log)
        log_layout.addWidget(btn_clear_log)

        main_layout.addWidget(log_group, 1)

    def _on_select_input(self):
        """选择输入目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输入目录", self.input_dir
        )
        if dir_path:
            self.input_dir = dir_path
            self.input_path_label.setText(self.input_dir)
            self._on_scan_files()

    def _on_select_output(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self.output_dir
        )
        if dir_path:
            self.output_dir = dir_path
            self.output_path_label.setText(self.output_dir)

    def _on_scan_files(self):
        """扫描视频文件"""
        self.file_list_widget.clear()
        self.video_files = scan_video_files(self.input_dir)

        for file_path in self.video_files:
            item = QListWidgetItem(os.path.basename(file_path))
            item.setData(Qt.UserRole, file_path)
            self.file_list_widget.addItem(item)

        self.lbl_file_count.setText(f"文件数量: {len(self.video_files)}")
        self._log(f"扫描完成，找到 {len(self.video_files)} 个视频文件")

        # 默认全选
        self.file_list_widget.selectAll()

    def _on_select_all_changed(self, state):
        """全选状态改变"""
        if state == Qt.Checked:
            self.file_list_widget.selectAll()
        else:
            self.file_list_widget.clearSelection()

    def _on_start_convert(self):
        """开始转换"""
        # 获取选中的文件
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要转换的视频文件！")
            return

        selected_files = []
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            selected_files.append(file_path)

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        # 创建并启动转换线程
        self.converter = VideoConverter(selected_files, self.output_dir)
        self.converter.progress_updated.connect(self._on_progress_updated)
        self.converter.file_started.connect(self._on_file_started)
        self.converter.file_finished.connect(self._on_file_finished)
        self.converter.all_finished.connect(self._on_all_finished)
        self.converter.start()

        # 更新UI状态
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        self._log(f"开始转换 {len(selected_files)} 个文件...")

    def _on_stop_convert(self):
        """停止转换"""
        if self.converter and self.converter.isRunning():
            self.converter.stop()
            self._log("正在停止转换...")

    def _on_progress_updated(self, progress):
        """进度更新"""
        self.progress_bar.setValue(progress)

    def _on_file_started(self, file_name):
        """文件开始处理"""
        self._log(f"正在转换: {file_name}")

    def _on_file_finished(self, file_name, success, message):
        """文件处理完成"""
        status = "✓ 成功" if success else "✗ 失败"
        self._log(f"{status} - {file_name}")
        if message:
            self._log(f"  └─ {message}")

    def _on_all_finished(self):
        """全部转换完成"""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._log("=" * 40)
        self._log("转换任务完成！")
        self._log("=" * 40)

    def _on_clear_log(self):
        """清空日志"""
        self.log_text.clear()

    def _log(self, message):
        """添加日志"""
        from PySide6.QtCore import QDateTime
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.log_text.append(f"[{timestamp}] {message}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.converter and self.converter.isRunning():
            self.converter.stop()
            self.converter.wait(2000)
        event.accept()
