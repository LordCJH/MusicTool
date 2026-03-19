"""
视频转MP3核心转换逻辑
"""
import os
import sys
import subprocess
from PySide6.QtCore import QThread, Signal


def get_ffmpeg_path():
    """获取FFmpeg可执行文件路径"""
    # 1. 首先检查本地tools目录
    if getattr(sys, 'frozen', False):
        # 打包后的exe运行环境
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    local_ffmpeg = os.path.join(base_dir, 'tools', 'ffmpeg', 'bin', 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg

    # 2. 检查系统PATH中的ffmpeg
    try:
        result = subprocess.run(
            ['where', 'ffmpeg'],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        if result.returncode == 0:
            return 'ffmpeg'
    except:
        pass

    return None


class VideoConverter(QThread):
    """视频转MP3转换器线程"""

    # 信号定义
    progress_updated = Signal(int)  # 总体进度百分比
    file_started = Signal(str)      # 开始处理文件
    file_finished = Signal(str, bool, str)  # 文件处理完成(文件名, 成功/失败, 消息)
    all_finished = Signal()         # 全部完成

    def __init__(self, file_list, output_dir):
        """
        初始化转换器

        Args:
            file_list: 待转换的视频文件路径列表
            output_dir: 输出目录路径
        """
        super().__init__()
        self.file_list = file_list
        self.output_dir = output_dir
        self._is_running = True
        self.ffmpeg_path = get_ffmpeg_path()

    def stop(self):
        """停止转换"""
        self._is_running = False

    def run(self):
        """执行批量转换"""
        total = len(self.file_list)

        for index, file_path in enumerate(self.file_list):
            if not self._is_running:
                break

            # 发送开始信号
            file_name = os.path.basename(file_path)
            self.file_started.emit(file_name)

            # 执行转换
            success, message = self._convert_file(file_path)

            # 发送完成信号
            self.file_finished.emit(file_name, success, message)

            # 更新总体进度
            progress = int((index + 1) / total * 100)
            self.progress_updated.emit(progress)

        self.all_finished.emit()

    def _convert_file(self, file_path):
        """
        转换单个视频文件为MP3

        Args:
            file_path: 视频文件路径

        Returns:
            (success: bool, message: str)
        """
        try:
            if not os.path.exists(file_path):
                return False, "文件不存在"

            if not self.ffmpeg_path:
                return False, "未找到FFmpeg，请确保tools/ffmpeg/bin/ffmpeg.exe存在"

            # 生成输出文件名
            file_name = os.path.basename(file_path)
            name_without_ext = os.path.splitext(file_name)[0]
            output_path = os.path.join(self.output_dir, f"{name_without_ext}.mp3")

            # 确保输出目录存在
            os.makedirs(self.output_dir, exist_ok=True)

            # 构建FFmpeg命令
            # MP3参数: 采样率44100Hz, 比特率192k
            cmd = [
                self.ffmpeg_path,
                '-i', file_path,           # 输入文件
                '-vn',                     # 不输出视频
                '-acodec', 'libmp3lame',   # MP3编码器
                '-ar', '44100',            # 采样率
                '-ab', '192k',             # 比特率
                '-y',                      # 覆盖输出文件
                output_path
            ]

            # 执行FFmpeg命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300,  # 5分钟超时
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )

            if result.returncode == 0:
                return True, f"已保存到: {output_path}"
            else:
                error_msg = result.stderr.decode('utf-8', errors='ignore')[-200:] if result.stderr else "未知错误"
                return False, f"FFmpeg错误: {error_msg}"

        except subprocess.TimeoutExpired:
            return False, "转换超时"
        except Exception as e:
            return False, f"转换失败: {str(e)}"


def scan_video_files(directory):
    """
    扫描目录中的视频文件

    Args:
        directory: 要扫描的目录路径

    Returns:
        视频文件路径列表
    """
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.m4v', '.webm'}
    video_files = []

    if not os.path.exists(directory):
        return video_files

    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        if os.path.isfile(file_path):
            ext = os.path.splitext(file_name)[1].lower()
            if ext in video_extensions:
                video_files.append(file_path)

    return sorted(video_files)


def check_ffmpeg():
    """检查ffmpeg是否可用"""
    return get_ffmpeg_path() is not None
