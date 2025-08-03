from config import LauncherConfig, DEFAULT_CONFIG
from libraries import Library, Native, Rule
import json
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


def get_lib_url(lib: dict):
    if "downloads" in lib:
        return lib["downloads"]["artifact"]["url"]

    url: str = lib.get("url", "https://libraries.minecraft.net").removesuffix("/")

    path, libname, version = str(lib["name"]).split(":")

    return f"{url}/{path.replace('.', '/')}/{libname}/{version}/{libname}-{version}.jar"


def join_libs(libs1: list[Library] | list[Native], libs2: list[Library] | list[Native]):
    combined_libs = {}

    for lib in libs1:
        combined_libs[lib.name] = lib

    for lib in libs2:
        combined_libs[lib.name] = lib

    return list(combined_libs.values())


def get_lib_path(lib: dict):
    if "downloads" in lib:
        return lib["downloads"]["artifact"]["path"]

    path, libname, version = str(lib["name"]).split(":")

    return f"{path.replace('.', '/')}/{libname}/{version}/{libname}-{version}.jar"


def parse_libraries(raw_version: dict):
    natives = []
    libraries = []

    if "libraries" not in raw_version:
        return (None, None)

    for lib in raw_version["libraries"]:
        # Parse natives
        split_name = lib["name"].split(":")
        if len(split_name) > 3:
            if "natives" in split_name[3]:
                url = get_lib_url(lib)
                rules = []
                if "rules" in lib:
                    rules = parse_rules(lib["rules"])

                native_platform = split_name[3].replace("natives-", "")

                natives.append(
                    Native(split_name[1], split_name[-1], url, native_platform, rules)
                )
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

                natives.append(
                    Native(split_name[1], split_name[-1], url, nat_name, rules)
                )

            continue

        # Parse libraries
        url = get_lib_url(lib)
        lib_path = get_lib_path(lib)

        rules = []

        if "rules" in lib:
            rules = parse_rules(lib["rules"])

        libraries.append(Library(split_name[1], split_name[-1], url, lib_path, rules))

    return (libraries, natives)


def parse_jvm_arguments(raw_version: dict):
    jvm_args = []

    if "arguments" not in raw_version or "jvm" not in raw_version["arguments"]:
        return None

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

    if "arguments" not in raw_version or "game" not in raw_version["arguments"]:
        if "minecraftArguments" not in raw_version:
            return None
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
    version_id: str
    version_name: str
    game_args: list[str]
    jvm_args: list[tuple[str, list[Rule]]] | None
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
        version_name: str,
        config: LauncherConfig = DEFAULT_CONFIG,
    ):
        self.version_name = version_name
        self.config = config
        self.version_dir = os.path.join(
            config.versions_dir, config.platform, version_name
        )
        self.version_manifest = os.path.join(self.version_dir, f"{version_name}.json")

        raw_version = None
        with open(self.version_manifest, "r") as vm:
            raw_version = json.loads(vm.read())

        self.version_id = raw_version["id"]

        asset_json_url = raw_version.get("assetIndex", {}).get("url", None)
        asset_index = raw_version.get("assetIndex", {}).get("id", None)
        client_url = raw_version.get("downloads", {}).get("client", {}).get("url", None)
        server_url = raw_version.get("downloads", {}).get("server", {}).get("url", None)

        java_version = raw_version.get("javaVersion", {}).get("component", None)

        main_class = raw_version.get("mainClass", None)

        jvm_args = parse_jvm_arguments(raw_version)
        game_args = parse_game_arguments(raw_version)

        libraries, natives = parse_libraries(raw_version)

        if "inheritsFrom" in raw_version:
            inherit_version = raw_version["inheritsFrom"]
            v = Version(inherit_version)

            asset_json_url = (
                asset_json_url if asset_json_url is not None else v.asset_json_url
            )
            asset_index = asset_index if asset_index is not None else v.asset_index
            client_url = client_url if client_url is not None else v.client_url
            server_url = server_url if server_url is not None else v.server_url
            java_version = java_version if java_version is not None else v.java_version
            main_class = main_class if main_class is not None else v.main_class

            if jvm_args and v.jvm_args:
                jvm_args = jvm_args + v.jvm_args
            else:
                jvm_args = v.jvm_args

            game_args = (
                game_args + v.game_args if game_args is not None else v.game_args
            )
            libraries = (
                join_libs(v.libraries, libraries)
                if libraries is not None
                else v.libraries
            )
            natives = v.natives + natives if natives is not None else v.natives

        assert asset_json_url is not None
        assert asset_index is not None
        assert client_url is not None
        assert server_url is not None
        assert java_version is not None
        assert main_class is not None
        assert game_args is not None
        assert libraries is not None
        assert natives is not None

        self.asset_json_url = asset_json_url
        self.asset_index = asset_index
        self.client_url = client_url
        self.server_url = server_url
        self.java_version = java_version
        self.main_class = main_class
        self.jvm_args = jvm_args
        self.game_args = game_args
        self.libraries = libraries
        self.natives = natives

    def __eq__(self, value: object, /) -> bool:
        if isinstance(value, Version):
            return self.version_name == value.version_name

        return False
