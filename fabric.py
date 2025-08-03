import os
import shutil
import json
import subprocess
import tempfile
from config import DEFAULT_CONFIG, LauncherConfig
import launcher
from util import download_file
import xml.etree.ElementTree as ET

FABRIC_MINECRAFT_MANIFEST = "https://meta.fabricmc.net/v2/versions/game"
FABRIC_LOADERS_MANIFEST = "https://meta.fabricmc.net/v2/versions/loader"
FABRIC_INSTALLER_VERSIONS = (
    "https://maven.fabricmc.net/net/fabricmc/fabric-installer/maven-metadata.xml"
)


def _download_loader_versions(config: LauncherConfig = DEFAULT_CONFIG):
    download_file(FABRIC_LOADERS_MANIFEST, config.fabric_loaders)


def _download_minecraft_versions(config: LauncherConfig = DEFAULT_CONFIG):
    download_file(FABRIC_MINECRAFT_MANIFEST, config.fabric_minecraft_versions)


def _download_installer_versions(config: LauncherConfig = DEFAULT_CONFIG):
    download_file(FABRIC_INSTALLER_VERSIONS, config.fabric_installers)


def _download_installer(installer_version: str, path: str):
    download_file(
        f"https://maven.fabricmc.net/net/fabricmc/fabric-installer/{installer_version}/fabric-installer-{installer_version}.jar",
        path,
    )


def get_supported_versions(config: LauncherConfig = DEFAULT_CONFIG):
    _download_minecraft_versions(config)

    supported_versions = None
    with open(config.fabric_minecraft_versions) as f:
        supported_versions = json.load(f)

    return [v["version"] for v in supported_versions]


def get_loaders(config: LauncherConfig = DEFAULT_CONFIG):
    _download_loader_versions(config)
    supported_loaders = None
    with open(config.fabric_loaders) as f:
        supported_loaders = json.load(f)

    return [v["version"] for v in supported_loaders]


def supported_version(minecraft_version: str, config: LauncherConfig = DEFAULT_CONFIG):
    supported_versions = get_supported_versions(config)

    return minecraft_version in supported_versions


def supported_loader(loader_version: str, config: LauncherConfig = DEFAULT_CONFIG):
    supported_loaders = get_loaders(config)

    return loader_version in supported_loaders


def install(
    minecraft_version: str,
    loader_version: str | None = None,
    config: LauncherConfig = DEFAULT_CONFIG,
):
    # TODO: Check if version is supported
    assert supported_version(minecraft_version, config)
    if loader_version:
        assert supported_loader(loader_version, config)
    else:
        loader_versions = get_loaders(config)
        loader_version = loader_versions[0]

    assert loader_version is not None

    version = launcher.install_version(minecraft_version, config)

    assert version is not None

    _download_installer_versions(config)

    root = ET.parse(config.fabric_installers).getroot()
    latest_installer = root.findtext("versioning/latest")

    assert latest_installer is not None

    fabric_version = None

    with tempfile.TemporaryDirectory() as tmpdir:
        installer = os.path.join(tmpdir, "installer.jar")
        _download_installer(latest_installer, installer)

        fabric_path = os.path.join(tmpdir, "client")
        os.mkdir(fabric_path)

        subprocess.run(
            [
                os.path.join(
                    config.runtime_dir,
                    config.platform,
                    version.java_version,
                    "bin",
                    "java",
                ),
                "-jar",
                installer,
                "client",
                "-dir",
                fabric_path,
                "-mcversion",
                minecraft_version,
                "-loader",
                loader_version,
                "-noprofile",
                "-snapshot",
            ]
        )

        shutil.copytree(
            os.path.join(fabric_path, "versions"),
            os.path.join(config.versions_dir, config.platform),
            dirs_exist_ok=True,
        )
        shutil.copytree(
            os.path.join(fabric_path, "libraries"),
            os.path.join(config.library_dir, config.platform),
            dirs_exist_ok=True,
        )

        fabric_version = os.listdir(os.path.join(fabric_path, "versions"))[0]

    assert fabric_version is not None
    launcher._install(fabric_version, config)

    return fabric_version
