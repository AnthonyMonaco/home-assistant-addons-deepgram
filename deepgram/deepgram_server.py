#!/usr/bin/env python3
"""
Wyoming Protocol Server for Deepgram Speech-to-Text
Built for Home Assistant addon integration
"""
import asyncio
import json
import logging
from functools import partial
from pathlib import Path

from deepgram import DeepgramClient, PrerecordedOptions, DeepgramClientOptions
from wyoming.asr import Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.event import Event
from wyoming.info import AsrModel, AsrProgram, Attribution, Info
from wyoming.server import AsyncEventHandler, AsyncServer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
_LOGGER = logging.getLogger(__name__)

# Configuration
OPTIONS_FILE = Path("/data/options.json")


def load_config():
    """Load configuration from Home Assistant addon options."""
    try:
        with open(OPTIONS_FILE, "r") as f:
            options = json.load(f)

        api_key = options.get("api_key", "").strip()
        if not api_key:
            raise ValueError("API key is required but not configured")

        _LOGGER.info(f"✅ API Key loaded: {api_key[:4]}****")
        return {"api_key": api_key}

    except FileNotFoundError:
        _LOGGER.error(f"❌ Options file not found: {OPTIONS_FILE}")
        raise
    except json.JSONDecodeError as e:
        _LOGGER.error(f"❌ Error parsing options.json: {e}")
        raise
    except Exception as e:
        _LOGGER.error(f"❌ Error loading configuration: {e}")
        raise


def make_wyoming_info() -> Info:
    """Create Wyoming protocol info describing this ASR service."""
    deepgram_attribution = Attribution(
        name="Deepgram",
        url="https://deepgram.com"
    )

    return Info(
        asr=[
            AsrProgram(
                name="deepgram",
                attribution=deepgram_attribution,
                installed=True,
                description="Deepgram cloud-based speech recognition",
                version="3.0.0",
                models=[
                    AsrModel(
                        name="nova-3",
                        attribution=deepgram_attribution,
                        installed=True,
                        description="Deepgram Nova-3",
                        version="3.0.0",
                        languages=["en"]
                    )
                ]
            )
        ]
    )


class DeepgramEventHandler(AsyncEventHandler):
    """Handle Wyoming protocol events and interface with Deepgram API."""

    def __init__(
        self,
        wyoming_info: Info,
        cli_args,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        _LOGGER.info("✅ New client connection established")

        self.cli_args = cli_args
        self.wyoming_info = wyoming_info
        self.client_id = id(self)

        # Initialize Deepgram client
        config = DeepgramClientOptions(
            api_key=cli_args["api_key"],
            options={"keepalive": "true"}
        )
        self.deepgram = DeepgramClient(api_key=cli_args["api_key"], config=config)

        # Audio buffer for current transcription
        self.audio_buffer = bytearray()

        # Audio format settings (defaults from Wyoming)
        self.sample_rate = 16000
        self.sample_width = 2  # 16-bit
        self.channels = 1      # mono

        # Transcription settings
        self.language = "en-US"
        self.model = "nova-3"

        _LOGGER.debug(f"Handler initialized for client {self.client_id}")

    async def handle_event(self, event: Event) -> bool:
        """
        Process Wyoming protocol events.

        Returns:
            bool: True to continue, False to close connection
        """
        try:
            # Describe request - send info about this ASR service
            if event.type == "describe":
                _LOGGER.info("📋 Received describe request")
                info_event = self.wyoming_info.event()
                _LOGGER.debug(f"Sending info event: {info_event}")
                await self.write_event(info_event)
                _LOGGER.debug("✅ Sent info response")
                return True

            # Transcribe request - set transcription parameters
            elif event.type == "transcribe":
                _LOGGER.info("🎤 Starting new transcription")
                self.audio_buffer.clear()

                # Parse transcription parameters
                if event.data:
                    self.language = event.data.get("language", self.language)
                    self.model = event.data.get("model", self.model)
                    _LOGGER.debug(f"Using model: {self.model}, language: {self.language}")

                return True

            # Audio start - configure audio format
            elif event.type == "audio-start":
                if event.data:
                    self.sample_rate = event.data.get("rate", self.sample_rate)
                    self.sample_width = event.data.get("width", self.sample_width)
                    self.channels = event.data.get("channels", self.channels)

                    _LOGGER.debug(
                        f"Audio format: {self.sample_rate}Hz, "
                        f"{self.sample_width * 8}-bit, "
                        f"{self.channels} channel(s)"
                    )
                return True

            # Audio chunk - accumulate audio data
            elif event.type == "audio-chunk":
                chunk = AudioChunk.from_event(event)
                self.audio_buffer.extend(chunk.audio)
                return True

            # Audio stop - transcribe accumulated audio
            elif event.type == "audio-stop":
                _LOGGER.info(f"🎧 Received {len(self.audio_buffer)} bytes of audio")

                # Perform transcription
                text = await self._transcribe_audio()

                # Send transcript back
                transcript_event = Transcript(text=text).event()
                await self.write_event(transcript_event)

                _LOGGER.info(f"📝 Transcription: '{text}'")

                # Clear buffer for next transcription
                self.audio_buffer.clear()
                return True

            else:
                _LOGGER.warning(f"⚠️  Unknown event type: {event.type}")
                return True

        except Exception as e:
            _LOGGER.error(f"❌ Error handling event {event.type}: {e}", exc_info=True)
            return False

    async def _transcribe_audio(self) -> str:
        """
        Send audio to Deepgram and return transcription.

        Returns:
            str: Transcribed text, or empty string on error
        """
        if not self.audio_buffer:
            _LOGGER.warning("⚠️  No audio data to transcribe")
            return ""

        try:
            # Convert PCM to WAV format
            wav_data = self._pcm_to_wav(
                bytes(self.audio_buffer),
                self.sample_rate,
                self.sample_width,
                self.channels
            )

            # Prepare Deepgram options
            options = PrerecordedOptions(
                model=self.model,
                language=self.language,
                smart_format=True,
                punctuate=True,
                diarize=False,
                utterances=False,
            )

            _LOGGER.debug(f"Sending {len(wav_data)} bytes to Deepgram")

            # Call Deepgram API (run in thread to avoid blocking)
            response = await asyncio.to_thread(
                self._call_deepgram_sync,
                wav_data,
                options
            )

            # Extract transcript from response
            text = self._extract_transcript(response)
            return text

        except Exception as e:
            _LOGGER.error(f"❌ Transcription failed: {e}", exc_info=True)
            return ""

    def _call_deepgram_sync(self, wav_data: bytes, options: PrerecordedOptions):
        """
        Synchronous call to Deepgram API (runs in thread).
        """
        return self.deepgram.listen.rest.v("1").transcribe_file(
            {"buffer": wav_data, "mimetype": "audio/wav"},
            options
        )

    def _extract_transcript(self, response) -> str:
        """
        Extract transcript text from Deepgram response.

        Args:
            response: Deepgram API response object

        Returns:
            str: Transcribed text
        """
        try:
            # Navigate response structure
            if hasattr(response, "results"):
                results = response.results
                channels = results.channels if hasattr(results, "channels") else []

                if channels and len(channels) > 0:
                    alternatives = channels[0].alternatives if hasattr(channels[0], "alternatives") else []

                    if alternatives and len(alternatives) > 0:
                        transcript = alternatives[0].transcript if hasattr(alternatives[0], "transcript") else ""
                        return transcript.strip()

            # Fallback: try dictionary access
            if isinstance(response, dict):
                return (
                    response.get("results", {})
                    .get("channels", [{}])[0]
                    .get("alternatives", [{}])[0]
                    .get("transcript", "")
                    .strip()
                )

            _LOGGER.warning("⚠️  Could not extract transcript from response")
            return ""

        except Exception as e:
            _LOGGER.error(f"❌ Error extracting transcript: {e}")
            return ""

    def _pcm_to_wav(
        self,
        pcm_data: bytes,
        sample_rate: int,
        sample_width: int,
        channels: int
    ) -> bytes:
        """
        Convert raw PCM audio to WAV format.

        Args:
            pcm_data: Raw PCM audio bytes
            sample_rate: Sample rate in Hz
            sample_width: Bytes per sample (2 for 16-bit)
            channels: Number of audio channels

        Returns:
            bytes: WAV file data
        """
        import io
        import wave

        buffer = io.BytesIO()

        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)

        return buffer.getvalue()

    async def disconnect(self) -> None:
        """Clean up when client disconnects."""
        _LOGGER.info(f"👋 Client {self.client_id} disconnected")
        await super().disconnect()


async def main() -> None:
    """Start the Wyoming server."""
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        _LOGGER.error(f"❌ Failed to load configuration: {e}")
        return

    # Create Wyoming info
    wyoming_info = make_wyoming_info()

    # Start server
    server_uri = "tcp://0.0.0.0:10301"
    _LOGGER.info(f"🚀 Starting Deepgram Wyoming server on {server_uri}")

    server = AsyncServer.from_uri(server_uri)

    try:
        await server.run(
            partial(DeepgramEventHandler, wyoming_info, config)
        )
    except KeyboardInterrupt:
        _LOGGER.info("🛑 Received shutdown signal")
    except Exception as e:
        _LOGGER.error(f"❌ Server error: {e}", exc_info=True)
    finally:
        _LOGGER.info("👋 Server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
