import os
import shutil
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


def _download_installer_versions(config: LauncherConfig = DEFAULT_CONFIG):
    download_file(FABRIC_INSTALLER_VERSIONS, config.fabric_installers)


def _download_installer(installer_version: str, path: str):
    download_file(
        f"https://maven.fabricmc.net/net/fabricmc/fabric-installer/{installer_version}/fabric-installer-{installer_version}.jar",
        path,
    )


def install(
    minecraft_version: str,
    loader_version: str = "",
    config: LauncherConfig = DEFAULT_CONFIG,
):
    # TODO: Check if version is supported

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
