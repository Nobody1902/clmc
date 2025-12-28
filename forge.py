from ast import arg
import shutil

from config import DEFAULT_CONFIG, LauncherConfig
import launcher
import libraries
from util import download_file, extract_zipfile, get_jar_mainclass, zipfile_exists
import tempfile
import os
import zipfile
import json
import subprocess
import xml.etree.ElementTree as ET
import versions

FORGE_VERSION_MANIFEST_URL = (
    "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml"
)


def _download_version_manifest(config: LauncherConfig = DEFAULT_CONFIG):
    download_file(FORGE_VERSION_MANIFEST_URL, config.forge_manifest)


def _download_installer(
    minecraft_version: str,
    forge_version: str,
    path: str,
):
    download_file(
        f"https://maven.minecraftforge.net/net/minecraftforge/forge/{minecraft_version}-{forge_version}/forge-{minecraft_version}-{forge_version}-installer.jar",
        path,
    )


def _run_processors(
    processors: list,
    data: dict,
    version: versions.Version,
    installer_path: str,
    lzma_path: str,
    side: str,
    config: LauncherConfig = DEFAULT_CONFIG,
):
    arguments = {}

    for key, value in data.items():
        client_value = value.get(side)
        # server_value = value.get("server")

        if client_value.startswith("[") and client_value.endswith("]"):
            arguments[f"{{{key}}}"] = libraries.get_library_path(
                client_value[1:-1], config
            )
        else:
            arguments[f"{{{key}}}"] = client_value

    arguments |= {
        "{MINECRAFT_JAR}": os.path.join(
            config.versions_dir, config.platform, version.version_name, "client.jar"
        ),
        "{SIDE}": side,
        "{INSTALLER}": installer_path,
        "{BINPATCH}": lzma_path,
    }

    with tempfile.TemporaryDirectory() as root:
        arguments["{ROOT}"] = root

        for p in processors:
            # Skip unwanted processors
            if side not in p.get("sides", [side]):
                continue

            jar_path = libraries.get_library_path(p["jar"], config)

            # Create the classpath
            classpath = ""
            for c in p["classpath"]:
                classpath += libraries.get_library_path(c, config)
                classpath += ";" if config.platform_clean == "windows" else ":"

            classpath += jar_path

            mainclass = get_jar_mainclass(jar_path)
            assert mainclass is not None

            args = []
            for a in p["args"]:
                v = arguments.get(a, a)
                if v.startswith("[") and v.endswith("]"):
                    args.append(libraries.get_library_path(v[1:-1], config))
                else:
                    args.append(v)

            java_exe = os.path.join(
                config.runtime_dir,
                config.platform,
                version.java_version,
                "bin",
                "java" + (".exe" if config.platform.startswith("windows") else ""),
            )

            if config.game_config.custom_java_path:
                java_exe = config.game_config.custom_java_path

            print(p, args)
            subprocess.call([java_exe, "-cp", classpath, mainclass, *args])


def install(
    minecraft_version: str,
    forge_version: str | None = None,
    config: LauncherConfig = DEFAULT_CONFIG,
) -> str:
    # TODO: Check if version is supported
    # TODO: Implement automatic version selection
    assert forge_version

    version_id = f"{minecraft_version}-{forge_version}"
    version_name = f"forge-{version_id}"
    install_path = os.path.join(config.versions_dir, config.platform, version_name)
    os.makedirs(install_path, exist_ok=True)

    version_json = os.path.join(install_path, f"{version_name}.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        installer = os.path.join(tmpdir, "installer.jar")

        _download_installer(minecraft_version, forge_version, installer)

        with zipfile.ZipFile(installer) as zf:
            with zf.open("install_profile.json") as f:
                install_profile = json.load(f)

            # Install libraries from install_profile
            if "libraries" in install_profile:
                libs, _ = versions.parse_libraries(install_profile)
                libraries.download_libraries(libs, config)

            # Extract the version.json
            if "versionInfo" in install_profile:
                with open(version_json, "w") as f:
                    json.dump(install_profile["versionInfo"], f)
            else:
                version_json_file = install_profile.get(
                    "json", "/version.json"
                ).removeprefix("/")
                zf.extract(
                    version_json_file,
                    tmpdir,
                )
                shutil.move(os.path.join(tmpdir, version_json_file), version_json)

            # Extract the forge library
            forge_lib_path = os.path.join(
                config.library_dir,
                config.platform,
                "net",
                "minecraftforge",
                "forge",
                version_name,
            )
            try:
                extract_zipfile(
                    zf,
                    f"maven/net/minecraftforge/forge/{version_id}/forge-{version_id}-universal.jar",
                    os.path.join(forge_lib_path, f"forge-{version_id}-universal.jar"),
                )
            except KeyError:
                pass

            try:
                extract_zipfile(
                    zf,
                    f"forge-{version_id}-universal.jar",
                    os.path.join(forge_lib_path, f"forge-{version_id}.jar"),
                )
            except KeyError:
                pass

            try:
                extract_zipfile(
                    zf,
                    f"maven/net/minecraftforge/forge/{version_id}/forge-{version_id}.jar",
                    os.path.join(forge_lib_path, f"forge-{version_id}.jar"),
                )
            except KeyError:
                pass

            # Extract client.lzma
            if zipfile_exists(zf, "data/client.lzma"):
                zf.extract("data/client.lzma", tmpdir)

        launcher.install_version(minecraft_version, config)
        version = launcher._install(version_name, config)

        if "processors" in install_profile:
            lzma_path = os.path.join(tmpdir, "data", "client.lzma")

            _run_processors(
                install_profile["processors"],
                install_profile["data"],
                version,
                installer,
                lzma_path,
                "client",
            )

    return f"forge-{minecraft_version}-{forge_version}"
