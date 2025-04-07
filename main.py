import launcher
from config import DEFAULT_CONFIG, DEFAULT_GAME_CONFIG
import sys

game_config = DEFAULT_GAME_CONFIG
game_config.username = "nobody1902"
# game_config.legacy_sounds = True

config = DEFAULT_CONFIG
config.game_config = game_config
# Change these config options to download Minecraft for another operating system
# config.platform = "windows-x64"
# config.platform_clean = "windows"

if len(sys.argv) > 1:
    launcher.install_version(sys.argv[1], config=config)
    launcher.launch(sys.argv[1], config=config)
