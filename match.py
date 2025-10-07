#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.markers import default_environment


ENV = default_environment()
def load_pipfile_lock(path: Path, sections=("default","develop")):
    data = json.loads(path.read_text())
    deps = {}
    for section in sections:
        for name, meta in data.get(section, {}).items():
            key = canonicalize_name(name)
            if "version" in meta:                 # e.g. "==1.2.3"
                deps[key] = meta["version"]
            elif "ref" in meta or "rev" in meta:  # git rev/ref
                ref = meta.get("ref") or meta.get("rev")
                deps[key] = f"git:{meta.get('git','')}@{ref}"
            elif "file" in meta:                  # local/remote file or sdist
                deps[key] = f"file:{meta['file']}"
            elif "url" in meta:
                deps[key] = f"url:{meta['url']}"
            else:
                # Fallback to whatever specifier Pipenv stored
                deps[key] = str(meta)
    return deps
def line_is_ignorable(line: str) -> bool:
    line = line.strip()
    return not line or line.startswith("#") or line.startswith("-r ") or line.startswith("--")
def load_requirements(path: Path):
    deps = {}
    for raw in path.read_text().splitlines():
        if line_is_ignorable(raw):
            continue
        req = Requirement(raw)
        # Skip requirements that don't apply to this environment
        if req.marker and not req.marker.evaluate(ENV):
            continue
        key = canonicalize_name(req.name)
        if req.url:                                # name @ https://... or file://...
            deps[key] = f"url:{req.url}"
        elif req.specifier:
            # prefer exact pin if present
            pins = [s for s in req.specifier if s.operator == "=="]
            deps[key] = f"=={pins[0].version}" if pins else str(req.specifier)
        else:
            deps[key] = ""                         # unpinned (will mismatch vs locked)
    return deps
def compare(lock_deps: dict, req_deps: dict, strict: bool):
    missing_in_lock = []   # in requirements but not in Pipfile.lock
    extra_in_lock = []     # in Pipfile.lock but not in requirements
    version_mismatches = []

    for name, req_pin in req_deps.items():
        lock_pin = lock_deps.get(name)
        if lock_pin is None:
            missing_in_lock.append(name)
        elif req_pin and lock_pin != req_pin:
            version_mismatches.append((name, req_pin, lock_pin))

    if strict:
        for name in lock_deps.keys() - req_deps.keys():
            extra_in_lock.append(name)

    ok = not (missing_in_lock or version_mismatches or (strict and extra_in_lock))
    return ok, missing_in_lock, version_mismatches, extra_in_lock
def main():
    p = argparse.ArgumentParser(description="Verify Pipfile.lock matches requirements.txt")
    p.add_argument("-l","--pipfile-lock", default="Pipfile.lock", type=Path)
    p.add_argument("-r","--requirements", default="requirements.txt", type=Path)
    p.add_argument("--sections", default="default,develop",
                   help="Comma-separated Pipfile.lock sections to check")
    p.add_argument("--strict", action="store_true",
                   help="Also fail on packages that exist in lock but not in requirements")
    args = p.parse_args()

    if not args.pipfile_lock.exists():
        print(f"ERROR: {args.pipfile_lock} not found"); return 2
    if not args.requirements.exists():
        print(f"ERROR: {args.requirements} not found"); return 2

    lock = load_pipfile_lock(args.pipfile_lock, tuple(s.strip() for s in args.sections.split(",")))
    reqs = load_requirements(args.requirements)

    ok, missing, mismatches, extras = compare(lock, reqs, args.strict)

    if not ok:
        print("Dependency check FAILED.")
        if missing:
            print("\nMissing in Pipfile.lock (present in requirements):")
            for n in sorted(missing): print(f"  - {n}")
        if mismatches:
            print("\nVersion mismatches:")
            for n, req_pin, lock_pin in sorted(mismatches):
                print(f"  - {n}: requirements has {req_pin}, Pipfile.lock has {lock_pin}")
        if extras and args.strict:
            print("\nExtras in Pipfile.lock (not in requirements):")
            for n in sorted(extras): print(f"  - {n}")
        return 1

    print("✅ Versions match between Pipfile.lock and requirements.")
    return 0
if __name__ == "__main__":
    sys.exit(main())