# download_jupyter_agent_dataset.py
import os
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download, login
from tqdm import tqdm
import sys

# Add your token here
HF_TOKEN = "hf_..."  # Replace with your actual token
login(token=HF_TOKEN)

REPO_ID = "jupyter-agent/jupyter-agent-dataset"

BASE_FOLDER = Path(os.path.expandvars(r"%USERPROFILE%\Downloads\Dataset\jupyter-agent"))
BASE_FOLDER.mkdir(parents=True, exist_ok=True)

def get_data_files():
    api = HfApi()
    print("Listing files in repo...")
    # Add repo_type="dataset"
    files = api.list_repo_files(REPO_ID, repo_type="dataset")
    # Take likely data files (parquet, arrow, jsonl, etc.); exclude docs
    data_files = [
        f for f in files
        if f.endswith((".parquet", ".arrow", ".json", ".jsonl", ".csv"))
           and not f.startswith(".")  # no hidden
           and "README" not in f
    ]
    print(f"Found {len(data_files)} data files")
    if data_files:
        print("Files:", data_files)
    return data_files

def download_file(file_path: str):
    local_path = BASE_FOLDER / file_path
    local_path.parent.mkdir(parents=True, exist_ok=True)

    if local_path.exists() and local_path.stat().st_size > 100_000:
        return "skip", str(local_path.name)

    try:
        hf_hub_download(
            repo_id=REPO_ID,
            filename=file_path,
            repo_type="dataset",  # Add this
            local_dir=BASE_FOLDER,
            local_dir_use_symlinks=False,
            resume_download=True,
        )
        return "success", str(local_path.name)
    except Exception as e:
        print(f"Failed {file_path}: {e}")
        return "fail", file_path

def main():
    dry_run = "--dry-run" in sys.argv

    data_files = get_data_files()
    if not data_files:
        print("No data files found. Maybe check repo structure manually.")
        return

    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be downloaded")
        print(f"Would download {len(data_files)} files to: {BASE_FOLDER}")
        return

    print(f"\nDownloading to: {BASE_FOLDER}")
    print("This should be ~7–30 GB depending on shards.\n")

    stats = {"success": 0, "skip": 0, "fail": 0}
    results = []

    for file_path in tqdm(data_files, desc="Downloading", unit="file"):
        status, name = download_file(file_path)
        stats[status] += 1
        results.append(f"{status.upper()}: {name}")

    print("\n" + "="*50)
    print("Finished!")
    print(f"Success : {stats['success']}")
    print(f"Skipped : {stats['skip']}")
    print(f"Failed  : {stats['fail']}")
    print(f"Total   : {sum(stats.values())} files")
    print("="*50)

    if results:
        print("\nDetails:")
        for r in results:
            print(r)

if __name__ == "__main__":
    main()