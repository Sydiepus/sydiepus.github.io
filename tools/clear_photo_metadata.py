"""Remove embedded metadata from JPG photos in assets/photos."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from PIL import Image
from imageio_ffmpeg import get_ffmpeg_exe

ROOT = Path(__file__).parent.parent.resolve()
DEFAULT_PHOTO_DIR = ROOT / "src" / "assets" / "photos"


def clear_metadata(photo_dir: Path) -> int:
    files = sorted({
        path for path in photo_dir.glob("*")
        if path.suffix.lower() == ".jpg" and not path.stem.endswith(".cleaned")
    })
    for source in files:
        target = source.with_name(source.stem + ".cleaned.jpg")
        if target.exists():
            target.unlink()

        with Image.open(source) as image:
            image.save(
                target,
                format="JPEG",
                quality="keep",
                exif=b"",
                icc_profile=None,
                comment=None,
            )
        source.unlink()
        os.replace(target, source)

    return len(files)


def clear_video_metadata(photo_dir: Path) -> int:
    files = sorted({
        path for path in photo_dir.glob("*")
        if path.suffix.lower() == ".mp4" and not path.stem.endswith(".cleaned")
    })
    ffmpeg = get_ffmpeg_exe()
    for source in files:
        target = source.with_name(source.stem + ".cleaned.mp4")
        if target.exists():
            target.unlink()
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(source),
                "-map_metadata",
                "-1",
                "-map",
                "0",
                "-c",
                "copy",
                str(target),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        source.unlink()
        os.replace(target, source)
    return len(files)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove embedded metadata from JPG photos and MP4 videos."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=DEFAULT_PHOTO_DIR,
        help="directory containing JPG photos (default: assets/photos)",
    )
    args = parser.parse_args()

    if not args.directory.is_dir():
        raise SystemExit(f"photo directory does not exist: {args.directory}")

    count = clear_metadata(args.directory)
    videos = clear_video_metadata(args.directory)
    print(
        f"cleaned {count} JPG photo{'s' if count != 1 else ''} and "
        f"{videos} MP4 video{'s' if videos != 1 else ''}"
    )


if __name__ == "__main__":
    main()
