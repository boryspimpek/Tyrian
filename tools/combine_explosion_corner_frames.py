"""
Combine Tyrian/Galaxid explosion corner frames into full combined explosion frames.

This script reads numbered explosion sprite PNGs like:
  explo_t02_large_ground_tl_f00.png
  explo_t03_large_ground_bl_f01.png
  ...

It composes the 4 corner explosion frames for each animation step into one image and
saves the result to an output directory.

Usage:
  python combine_explosion_corner_frames.py --source /path/to/Galaxid/data/explosion_sprites --out /path/to/output

By default it combines two groups:
  large_ground (types 2,4,3,5)
  large_air   (types 7,9,8,10)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

DEFAULT_SOURCE = Path(r"C:\Users\borys\projekty\Tyrian\extracted_tiles\explosions")

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("Pillow is required. Install with: pip install pillow") from exc

TYPE_LABELS: Dict[int, str] = {
    0: "hit_flash",
    1: "small_enemy",
    2: "large_ground_tl",
    3: "large_ground_bl",
    4: "large_ground_tr",
    5: "large_ground_br",
    6: "white_smoke",
    7: "large_air_tl",
    8: "large_air_bl",
    9: "large_air_tr",
    10: "large_air_br",
    11: "flash_short",
    12: "medium",
    13: "brief",
}

TYPE_TTL: Dict[int, int] = {
    0: 7,
    1: 12,
    2: 12,
    3: 12,
    4: 12,
    5: 12,
    6: 7,
    7: 12,
    8: 12,
    9: 12,
    10: 12,
    11: 3,
    12: 7,
    13: 3,
}

GROUPS: Dict[str, Tuple[List[int], List[Tuple[int, int]]]] = {
    "large_ground": (
        [2, 4, 3, 5],
        [(-6, -14), (6, -14), (-6, -2), (6, -2)],
    ),
    "large_air": (
        [7, 9, 8, 10],
        [(-6, -14), (6, -14), (-6, -1), (6, -1)],
    ),
}


def load_textures(folder: Path, type_id: int) -> List[Image.Image]:
    label = TYPE_LABELS.get(type_id, f"type{type_id:02d}")
    ttl = TYPE_TTL.get(type_id, 0)
    textures: List[Image.Image] = []

    for frame in range(ttl):
        filename = f"explo_t{type_id:02d}_{label}_f{frame:02d}.png"
        path = folder / filename
        if not path.exists():
            continue
        textures.append(Image.open(path).convert("RGBA"))

    return textures


def combine_group(folder: Path, output: Path, group_name: str) -> None:
    type_ids, offsets = GROUPS[group_name]
    textures_by_type: List[List[Image.Image]] = []

    for type_id in type_ids:
        textures = load_textures(folder, type_id)
        if not textures:
            raise FileNotFoundError(f"No textures found for type {type_id} in {folder}")
        textures_by_type.append(textures)

    max_frames = max(len(textures) for textures in textures_by_type)
    origin = (0, 0)

    output_dir = output / group_name
    output_dir.mkdir(parents=True, exist_ok=True)

    for frame_index in range(max_frames):
        # Determine canvas bounds
        positions = []
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        for textures, offset in zip(textures_by_type, offsets):
            if frame_index >= len(textures):
                continue
            texture = textures[frame_index]
            half_w = texture.width // 2
            half_h = texture.height // 2
            top_left_x = offset[0] - half_w
            top_left_y = offset[1] - half_h
            bottom_right_x = top_left_x + texture.width
            bottom_right_y = top_left_y + texture.height

            min_x = min(min_x, top_left_x)
            min_y = min(min_y, top_left_y)
            max_x = max(max_x, bottom_right_x)
            max_y = max(max_y, bottom_right_y)
            positions.append((texture, top_left_x, top_left_y))

        if min_x == float("inf"):
            raise RuntimeError("No textures available for this frame index")

        canvas_width = int(max_x - min_x)
        canvas_height = int(max_y - min_y)
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

        for texture, top_left_x, top_left_y in positions:
            paste_x = int(top_left_x - min_x)
            paste_y = int(top_left_y - min_y)
            canvas.alpha_composite(texture, (paste_x, paste_y))

        output_path = output_dir / f"{group_name}_f{frame_index:02d}.png"
        canvas.save(output_path)
        print(f"Saved {output_path}")


def infer_default_source() -> Path:
    current = Path(__file__).resolve()
    tyrian_root = current.parents[1]
    galaxid_root = tyrian_root.parent / "Galaxid"
    return (galaxid_root / "data" / "explosion_sprites") if galaxid_root.exists() else Path(".")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine explosion corner frames into composed images.")
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Folder with explo_tXX_..._fYY.png sprites (default is Tyrian extracted_tiles/explosions)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "extracted_tiles" / "combined_explosion_frames",
        help="Output folder for combined images",
    )
    parser.add_argument(
        "--group",
        choices=list(GROUPS.keys()) + ["all"],
        default="all",
        help="Which explosion group to combine",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source
    output = args.out

    if not source.exists():
        raise SystemExit(f"Source folder does not exist: {source}")

    groups = GROUPS.keys() if args.group == "all" else [args.group]
    output.mkdir(parents=True, exist_ok=True)

    for group_name in groups:
        print(f"Combining group: {group_name}")
        combine_group(source, output, group_name)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
