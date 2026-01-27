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
    level=logging.INFO,
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

        # Load all configuration options with defaults
        config = {
            "api_key": api_key,
            # Model and language
            "model": options.get("model", "nova-3"),
            "language": options.get("language", "en-US"),
            # Deepgram features
            "smart_format": options.get("smart_format", True),
            "punctuate": options.get("punctuate", False),
            "diarize": options.get("diarize", False),
            "utterances": options.get("utterances", False),
            "profanity_filter": options.get("profanity_filter", False),
            "numerals": options.get("numerals", True),
            "redact": options.get("redact", []) if options.get("redact") else [],
            "keywords": options.get("keywords", ""),
            "search": options.get("search", ""),
            "replace": options.get("replace", ""),
            # Performance settings
            "timeout": int(options.get("timeout", 30)),
            "max_retries": int(options.get("max_retries", 3)),
            "retry_delay": float(options.get("retry_delay", 1.0)),
            "log_level": options.get("log_level", "info"),
            # Wyoming-specific settings
            "endpointing": int(options.get("endpointing", 300)),
            "vad_events": options.get("vad_events", True),
            "utterance_end_ms": int(options.get("utterance_end_ms", 700)),
        }

        # Validate ranges
        config["timeout"] = max(1, min(120, config["timeout"]))
        config["max_retries"] = max(0, min(5, config["max_retries"]))
        config["retry_delay"] = max(0.1, min(10.0, config["retry_delay"]))

        # Set log level
        log_level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
        }
        logging.getLogger().setLevel(log_level_map.get(config["log_level"], logging.INFO))

        # Log configuration summary (mask sensitive values)
        _LOGGER.info(f"✅ API Key loaded: {api_key[:4]}****")
        _LOGGER.info(f"📊 Configuration loaded:")
        _LOGGER.info(f"   Model: {config['model']}")
        _LOGGER.info(f"   Language: {config['language']}")
        _LOGGER.info(f"   Smart Format: {config['smart_format']}")
        _LOGGER.info(f"   Punctuate: {config['punctuate']}")
        _LOGGER.info(f"   Diarize: {config['diarize']}")
        _LOGGER.info(f"   Utterances: {config['utterances']}")
        _LOGGER.info(f"   Timeout: {config['timeout']}s")
        _LOGGER.info(f"   Max Retries: {config['max_retries']}")
        _LOGGER.info(f"   Log Level: {config['log_level']}")

        return config

    except FileNotFoundError:
        _LOGGER.error(f"❌ Options file not found: {OPTIONS_FILE}")
        raise
    except json.JSONDecodeError as e:
        _LOGGER.error(f"❌ Error parsing options.json: {e}")
        raise
    except Exception as e:
        _LOGGER.error(f"❌ Error loading configuration: {e}")
        raise


def make_wyoming_info(config: dict) -> Info:
    """Create Wyoming protocol info describing this ASR service."""
    deepgram_attribution = Attribution(
        name="Deepgram",
        url="https://deepgram.com"
    )

    # List of all supported models
    all_models = [
        "nova-3", "nova-2", "nova-2-general", "nova-2-meeting", "nova-2-phonecall",
        "nova-2-finance", "nova-2-conversationalai", "nova-2-voicemail",
        "nova-2-video", "nova-2-medical", "nova-2-drivethru", "nova-2-automotive",
        "enhanced", "base"
    ]

    # List of all supported languages
    all_languages = [
        "en", "en-US", "en-GB", "en-AU", "en-NZ", "en-IN",
        "es", "es-419", "fr", "fr-CA", "de", "de-CH",
        "pt", "pt-BR", "pt-PT", "it", "nl", "ja", "ko",
        "zh", "zh-CN", "zh-TW", "ru", "tr", "pl", "sv",
        "da", "no", "fi", "hi", "id", "th", "uk"
    ]

    # Create AsrModel entries for all models
    models = [
        AsrModel(
            name=model,
            attribution=deepgram_attribution,
            installed=True,
            description=f"Deepgram {model}",
            version="0.3.0",
            languages=all_languages
        )
        for model in all_models
    ]

    return Info(
        asr=[
            AsrProgram(
                name="deepgram",
                attribution=deepgram_attribution,
                installed=True,
                description="Deepgram cloud-based speech recognition with enhanced features",
                version="0.3.0",
                models=models
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

        # Store configuration
        self.config = cli_args

        # Initialize Deepgram client
        client_config = DeepgramClientOptions(
            api_key=cli_args["api_key"],
            options={"keepalive": "true"}
        )
        self.deepgram = DeepgramClient(api_key=cli_args["api_key"], config=client_config)

        # Audio buffer for current transcription
        self.audio_buffer = bytearray()

        # Audio format settings (defaults from Wyoming)
        self.sample_rate = 16000
        self.sample_width = 2  # 16-bit
        self.channels = 1      # mono

        # Transcription settings (can be overridden per request)
        self.language = cli_args.get("language", "en-US")
        self.model = cli_args.get("model", "nova-3")

        # Retry tracking
        self.retry_count = 0
        self.total_retries = 0

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
                try:
                    await self.write_event(info_event)
                    _LOGGER.debug("✅ Sent info response")
                except ConnectionResetError:
                    _LOGGER.debug("Client closed connection after receiving info (normal behavior)")
                    return False
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

    async def _call_with_retry(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry logic.

        Args:
            func: The function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            The result of func

        Raises:
            The last exception if all retries fail
        """
        import random

        max_retries = self.config.get("max_retries", 3)
        retry_delay = self.config.get("retry_delay", 1.0)

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    # Calculate exponential backoff with jitter
                    delay = retry_delay * (2 ** (attempt - 1))
                    jitter = random.uniform(0, 0.1 * delay)
                    total_delay = delay + jitter

                    _LOGGER.info(f"🔄 Retry attempt {attempt}/{max_retries} after {total_delay:.2f}s")
                    await asyncio.sleep(total_delay)
                    self.total_retries += 1

                result = await func(*args, **kwargs)

                if attempt > 0:
                    _LOGGER.info(f"✅ Retry successful on attempt {attempt}")

                return result

            except asyncio.TimeoutError as e:
                last_exception = e
                _LOGGER.warning(f"⏱️  Timeout on attempt {attempt + 1}/{max_retries + 1}")
                if attempt >= max_retries:
                    raise

            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()

                # Check if it's a retryable error
                retryable = any(keyword in error_msg for keyword in [
                    "timeout", "connection", "network", "502", "503", "504"
                ])

                if not retryable or attempt >= max_retries:
                    _LOGGER.error(f"❌ Non-retryable error or max retries reached: {e}")
                    raise

                _LOGGER.warning(f"⚠️  Retryable error on attempt {attempt + 1}: {e}")

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception

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

            # Prepare Deepgram options with all configured features
            options = PrerecordedOptions(
                model=self.model,
                language=self.language,
                smart_format=self.config.get("smart_format", True),
                punctuate=self.config.get("punctuate", False),
                diarize=self.config.get("diarize", False),
                utterances=self.config.get("utterances", False),
                profanity_filter=self.config.get("profanity_filter", False),
                numerals=self.config.get("numerals", True),
            )

            # Add optional features if configured
            redact = self.config.get("redact", [])
            if redact and isinstance(redact, list) and len(redact) > 0:
                options.redact = redact

            keywords = self.config.get("keywords", "")
            if keywords and keywords.strip():
                options.keywords = keywords.strip()

            search = self.config.get("search", "")
            if search and search.strip():
                options.search = search.strip()

            replace = self.config.get("replace", "")
            if replace and replace.strip():
                options.replace = replace.strip()

            _LOGGER.debug(f"Sending {len(wav_data)} bytes to Deepgram with model={self.model}, language={self.language}")

            # Call Deepgram API with timeout and retry logic
            timeout = self.config.get("timeout", 30)

            async def call_api():
                return await asyncio.wait_for(
                    asyncio.to_thread(
                        self._call_deepgram_sync,
                        wav_data,
                        options
                    ),
                    timeout=timeout
                )

            response = await self._call_with_retry(call_api)

            # Extract transcript from response
            text = self._extract_transcript(response)
            return text

        except asyncio.TimeoutError:
            _LOGGER.error(f"⏱️  Transcription timeout after {self.config.get('timeout', 30)}s (audio size: {len(self.audio_buffer)} bytes)")
            return ""
        except Exception as e:
            error_type = type(e).__name__
            _LOGGER.error(f"❌ Transcription failed ({error_type}): {e}", exc_info=True)
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
    wyoming_info = make_wyoming_info(config)

    # Start server
    server_uri = "tcp://0.0.0.0:10301"
    _LOGGER.info(f"🚀 Starting Deepgram Wyoming server v0.3.0 on {server_uri}")

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
