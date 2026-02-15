import os
import pymupdf.layout          # Activate improved layout analysis (must come before pymupdf4llm)
import pymupdf4llm
from pathlib import Path
from tqdm import tqdm
import argparse
import shutil


def convert_pdf_to_md(pdf_path: Path, md_path: Path) -> bool:
    """
    Convert one PDF to Markdown (text only, no images).
    Returns True if successful.
    """
    try:
        md_text = pymupdf4llm.to_markdown(
            pdf_path,
            page_chunks=False,              # whole document
            write_images=False,             # no image extraction
            ignore_images=True,
            ignore_graphics=True,
            show_progress=False,
            margins=(36, 40, 36, 40),       # balanced margins
            table_strategy="lines_strict",  # good balance for academic tables
            # hdr_info=None,                # uncomment if header detection is too aggressive
        )

        # Ensure target parent folder exists
        md_path.parent.mkdir(parents=True, exist_ok=True)

        # Write clean UTF-8 markdown
        md_path.write_text(md_text.strip(), encoding="utf-8")
        return True

    except Exception as e:
        print(f"  ✗ Failed: {pdf_path.name}  →  {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert research PDFs to clean Markdown – saved in Papers_Converted")
    parser.add_argument(
        "--root",
        type=str,
        default=os.path.expanduser("~/Downloads/Papers"),
        help="Source folder with original PDFs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be converted (no files written)",
    )
    args = parser.parse_args()

    source_root = Path(args.root).resolve()
    if not source_root.is_dir():
        print(f"Error: Source folder not found → {source_root}")
        return

    # Target root = sibling folder named Papers_Converted
    target_root = source_root.parent / "Papers_Converted"
    print(f"Source: {source_root}")
    print(f"Target: {target_root}\n")

    pdf_files = sorted(source_root.rglob("*.pdf"))
    if not pdf_files:
        print("No .pdf files found.")
        return

    print(f"Found {len(pdf_files)} PDF files.\n")

    success = 0
    skipped = 0
    failed = 0

    for pdf_path in tqdm(pdf_files, desc="Converting", unit="paper"):
        # Compute relative path from source root
        rel_path = pdf_path.relative_to(source_root)

        # Build target path: same subfolders + .md
        target_md_path = target_root / rel_path.with_suffix(".md")

        if target_md_path.exists():
            print(f"  - Skipped (already exists): {rel_path}")
            skipped += 1
            continue

        if args.dry_run:
            print(f"  Would convert: {rel_path} → {target_md_path.relative_to(target_root)}")
            continue

        # Optional: copy folder structure early (nice for partial runs)
        target_md_path.parent.mkdir(parents=True, exist_ok=True)

        ok = convert_pdf_to_md(pdf_path, target_md_path)
        if ok:
            success += 1
            # print(f"  ✓ {rel_path} → {target_md_path.name}")  # uncomment for verbose
        else:
            failed += 1

    print("\n" + "═" * 70)
    print("Conversion finished:")
    print(f"  • Successfully converted : {success:3d}")
    print(f"  • Skipped (already exist) : {skipped:3d}")
    print(f"  • Failed                  : {failed:3d}")
    print(f"  • Total processed         : {len(pdf_files):3d}")
    print("═" * 70)

    if success > 0:
        print(f"Markdown files are in: {target_root}")
        print("You can now feed them to your local LLM.\n")


if __name__ == "__main__":
    main()