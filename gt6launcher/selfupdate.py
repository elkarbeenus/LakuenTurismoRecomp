"""In-app updater for LakuenTurismoRecomp.

At start the launcher asks the project's own GitHub releases whether a newer version
exists. If so it shows an Update button; one click downloads the new AppImage, checks it
against the release's SHA256SUMS.txt, replaces the running AppImage file atomically and
restarts. Settings, saves, firmware, game data and the shader/PPU caches live in
~/.local/share/gt6-launcher and are never touched.

``__version__`` must match the release tag (``1.0.1`` for tag ``v1.0.1``). Drafts and tags
that are not version numbers are ignored. Test builds are published as pre-releases
(``v1.0.1-beta1``) and are offered too. Network errors are silent: the check must never get
in the way of starting the game.

Environment:
  LTR_NO_UPDATE_CHECK=1   no check at start (offline use)
  LTR_UPDATE_REPO=o/r     other repository (testing)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import threading
import urllib.request
from typing import Callable, Optional

REPO = os.environ.get("LTR_UPDATE_REPO") or "elkarbeenus/Gran-Turismo-6-PC"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases?per_page=30"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"
ASSET_NAME = "LakuenTurismoRecomp-x86_64.AppImage"
SUMS_NAME = "SHA256SUMS.txt"

_STAGES = {"alpha": 0, "beta": 1, "rc": 2}
_STABLE = 3
_VERSION_RE = re.compile(
    r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-_. ]?(alpha|beta|rc|test)[-_. ]?(\d*))?$", re.IGNORECASE)


class UpdateError(Exception):
    pass


def parse_version(text: str) -> Optional[tuple[int, int, int, int, int]]:
    """'v1.2-beta2' -> (1, 2, 0, 1, 2); '1.1.3' -> (1, 1, 3, 3, 0). None if not a version.
    A stable release sorts after every pre-release of the same number; a bare 'beta'
    counts as beta 1. 'test' counts like 'beta'."""
    m = _VERSION_RE.match((text or "").strip())
    if not m:
        return None
    major, minor, patch, stage, num = m.groups()
    stage = (stage or "").lower()
    if stage == "test":
        stage = "beta"
    rank = _STAGES[stage] if stage else _STABLE
    n = int(num) if num else (1 if stage else 0)
    return int(major), int(minor or 0), int(patch or 0), rank, n


def is_prerelease_version(text: str) -> bool:
    v = parse_version(text)
    return v is not None and v[3] != _STABLE


def display_version(text: str) -> str:
    """'1.0.1-beta2' -> 'v1.0.1 Test 2'; '1.0.0' -> 'v1.0.0'."""
    v = parse_version(text)
    if v is None:
        return text
    base = f"v{v[0]}.{v[1]}.{v[2]}"
    return base if v[3] == _STABLE else f"{base} Test {v[4]}"


def _asset_url(release: dict, name: str) -> str:
    for a in release.get("assets") or []:
        if a.get("name") == name:
            return a.get("browser_download_url") or ""
    return ""


def newer_release(current: str, releases: list[dict]) -> Optional[dict]:
    """The newest published release (test build or stable) newer than ``current``, or None."""
    cur = parse_version(current)
    if cur is None:
        return None
    best, best_key = None, cur
    for r in releases:
        if r.get("draft"):
            continue
        key = parse_version(r.get("tag_name", ""))
        if key is None:
            continue
        if key > best_key:
            best, best_key = r, key
    if best is None:
        return None
    tag = best.get("tag_name", "")
    return {"tag": tag, "version": display_version(tag),
            "name": best.get("name") or tag,
            "url": best.get("html_url") or RELEASES_PAGE,
            "prerelease": bool(best.get("prerelease")),
            "notes": best.get("body") or "",
            "appimage_url": _asset_url(best, ASSET_NAME),
            "sums_url": _asset_url(best, SUMS_NAME)}


def _request(url: str, accept: str = "application/octet-stream") -> urllib.request.Request:
    from . import __version__
    return urllib.request.Request(url, headers={
        "User-Agent": f"LakuenTurismoRecomp/{__version__}", "Accept": accept})


def fetch_releases(timeout: float = 10.0) -> list[dict]:
    with urllib.request.urlopen(_request(RELEASES_API, "application/vnd.github+json"), timeout=timeout) as r:
        data = json.load(r)
    return data if isinstance(data, list) else []


def check(current: Optional[str] = None, timeout: float = 10.0) -> Optional[dict]:
    """Newer release for this launcher, or None (also None on any network or parse error)."""
    if os.environ.get("LTR_NO_UPDATE_CHECK"):
        return None
    if current is None:
        from . import __version__ as current
    try:
        return newer_release(current, fetch_releases(timeout))
    except Exception:  # offline, rate limited, GitHub down: never bother the user
        return None


# ----------------------------------------------------------------------------- install

def running_appimage() -> Optional[str]:
    """Path of the AppImage file we were started from, or None (source/dev run)."""
    p = os.environ.get("APPIMAGE")
    return os.path.realpath(p) if p and os.path.isfile(p) else None


def can_self_update() -> bool:
    p = running_appimage()
    return bool(p) and os.access(os.path.dirname(p), os.W_OK)


def parse_sums(text: str, name: str) -> Optional[str]:
    """SHA-256 for ``name`` from a sha256sum-style file ('<hex>  <name>' or '<hex> *<name>')."""
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[-1].lstrip("*") == name and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
            return parts[0].lower()
    return None


def install(rel: dict, progress: Callable[[int, int], None] = lambda d, t: None,
            cancel: Optional[threading.Event] = None, target: Optional[str] = None) -> str:
    """Download, verify and swap in the new AppImage. Returns the path of the AppImage.
    The running file is only replaced after the checksum matched."""
    target = target or running_appimage()
    if not target:
        raise UpdateError("Not started from an AppImage - download the update from the release page.")
    if not rel.get("appimage_url") or not rel.get("sums_url"):
        raise UpdateError(f"Release {rel.get('tag')} has no {ASSET_NAME} or {SUMS_NAME}.")

    with urllib.request.urlopen(_request(rel["sums_url"]), timeout=30) as r:
        expected = parse_sums(r.read().decode("utf-8", "replace"), ASSET_NAME)
    if not expected:
        raise UpdateError(f"{SUMS_NAME} has no checksum for {ASSET_NAME}.")

    part = target + ".update-part"
    h = hashlib.sha256()
    try:
        with urllib.request.urlopen(_request(rel["appimage_url"]), timeout=60) as r, open(part, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            done = 0
            while True:
                if cancel is not None and cancel.is_set():
                    raise UpdateError("Cancelled")
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                h.update(chunk)
                done += len(chunk)
                progress(done, total)
            f.flush()
            os.fsync(f.fileno())
        if h.hexdigest() != expected:
            raise UpdateError("Checksum mismatch - the download is damaged. Nothing was changed.")
        mode = os.stat(target).st_mode if os.path.exists(target) else 0o755
        os.chmod(part, stat.S_IMODE(mode) | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        os.replace(part, target)  # atomic on the same filesystem; the running copy keeps its inode
    finally:
        if os.path.exists(part):
            try:
                os.remove(part)
            except OSError:
                pass
    return target


def _launch_env() -> dict[str, str]:
    env = dict(os.environ)
    for var in ("LD_LIBRARY_PATH", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "PYTHONPATH",
                "PYTHONHOME", "GST_PLUGIN_PATH", "SSL_CERT_FILE"):
        orig = env.pop(var + "_ORIG", None)
        if orig is not None:
            env[var] = orig
        elif getattr(sys, "_MEIPASS", None) or os.environ.get("APPDIR"):
            env.pop(var, None)
    for var in ("APPIMAGE", "APPDIR", "ARGV0", "OWD"):
        env.pop(var, None)
    return env


def restart(appimage: str) -> None:
    """Start the (new) AppImage as a separate process. The caller then quits."""
    subprocess.Popen([appimage], env=_launch_env(), start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     cwd=os.path.expanduser("~"))
