# 灵感画布 - 智能语音识别助手 (Inspiration Canvas Voice Assistant)

这是一个集成了强大的开源语音转文字（STT）模型，并配备极简且炫酷的前端界面的本地化语音助手。专门为持续捕捉灵感、会议记录以及无缝的语音与文本编辑混合工作流设计。

## ✨ 核心特性 
* **先进流式识别引擎**：基于本地部署的深度学习语音模型 (SenseVoiceSmall)，隐私安全无泄漏，拾音精确。
* **Gemini 风格记录系统**：
  * 支持无限嵌套的历史对话管理架构。
  * 自动记录与智能重载最近一次的语音对话上下文。
  * 完整的侧边栏（新建子层级、改名、删除）便捷式文件管理。
* **Smart Appending (混合编辑文本)**：区别于传统的“一句一刷新”与自动强制换行逻辑，本框架允许您在线修改和续写识别结果，并支持富文本级别的**实时动态插写，毫不突兀的体验。
* **色彩冲击 UI**：极致美感的神级七彩同心射线（`repeating-radial-gradient`）沉浸式全屏背景，海军深蓝中心保护阅读视野。无 `alert()` 不阻断的优雅悬浮吐丝 (Toast) 提示。
* **防阻塞异步优化**：后端麦克风流 (`pyaudio`) 从线程层面进行了全面改造，彻底消除按钮延迟。

## 🛠️ 安装环境与启动指南

### 1. 依赖安装
首先，确保您拥有 Python 环境。推荐在您的终端中新建一个虚机环境 (Anaconda / venv)：

```bash
conda create -n voice_to_gemini python=3.10
conda activate voice_to_gemini

# 安装核心依赖
pip install fastapi uvicorn pyaudio numpy funasr torch
```

*注意: 运行 `pyaudio` 在 Windows 下可能需要安装 C++ Build Tools，或通过 `.whl` 二进制文件安装。*

### 2. 启动服务
在项目根目录 `f:\audio_recognition` 下：
```bash
python asr.py
```
> 服务器会在 `0.0.0.0:8000` 启动，并预加载模型至显存 (自动切换 CPU/GPU)。

### 3. 访问客户端
打开您的现代浏览器，直接访问：
```
http://127.0.0.1:8000
```

## 📁 项目结构
* `asr.py`: FastAPI 的主网关，连接了 PyAudio 控制器、模型推理引擎与系统 API 调度系统。
* `audio_utils.py`: 高级语音清理、静音段 VAD 检测算法组件与基底的存档格式封装。
* `file_utils.py`: 为无极分类重度开发的树形历史管理逻辑，赋予侧边栏 Notion/Gemini 的功能调度。
* `static/index.html`: 全站所有的客户端呈现代码，融合了 JS 请求调度、深空质感的 CSS 代码、以及平滑动画。
* `output/`: 您的所有录音和识别对话默认生成在同级下（会按日期自动编号排好）。

## 📝 许可证
该项目采用 MIT License 开源，详见 [LICENSE](./LICENSE) 文件。
