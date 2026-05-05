import asyncio
import sys
import signal
import datetime
import threading
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from logger import logger
from config import settings
from utils import handle_errors, ensure_dir
from voice import VoiceEngine
from audio_stream import AudioStream
from brain import Brain
from planner import Planner
from memory import Memory

class KolimariiAssistant:
    def __init__(self):
        self.running = False
        logger.info("Initializing Kolimarii Assistant...")
        
        ensure_dir("logs")
        self.memory = Memory()
        self.audio = AudioStream()
        self.voice = VoiceEngine()
        self.planner = Planner(memory=self.memory)
        self.brain = Brain(memory=self.memory, planner=self.planner)

    async def initialize_components(self):
        # Check for critical API keys (Any of the supported LLMs)
        ai_keys = [settings.ai.anthropic_api_key, settings.ai.openai_api_key, settings.ai.mistral_api_key]
        has_valid_key = any(k and "your_" not in k for k in ai_keys)
        
        if not has_valid_key:
            logger.error("No valid AI API Key found! Assistant will be unable to process requests.")
            logger.info("Please update your .env file with an Anthropic, OpenAI, or Mistral key.")
        
        self.voice.init_wake_word()
        await asyncio.to_thread(self.voice.load_stt_model, "base")
        
        if not self.voice.porcupine:
            logger.warning("Wake word detection disabled. Sound detection will be used instead.")
            
        self.voice.speak("Kolimarii system online and ready.")

    async def process_user_request(self, text: str):
        if not text or len(text) < 2: return {"text": "I'm listening..."}
        
        response_data = await self.brain.process_query(text)

        response_text = response_data.get("text", "")
        if response_text:
            self.voice.speak(response_text)
        return response_data

    async def start_voice_loop(self):
        self.running = True
        self.audio.start()
        try:
            while self.running:
                pcm = self.audio.read()
                if self.voice.porcupine:
                    if self.voice.process_wake_word(pcm):
                        self.voice.speak("Yes?")
                        command = await asyncio.to_thread(self.voice.listen_and_transcribe, self.audio)
                        await self.process_user_request(command)
                else:
                    rms = np.sqrt(np.mean(pcm.astype(np.float32)**2))
                    if rms > 700: # Lowered from 1000 for better sensitivity
                        command = await asyncio.to_thread(self.voice.listen_and_transcribe, self.audio)
                        await self.process_user_request(command)
                await asyncio.sleep(0.01)
        finally:
            self.audio.stop()

# --- WEB SERVER BRIDGE ---
app = Flask(__name__)
CORS(app)
assistant = KolimariiAssistant()

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    query = data.get("query")
    # Run async logic in synchronous Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(assistant.process_user_request(query))
    return jsonify(response)

@app.route('/config', methods=['POST'])
def update_config():
    data = request.json
    try:
        from dotenv import set_key
        env_file = ".env"
        for key, value in data.items():
            if value: # Only update if value is provided
                set_key(env_file, key.upper(), value)
        return jsonify({"status": "success", "message": "Settings updated. Please restart Kolimarii for changes to take effect."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    import psutil
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    
    # Check phone connection
    phone_connected = assistant.planner.android.is_connected()
    
    return jsonify({
        "cpu": cpu,
        "ram": ram,
        "phone": "Connected" if phone_connected else "Disconnected",
        "time": assistant.planner.get_time()
    })

def run_web_server():
    app.run(port=5000, debug=False, use_reloader=False)

async def main():
    await assistant.initialize_components()
    
    # Start web server in background thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    logger.info("Web Server active at http://localhost:5000")
    
    await assistant.start_voice_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
