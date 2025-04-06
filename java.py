from config import LauncherConfig, DEFAULT_CONFIG
from util import download_file, download_files
import json
import os
import stat

JAVA_MANIFEST = "https://launchermeta.mojang.com/v1/products/java-runtime/2ec0cc96c44e5a76b9c8b7c39df7210883d12871/all.json"


def _download_java_manifest(config: LauncherConfig = DEFAULT_CONFIG):
    download_file(JAVA_MANIFEST, os.path.join(config.runtime_dir, "runtimes.json"))


def download_java(version: str, config: LauncherConfig = DEFAULT_CONFIG):
    if not os.path.exists(os.path.join(config.runtime_dir, "runtimes.json")):
        _download_java_manifest(config)

    raw_runtimes = None
    with open(os.path.join(config.runtime_dir, "runtimes.json"), "r") as rm:
        raw_runtimes = json.loads(rm.read())

    if version not in raw_runtimes["gamecore"].keys():
        print(f'Unknown java runtime name: "{version}"')
        return -1

    java_json = raw_runtimes[config.platform][version]
    if len(java_json) == 0:
        print(f'"{version}" isn\'t supported on {config.platform}')
        return -1

    java_files_manifest = os.path.join(
        config.runtime_dir, config.platform, version, f"{version}.json"
    )
    if os.path.exists(java_files_manifest):
        print(f"{version} is already installed!")
        return 0

    download_file(java_json[0]["manifest"]["url"], java_files_manifest)

    raw_files = None
    with open(java_files_manifest, "r") as jf:
        raw_files = json.loads(jf.read())

    urls = []
    paths = []
    links = []
    executables = []

    for file in raw_files["files"]:
        value = raw_files["files"][file]

        if value["type"] == "directory":
            os.makedirs(
                os.path.join(config.runtime_dir, config.platform, version, file),
                exist_ok=True,
            )
            continue

        if value["type"] == "link":
            links.append((file, value["target"]))
            continue

        urls.append(value["downloads"]["raw"]["url"])
        paths.append(os.path.join(config.runtime_dir, config.platform, version, file))

        if value["executable"]:
            executables.append(
                os.path.join(config.runtime_dir, config.platform, version, file)
            )

    download_files(urls, paths, desc="Downloading java")

    # Chmod executables
    for exe in executables:
        os.chmod(
            exe,
            stat.S_IRUSR
            | stat.S_IWUSR
            | stat.S_IRGRP
            | stat.S_IWGRP
            | stat.S_IROTH
            | stat.S_IEXEC,
        )
        pass

    # Create links
    for dest, target in links:
        file = os.path.join(config.runtime_dir, config.platform, version, dest)
        if os.path.exists(file):
            print(f"Link {os.path.basename(file)} already exists!")
            continue
        os.symlink(os.path.join(os.path.dirname(file), target), file)
