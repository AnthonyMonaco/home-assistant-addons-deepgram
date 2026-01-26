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
