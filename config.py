import os
import platform


def _get_platform():
    match platform.system():
        case "Linux":
            if platform.architecture()[0] == "32bit":
                return "linux-i386"
            else:
                return "linux"

        case "Windows":
            if platform.architecture()[0] == "32bit":
                return "windows-x86"
            else:
                return "windows-x64"

        case "Darwin":
            if platform.architecture()[0] == "arm64":
                return "mac-os-arm64"
            else:
                return "mac-os"

        case _:
            return "gamecore"


def _get_architecture():
    match platform.architecture()[0]:
        case "64bit":
            return "x64"
        case "32bit":
            return "x86"
        case "arm64":
            return "arm64"


class GameConfig:
    def __init__(
        self,
        username: str = "player01",
        launcher_name: str = "clmc",
        launcher_version: str = "0.1",
        custom_jvm_args: list | None = None,
        custom_game_args: list | None = None,
        custom_java_path: str | None = None,
        legacy_sounds: bool = False,
    ):
        self.launcher_name = launcher_name
        self.launcher_version = launcher_version
        self.username = username
        self.custom_jvm_args = custom_jvm_args if custom_jvm_args else []
        self.custom_game_args = custom_game_args if custom_game_args else []
        self.custom_java_path = custom_java_path
        # Legacy sound by using a proxy with sounds
        self.legacy_sounds = legacy_sounds


DEFAULT_GAME_CONFIG = GameConfig()


class LauncherConfig:
    def __init__(
        self,
        minecraft_dir: str,
        game_config: GameConfig = DEFAULT_GAME_CONFIG,
        profile_dir: str = "profiles",
        runtime_dir: str = "runtime",
        versions_dir: str = "versions",
        library_dir: str = "libraries",
        assets_dir: str = "assets",
        game_dir: str = "game",
        platform=_get_platform(),
        architecture=_get_architecture(),
    ):
        self.minecraft_dir = minecraft_dir
        self.game_config = game_config
        # Directories
        self.profile_dir = os.path.join(self.minecraft_dir, profile_dir)
        self.runtime_dir = os.path.join(self.minecraft_dir, runtime_dir)
        self.versions_dir = os.path.join(self.minecraft_dir, versions_dir)
        self.library_dir = os.path.join(self.minecraft_dir, library_dir)
        self.assets_dir = os.path.join(self.minecraft_dir, assets_dir)
        self.game_dir = os.path.join(self.minecraft_dir, game_dir)
        # Files
        self.version_manifest = os.path.join(
            self.minecraft_dir, "version_manifest.json"
        )
        # Fabric
        self.fabric_installers = os.path.join(
            self.minecraft_dir, "fabric_installers.json"
        )
        self.fabric_loaders = os.path.join(self.minecraft_dir, "fabric_loaders.json")
        self.fabric_minecraft_versions = os.path.join(
            self.minecraft_dir, "fabric_minecraft_versions.json"
        )

        # Forge
        self.forge_manifest = os.path.join(self.minecraft_dir, "forge_manifest.xml")

        # Platform
        self.platform = platform
        self.platform_clean = (
            self.platform.replace("-x64", "").replace("-x86", "").replace("-arm64", "")
        )
        self.architecture = architecture

    minecraft_dir: str
    profile_dir: str

    def __repr__(self):
        return f"{self.minecraft_dir}"

    def __str__(self):
        return self.__repr__()


DEFAULT_CONFIG = LauncherConfig(os.path.join(os.getcwd(), ".minecraft"))
