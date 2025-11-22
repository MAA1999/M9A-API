#!/usr/bin/env python3
"""
Generate manifest.json files for the M9A API directory structure.

This script creates a hierarchical manifest structure:
- api/manifest.json (root)
- api/resource/manifest.json
- api/resource/data/manifest.json
- api/resource/data/activity/manifest.json (files)

Each manifest contains either:
- "directories": list of subdirectories with their manifest paths
- "files": list of files with metadata (name, path, size, updated, hash)

File hash: SHA256 of file content for integrity verification
"""

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hex string of SHA256 hash
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_current_timestamp():
    """Get current UTC timestamp in milliseconds."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def get_file_commit_time(file_path: Path) -> int:
    """
    Get the last commit time of a file from Git history.
    Falls back to filesystem mtime if Git is not available or file is not tracked.

    Args:
        file_path: Path to the file

    Returns:
        Unix timestamp in milliseconds
    """
    try:
        # Get the last commit timestamp for this file
        # %ct = committer date, UNIX timestamp
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", str(file_path)],
            capture_output=True,
            text=True,
            cwd=file_path.parent,
            timeout=5,
        )

        if result.returncode == 0 and result.stdout.strip():
            # Convert seconds to milliseconds
            commit_time_sec = int(result.stdout.strip())
            return commit_time_sec * 1000
    except (
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
        FileNotFoundError,
        ValueError,
    ):
        pass

    # Fallback to filesystem mtime
    return int(file_path.stat().st_mtime * 1000)


def generate_file_manifest(directory: Path, api_root: Path) -> dict:
    """
    Generate manifest for a directory containing data files.

    Args:
        directory: Path to the directory containing files
        api_root: Path to the api directory (for calculating relative paths)

    Returns:
        Dict with 'files' list and 'updated' timestamp
    """
    files = []

    # Find all files (excluding manifest.json itself)
    for file in sorted(directory.glob("*")):
        # Skip directories and manifest.json itself
        if file.is_dir() or file.name == "manifest.json":
            continue

        stat_info = file.stat()
        # 使用文件系统的修改时间（毫秒）
        file_mtime_ms = int(stat_info.st_mtime * 1000)
        # 计算文件 hash
        file_hash = calculate_file_hash(file)

        # 计算从 api 根目录开始的相对路径
        relative_path = file.relative_to(api_root).as_posix()

        file_info = {
            "name": file.name,
            "path": relative_path,
            "size": stat_info.st_size,
            "updated": file_mtime_ms,
            "hash": file_hash,
        }
        files.append(file_info)

    # The directory's updated time is the most recent file time
    if files:
        most_recent = max(f["updated"] for f in files)
    else:
        most_recent = get_current_timestamp()

    return {"files": files, "updated": most_recent}


def generate_directory_manifest(base_path: Path, subdirs: list[dict]) -> dict:
    """
    Generate manifest for a directory containing subdirectories.

    Args:
        base_path: Path to the directory containing subdirectories
        subdirs: List of subdirectory info dicts with 'name' and 'manifest' keys

    Returns:
        Dict with 'directories' list (with updated timestamps) and 'updated' timestamp
    """
    # Add 'updated' timestamp to each subdirectory by reading its manifest
    enriched_subdirs = []
    for subdir_info in subdirs:
        subdir_manifest_path = base_path / subdir_info["manifest"]

        # Read the subdirectory's manifest to get its updated timestamp
        if subdir_manifest_path.exists():
            with open(subdir_manifest_path, "r", encoding="utf-8") as f:
                subdir_manifest = json.load(f)
                subdir_updated = subdir_manifest.get("updated", get_current_timestamp())
        else:
            subdir_updated = get_current_timestamp()

        enriched_subdirs.append(
            {
                "name": subdir_info["name"],
                "manifest": subdir_info["manifest"],
                "updated": subdir_updated,
            }
        )

    # The directory's updated time is the most recent subdirectory time
    if enriched_subdirs:
        most_recent = max(d["updated"] for d in enriched_subdirs)
    else:
        most_recent = get_current_timestamp()

    return {"directories": enriched_subdirs, "updated": most_recent}


def write_manifest(manifest: dict, output_path: Path):
    """Write manifest dict to JSON file with pretty formatting."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"✓ Generated: {output_path}")


def generate_manifests_recursively(directory: Path, api_root: Path) -> dict | None:
    """
    Recursively generate manifests for a directory and its subdirectories.

    Args:
        directory: Path to the directory to process
        api_root: Path to the api directory (for calculating relative paths)

    Returns:
        The manifest dict for this directory, or None if directory doesn't exist
    """
    if not directory.exists():
        return None

    # Find all subdirectories (excluding hidden dirs and __pycache__)
    subdirs = [
        d
        for d in sorted(directory.iterdir())
        if d.is_dir() and not d.name.startswith(".") and d.name != "__pycache__"
    ]

    # If there are subdirectories, process them recursively
    if subdirs:
        subdir_manifests = []
        for subdir in subdirs:
            subdir_manifest = generate_manifests_recursively(subdir, api_root)
            if subdir_manifest is not None:
                # Write the subdirectory's manifest
                manifest_path = subdir / "manifest.json"
                write_manifest(subdir_manifest, manifest_path)

                subdir_manifests.append(
                    {"name": subdir.name, "manifest": f"{subdir.name}/manifest.json"}
                )

        # Generate directory manifest with subdirectories
        return generate_directory_manifest(directory, subdir_manifests)
    else:
        # Leaf directory - generate file manifest
        return generate_file_manifest(directory, api_root)


def main():
    """Generate all manifest files in the M9A API directory structure."""
    # Get the repository root directory
    repo_root = Path(__file__).resolve().parent.parent
    m9a_root = repo_root / "M9A"

    if not m9a_root.exists():
        print(f"Error: M9A directory not found at {m9a_root}")
        return 1

    print("Generating manifest files...")
    print(f"Base directory: {m9a_root}")
    print()

    # Start recursive generation from api directory
    api_dir = m9a_root / "api"
    if not api_dir.exists():
        print(f"Error: api directory not found at {api_dir}")
        return 1

    api_manifest = generate_manifests_recursively(api_dir, api_dir)
    if api_manifest:
        write_manifest(api_manifest, api_dir / "manifest.json")

    print()
    print("✅ All manifest files generated successfully!")
    return 0


if __name__ == "__main__":
    exit(main())
