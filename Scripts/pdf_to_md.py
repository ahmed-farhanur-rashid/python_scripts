"""
pdf_to_md.py — Research-grade PDF → Markdown converter
Preserves equations, tables, figures, and citations.
Uses marker-pdf for conversion, ollama for citation extraction.

Install:
    pip install marker-pdf
    # For citation extraction:
    pip install ollama  (requires Ollama running locally)
"""

import os
import json
import argparse
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
CONVERTED_DIR   = "Converted"
CITATIONS_FILE  = "citations.json"
DEFAULT_WORKERS = 2          # keep low — marker-pdf is CPU/GPU heavy
OLLAMA_MODEL    = "llama3"   # change to any model you have pulled


# ── Conversion ────────────────────────────────────────────────────────────────

def convert_pdf(pdf_path: Path) -> str:
    """
    Convert a single PDF to Markdown using marker-pdf.

    marker-pdf is purpose-built for academic documents:
      • handles multi-column layouts
      • preserves LaTeX equations as $...$ blocks
      • produces clean table markdown
      • respects figure captions
      • retains footnote text inline

    Returns the markdown string.
    """
    # Import here so the rest of the script stays importable without marker installed
    from marker.convert import convert_single_pdf
    from marker.models import load_all_models

    models = load_all_models()   # cached after first call in the same process
    full_text, _metadata, _images = convert_single_pdf(
        str(pdf_path),
        models,
        langs=["English"],        # add more ISO-639-1 codes if needed
        batch_multiplier=2,       # higher = faster on GPU, lower on CPU
    )
    return full_text


# ── Citation extraction ───────────────────────────────────────────────────────

CITATION_SYSTEM_PROMPT = """\
You are a citation parser for academic papers.
Given the References section of a research paper, extract every citation
as a structured JSON array.  Return ONLY the JSON — no explanation, no
markdown fences.

Each entry must have:
  - "id"      : the in-text key, e.g. "[1]", "[Smith2020]", "Smith et al. 2020"
  - "authors" : list of author strings
  - "year"    : 4-digit year string or ""
  - "title"   : paper / book title string
  - "venue"   : journal, conference, or publisher (empty string if absent)
  - "doi"     : DOI string (empty string if absent)
"""


def extract_references_section(markdown: str) -> str:
    """
    Pull the References / Bibliography / Works Cited section from the markdown.
    Returns an empty string if none is found.
    """
    import re
    # Match common headings regardless of heading level
    pattern = re.compile(
        r"^#{1,3}\s*(?:references|bibliography|works cited)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(markdown)
    if not match:
        return ""
    return markdown[match.start():]


def extract_citations_with_ollama(references_text: str, model: str = OLLAMA_MODEL) -> list[dict]:
    """
    Use a local Ollama model to parse the references section into structured data.
    Returns a list of citation dicts, or [] on failure.
    """
    if not references_text.strip():
        return []

    try:
        import ollama
    except ImportError:
        log.warning("ollama package not installed — skipping citation extraction. "
                    "Run: pip install ollama")
        return []

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": CITATION_SYSTEM_PROMPT},
                {"role": "user",   "content": references_text[:8000]},  # guard context window
            ],
            options={"temperature": 0},   # deterministic for structured extraction
        )
        raw = response["message"]["content"].strip()
        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except json.JSONDecodeError as e:
        log.warning("Citation JSON parse error: %s", e)
        return []
    except Exception as e:
        log.warning("Ollama error during citation extraction: %s", e)
        return []


# ── Post-processing helpers ───────────────────────────────────────────────────

def clean_markdown(text: str) -> str:
    """
    Light post-processing to improve markdown consistency.
    marker-pdf output is already high quality; we only fix small papercuts.
    """
    import re
    lines = text.splitlines()
    cleaned = []
    prev_blank = False

    for line in lines:
        stripped = line.rstrip()

        # Collapse 3+ consecutive blank lines into two
        if stripped == "":
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False

        # Normalise Windows line endings that may survive in extracted text
        cleaned.append(stripped)

    # Ensure a single trailing newline
    return "\n".join(cleaned).strip() + "\n"


# ── Per-file orchestration ────────────────────────────────────────────────────

def process_pdf(
    pdf_path: Path,
    output_dir: Path,
    extract_citations: bool,
    ollama_model: str,
) -> dict:
    """
    Convert one PDF and optionally extract its citations.
    Returns a result dict suitable for a summary report.
    """
    base    = pdf_path.stem
    md_path = output_dir / (base + ".md")

    if md_path.exists():
        log.info("Skip (exists): %s", pdf_path.name)
        return {"file": str(pdf_path), "status": "skipped"}

    try:
        log.info("Converting: %s", pdf_path)
        raw_md   = convert_pdf(pdf_path)
        clean_md = clean_markdown(raw_md)

        md_path.write_text(clean_md, encoding="utf-8")
        log.info("✅  Written: %s", md_path)

        citations = []
        if extract_citations:
            refs = extract_references_section(clean_md)
            if refs:
                log.info("   Extracting citations via Ollama (%s)…", ollama_model)
                citations = extract_citations_with_ollama(refs, ollama_model)
                if citations:
                    cit_path = output_dir / (base + "_citations.json")
                    cit_path.write_text(
                        json.dumps(citations, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    log.info("   📚  %d citations saved → %s", len(citations), cit_path.name)
                else:
                    log.info("   (no citations extracted)")
            else:
                log.info("   (no references section found)")

        return {
            "file":      str(pdf_path),
            "status":    "ok",
            "md":        str(md_path),
            "citations": len(citations),
        }

    except Exception as exc:
        log.error("❌  %s | %s", pdf_path, exc)
        return {"file": str(pdf_path), "status": "error", "error": str(exc)}


# ── Directory walker ──────────────────────────────────────────────────────────

def walk_and_convert(
    root: Path,
    extract_citations: bool,
    ollama_model: str,
    workers: int,
) -> None:
    """
    Recursively convert all PDFs under `root`, mirroring the folder structure
    into a sibling `Converted/` subdirectory at each level.

    Skipping logic:
      • Any directory named "Converted" is skipped entirely (no double-processing).
      • Already-converted files (md exists) are skipped without re-reading the PDF.
    """
    tasks = []
    for current, dirs, files in os.walk(root):
        # Don't recurse into already-converted folders
        dirs[:] = [d for d in dirs if d != CONVERTED_DIR]

        pdf_files = [f for f in files if f.lower().endswith(".pdf")]
        if not pdf_files:
            continue

        current_path = Path(current)
        output_dir   = current_path / CONVERTED_DIR
        output_dir.mkdir(exist_ok=True)

        for fname in pdf_files:
            tasks.append((current_path / fname, output_dir))

    if not tasks:
        log.info("No PDFs found under %s", root)
        return

    log.info("Found %d PDF(s) to process (workers=%d)", len(tasks), workers)
    results = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(process_pdf, pdf, out, extract_citations, ollama_model): pdf
            for pdf, out in tasks
        }
        for fut in as_completed(futures):
            results.append(fut.result())

    # Summary
    ok      = sum(1 for r in results if r["status"] == "ok")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors  = sum(1 for r in results if r["status"] == "error")
    log.info("Done — %d converted, %d skipped, %d errors", ok, skipped, errors)

    if errors:
        for r in results:
            if r["status"] == "error":
                log.error("  FAIL: %s — %s", r["file"], r.get("error"))


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Convert research PDFs to Markdown, with optional citation extraction.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_to_md.py /data/papers
  python pdf_to_md.py /data/papers --citations
  python pdf_to_md.py /data/papers --citations --model mistral --workers 1
        """,
    )
    p.add_argument("root", type=Path, help="Root directory containing PDFs")
    p.add_argument(
        "--citations", action="store_true",
        help="Extract structured citations with a local Ollama model",
    )
    p.add_argument(
        "--model", default=OLLAMA_MODEL,
        help=f"Ollama model to use for citation extraction (default: {OLLAMA_MODEL})",
    )
    p.add_argument(
        "--workers", type=int, default=DEFAULT_WORKERS,
        help=f"Parallel conversion workers (default: {DEFAULT_WORKERS}). "
             "Keep at 1-2 unless you have a strong GPU.",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

    if not args.root.is_dir():
        log.error("Not a directory: %s", args.root)
        raise SystemExit(1)

    walk_and_convert(
        root=args.root,
        extract_citations=args.citations,
        ollama_model=args.model,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
