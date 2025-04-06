import launcher
from config import DEFAULT_CONFIG
import sys

config = DEFAULT_CONFIG
# config.platform = "windows-x64"
# config.platform_clean = "windows"

if len(sys.argv) > 1:
    launcher.install_version(sys.argv[1])
    launcher.launch(sys.argv[1])

# forge.install_forge("1.21.4", "54.0.26")
# forge.launch("1.21.4", "54.0.26")
