import os
import shutil
import subprocess
import tempfile
import zipfile
import json
from config import LauncherConfig, DEFAULT_CONFIG
import forge
import fabric
import launcher
from util import download_files


def _install_mod_loader(
    mc_version: str,
    loader_version: str,
    id: str,
    config: LauncherConfig = DEFAULT_CONFIG,
) -> str:
    match id:
        case "forge":
            return forge.install(mc_version, loader_version, config=config)
        case "fabric-loader":
            return fabric.install(mc_version, loader_version, config=config)
        case m:
            raise Exception(f"Unimplemented mod loader: {m}")


def install(mrpack: str, config: LauncherConfig = DEFAULT_CONFIG) -> str:
    with zipfile.ZipFile(mrpack) as zf:
        with zf.open("modrinth.index.json") as j:
            manifest = json.load(j)

        mc_version = manifest["dependencies"]["minecraft"]
        mod_loader = None

        # Assuming there's only one mod loader per modpack
        for id, version in manifest["dependencies"].items():
            if id == "minecraft":
                continue
            mod_loader = (id, version)

        if mod_loader:
            version = _install_mod_loader(
                mc_version, mod_loader[1], mod_loader[0], config=config
            )
        else:
            v = launcher.install_version(mc_version, config=config)
            assert v is not None
            version = v.version_name

        # Create instance
        name = manifest["name"]
        mrpack_version = manifest["versionId"]

        instance_dir = os.path.join(config.instances_dir, name)
        os.makedirs(instance_dir, exist_ok=True)

        game_dir = os.path.join(config.game_dir, name)
        os.makedirs(game_dir, exist_ok=True)

        with open(os.path.join(instance_dir, "instance.json"), "w") as d:
            json.dump(
                {"name": name, "version": mrpack_version, "minecraft": version}, d
            )

        urls, paths = [], []

        for f in manifest["files"]:
            path = f["path"]
            downloads = f["downloads"]
            if "env" in f:
                if f["env"]["client"] != "required":
                    continue

            urls.append(downloads[0])
            paths.append(os.path.join(game_dir, path))

        download_files(urls, paths, desc="Downloading files")
        with tempfile.TemporaryDirectory() as tmpdir:
            zf.extractall(tmpdir)
            shutil.copytree(
                os.path.join(tmpdir, "overrides"), game_dir, dirs_exist_ok=True
            )

    return version
