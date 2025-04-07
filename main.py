import launcher
from config import DEFAULT_CONFIG
import sys

config = DEFAULT_CONFIG
# Change these config options to download Minecraft for another operating system
# config.platform = "windows-x64"
# config.platform_clean = "windows"

if len(sys.argv) > 1:
    launcher.install_version(sys.argv[1], config=config)
    launcher.launch(sys.argv[1], config=config)
