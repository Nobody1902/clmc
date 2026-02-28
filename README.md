# CLMC

- A custom minecraft launcher written in python.
- All fabric versions are supported.
- All forge versions should work.
- The Modrinth modpack format ([.mrpack](https://support.modrinth.com/en/articles/8802351-modrinth-modpack-format-mrpack)) is supported.
- Authentication isn't supported.

## Installation

- First, install the required libraries (tqdm, requests) with `pip install -r requirements.txt` or do it manually.
- Then use main.py to install and launch minecraft (eg. `python main.py install 1.21.8`, `python main.py launch 1.21.8`).
  - Or install fabric (eg. `python main.py fabric 1.21.8`)
  - Or install forge (eg. `python main.py forge 1.21.11 61.1.1`)
  - Or install an mrpack (eg. `python main.py mrpack modpack.mrpack`)
    > To launch the instance installed from the mrpack use `python main.py instance ${mrpack name}`

- By default, mincraft will be installed in `.minecraft`.

## Future
- CurseForge zip support will be implemented soon.
- Installing and running minecraft servers is planned.
- Once a clean cli is implemented, I might start working on a tui for the launcher.

## Credits

- [wiki.vg](https://wiki.vg/)
- [minecraft-launcher-lib](https://codeberg.org/JakobDev/minecraft-launcher-lib)
- [tomsik68/mclauncher-api](https://github.com/tomsik68/mclauncher-api/wiki)
