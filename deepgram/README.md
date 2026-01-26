# Deepgram Add-on Updates for x86 Support

## Files to Update in Your GitHub Repository

Replace the following files in your `deepgram/` directory:

1. **config.yaml** - Added amd64 and i386 architecture support, bumped version to 0.2.0
2. **Dockerfile** - Changed to use ARG BUILD_FROM for multi-architecture support
3. **build.yaml** - NEW FILE - Defines base images for each architecture

## How to Apply These Changes

### Option 1: Manual Upload via GitHub Web Interface
1. Go to https://github.com/brian-makes-things/home-assistant-addons
2. Navigate to the `deepgram/` folder
3. Click on each file and use "Edit" to replace contents
4. Upload `build.yaml` as a new file
5. Commit the changes

### Option 2: Using Git Locally
```bash
# Clone your repo
cd /config
git clone https://github.com/brian-makes-things/home-assistant-addons.git
cd home-assistant-addons/deepgram

# Copy the updated files
cp /config/deepgram-addon-updates/config.yaml .
cp /config/deepgram-addon-updates/Dockerfile .
cp /config/deepgram-addon-updates/build.yaml .

# Commit and push
git add config.yaml Dockerfile build.yaml
git commit -m "Add x86 (amd64, i386) architecture support"
git push origin main
```

## Changes Made

### config.yaml
- Added `amd64` and `i386` to the `arch` list
- Bumped version from 0.1.0 to 0.2.0

### Dockerfile
- Changed `FROM ghcr.io/home-assistant/aarch64-base:latest` to use `ARG BUILD_FROM` and `FROM $BUILD_FROM`
- This allows Home Assistant to automatically use the correct base image for each architecture

### build.yaml (NEW)
- Maps each architecture to its corresponding Home Assistant base image
- Required for multi-architecture builds
