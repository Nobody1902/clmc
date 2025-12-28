import fabric
import forge
import launcher
import mrpack
from config import DEFAULT_CONFIG, DEFAULT_GAME_CONFIG
import sys

game_config = DEFAULT_GAME_CONFIG
game_config.username = "nobody1902"
# game_config.custom_java_path = "/bin/java"
# game_config.legacy_sounds = True

config = DEFAULT_CONFIG
config.game_config = game_config
# Change these config options to download Minecraft for another operating system
# config.platform = "windows-x64"
# config.platform_clean = "windows"

# forge.install("1.21.11", "61.0.3", config=config)
# forge.install("1.18.2", "40.3.12", config=config)
# forge.install("1.12.2", "14.23.5.2859", config=config)
# launcher.launch("forge-1.21.11-61.0.3", config=config)
# launcher.launch("forge-1.18.2-40.3.12", config=config)
# launcher.launch("forge-1.12.2-14.23.5.2859", config=config)

# mrpack.install(sys.argv[1])
launcher.launch_instance(sys.argv[1], config=config)

# if len(sys.argv) > 2:
#     if sys.argv[1] == "install":
#         launcher.install_version(sys.argv[2], config=config)
#     elif sys.argv[1] == "launch":
#         launcher.launch(sys.argv[2], config=config)
#     elif sys.argv[1] == "fabric":
#         version = fabric.install(sys.argv[2], config=config)
#         print(version)
#     elif sys.argv[1] == "forge":
#         version = forge.install(sys.argv[2], sys.argv[3], config=config)
#         print(version)
