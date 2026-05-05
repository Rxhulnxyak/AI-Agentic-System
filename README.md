# Kolimarii: Personal Neural Assistant

Kolimarii is a high-performance, cross-platform AI assistant designed for system-level automation, web intelligence, and smart home control. It features a stunning glassmorphic UI and supports voice-activated commands.

## 🧠 Intelligence & Brain
Kolimarii uses a multi-provider "Brain" system that supports:
- **OpenAI** (GPT-4o)
- **Anthropic** (Claude 3.5 Sonnet)
- **Mistral** (Mistral Large)

It includes a **Long-term Memory** system powered by ChromaDB, allowing it to remember user preferences and past interactions across sessions.

## 🛠️ Key Capabilities

- **Desktop Automation**: Open apps, type text, press hotkeys, and read screen content via OCR.
- **Web Intelligence**: Real-time search, news retrieval, image search, and deep-page scraping.
- **Android Integration**: Send SMS, read notifications, and take phone screenshots via ADB.
- **Smart Home**: Control lights, switches, and check device status via Home Assistant integration.
- **Voice Stack**: 
    - **Wake Word**: "Computer" (PvPorcupine).
    - **STT**: Whisper Base for high-accuracy transcription.
    - **TTS**: Premium voices via ElevenLabs or fast local synthesis via pyttsx3.

## 🖥️ User Interface
A futuristic dashboard featuring:
- **Neural Orb**: Interactive visual feedback for thinking and speaking states.
- **Activity Log**: Real-time monitoring of tool execution.
- **System Telemetry**: Live tracking of CPU, RAM, and phone connection status.

## 🚀 Quick Start

### 1. Configuration
Update the `.env` file with your API keys:
```env
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
MISTRAL_API_KEY=your_key
HASS_URL=your_home_assistant_url
```

### 2. Run the Assistant
```powershell
python main.py
```

### 3. Open the UI
Launch `index.html` in any modern web browser to interact with the visual dashboard.

## 🔧 Troubleshooting
If you encounter a `Mistral` import error, ensure you are using the modern SDK import path:
`from mistralai.client import Mistral`

---
*Next-generation cognitive automation.*
