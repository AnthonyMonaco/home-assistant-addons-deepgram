## 0.3.0

### Bug Fixes
- Fixed AttributeError when optional string parameters (keywords, search, replace) are passed as lists or None values
- Added robust type handling for configuration values to prevent crashes on unexpected input types
- Fixed "Keywords are not supported for Nova-3" error by implementing automatic keyterm/keywords parameter selection based on model
- Upgraded deepgram-sdk to >=4.8.0 for Nova-3 keyterm support

### New Features
- **Model Selection**: Support for all Deepgram models including nova-3, nova-2 variants (general, meeting, phonecall, finance, conversationalai, voicemail, video, medical, drivethru, automotive), enhanced, and base models
- **Multi-Language Support**: Added support for 30+ languages and regional variants (English, Spanish, French, German, Portuguese, Italian, Dutch, Japanese, Korean, Chinese, Russian, Turkish, Polish, Swedish, Danish, Norwegian, Finnish, Hindi, Indonesian, Thai, Ukrainian)
- **Deepgram Features**: Added configurable transcription features:
  - `smart_format` - Smart formatting for proper nouns and phrases
  - `punctuate` - Automatic punctuation
  - `diarize` - Speaker diarization (identify different speakers)
  - `utterances` - Split into natural speech segments
  - `profanity_filter` - Filter profanity from transcripts
  - `numerals` - Convert numbers to numerals
- **Advanced Features**: Added PII redaction, keyword boosting, search, and find/replace
- **Performance Settings**:
  - Configurable timeout (1-120 seconds, default: 30s)
  - Retry logic with exponential backoff (0-5 retries, default: 3)
  - Configurable retry delay (0.1-10.0 seconds, default: 1.0s)
  - Adjustable log level (debug, info, warning, error)
- **Wyoming Protocol Settings**: Added endpointing, VAD events, and utterance end timing controls

### Improvements
- Enhanced Wyoming info response to advertise all available models and languages
- Improved error handling with distinction between timeout, network, and API errors
- Added exponential backoff retry strategy with jitter to prevent thundering herd
- Graceful degradation on timeout (returns empty transcript instead of crashing)
- Enhanced logging with detailed debug information and configuration summary
- Improved configuration validation with range checking and sensible defaults
- Better error messages for troubleshooting

### Performance
- Implemented timeout handling to prevent long waits on slow API calls
- Added retry logic for transient network failures
- Optimized connection pooling with keepalive configuration
- Added jitter to retry delays for better distributed retry behavior

### Documentation
- Comprehensive configuration reference with examples
- Model selection guide with use case recommendations
- Language support documentation
- Performance tuning guide with trade-off analysis
- Troubleshooting guide for common issues
- Configuration examples for different scenarios (high accuracy, low latency, multi-language, medical)

### Breaking Changes
- None (all new options are optional with backward-compatible defaults)

## 0.2.2

- Upgraded Deepgram SDK from 3.x to 5.x for AsyncDeepgramClient support
- Updated API calls to match SDK 5.x syntax (listen.v1.media.transcribe_file)
- Changed response parsing to use attribute access instead of dictionary access

## 0.2.1

- Fixed S6 run script by removing references to non-existent config options
- Fixed Dockerfile healthcheck to use Python socket test instead of nc command
- Fixed Python async/sync mismatch by using AsyncDeepgramClient
- Added comprehensive error handling for API responses
- Added safe dictionary access with validation for transcription results
- Improved API key validation with better error messages

## 0.2.0

- Updated Wyoming protocol integration
- Improved logging and event handling

## 0.1.0

- Initial release
