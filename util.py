import zipfile
import requests

from tqdm import tqdm
import os

from concurrent.futures import ThreadPoolExecutor, as_completed


def download_file(
    url: str, dest_path: str, keep_bar: bool = True, overwrite: bool = False
):
    """Download a single file from a URL."""
    if os.path.exists(dest_path) and not overwrite:
        return
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get("content-length", 0))

        if not response.ok:
            raise requests.exceptions.MissingSchema()

        with (
            open(dest_path, "wb") as file,
            tqdm(
                desc=os.path.basename(dest_path),
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                leave=keep_bar,
            ) as bar,
        ):
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)
    except requests.exceptions.MissingSchema:
        print(f"\nFailed to download: {os.path.basename(dest_path)}\n")
        raise Exception(f"Failed to download: {url}")


def download_files(urls: list[str], files: list[str], desc: str = "Downloading"):
    """Download multiple files in parallel with a progress bar."""
    with tqdm(total=len(urls), desc=desc) as overall_bar:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(download_file, url, path, False): path
                for url, path in zip(urls, files)
            }
            for future in as_completed(futures):
                future.result()
                overall_bar.update(1)


def get_jar_mainclass(jar: str):
    zf = zipfile.ZipFile(jar)

    with zf.open("META-INF/MANIFEST.MF") as man:
        lines = man.read().decode().splitlines()

    zf.close()

    for line in lines:
        if line.startswith("Main-Class: "):
            return line.removeprefix("Main-Class: ").replace("\n", "")


def remove_duplicates(input: list):
    seen = []
    result = []
    for item in input:
        if item not in seen:
            seen.append(item)
            result.append(item)

    return result


def zipfile_exists(zf: zipfile.ZipFile, path: str):
    file_list = zf.namelist()
    return (
        path in file_list
        or path.endswith("/")
        and any(f.startswith(path) for f in file_list)
    )


def extract_zipfile(zf: zipfile.ZipFile, file: str, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zf.open(file, "r") as f:
        with open(path, "wb") as o:
            o.write(f.read())
