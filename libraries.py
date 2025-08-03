from config import LauncherConfig, DEFAULT_CONFIG
from util import download_files
from zipfile import ZipFile
import shutil
from pathlib import Path
import tempfile
import os


class Rule:
    action: bool
    os: str
    arch: str
    version: str
    features: list[str]

    def __init__(self, action: bool = True, os="", arch="", version="", features=None):
        self.action = action
        self.os = os
        self.arch = arch
        self.version = version
        self.features = features if features else []


class Library:
    name: str
    version: str
    url: str
    path: str
    rules: list[Rule]

    def __init__(self, name: str, version: str, url: str, path: str, rules=[]) -> None:
        self.name = name
        self.version = version
        self.url = url
        self.path = path
        self.rules = rules


class Native:
    url: str
    name: str
    version: str
    platform: str
    rules: list[Rule]

    def __init__(
        self, name: str, version: str, url: str, platform: str, rules=[]
    ) -> None:
        self.name = name
        self.version = version
        self.url = url
        self.rules = rules
        self.platform = platform


def check_rules(rules: list[Rule], config: LauncherConfig = DEFAULT_CONFIG):
    for rule in rules:
        action = rule.action

        if rule.os != "":
            if not config.platform_clean == rule.os and action:
                return False
        if rule.arch != "":
            if not config.architecture == rule.os and action:
                return False

        if len(rule.features) > 0:
            return False

        # TODO: Implement version rule
        if rule.version != "":
            print(rule.version)
            return True

        # assert rule.version == ""

    return True


# Only used by forge (for now)
def get_library_path(lib: str, config: LauncherConfig = DEFAULT_CONFIG):
    libpath = os.path.join(config.library_dir, config.platform)
    parts = lib.split(":")
    base_path, libname, version = parts[0:3]
    for i in base_path.split("."):
        libpath = os.path.join(libpath, i)
    try:
        version, fileend = version.split("@")
    except ValueError:
        fileend = "jar"

    filename = (
        f"{libname}-{version}{''.join(map(lambda p: f'-{p}', parts[3:]))}.{fileend}"
    )
    libpath = os.path.join(libpath, libname, version, filename)
    return libpath


def download_libraries(libraries, config: LauncherConfig = DEFAULT_CONFIG):
    urls = []
    paths = []

    for lib in libraries:
        if not check_rules(lib.rules, config):
            continue

        urls.append(lib.url)
        paths.append(os.path.join(config.library_dir, config.platform, lib.path))

    download_files(urls, paths, desc="Downloading libraries")


def download_natives(
    natives: list[Native], version_name: str, config: LauncherConfig = DEFAULT_CONFIG
):
    urls = []
    paths = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for native in natives:
            if native.platform == config.platform_clean and check_rules(
                native.rules, config
            ):
                urls.append(native.url)
                paths.append(
                    os.path.join(tmpdir, f"{native.name.replace(':', '_')}.jar")
                )

        download_files(urls, paths, desc="Downloading natives")

        for nat_path in paths:
            with ZipFile(nat_path, "r") as jar:
                jar.extractall(os.path.join(tmpdir, nat_path[: len(nat_path) - 4]))

            natives_dir = os.path.join(
                config.versions_dir, config.platform, version_name, "natives/"
            )
            os.makedirs(natives_dir, exist_ok=True)

            for f in Path(nat_path[: len(nat_path) - 4]).glob("**/*"):
                print(f)
                file = os.path.join(nat_path[: len(nat_path) - 4], f)
                if not os.path.isfile(file):
                    continue
                shutil.copy(file, natives_dir)
