from config import LauncherConfig, DEFAULT_CONFIG
from libraries import Library, Native, Rule
import manifest
from util import download_file
import json
import shutil
import os


def parse_rules(rules_json):
    rules = []
    for r in rules_json:
        action = r["action"] == "allow"
        if "os" not in r and "features" not in r:
            rules.append(Rule(action))
            continue

        os_name = ""
        os_version = ""
        os_arch = ""
        features = None

        if "os" in r:
            if "name" in r["os"]:
                os_name = r["os"]["name"]

            if "version" in r["os"]:
                os_version = r["os"]["name"]

            if "arch" in r["os"]:
                os_arch = r["os"]["arch"]

        if "features" in r:
            features = []
            for f in r["features"]:
                features.append(f)

        rules.append(Rule(action, os_name, os_arch, os_version, features))

    return rules


def parse_libraries(raw_version: dict):
    natives = []
    libraries = []
    for lib in raw_version["libraries"]:
        # Parse natives
        split_name = lib["name"].split(":")
        if len(split_name) > 3:
            if "natives" in split_name[3]:
                url = lib["downloads"]["artifact"]["url"]
                rules = []
                if "rules" in lib:
                    rules = parse_rules(lib["rules"])

                native_platform = split_name[3].replace("natives-", "")

                natives.append(Native(url, lib["name"], native_platform, rules))
                continue

        if "natives" in lib:
            for nat_name in lib["natives"]:
                native_name = lib["natives"][nat_name]
                if native_name not in lib["downloads"]["classifiers"]:
                    continue
                native = lib["downloads"]["classifiers"][native_name]

                url = native["url"]

                rules = []
                if "rules" in lib:
                    rules = parse_rules(lib["rules"])

                natives.append(Native(url, lib["name"], nat_name, rules))

            continue

        # Parse libraries
        url = lib["downloads"]["artifact"]["url"]
        lib_path = lib["downloads"]["artifact"]["path"]

        rules = []

        if "rules" in lib:
            rules = parse_rules(lib["rules"])

        libraries.append(Library(url, lib_path, rules))

    return (libraries, natives)


def parse_jvm_arguments(raw_version: dict):
    jvm_args = []

    if "arguments" not in raw_version:
        jvm_args.append("-Djava.library.path=${natives_directory}")
        jvm_args.append("-cp")
        jvm_args.append("${classpath}")
        return jvm_args

    for arg in raw_version["arguments"]["jvm"]:
        if isinstance(arg, str):
            jvm_args.append(arg)
            continue
        rules = []
        if "rules" in arg:
            rules = parse_rules(arg["rules"])

        if isinstance(arg["value"], list):
            for a in arg["value"]:
                jvm_args.append((a, rules))

        elif isinstance(arg["value"], str):
            jvm_args.append((arg["value"], rules))

    return jvm_args


def parse_game_arguments(raw_version: dict):
    game_args = []

    if "arguments" not in raw_version:
        game_args = raw_version["minecraftArguments"].split(" ")
        return game_args

    for arg in raw_version["arguments"]["game"]:
        if isinstance(arg, str):
            game_args.append(arg)
            continue
        rules = []
        if "rules" in arg:
            rules = parse_rules(arg["rules"])

        if isinstance(arg["value"], list):
            for a in arg["value"]:
                game_args.append((a, rules))

        elif isinstance(arg["value"], str):
            game_args.append((arg["value"], rules))

    return game_args


class Version:
    version: manifest.ManifestVersion
    game_args: list[str]
    jvm_args: list
    asset_index: str
    asset_json_url: str
    client_url: str
    server_url: str | None
    java_version: str
    main_class: str
    libraries: list[Library]
    natives: list[Native]

    def __init__(
        self,
        version: manifest.ManifestVersion,
        config: LauncherConfig = DEFAULT_CONFIG,
        silent: bool = False,
    ):
        self.version = version
        self.config = config
        self.version_dir = os.path.join(
            config.versions_dir, config.platform, str(self.version)
        )
        self.version_manifest = os.path.join(
            self.version_dir, f"{str(self.version)}.json"
        )

        if not os.path.exists(self.version_manifest):
            self._download_version_manifest()

        raw_version = None
        with open(self.version_manifest, "r") as vm:
            raw_version = json.loads(vm.read())

        self.asset_json_url = raw_version["assetIndex"]["url"]
        self.asset_index = raw_version["assetIndex"]["id"]
        self.client_url = raw_version["downloads"]["client"]["url"]
        if "server" in raw_version["downloads"]:
            self.server_url = raw_version["downloads"]["server"]["url"]
        else:
            self.server_url = None

        if "javaVersion" in raw_version:
            self.java_version = raw_version["javaVersion"]["component"]
        else:
            self.java_version = "jre-legacy"

        self.main_class = raw_version["mainClass"]

        self.jvm_args = parse_jvm_arguments(raw_version)
        self.game_args = parse_game_arguments(raw_version)

        self.libraries, self.natives = parse_libraries(raw_version)

        if silent:
            shutil.rmtree(self.version_dir)

    def _download_version_manifest(self):
        download_file(self.version.url, self.version_manifest)

    def __eq__(self, value: object, /) -> bool:
        if isinstance(value, str) or isinstance(value, manifest.ManifestVersion):
            return self.version == value
        if isinstance(value, Version):
            return self.version == value.version

        return False
