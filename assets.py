from config import LauncherConfig, DEFAULT_CONFIG
from util import download_file, download_files
import json
import os

ASSETS_URL = "https://resources.download.minecraft.net"


def _download_asset_manifest(
    asset_index: str, url: str, config: LauncherConfig = DEFAULT_CONFIG
):
    download_file(
        url, os.path.join(config.assets_dir, "indexes", f"{asset_index}.json")
    )


def download_assets(
    asset_index: str, url: str, config: LauncherConfig = DEFAULT_CONFIG
):
    indexes_dir = os.path.join(config.assets_dir, "indexes")
    objects_dir = os.path.join(config.assets_dir, "objects")
    if not os.path.exists(os.path.join(indexes_dir, f"{asset_index}.json")):
        _download_asset_manifest(asset_index, url, config)

    else:
        print(f"Assets {asset_index} are already installed!")
        return 0

    raw_assets = None
    with open(os.path.join(indexes_dir, f"{asset_index}.json"), "r") as ai:
        raw_assets = json.loads(ai.read())

    urls = []
    paths = []

    for ra in raw_assets["objects"]:
        asset_hash = raw_assets["objects"][ra]["hash"]
        urls.append(f"{ASSETS_URL}/{asset_hash[:2]}/{asset_hash}")
        paths.append(os.path.join(objects_dir, asset_hash[:2], asset_hash))

    download_files(urls, paths, desc="Downloading objects")
