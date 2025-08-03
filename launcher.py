from util import download_file, remove_duplicates
from manifest import VersionManifest
import versions
import java
import assets
import libraries
from config import LauncherConfig, DEFAULT_CONFIG
import subprocess
import os


def _install(
    version_name: str, config: LauncherConfig = DEFAULT_CONFIG
) -> versions.Version:
    version_dir = os.path.join(config.versions_dir, config.platform, version_name)

    version = versions.Version(version_name)

    if os.path.exists(os.path.join(version_dir, "client.jar")):
        print("Version is already installed.")
        return version

    download_file(version.client_url, os.path.join(version_dir, "client.jar"))
    if version.server_url:
        download_file(version.server_url, os.path.join(version_dir, "server.jar"))

    java.download_java(version.java_version, config)

    assets.download_assets(version.asset_index, version.asset_json_url, config)

    libraries.download_libraries(version.libraries, config)
    libraries.download_natives(version.natives, version_name, config)

    return version


def install_version(
    version_id: str, config: LauncherConfig = DEFAULT_CONFIG
) -> versions.Version | None:
    manifest = VersionManifest(config)

    if version_id not in manifest.versions:
        print("This version doesn't exist!")
        return

    print(f"Installing {version_id}")

    manifest[version_id]._download(
        os.path.join(
            config.versions_dir,
            config.platform,
            version_id,
            f"{version_id}.json",
        )
    )

    version = _install(f"{version_id}", config)

    print(f"Successfully installed {version_id}")

    return version


def launch(version_name: str, config: LauncherConfig = DEFAULT_CONFIG):
    version_dir = os.path.join(config.versions_dir, config.platform, version_name)
    if not os.path.exists(version_dir):
        print("Version is not installed!")
        return -1

    version = versions.Version(version_name, config)

    java_exe = os.path.join(
        config.runtime_dir,
        config.platform,
        version.java_version,
        "bin",
        "java" + (".exe" if config.platform.startswith("windows") else ""),
    )
    classpath_sep = ";" if config.platform.startswith("windows") else ":"
    classpath = ""

    for lib in set(version.libraries):
        if not libraries.check_rules(lib.rules, config):
            continue
        classpath += (
            os.path.join(config.library_dir, config.platform, lib.path) + classpath_sep
        )

    classpath += os.path.join(version_dir, "client.jar")

    jvm_args: list[str] = []

    # Legacy sound
    if config.game_config.legacy_sounds:
        jvm_args.append("-Dhttp.proxyHost=betacraft.uk")
        jvm_args.append("-Djava.util.Arrays.useLegacyMergeSort=true")

    if not version.jvm_args:
        jvm_args.append("-Djava.library.path=${natives_directory}")
        jvm_args.append("-cp")
        jvm_args.append("${classpath}")
    else:
        for arg in remove_duplicates(version.jvm_args):
            if isinstance(arg, str):
                jvm_args.append(arg)
                continue

            val, rules = arg
            if libraries.check_rules(rules, config):
                jvm_args.append(val)

    # Append the user defined jvm args
    jvm_args.extend(config.game_config.custom_jvm_args)

    for i in range(len(jvm_args)):
        jvm_args[i] = jvm_args[i].replace(
            "${natives_directory}", os.path.join(version_dir, "natives")
        )
        jvm_args[i] = jvm_args[i].replace(
            "${launcher_name}", config.game_config.launcher_name
        )
        jvm_args[i] = jvm_args[i].replace(
            "${launcher_version}", config.game_config.launcher_version
        )
        jvm_args[i] = jvm_args[i].replace("${classpath}", classpath)

    game_args: list[str] = []
    for arg in version.game_args:
        if isinstance(arg, str):
            game_args.append(arg)
            continue

        val, rules = arg  # pyright: ignore
        if libraries.check_rules(rules, config):
            game_args.append(val)

    # Append the user defined game args
    game_args.extend(config.game_config.custom_game_args)

    for i in range(len(game_args)):
        game_args[i] = game_args[i].replace(
            "${clientid}", "clientid"
        )  # TODO: Implement auth - clientid
        game_args[i] = game_args[i].replace(
            "${auth_xuid}", "auth_xuid"
        )  # TODO: Implement auth - auth_xuid
        game_args[i] = game_args[i].replace(
            "${auth_player_name}", config.game_config.username
        )  # Offline mode
        game_args[i] = game_args[i].replace("${version_name}", version_name)
        game_args[i] = game_args[i].replace(
            "${game_directory}", os.path.join(config.game_dir, version_name)
        )
        game_args[i] = game_args[i].replace("${assets_root}", config.assets_dir)
        game_args[i] = game_args[i].replace("${assets_index_name}", version.asset_index)
        game_args[i] = game_args[i].replace(
            "${auth_uuid}", "f81d4fae-7dec-11d0-a765-00a0c91e6bf6"
        )  # TODO: Implement auth - auth_uuid
        game_args[i] = game_args[i].replace(
            "${auth_access_token}", "auth_access_token"
        )  # TODO: Implement auth - auth_access_token
        game_args[i] = game_args[i].replace(
            "${user_type}", "user_type"
        )  # TODO: Implement auth - user_type
        game_args[i] = game_args[i].replace(
            "${user_properties}", "user_properties"
        )  # TODO: Figure out what this does (1.8 only?)
        game_args[i] = game_args[i].replace(
            "${version_type}", version_name
        )  # TODO: Modded update the name
        game_args[i] = game_args[i].replace("${quickPlayPath}", "logs")

    print(game_args)
    print(jvm_args)
    os.makedirs(os.path.join(config.game_dir, version_name), exist_ok=True)

    # Launch the game
    subprocess.call(
        [java_exe, *jvm_args, version.main_class, *game_args],
        cwd=os.path.join(config.game_dir, version_name),
    )
