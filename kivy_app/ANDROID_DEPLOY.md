# Android Deployment Guide

## Option 1: Kivy Launcher (Quick Testing)

1. Install **Kivy Launcher** from Google Play Store
2. Connect your phone to your computer
3. Copy the `kivy_app` folder to `/sdcard/kivy/tapsplit/` on your phone
4. Open Kivy Launcher and tap "tapsplit"

## Option 2: Build APK with Buildozer

### Prerequisites
You need a Linux environment (Ubuntu/WSL) with:
- Python 3.8+
- Buildozer
- Java JDK 11+
- Android SDK/NDK (Buildozer will download these)

### Steps

1. **Install Buildozer:**
   ```bash
   pip install buildozer
   pip install cython
   ```

2. **Navigate to the kivy_app folder:**
   ```bash
   cd /mnt/c/Users/USER/desktop/tap/kivy_app
   ```

3. **Initialize Buildozer (if buildozer.spec doesn't exist):**
   ```bash
   buildozer init
   ```

4. **Build the APK:**
   ```bash
   buildozer android debug
   ```

5. **The APK will be created in `bin/` folder**

6. **Install on your phone:**
   - Copy the APK to your phone
   - Enable "Install from unknown sources"
   - Open the APK to install

### Build for Release (Play Store)
```bash
buildozer android release
```

## Option 3: Google Colab (Cloud Build)

If you don't want to set up the build environment locally, use Google Colab:

1. Go to https://colab.research.google.com/
2. Create a new notebook
3. Run this code:

```python
!pip install buildozer
!pip install cython

# Upload your kivy_app folder
from google.colab import files
uploaded = files.upload()  # Upload all .py files

# Create buildozer.spec
%%writefile buildozer.spec
[app]
title = Tap & Split
package.name = tapsplit
package.domain = org.tapsplit
source.dir = .
version = 1.0.0
requirements = python3,kivy,kivymd,httpx,websockets,pillow
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2

# Build
!buildozer android debug

# Download the APK
from google.colab import files
!ls bin/
files.download('bin/tapsplit-1.0.0-arm64-v8a-debug.apk')
```

## Important Notes

1. **Backend Server:** The app connects to `http://localhost:8000` by default. For Android, you need to:
   - Run the backend on a public server, OR
   - Use your computer's IP address (e.g., `http://192.168.1.100:8000`)
   - Update `api_client.py` with the correct URL

2. **To change the API URL for Android:**
   Edit `api_client.py`:
   ```python
   def __init__(self, base_url: str = "http://YOUR_COMPUTER_IP:8000"):
   ```

3. **Network:** Make sure your phone and computer are on the same WiFi network
