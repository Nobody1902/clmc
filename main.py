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

# config.platform = "windows-x64"
# config.platform_clean = "windows"

if len(sys.argv) > 2:
    if sys.argv[1] == "install":
        launcher.install_version(sys.argv[2], config=config)
    elif sys.argv[1] == "launch":
        launcher.launch(sys.argv[2], config=config)
    elif sys.argv[1] == "instance":
        launcher.launch_instance(sys.argv[2], config=config)
    elif sys.argv[1] == "fabric":
        version = fabric.install(sys.argv[2], config=config)
        print(version)
    elif sys.argv[1] == "forge":
        version = forge.install(sys.argv[2], sys.argv[3], config=config)
        print(version)
    elif sys.argv[1] == "mrpack":
        _, instance = mrpack.install(sys.argv[2], config=config)
        print(instance)
