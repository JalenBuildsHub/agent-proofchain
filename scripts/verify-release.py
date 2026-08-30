#!/usr/bin/env python3
"""Verify the exact wheel and sdist intended for an Agent ProofChain release."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import stat
import tarfile
import tomllib
import zipfile
from email.parser import Parser
from pathlib import Path, PurePosixPath
from typing import Any

EXPECTED_NAME = "agent-proofchain"
EXPECTED_WHEEL_PACKAGE = "proofchain/__init__.py"
FORBIDDEN_PARTS = {
    ".agent",
    ".github",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "artifacts",
    "build",
    "dist",
    "reports",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_member(name: str) -> PurePosixPath:
    normalized = name.replace("\\", "/")
    member = PurePosixPath(normalized)
    if (
        member.is_absolute()
        or ".." in member.parts
        or (member.parts and member.parts[0].endswith(":"))
    ):
        raise ValueError(f"unsafe archive path: {name}")
    if any(part in FORBIDDEN_PARTS for part in member.parts):
        raise ValueError(f"forbidden release content: {name}")
    return member


def _project_metadata(root: Path) -> tuple[str, str]:
    document = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project = document["project"]
    return str(project["version"]), str(project["requires-python"])


def _source_version(root: Path) -> str:
    module = ast.parse((root / "src" / "proofchain" / "__init__.py").read_text(encoding="utf-8"))
    for statement in module.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in statement.targets
        ):
            value = ast.literal_eval(statement.value)
            if isinstance(value, str):
                return value
    raise ValueError("src/proofchain/__init__.py must define a literal __version__")


def _verify_wheel(path: Path, version: str, requires_python: str) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        members = []
        for info in archive.infolist():
            member = _validate_member(info.filename)
            if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                raise ValueError(f"wheel must not contain symbolic links: {info.filename}")
            if "tests" in member.parts:
                raise ValueError(f"wheel must not contain tests: {info.filename}")
            members.append(member)
        if PurePosixPath(EXPECTED_WHEEL_PACKAGE) not in members:
            raise ValueError("wheel does not contain the proofchain package")
        metadata_names = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_names) != 1:
            raise ValueError("wheel must contain exactly one METADATA file")
        metadata = Parser().parsestr(archive.read(metadata_names[0]).decode("utf-8"))

    if metadata["Name"] != EXPECTED_NAME:
        raise ValueError(f"unexpected wheel name: {metadata['Name']}")
    if metadata["Version"] != version:
        raise ValueError(f"unexpected wheel version: {metadata['Version']}")
    actual_specifiers = {
        item.strip() for item in str(metadata["Requires-Python"]).split(",") if item.strip()
    }
    expected_specifiers = {item.strip() for item in requires_python.split(",") if item.strip()}
    if actual_specifiers != expected_specifiers:
        raise ValueError(f"unexpected Requires-Python: {metadata['Requires-Python']}")
    return {
        "file": path.name,
        "sha256": _sha256(path),
        "size": path.stat().st_size,
    }


def _verify_sdist(path: Path, version: str) -> dict[str, Any]:
    with tarfile.open(path, mode="r:gz") as archive:
        members = []
        package_info = None
        for archive_member in archive.getmembers():
            member = _validate_member(archive_member.name)
            if archive_member.issym() or archive_member.islnk():
                raise ValueError(f"sdist must not contain links: {archive_member.name}")
            if not (archive_member.isfile() or archive_member.isdir()):
                raise ValueError(f"sdist contains unsupported member: {archive_member.name}")
            members.append(member)
            if archive_member.isfile() and member.name == "PKG-INFO":
                extracted = archive.extractfile(archive_member)
                if extracted is None:
                    raise ValueError("could not read sdist PKG-INFO")
                package_info = Parser().parsestr(extracted.read().decode("utf-8"))
    roots = {member.parts[0] for member in members if member.parts}
    if len(roots) != 1:
        raise ValueError("sdist must contain exactly one top-level directory")
    root = next(iter(roots))
    required = {
        PurePosixPath(root, "LICENSE"),
        PurePosixPath(root, "README.md"),
        PurePosixPath(root, "pyproject.toml"),
        PurePosixPath(root, "src", "proofchain", "__init__.py"),
    }
    if not required.issubset(set(members)):
        missing = sorted(str(item) for item in required - set(members))
        raise ValueError(f"sdist is missing required files: {missing}")
    normalized_version = version.replace("-", "_")
    if normalized_version not in root.replace("-", "_"):
        raise ValueError(f"sdist root does not encode version {version}: {root}")
    if package_info is None:
        raise ValueError("sdist does not contain PKG-INFO")
    if package_info["Name"] != EXPECTED_NAME or package_info["Version"] != version:
        raise ValueError("sdist package metadata does not match the project")
    return {
        "file": path.name,
        "sha256": _sha256(path),
        "size": path.stat().st_size,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dist", type=Path)
    parser.add_argument("--tag")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    version, requires_python = _project_metadata(root)
    if _source_version(root) != version:
        raise ValueError("source __version__ does not match the project version")
    if args.tag and args.tag != f"v{version}":
        raise ValueError(f"tag {args.tag!r} does not match project version v{version}")

    wheels = sorted(args.dist.glob("*.whl"))
    sdists = sorted(args.dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("release directory must contain exactly one wheel and one sdist")

    receipt = {
        "schema_version": 1,
        "name": EXPECTED_NAME,
        "version": version,
        "requires_python": requires_python,
        "artifacts": [
            _verify_wheel(wheels[0], version, requires_python),
            _verify_sdist(sdists[0], version),
        ],
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
