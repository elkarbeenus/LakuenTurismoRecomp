# LakuenTurismoRecomp

A single AppImage for SteamOS (desktop mode) that runs Gran Turismo 6 on a GT6-optimised
RPCS3 build, with stable pre-tuned settings and a built-in auto-updater.

Based on [Mabec-games/Gran-Turismo-6-PC](https://github.com/Mabec-games/Gran-Turismo-6-PC)
(v1.2 Beta 5). Unofficial fan project, not affiliated with Sony or Polyphony Digital.

## What's different from upstream

- **Linux/SteamOS only:** one file, `LakuenTurismoRecomp-x86_64.AppImage`. No Windows builds.
- **In-app auto-update:** on start the app checks this repository for a newer release and asks
  whether to update now or keep playing the current version. One click downloads the new AppImage,
  verifies it with SHA-256, replaces the old file and restarts. Settings, saves, firmware, game updates
  and shader caches are kept (`~/.local/share/gt6-launcher`). Set `LTR_NO_UPDATE_CHECK=1` to play offline.
- **Pre-tuned settings**, applied automatically on first start:

  | Area | Setting |
  |---|---|
  | CPU | SPU Block Size *Mega*, OS thread scheduler |
  | Graphics | 1080p output, 150 % resolution scale, Sharper MLAA, sharp shadows, Strict Rendering (AMD fix), 16x AF |
  | Stability | ZCull queries off, no multithreaded RSX, tiled memory handling on, fullscreen, 60 FPS |

  Previous settings can be brought back at any time with *Restore previous settings*.
  On an 800p screen (Steam Deck) the handheld preset is used instead.

## Usage

1. Download the latest `LakuenTurismoRecomp-x86_64.AppImage` from
   [Releases](https://github.com/elkarbeenus/Gran-Turismo-6-PC/releases).
2. Right-click → Properties → *Executable* (or `chmod +x LakuenTurismoRecomp-x86_64.AppImage`), then start it.
3. In the **Setup** tab: install the firmware, add your GT6 disc image, install updates up to 1.22.
4. **PLAY.** The first start compiles for about 8 minutes; the first start of 1.22 takes about 30 minutes in total.

You need your own copy of Gran Turismo 6 (disc image). No game files, firmware or keys are included;
firmware and game updates are downloaded directly from Sony's servers.

## Building

`.github/workflows/linux.yml` builds RPCS3 from the official source (pinned commit) plus the patches in
`emulator/gt6-patches/`, packs the AppImage and smoke-tests it. Bumping `__version__` in
`gt6launcher/__init__.py` on `main` (with `release-notes/v<version>.md`) makes the workflow create the tag
and the release with the AppImage and `SHA256SUMS.txt`. Test builds use versions like `1.0.1-test1` and are
published as pre-releases. Local build: `packaging/build_appimage.sh`.

Updater tests: `python3 -m unittest tests/test_selfupdate.py`

## Credits

Mabec-games (GT6 PC Launcher), RPCS3, AlexHaust, Nenkai, abowen, Lunard, FlexBy, Edo and the RPCS3 wiki.
License: GPL-3.0 (see `LICENSE`).
