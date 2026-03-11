import os
import queue
import numpy as np
import pyaudio
import torch
import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from funasr import AutoModel
import uvicorn

from audio_utils import (
    super_clean, 
    is_silent, 
    create_session_folder, 
    create_segment_folder, 
    save_result,
    AudioState
)

# 路径与环境配置
os.environ['MODELSCOPE_CACHE'] = r'F:\audio_recognition'
os.environ['HF_HOME'] = r'F:\audio_recognition\hf_cache'

if not os.path.exists(os.environ['MODELSCOPE_CACHE']):
    os.makedirs(os.environ['MODELSCOPE_CACHE'])

app = FastAPI(title="Audio Recognition API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 全局状态
class AppState:
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = None
    audio = None
    stream = None
    audio_queue = queue.Queue()
    status = AudioState.IDLE
    current_session_dir = None
    last_text = ""
    session_texts = []
    recognition_task = None
    
    # 录音配置
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 16000
    VAD_THRESHOLD = 300

state = AppState()

def audio_callback(in_data, frame_count, time_info, status):
    if state.status == AudioState.RECORDING:
        state.audio_queue.put(in_data)
    return (None, pyaudio.paContinue)

@app.on_event("startup")
async def startup_event():
    print(f"--- 硬件检测：[{state.device}] ---")
    state.model = AutoModel(
        model="iic/SenseVoiceSmall",
        device=state.device,
        disable_update=True
    )
    
    # 初始化 PyAudio
    state.audio = pyaudio.PyAudio()
    state.stream = state.audio.open(
        format=state.FORMAT, channels=state.CHANNELS, rate=state.RATE, input=True,
        frames_per_buffer=state.CHUNK, stream_callback=audio_callback,
        start=False # 初始为冻结状态
    )
    
    # 开启后台识别循环
    state.recognition_task = asyncio.create_task(recognition_loop())
    print("\n>>> 音频服务已启动，处于空闲(IDLE)状态，等待 API 指令(127.0.0.1:8000)...\n")
    
@app.on_event("shutdown")
async def shutdown_event():
    state.status = AudioState.IDLE
    if state.stream:
        state.stream.stop_stream()
        state.stream.close()
    if state.audio:
        state.audio.terminate()
    if state.recognition_task:
        state.recognition_task.cancel()
    print("已安全关闭资源。")

async def recognition_loop():
    output_file = os.path.join(os.environ['MODELSCOPE_CACHE'], "learning_results.txt")
    while True:
        if state.status != AudioState.RECORDING:
            await asyncio.sleep(0.5)
            continue
            
        # 从队列获取音频
        try:
            data = state.audio_queue.get_nowait()
        except queue.Empty:
            await asyncio.sleep(0.1)
            continue
            
        if is_silent(data, state.VAD_THRESHOLD):
            continue
            
        audio_int16 = np.frombuffer(data, dtype=np.int16)
        audio_data = audio_int16.astype(np.float32) / 32768.0
        
        try:
            # 使用 asyncio.to_thread 防止阻塞事件循环
            res = await asyncio.to_thread(
                state.model.generate,
                input=audio_data, 
                cache={}, 
                language="auto", 
                use_itn=True
            )
            
            if res:
                raw_result = res[0]['text']
                clean_result = super_clean(raw_result)
                
                # 过滤掉过短的无意义噪音和重复内容
                if len(clean_result) > 1 and clean_result != state.last_text:
                    print(f"\r[识别]: {clean_result}          ", flush=True)
                    
                    # 保存到汇总文件
                    with open(output_file, "a", encoding="utf-8") as f:
                        f.write(clean_result + "\n")
                        
                    # 创建子文件夹并保存单次结果
                    if state.current_session_dir:
                        segment_dir = create_segment_folder(state.current_session_dir)
                        # We save it but we don't append newline in session_texts necessarily
                        save_result(segment_dir, clean_result)
                        
                    state.last_text = clean_result
                    
                    # Instead of treating each segment as a totally independent line, 
                    # we append without newline unless a pause happened.
                    if state.session_texts and state.session_texts[-1] == "\n":
                        state.session_texts.append(clean_result)
                    else:
                        # Append continuously to the last segment or create first setup
                        if not state.session_texts:
                            state.session_texts.append(clean_result)
                        else:
                            state.session_texts[-1] += clean_result
        except Exception as e:
            print(f"\n[错误] 识别过程发生异常: {str(e)}")

# --- API 接口部分 ---

class StartRequest(BaseModel):
    session_name: str = "default_session"

@app.post("/api/start")
async def start_recording(req: StartRequest):
    if state.status == AudioState.RECORDING:
        return {"status": "error", "message": "已经在录音中"}
        
    if state.status == AudioState.IDLE:
        # 创建新的会话文件夹
        base_dir = os.path.join(os.environ['MODELSCOPE_CACHE'], "output")
        state.current_session_dir = create_session_folder(base_dir, req.session_name)
        state.session_texts = []
    
    state.status = AudioState.RECORDING
    await asyncio.to_thread(state.stream.start_stream)
    return {"status": "success", "message": "开始录音，输出目录已准备", "session_dir": state.current_session_dir}

@app.post("/api/pause")
async def pause_recording():
    if state.status != AudioState.RECORDING:
        return {"status": "error", "message": "当前不在录音状态"}
        
    state.status = AudioState.PAUSED
    await asyncio.to_thread(state.stream.stop_stream)
    # 增加一个换行标记位
    if state.session_texts and state.session_texts[-1] != "\n":
        state.session_texts.append("\n")
        
    return {"status": "success", "message": "暂停录音"}

@app.post("/api/stop")
async def stop_recording():
    state.status = AudioState.IDLE
    if state.stream and state.stream.is_active():
        await asyncio.to_thread(state.stream.stop_stream)
    
    # 清空队列中遗留的数据
    while not state.audio_queue.empty():
        state.audio_queue.get()
        
    finished_session = state.current_session_dir
    state.current_session_dir = None
    state.last_text = ""
    return {"status": "success", "message": "停止录音", "session_dir": finished_session}

@app.get("/api/status")
async def get_status():
    return {"status": state.status.value, "session_dir": state.current_session_dir}

@app.get("/api/text")
async def get_text():
    return {"status": "success", "session_dir": state.current_session_dir, "texts": state.session_texts}

@app.get("/api/history")
async def get_history():
    base_dir = os.path.join(os.environ['MODELSCOPE_CACHE'], "output")
    if not os.path.exists(base_dir):
        return {"history": []}
    
    sessions = []
    for d in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, d)):
            sessions.append(d)
    
    sessions.sort(reverse=True)
    return {"history": sessions}

@app.get("/api/history/{session_name}")
async def get_session_history(session_name: str):
    base_dir = os.path.join(os.environ['MODELSCOPE_CACHE'], "output")
    session_dir = os.path.join(base_dir, session_name)
    if not os.path.exists(session_dir):
        return {"texts": []}
        
    texts = []
    segments = []
    for d in os.listdir(session_dir):
        seg_dir = os.path.join(session_dir, d)
        if os.path.isdir(seg_dir):
            segments.append(seg_dir)
            
    segments.sort()
    for seg in segments:
        txt_path = os.path.join(seg, "result.txt")
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                texts.append(f.read().strip())
                
    return {"texts": texts}

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Please create static/index.html"

if __name__ == "__main__":
    print("正在启动 FastAPI 服务器...")
    uvicorn.run("asr:app", host="0.0.0.0", port=8000, reload=False)