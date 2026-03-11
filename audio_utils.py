import os
import re
import datetime
import numpy as np
from enum import Enum

class AudioState(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"

def super_clean(raw_text: str) -> str:
    """清理语音识别结果中的标签和无意义词"""
    # 移除所有中括号和尖括号内的标签 [zh], <|EMO|>, etc.
    text = re.sub(r'\[.*?\]|<\|.*?\|>', '', raw_text)
    
    # 移除常见的幻听词和无意义英文
    garbage_words = [
        'Yeah', 'Okay', 'withitn', 'Speech', 'EMO_UNKNOWN', 
        'NEUTRAL', 'HAPPY', 'SAD', 'ANGRY', 'nospeech'
    ]
    for word in garbage_words:
        # (?i) 忽略大小写，边界匹配用非字母数字字符或者开头结尾
        text = re.sub(rf'(?i)(^|[^a-zA-Z]){word}([^a-zA-Z]|$)', r'\1\2', text)
    
    # 移除多余标点和空格 (保留中英文字符、数字和基础标点)
    text = re.sub(r'[^\w\s\u4e00-\u9fa5，。！？,!?]', '', text) 
    return text.strip()

def is_silent(audio_data: bytes, threshold: int = 300) -> bool:
    """检测音频是否是静音"""
    audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
    if len(audio_int16) == 0:
        return True
    return np.abs(audio_int16).mean() < threshold

def create_session_folder(base_dir: str, session_name: str) -> str:
    """创建主会话文件夹"""
    session_dir = os.path.join(base_dir, session_name)
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    else:
        # 如果存在重名，则追加时间戳
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(base_dir, f"{session_name}_{timestamp}")
        os.makedirs(session_dir)
    return session_dir

def create_segment_folder(session_dir: str) -> str:
    """在当前会话下创建单次说话的子文件夹"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_name = os.path.basename(session_dir)
    # 取基底的名称，如果基底名称带时间戳后缀也可以
    clean_session_name = session_name.split('_202')[0] if '_202' in session_name else session_name
    
    folder_name = f"{timestamp}_{clean_session_name}"
    segment_dir = os.path.join(session_dir, folder_name)
    os.makedirs(segment_dir, exist_ok=True)
    return segment_dir

def save_result(segment_dir: str, text: str) -> str:
    """保存文本结果到指定子目录"""
    file_path = os.path.join(segment_dir, "result.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    return file_path
