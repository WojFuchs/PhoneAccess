"""Read-only inventory of all files exposed by the phone's USB/MTP storage.

Writes metadata locally. Never copies content or mutates the phone.
"""
import argparse
import csv
from datetime import datetime
from pathlib import Path
import sys
import time

import win32com.client


def timestamp():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="ThinkPhone", help="Device name substring")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = (args.output or Path(__file__).resolve().parent / "local_artifacts" /
              f"phone_inventory_{datetime.now():%Y%m%d_%H%M%S}.txt").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    shell = win32com.client.Dispatch("Shell.Application")
    devices = [item for item in shell.NameSpace(17).Items()
               if args.device.casefold() in item.Name.casefold()]
    if len(devices) != 1:
        raise RuntimeError(f"Expected exactly one matching phone; found {len(devices)}")
    device = devices[0]
    total_files = total_bytes = errors = folders = batch_files = batch_bytes = 0
    started = batch_started = time.perf_counter()
    interrupted = False
    # Exclusive creation prevents overwriting an existing inventory.
    with output.open("x", encoding="utf-8", newline="") as report:
        writer = csv.writer(report, delimiter="\t", lineterminator="\n")

        def log(message):
            print(message, flush=True)
            report.write(f"# {message}\n")
            report.flush()

        def error(path, exc):
            nonlocal errors
            errors += 1
            log(f"ERROR {path!r}: {exc}")

        def batch():
            nonlocal batch_files, batch_bytes, batch_started
            now = time.perf_counter()
            elapsed = max(now - batch_started, 1e-9)
            log(f"{timestamp()} | paczka: {batch_files} plików, {batch_bytes} B | "
                f"{elapsed:.3f} s | {batch_bytes / elapsed:.2f} B/s | "
                f"{batch_files / elapsed:.2f} file/s | łącznie: {total_files} plików, "
                f"{total_bytes} B | błędy: {errors}")
            batch_files = batch_bytes = 0
            batch_started = time.perf_counter()

        log(f"START {timestamp()} | telefon: {device.Name} | raport: {output}")
        log("Tylko odczyt metadanych; B/s oznacza sumę rozmiarów opisanych plików / czas, "
            "nie transfer zawartości. Zakres: wszystkie pamięci i pliki widoczne przez MTP.")
        writer.writerow(["path", "size_bytes", "modTime", "status"])
        # Iterative depth-first traversal, without arbitrary depth or hidden-file limits.
        stack = [(device.GetFolder, device.Name)]
        try:
            while stack:
                folder, prefix = stack.pop()
                folders += 1
                try:
                    items = folder.Items()
                    child_folders = []
                    for item in items:
                        path = prefix
                        try:
                            name = str(item.Name)
                            path = f"{prefix}/{name}"
                            if item.IsFolder:
                                child_folders.append((item.GetFolder, path))
                                continue
                            issues = []
                            try:
                                raw_name = item.ExtendedProperty("System.FileName")
                                if isinstance(raw_name, str) and raw_name:
                                    path = f"{prefix}/{raw_name}"
                            except Exception:
                                pass  # Preserve display name if actual filename is unavailable.
                            size = None
                            modified = ""
                            try:
                                size = item.ExtendedProperty("System.Size")
                                if type(size) is not int or size < 0:
                                    raise ValueError(f"Invalid exact size: {size!r}")
                            except Exception as exc:
                                size = None
                                issues.append(f"size: {exc}")
                            try:
                                value = item.ExtendedProperty("System.DateModified")
                                if not isinstance(value, datetime):
                                    raise ValueError(f"Invalid modTime: {value!r}")
                                # Keep source timezone; never invent or convert missing timezone.
                                modified = value.isoformat(timespec="seconds")
                                if value.tzinfo is None:
                                    issues.append("modTime timezone unavailable")
                            except Exception as exc:
                                issues.append(f"modTime: {exc}")
                            writer.writerow([path, size if size is not None else "",
                                             modified, "; ".join(issues) or "OK"])
                            total_files += 1
                            batch_files += 1
                            if size is not None:
                                total_bytes += size
                                batch_bytes += size
                            if issues:
                                error(path, "; ".join(issues))
                            if batch_files == 100:
                                batch()
                        except Exception as exc:
                            error(path, exc)
                    stack.extend(reversed(child_folders))
                except Exception as exc:
                    error(prefix, exc)
        except KeyboardInterrupt:
            interrupted = True
            log("Przerwano skanowanie; raport zawiera dotychczasowe wyniki.")
        finally:
            if batch_files:
                batch()
            elapsed = max(time.perf_counter() - started, 1e-9)
            log(f"END {timestamp()} | status: "
                f"{'INTERRUPTED' if interrupted else 'ERRORS' if errors else 'OK'} | "
                f"{total_files} plików, {total_bytes} B, {folders} folderów | "
                f"{elapsed:.3f} s | {total_bytes / elapsed:.2f} B/s | "
                f"{total_files / elapsed:.2f} file/s | błędy: {errors}")
    return 2 if interrupted or errors else 0


if __name__ == "__main__":
    sys.exit(main())
