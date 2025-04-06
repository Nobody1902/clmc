import json
from config import DEFAULT_CONFIG, LauncherConfig
from util import download_file
import os

VERSION_MANIFEST = "https://launchermeta.mojang.com/mc/game/version_manifest.json"


class ManifestVersion:
    id: str
    type: str
    url: str
    time: str
    release_time: str

    def __init__(self, id: str, type: str, url: str, time: str, release_time: str):
        self.id = id
        self.type = type
        self.url = url
        self.time = time
        self.release_time = release_time

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"{self.id}"

    def __eq__(self, value: object, /) -> bool:
        if isinstance(value, str):
            return self.id == value
        if isinstance(value, ManifestVersion):
            return self.id == value.id

        return False


class VersionManifest:
    versions: list[ManifestVersion] | list[str]

    latest_relase: str
    latest_snapshot: str

    def __init__(self, config: LauncherConfig = DEFAULT_CONFIG):
        self.config = config
        if not os.path.exists(config.version_manifest):
            print(config.version_manifest)
            self._download_version_manifest()

        raw_manifest = None
        with open(config.version_manifest, "r") as vm:
            raw_manifest = json.loads(vm.read())

        self.latest_relase = raw_manifest["latest"]["release"]
        self.latest_snapshot = raw_manifest["latest"]["snapshot"]

        self.versions = []
        for v in raw_manifest["versions"]:
            self.versions.append(
                ManifestVersion(
                    v["id"], v["type"], v["url"], v["time"], v["releaseTime"]
                )
            )

    def __getitem__(self, i):
        if isinstance(i, int):
            return self.versions[i]
        elif isinstance(i, str):
            if i == "latest_relase":
                return self.latest_relase
            elif i == "latest_snapshot":
                return self.latest_snapshot

            return next((x for x in self.versions if x == i), None)

    def _download_version_manifest(self):
        download_file(VERSION_MANIFEST, self.config.version_manifest)
