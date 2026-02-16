# download_the_stack_dedup_python.py
import os
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download, login
from tqdm import tqdm
import sys

# Add your token here
HF_TOKEN = "hf_..."  # Replace with your actual token
login(token=HF_TOKEN)

REPO_ID = "bigcode/the-stack-dedup"
DATA_DIR = "data/python"  # only this subfolder

BASE_FOLDER = Path(os.path.expandvars(r"%USERPROFILE%\Downloads\Dataset\the-stack-dedup"))
BASE_FOLDER.mkdir(parents=True, exist_ok=True)

def get_parquet_files():
    api = HfApi()
    print("Listing all files in repo... (may take 30–90 seconds)")
    # ADD repo_type="dataset" here!
    files = api.list_repo_files(REPO_ID, repo_type="dataset")
    parquet_files = [
        f for f in files
        if f.startswith(f"{DATA_DIR}/") and f.endswith(".parquet")
    ]
    print(f"Found {len(parquet_files)} .parquet files in {DATA_DIR}")
    if parquet_files:
        print("First few:", parquet_files[:3])
        print("Last few :", parquet_files[-3:])
    return parquet_files

def download_file(file_path: str):
    local_path = BASE_FOLDER / file_path
    local_path.parent.mkdir(parents=True, exist_ok=True)

    if local_path.exists() and local_path.stat().st_size > 1_000_000:
        return "skip", str(local_path.name)

    try:
        hf_hub_download(
            repo_id=REPO_ID,
            filename=file_path,
            repo_type="dataset",  # ADD THIS!
            local_dir=BASE_FOLDER,
            local_dir_use_symlinks=False,
            resume_download=True,
        )
        return "success", str(local_path.name)
    except Exception as e:
        print(f"Failed {file_path}: {e}")
        return "fail", str(file_path)

def main():
    dry_run = "--dry-run" in sys.argv

    parquet_files = get_parquet_files()
    if not parquet_files:
        print("No parquet files found. Check repo or your access.")
        return

    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be downloaded")
        print(f"Would download {len(parquet_files)} files to: {BASE_FOLDER}")
        return

    print("\nStarting download...")
    print(f"Target folder: {BASE_FOLDER}")
    print("WARNING: This can be 100–250+ GB. Interrupt with Ctrl+C if needed.\n")

    stats = {"success": 0, "skip": 0, "fail": 0}
    results = []

    for file_path in tqdm(parquet_files, desc="Downloading", unit="file"):
        status, name = download_file(file_path)
        stats[status] += 1
        results.append(f"{status.upper()}: {name}")

        if (stats["success"] + stats["skip"] + stats["fail"]) % 10 == 0:
            print(f"  Progress → Success: {stats['success']} | Skip: {stats['skip']} | Fail: {stats['fail']}")

    print("\n" + "="*60)
    print("Download finished!")
    print(f"Success : {stats['success']}")
    print(f"Skipped : {stats['skip']}")
    print(f"Failed  : {stats['fail']}")
    print(f"Total   : {sum(stats.values())} files")
    print("="*60)

    if results:
        print("\nDetails:")
        for r in results:
            print(r)

if __name__ == "__main__":
    main()