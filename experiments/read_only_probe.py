"""Read phone metadata; optionally download two files to this repository.

Never invokes device verbs, writes device properties, or changes phone content.
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
import sys

import win32com.client

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    shell = win32com.client.Dispatch("Shell.Application")
    devices = [item for item in shell.NameSpace(17).Items()
               if "motorola" in item.Name.lower()]
    if len(devices) != 1:
        raise RuntimeError(f"Expected one Motorola phone, found {len(devices)}")
    device = devices[0]
    stores = list(device.GetFolder.Items())
    if len(stores) != 1:
        raise RuntimeError("Expected one storage; refusing to guess")
    storage = stores[0]
    pictures = next(item for item in storage.GetFolder.Items()
                    if item.IsFolder and item.Name.lower() == "pictures")
    selected = []
    count = 0

    def walk(folder, prefix, depth=0):
        nonlocal count
        if depth >= 10:
            raise RuntimeError("Depth limit reached")
        for item in folder.Items():
            relative = f"{prefix}/{item.Name}"
            if item.IsFolder:
                walk(item.GetFolder, relative, depth + 1)
            else:
                count += 1
                if len(selected) < 2:
                    size = item.ExtendedProperty("System.Size")
                    modified = item.ExtendedProperty("System.DateModified")
                    if not isinstance(size, int) or size < 0:
                        raise RuntimeError(f"Invalid raw size: {size!r}")
                    if not isinstance(modified, datetime) or modified.tzinfo is None:
                        raise RuntimeError(f"Invalid timezone-aware date: {modified!r}")
                    selected.append((item, {
                        "path": relative, "size_bytes": size,
                        "modified_raw": modified.isoformat(),
                        "modified_local": modified.astimezone().isoformat(),
                        "size_type": type(size).__name__,
                        "date_type": type(modified).__name__,
                    }))

    print("Scanning Pictures (read only)...", flush=True)
    walk(pictures.GetFolder, "Pictures")
    print(f"Found {count} files; selected: {[data for _, data in selected]}", flush=True)
    report = {"device": device.Name, "storage": storage.Name,
              "files_count": count, "files": [data for _, data in selected]}
    run_dir = ROOT / "local_artifacts" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir.mkdir(parents=True, exist_ok=False)
    if args.download:
        for index, (item, data) in enumerate(selected, 1):
            destination = run_dir / f"download_{index}"
            destination.mkdir()
            # CopyHere belongs to the LOCAL destination Folder object.
            local_folder = shell.NameSpace(str(destination))
            if local_folder is None:
                raise RuntimeError("Local destination unavailable")
            local_folder.CopyHere(item, 4 | 16 | 512 | 1024)
            deadline = time.monotonic() + 45
            expected = None
            stable = 0
            while time.monotonic() < deadline:
                candidates = [path for path in destination.iterdir() if path.is_file()]
                expected = candidates[0] if len(candidates) == 1 else None
                if expected is not None and expected.stat().st_size == data["size_bytes"]:
                    stable += 1
                    if stable >= 3:
                        break
                else:
                    stable = 0
                time.sleep(0.5)
            else:
                raise RuntimeError(f"Download not verified: {expected}")
            data["local_path"] = str(expected.relative_to(ROOT))
            data["local_size_bytes"] = expected.stat().st_size
            data["download_verified_by_size"] = True
    (run_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Report: {run_dir / 'report.json'}")


if __name__ == "__main__":
    main()
