"""
fetch_factors.py — download the factor rasters on a fresh install
==================================================================
models/factors/ is kept out of git. Point query and the rainfall scenario need
it, so a fresh deployment fetches it (~160 MB, losslessly recompressed) from the
GitHub release named in models/factors_manifest.json, checking every file's
size and SHA-256.

The app calls start() at boot, which downloads in a background thread, and
wait() wherever it needs the files. To fetch them by hand instead:

    python fetch_factors.py
"""
import hashlib
import json
import os
import threading
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FACT = os.path.join(HERE, "models", "factors")
MANIFEST = os.path.join(HERE, "models", "factors_manifest.json")

_lock = threading.Lock()
_thread = None
_error = None
_progress = {"done": 0, "total": 0}


def _manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def missing():
    """Names of factor rasters not yet in models/factors/.

    Presence is enough: downloads land under a .part name and are renamed only
    after their checksum passes. Sizes are not compared because the release
    copies are losslessly recompressed (same pixels, different bytes) and a
    local copy from the original analysis is just as valid.
    """
    return [name for name in _manifest()["files"]
            if not os.path.isfile(os.path.join(FACT, name))]


def fetch(progress=None):
    """Download every missing raster, verifying each before moving it into place.

    progress(done_bytes, total_bytes) is called as data arrives.
    """
    m = _manifest()
    todo = missing()
    os.makedirs(FACT, exist_ok=True)
    total = sum(m["files"][name]["size"] for name in todo)
    done = 0
    _progress.update(done=0, total=total)
    for name in todo:
        meta = m["files"][name]
        part = os.path.join(FACT, name + ".part")
        digest = hashlib.sha256()
        with urllib.request.urlopen(m["base_url"] + name, timeout=60) as resp, open(part, "wb") as out:
            for chunk in iter(lambda: resp.read(1 << 20), b""):
                out.write(chunk)
                digest.update(chunk)
                done += len(chunk)
                _progress["done"] = done
                if progress:
                    progress(done, total)
        if digest.hexdigest() != meta["sha256"] or os.path.getsize(part) != meta["size"]:
            os.remove(part)
            raise RuntimeError(f"{name} failed its checksum; not installed")
        os.replace(part, os.path.join(FACT, name))


def _run():
    global _error
    try:
        fetch()
        _error = None
    except Exception as exc:  # reported to the caller by wait()
        _error = exc


def start():
    """Begin downloading in the background. No-op if nothing is missing or a download is running."""
    global _thread
    with _lock:
        if (_thread is None or not _thread.is_alive()) and missing():
            _thread = threading.Thread(target=_run, name="fetch-factors", daemon=True)
            _thread.start()


def wait(progress=None, poll=0.5):
    """Block until every raster is present, starting the download if needed.

    progress(done_bytes, total_bytes) is called while waiting. Raises
    RuntimeError if the download failed; a later call retries it.
    """
    start()
    while _thread is not None and _thread.is_alive():
        if progress:
            progress(_progress["done"], _progress["total"])
        _thread.join(poll)
    if missing():
        raise RuntimeError(f"model rasters could not be downloaded: {_error}")


if __name__ == "__main__":
    todo = missing()
    if not todo:
        print("All factor rasters present.")
    else:
        print(f"Downloading {len(todo)} raster(s) into {FACT} ...")
        fetch(progress=lambda done, total: print(f"\r  {done / 1e6:6.1f} / {total / 1e6:.1f} MB", end=""))
        print("\nDone.")
