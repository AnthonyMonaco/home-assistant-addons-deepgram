# Home Assistant Add-on: Deepgram

## Installation

Follow these steps to get the add-on installed on your system:

1. Navigate in your Home Assistant frontend to **Settings** -> **Add-ons** -> **Add-on store**.
2. Using the vertical three-dots menu on the right navigate to repositories and add
```
https://github.com/brian-makes-things/home-assistant-addons
```
3. Back in the add-on store find the "Deepgram" add-on and click it.
4. Click on the "INSTALL" button.

## How to use

After this add-on is installed and running, it will be automatically discovered
by the Wyoming integration in Home Assistant. To finish the setup,
click the following my button:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=wyoming)

Alternatively, you can install the Wyoming integration manually, see the
[Wyoming integration documentation](https://www.home-assistant.io/integrations/wyoming/)
for more information.

## Configuration

### Required Options

#### Option: `api_key` (required)

You will need to have an account at [Deepgram](https://deepgram.com).
While logged in to your account you can go to the [Deepgram console](https://console.deepgram.com) and create an API key.

**Example:**
```yaml
api_key: "YOUR_DEEPGRAM_API_KEY"
```

### Model Selection

#### Option: `model`

Select which Deepgram model to use for transcription. Different models offer trade-offs between accuracy, speed, and specialization.

**Default:** `nova-3`

**Available models:**
- **nova-3** - Latest and most accurate model (recommended for most use cases)
- **nova-2** - Previous generation general-purpose model
- **nova-2-general** - General purpose conversations
- **nova-2-meeting** - Optimized for meetings and conferences
- **nova-2-phonecall** - Optimized for phone call audio
- **nova-2-finance** - Specialized for financial terminology
- **nova-2-conversationalai** - Optimized for conversational AI
- **nova-2-voicemail** - Optimized for voicemail transcription
- **nova-2-video** - Optimized for video content
- **nova-2-medical** - Specialized for medical terminology
- **nova-2-drivethru** - Optimized for drive-thru audio
- **nova-2-automotive** - Specialized for automotive terminology
- **enhanced** - Enhanced general model
- **base** - Base model (faster, less accurate)

**Recommendations:**
- **Home automation:** Use `nova-3` for best accuracy with voice commands
- **Specialized terminology:** Use domain-specific models (medical, finance, automotive)
- **Low latency priority:** Use `base` for fastest response
- **Phone/intercom:** Use `nova-2-phonecall` for phone-quality audio

**Example:**
```yaml
model: nova-3
```

### Language Options

#### Option: `language`

Select the language for transcription. Deepgram supports 30+ languages and regional variants.

**Default:** `en-US`

**Available languages:**
- **English:** `en`, `en-US`, `en-GB`, `en-AU`, `en-NZ`, `en-IN`
- **Spanish:** `es`, `es-419` (Latin American)
- **French:** `fr`, `fr-CA` (Canadian)
- **German:** `de`, `de-CH` (Swiss)
- **Portuguese:** `pt`, `pt-BR` (Brazilian), `pt-PT` (European)
- **Italian:** `it`
- **Dutch:** `nl`
- **Japanese:** `ja`
- **Korean:** `ko`
- **Chinese:** `zh`, `zh-CN` (Simplified), `zh-TW` (Traditional)
- **Russian:** `ru`
- **Turkish:** `tr`
- **Polish:** `pl`
- **Swedish:** `sv`
- **Danish:** `da`
- **Norwegian:** `no`
- **Finnish:** `fi`
- **Hindi:** `hi`
- **Indonesian:** `id`
- **Thai:** `th`
- **Ukrainian:** `uk`

**Example:**
```yaml
language: en-US
```

### Transcription Features

#### Option: `smart_format`

Apply smart formatting to transcripts (proper nouns, products, phrases).

**Default:** `true`
**Values:** `true` or `false`

**Example:**
```yaml
smart_format: true
```

#### Option: `punctuate`

Add punctuation to transcripts.

**Default:** `false`
**Values:** `true` or `false`

**Note:** When `smart_format` is enabled, punctuation is included automatically. Enable this separately only if you want punctuation without smart formatting.

**Example:**
```yaml
punctuate: false
```

#### Option: `diarize`

Enable speaker diarization (identify different speakers in the audio).

**Default:** `false`
**Values:** `true` or `false`

**Use cases:**
- Multi-person conversations
- Meeting transcriptions
- Identifying who said what

**Example:**
```yaml
diarize: false
```

#### Option: `utterances`

Split transcript into utterances (natural speech segments).

**Default:** `false`
**Values:** `true` or `false`

**Use cases:**
- Detailed conversation analysis
- Identifying natural speech breaks
- Better timing information

**Example:**
```yaml
utterances: false
```

#### Option: `profanity_filter`

Filter profanity from transcripts.

**Default:** `false`
**Values:** `true` or `false`

**Example:**
```yaml
profanity_filter: false
```

#### Option: `numerals`

Convert numbers to numerals (e.g., "twenty three" → "23").

**Default:** `true`
**Values:** `true` or `false`

**Example:**
```yaml
numerals: true
```

### Advanced Features

#### Option: `redact`

Redact sensitive information (PII) from transcripts.

**Default:** None
**Values:** `pci`, `numbers`, `ssn` (can specify multiple as a list)

**Options:**
- `pci` - Redact credit card numbers
- `numbers` - Redact all numbers
- `ssn` - Redact social security numbers

**Example:**
```yaml
redact:
  - pci
  - ssn
```

#### Option: `keywords`

Boost specific keywords to improve recognition accuracy.

**Default:** None
**Format:** Comma-separated list with optional intensifiers

**Note:** For Nova-3 models, this parameter is automatically mapped to the `keyterm` API parameter (Nova-3 requires `keyterm` instead of `keywords`). For older models (Nova-2, Enhanced, Base), this uses the standard `keywords` parameter.

**Example:**
```yaml
keywords: "home assistant:2, alexa:-1, turn on:1"
```

**For Home Assistant:**
```yaml
keywords: "turn on, turn off, lights, temperature, lock, unlock"
```

#### Option: `search`

Search for specific terms in the transcript.

**Default:** None
**Format:** Comma-separated list of search terms

**Example:**
```yaml
search: "turn on, turn off, set temperature"
```

#### Option: `replace`

Find and replace specific terms in the transcript.

**Default:** None
**Format:** Comma-separated list of "find:replace" pairs

**Example:**
```yaml
replace: "HA:Home Assistant, temp:temperature"
```

### Performance Settings

#### Option: `timeout`

Maximum time (in seconds) to wait for Deepgram API response.

**Default:** `30`
**Range:** `1` to `120`

**Recommendations:**
- **Short commands (< 5 seconds audio):** 10-15 seconds
- **Normal usage (5-15 seconds audio):** 30 seconds (default)
- **Long audio (> 15 seconds):** 60-120 seconds

**Note:** Timeout includes network latency and processing time. Too short values may cause failures on slower connections.

**Example:**
```yaml
timeout: 30
```

#### Option: `max_retries`

Number of retry attempts for failed API calls.

**Default:** `3`
**Range:** `0` to `5`

**Recommendations:**
- **Unreliable network:** 3-5 retries
- **Stable network:** 1-2 retries
- **No retries (fastest failure):** 0

**Example:**
```yaml
max_retries: 3
```

#### Option: `retry_delay`

Initial delay (in seconds) before first retry. Subsequent retries use exponential backoff.

**Default:** `1.0`
**Range:** `0.1` to `10.0`

**How it works:**
- First retry: waits `retry_delay` seconds
- Second retry: waits `retry_delay * 2` seconds
- Third retry: waits `retry_delay * 4` seconds
- Jitter is added to prevent thundering herd

**Recommendations:**
- **Fast retry:** 0.5-1.0 seconds
- **Conservative retry:** 2.0-5.0 seconds

**Example:**
```yaml
retry_delay: 1.0
```

#### Option: `log_level`

Logging verbosity level.

**Default:** `info`
**Values:** `debug`, `info`, `warning`, `error`

**Recommendations:**
- **Normal operation:** `info`
- **Troubleshooting:** `debug`
- **Production (minimal logs):** `warning` or `error`

**Example:**
```yaml
log_level: info
```

### Wyoming Protocol Settings

#### Option: `endpointing`

Voice activity detection endpoint sensitivity (milliseconds).

**Default:** `300`
**Range:** `0` to `2000`

**Example:**
```yaml
endpointing: 300
```

#### Option: `vad_events`

Enable voice activity detection events.

**Default:** `true`
**Values:** `true` or `false`

**Example:**
```yaml
vad_events: true
```

#### Option: `utterance_end_ms`

Milliseconds of silence to consider utterance ended.

**Default:** `700`
**Range:** `0` to `3000`

**Example:**
```yaml
utterance_end_ms: 700
```

## Configuration Examples

### Basic Configuration (Minimal)
```yaml
api_key: "YOUR_DEEPGRAM_API_KEY"
```

### High Accuracy Configuration
```yaml
api_key: "YOUR_DEEPGRAM_API_KEY"
model: nova-3
language: en-US
smart_format: true
punctuate: false
diarize: true
utterances: true
numerals: true
timeout: 60
max_retries: 3
log_level: info
```

### Low Latency Configuration
```yaml
api_key: "YOUR_DEEPGRAM_API_KEY"
model: base
language: en-US
smart_format: false
punctuate: false
timeout: 10
max_retries: 1
retry_delay: 0.5
```

### Multi-Language Household
```yaml
api_key: "YOUR_DEEPGRAM_API_KEY"
model: nova-3
language: en-US  # Default language
smart_format: true
timeout: 30
max_retries: 3
```

### Medical/Professional Use
```yaml
api_key: "YOUR_DEEPGRAM_API_KEY"
model: nova-2-medical
language: en-US
smart_format: true
diarize: true
redact:
  - pci
  - ssn
timeout: 60
```

## Troubleshooting

### Transcription Timeouts

**Symptoms:** Empty transcripts, timeout errors in logs

**Solutions:**
1. Increase `timeout` value (try 60 or 120 seconds)
2. Check network connectivity to Deepgram API
3. Reduce audio length if possible
4. Check log level `debug` for detailed timing info

### API Rate Limits

**Symptoms:** 429 errors in logs, frequent failures

**Solutions:**
1. Increase `retry_delay` to 2.0 or higher
2. Reduce `max_retries` to avoid queuing too many requests
3. Check your Deepgram account plan limits
4. Contact Deepgram support to increase rate limits

### Poor Transcription Accuracy

**Symptoms:** Wrong words, missing words

**Solutions:**
1. Use `nova-3` model for best accuracy
2. Enable `smart_format` for better formatting
3. Use domain-specific models (medical, finance, etc.)
4. Use `keywords` to boost recognition of specific terms
5. Check audio quality (sample rate, noise level)
6. Verify correct `language` setting

### Retry Exhaustion

**Symptoms:** Max retries reached, consistent failures

**Solutions:**
1. Check network connectivity
2. Verify API key is valid
3. Check Deepgram service status
4. Increase `timeout` (may be timing out too quickly)
5. Check logs for specific error messages

### Language Detection Issues

**Symptoms:** Wrong language detected, poor accuracy for non-English

**Solutions:**
1. Explicitly set `language` option to match your speech
2. Use regional variants (e.g., `en-GB` vs `en-US`)
3. Ensure model supports your language
4. Check audio quality

### Connection Issues

**Symptoms:** Connection reset, network errors

**Solutions:**
1. Verify internet connectivity
2. Check firewall/proxy settings
3. Verify Deepgram API is accessible
4. Increase `retry_delay` and `max_retries`

## Performance Tuning Guide

### Understanding Trade-offs

| Priority | Model | Timeout | Retries | Smart Format |
|----------|-------|---------|---------|--------------|
| **Accuracy** | nova-3 | 60s | 3-5 | true |
| **Speed** | base | 10s | 0-1 | false |
| **Balanced** | nova-3 | 30s | 2-3 | true |

### Audio Length Recommendations

| Audio Length | Timeout | Model |
|--------------|---------|-------|
| < 5 seconds | 15s | nova-3 |
| 5-15 seconds | 30s | nova-3 |
| 15-30 seconds | 60s | nova-3 or nova-2 |
| > 30 seconds | 120s | nova-2 or base |

### Network Quality Recommendations

| Network | Timeout | Max Retries | Retry Delay |
|---------|---------|-------------|-------------|
| **Excellent** | 15s | 1 | 0.5s |
| **Good** | 30s | 2 | 1.0s |
| **Fair** | 60s | 3 | 2.0s |
| **Poor** | 120s | 5 | 5.0s |

## Support

If you think you've found a bug, please [open an issue on my GitHub][issue]

[issue]: https://github.com/brian-makes-things/home-assistant-addons/issues
