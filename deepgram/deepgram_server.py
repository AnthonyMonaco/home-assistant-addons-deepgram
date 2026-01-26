import asyncio
import json
import os
import logging
from deepgram import AsyncDeepgramClient
from wyoming.event import Event
from wyoming.server import AsyncEventHandler, AsyncServer
from wyoming.info import Info, Describe, AsrProgram, AsrModel, Attribution

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OPTIONS_FILE = "/data/options.json"

class DeepgramSTT:
    def __init__(self):
        deepgram_api_key = load_api_key()
        self.dg_client = AsyncDeepgramClient(deepgram_api_key)

    async def transcribe(self, audio_data: bytes, sample_rate: int):
        """
        Send audio data to Deepgram and return transcription.
        """
        try:
            # SDK v5 API uses direct parameters instead of PrerecordedOptions object
            response = await self.dg_client.listen.v1.media.transcribe_file(
                request=audio_data,
                model="nova-3",
                smart_format=True,
                encoding="linear16",
                sample_rate=sample_rate,
                channels=1,
                language="en-US",
                punctuate=True,
            )

            # Safe attribute/dictionary access with validation
            if not response or not hasattr(response, 'results'):
                logger.error("Invalid response from Deepgram: missing 'results'")
                return ""

            results = response.results
            if not hasattr(results, 'channels') or not results.channels:
                logger.error("Invalid response from Deepgram: no channels found")
                return ""

            channels = results.channels
            if len(channels) == 0:
                logger.error("Invalid response from Deepgram: empty channels")
                return ""

            alternatives = channels[0].alternatives if hasattr(channels[0], 'alternatives') else []

            if not alternatives or len(alternatives) == 0:
                logger.error("Invalid response from Deepgram: no alternatives found")
                return ""

            transcript = alternatives[0].transcript if hasattr(alternatives[0], 'transcript') else ""

            return transcript
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return ""

class State:
    def __init__(self):
        self.sessions = {}

    def get_session(self, session_id):
        return self.sessions.get(session_id)

    def set_session(self, session_id, data):
        self.sessions[session_id] = data

    def delete_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]

class EventHandler(AsyncEventHandler):
    WYOMING_INFO = Info(
        asr=[
            AsrProgram(
                name="Deepgram",
                description="A speech recognition toolkit",
                attribution=Attribution(
                    name="Deepgram",
                    url="https://deepgram.com",
                ),
                installed=True,
                version='1.0',
                models=[
                    AsrModel(
                        name='general-nova-3',
                        description='Nova 3',
                        attribution=Attribution(
                            name="Deepgram",
                            url="https://deepgram.com",
                        ),
                        installed=True,
                        version=None,
                        languages=['en'],
                    )
                ]
            )
        ]
    )

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        """Initialize Wyoming event handler."""
        logger.info(f"✅ New connection")

        super().__init__(*args, **kwargs)

        state = State()
        self.stt = DeepgramSTT()
        self.audio_data = b""
        self.sample_rate = 16000  # Default sample rate; can be adjusted
        wyoming_info = self.WYOMING_INFO
        self.wyoming_info_event = wyoming_info.event()

    async def handle_event(self, event: Event) -> bool:
        """Process and log all incoming Wyoming protocol events."""
        try:
            if event.type == "describe":
                logger.info("📤 Responding to describe event.")
                await self.write_event(self.wyoming_info_event)
            elif event.type == "audio-chunk":
                self.audio_data += event.payload
            elif event.type == "audio-stop":
                logger.info(f"Received Wyoming event: {event.type} - Data: {event.data}")
                # Send to Deepgram and get transcription
                text = await self.stt.transcribe(self.audio_data, self.sample_rate)
                result_event = Event(type="transcript", data={"text": text})

                logger.info(f"Sending Transcript Event: {text}")

                await self.write_event(result_event)
                self.audio_data = b""  # Reset for next transcription
            else:
                logger.info(f"Received Wyoming event: {event.type} - Data: {event.data}")

            return True
        except Exception as e:
            logger.error(f"Error handling event {event.type}: {e}")
            return False

def load_api_key():
    """Load the API key from the options.json file."""
    try:
        with open(OPTIONS_FILE, "r") as f:
            options = json.load(f)
        api_key = options.get("api_key", "")

        if not api_key:
            logger.error("⚠️ API key is missing! Set it in the Deepgram addon settings.")
            raise ValueError("API key is required but not configured")

        logger.info(f"✅ API Key Loaded: {api_key[:4]}****")
        return api_key
    except FileNotFoundError:
        logger.error(f"Options file not found: {OPTIONS_FILE}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing options.json: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading options.json: {e}")
        raise

async def main():
    """Starts the Wyoming Deepgram STT server using DeepgramServer."""
    server = AsyncServer.from_uri('tcp://0.0.0.0:10301')
    try:
        logger.info('Starting Wyoming Server')
        await server.run(EventHandler)
    except asyncio.CancelledError:
        await server.stop()

if __name__ == "__main__":
    asyncio.run(main())
