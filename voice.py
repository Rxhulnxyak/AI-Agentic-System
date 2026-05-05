import os
import pvporcupine
import whisper
import pyttsx3
import numpy as np
from elevenlabs import play
from elevenlabs.client import ElevenLabs
from logger import logger
from config import settings
from utils import handle_errors, time_it
from audio_stream import AudioStream

class VoiceEngine:
    """Core engine for STT, TTS, and Wake Word detection."""

    def __init__(self):
        self.settings = settings.voice
        self.stt_model = None
        self.tts_engine = pyttsx3.init()
        self.porcupine = None
        self.el_client = None
        
        # Set pyttsx3 voice to female (usually index 1 on Windows)
        voices = self.tts_engine.getProperty('voices')
        self.tts_engine.setProperty('rate', 170) # Slowed down from 200
        for voice in voices:
            if "female" in voice.name.lower() or "zira" in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        # Initialize ElevenLabs client if key is present
        if self.settings.elevenlabs_api_key and "your_" not in self.settings.elevenlabs_api_key:
            try:
                self.el_client = ElevenLabs(api_key=self.settings.elevenlabs_api_key)
                logger.info("ElevenLabs Client initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize ElevenLabs client: {e}")
        else:
            logger.info("ElevenLabs API Key not set. Using pyttsx3 for TTS.")

    @handle_errors("Voice")
    def init_wake_word(self):
        """Initializes PvPorcupine for wake word detection."""
        if not self.settings.pvporcupine_api_key or "your_" in self.settings.pvporcupine_api_key:
            logger.warning("PvPorcupine API Key missing or default. Wake word detection disabled.")
            return

        try:
            self.porcupine = pvporcupine.create(
                access_key=self.settings.pvporcupine_api_key,
                keywords=['computer']
            )
            logger.info("Wake word detection ('computer') initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Porcupine: {e}")
            logger.warning("Please ensure your PVPORCUPINE_API_KEY is correct in .env")

    @handle_errors("Voice")
    @time_it
    def load_stt_model(self, model_size: str = "base"):
        """Loads the Whisper STT model."""
        logger.info(f"Loading Whisper STT model ({model_size})...")
        self.stt_model = whisper.load_model(model_size)
        logger.success("Whisper STT model loaded.")

    @handle_errors("Voice")
    def speak(self, text: str):
        """Speaks the given text using ElevenLabs or pyttsx3."""
        logger.info(f"Speaking: {text}")
        
        if self.el_client:
            try:
                # ElevenLabs v2.x usage
                voice_id = os.getenv("ELEVENLABS_VOICE_ID", "Rachel")
                audio = self.el_client.text_to_speech.convert(
                    text=text,
                    voice_id=voice_id,
                    model_id="eleven_multilingual_v2"
                )
                # Join the generator chunks into bytes
                play(b"".join(audio))
                return
            except Exception as e:
                logger.warning(f"ElevenLabs failed, falling back to pyttsx3: {e}")

        # Fallback to pyttsx3
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    @handle_errors("Voice")
    def listen_and_transcribe(self, audio_stream: AudioStream) -> str:
        """Listens for speech and transcribes it using Whisper with silence detection."""
        logger.info("Listening for command...")
        frames = []
        silent_chunks = 0
        max_chunks = int(16000 / 512 * 10) # 10 seconds max
        silence_threshold = int(16000 / 512 * 2) # 2 seconds of silence
        
        for i in range(0, max_chunks):
            chunk = audio_stream.read()
            frames.append(chunk)
            
            # Simple silence detection
            rms = np.sqrt(np.mean(chunk.astype(np.float32)**2))
            if rms < 500: # Silence threshold
                silent_chunks += 1
            else:
                silent_chunks = 0
                
            if silent_chunks > silence_threshold and i > int(16000 / 512 * 1): # At least 1s of audio
                logger.info("Silence detected, stopping recording.")
                break
        
        audio_data = np.concatenate(frames).astype(np.float32) / 32768.0
        
        if self.stt_model:
            result = self.stt_model.transcribe(audio_data, fp16=False)
            transcription = result.get("text", "").strip()
            logger.info(f"Transcription: {transcription}")
            return transcription
        return ""

    def process_wake_word(self, pcm_chunk: np.ndarray) -> bool:
        """Processes a chunk of PCM data to check for the wake word."""
        if not self.porcupine:
            return False
        
        if len(pcm_chunk) != self.porcupine.frame_length:
            return False
            
        result = self.porcupine.process(pcm_chunk)
        return result >= 0

    def cleanup(self):
        """Cleans up resources."""
        if self.porcupine:
            self.porcupine.delete()
        logger.info("Voice engine resources cleaned up.")
