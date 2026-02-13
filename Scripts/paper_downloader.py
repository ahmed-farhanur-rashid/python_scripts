import os
import requests
from tqdm import tqdm
import time
import shutil

# ===============================
# CONFIG
# ===============================

BASE_DIR = os.path.expanduser("~/Downloads/Papers")
DELAY_BETWEEN_DOWNLOADS = 1  # seconds
MAX_RETRIES = 3

# ===============================
# PAPER STRUCTURE
# ===============================

papers = {
    "I. Core Transformer & Architectural Foundations": [
        ("01 Attention Is All You Need", "https://arxiv.org/pdf/1706.03762.pdf"),
        ("02 On Layer Normalization in the Transformer Architecture", "https://arxiv.org/pdf/2002.04745.pdf"),
        ("03 Root Mean Square Layer Normalization RMSNorm", "https://arxiv.org/pdf/1910.07467.pdf"),
        ("04 RoFormer Enhanced Transformer with Rotary Position Embedding", "https://arxiv.org/pdf/2104.09864.pdf"),
        ("05 ALiBi Train Short Test Long", "https://arxiv.org/pdf/2108.12409.pdf"),
        ("06 Transformer-XL Attentive Language Models Beyond Fixed-Length Context", "https://arxiv.org/pdf/1901.02860.pdf"),
        ("07 Reformer The Efficient Transformer", "https://arxiv.org/pdf/2001.04451.pdf"),
        ("08 Linformer Self-Attention with Linear Complexity", "https://arxiv.org/pdf/2006.04768.pdf"),
        ("09 Performer Fast Attention via FAVOR+", "https://arxiv.org/pdf/2009.14794.pdf"),
        ("10 FlashAttention Fast and Memory-Efficient Exact Attention", "https://arxiv.org/pdf/2205.14135.pdf"),
        ("11 FlashAttention-2 Faster Attention with Better Parallelism", "https://arxiv.org/pdf/2307.08691.pdf"),
        ("12 Hyena Hierarchy Towards Larger Convolutional Language Models", "https://arxiv.org/pdf/2302.10866.pdf"),
        ("13 Mamba Linear-Time Sequence Modeling with Selective State Spaces", "https://arxiv.org/pdf/2312.00752.pdf"),
        ("14 GLU Variants Improve Transformer", "https://arxiv.org/pdf/2002.05202.pdf"),
        ("15 Gated Attention Units GAU", "https://arxiv.org/pdf/2202.10447.pdf"),
    ],
    "II. Efficient Mini LLM Compression-Oriented Papers": [
        ("16 DistilBERT Smaller Faster Cheaper", "https://arxiv.org/pdf/1910.01108.pdf"),
        ("17 TinyBERT Distilling BERT", "https://arxiv.org/pdf/1909.10351.pdf"),
        ("18 MobileBERT A Compact Task-Agnostic BERT", "https://arxiv.org/pdf/2004.02984.pdf"),
        ("19 ALBERT A Lite BERT", "https://arxiv.org/pdf/1909.11942.pdf"),
        ("20 LoRA Low-Rank Adaptation of Large Language Models", "https://arxiv.org/pdf/2106.09685.pdf"),
        ("21 QLoRA Efficient Finetuning of Quantized LLMs", "https://arxiv.org/pdf/2305.14314.pdf"),
        ("22 GPTQ Accurate Post-Training Quantization for GPT", "https://arxiv.org/pdf/2210.17323.pdf"),
        ("23 AWQ Activation-Aware Weight Quantization", "https://arxiv.org/pdf/2306.00978.pdf"),
        ("24 SparseGPT Massive Language Models Can Be Accurately Pruned in One-Shot", "https://arxiv.org/pdf/2301.00774.pdf"),
        ("25 MINI-LLM Memory-Efficient Structured Pruning for Large Language Models", "https://arxiv.org/pdf/2402.12528.pdf"),
        ("26 Lottery Ticket Hypothesis", "https://arxiv.org/pdf/1803.03635.pdf"),
        ("27 Training Deep Nets with Sublinear Memory Cost", "https://arxiv.org/pdf/1604.06174.pdf"),
        ("28 ZeRO Memory Optimizations Toward Training Trillion Parameter Models", "https://arxiv.org/pdf/1910.02054.pdf"),
        ("29 DeepSpeed Ulysses: System Optimizations for Enabling Training of Extreme Long Sequence Transformer Models", "https://arxiv.org/pdf/2309.14509.pdf"),
        ("30 SlimLLM Accurate Structured Pruning for Large Language Models", "https://arxiv.org/pdf/2505.22689.pdf")
    ],
    "III. Code-Specific LLMs": [
        ("31 CodeBERT A Pre-Trained Model for Programming and Natural Languages", "https://arxiv.org/pdf/2002.08155.pdf"),
        ("32 GraphCodeBERT Pre-training Code Representations with Data Flow", "https://arxiv.org/pdf/2009.08366.pdf"),
        ("33 CodeT5 Identifier-Aware Encoder-Decoder for Code", "https://arxiv.org/pdf/2109.00859.pdf"),
        ("34 CodeGen An Open Large Language Model for Code Generation", "https://arxiv.org/pdf/2203.13474.pdf"),
        ("35 PolyCoder Open Source Code Models", "https://arxiv.org/pdf/2202.13169.pdf"),
        ("36 SantaCoder Don't Reach for the Stars", "https://arxiv.org/pdf/2301.03988.pdf"),
        ("37 StarCoder May the Source Be With You", "https://arxiv.org/pdf/2305.06161.pdf"),
        ("38 PaLM-Coder Program Synthesis with Large Language Models", "https://arxiv.org/pdf/2204.02311.pdf"),
        ("39 InCoder A Generative Model for Code Infilling", "https://arxiv.org/pdf/2204.05999.pdf"),
        ("40 Evaluating Large Language Models Trained on Code Codex Paper", "https://arxiv.org/pdf/2107.03374.pdf"),
        ("41 DeepSeek-Coder When the Large Language Model Meets Programming", "https://arxiv.org/pdf/2401.14196.pdf"),
        ("42 Phi-1.5 Textbooks Are All You Need II Technical Report", "https://arxiv.org/pdf/2309.05463.pdf"),
        ("43 L2CEval: Evaluating Language-to-Code Generation Capabilities of Large Language Models", "https://arxiv.org/pdf/2309.17446.pdf")
    ],
    "IV. Tokenization for Code": [
        ("44 SentencePiece A Simple and Language Independent Subword Tokenizer", "https://arxiv.org/pdf/1808.06226.pdf"),
        ("45 Byte Pair Encoding BPE Original Neural Machine Translation", "https://arxiv.org/pdf/1508.07909.pdf"),
        ("46 Unigram Language Model for Tokenization", "https://arxiv.org/pdf/1804.10959.pdf"),
        ("47 Tokenization Effects in Code Language Modeling", "https://arxiv.org/pdf/2308.01417.pdf"),
        ("48 How Different Tokenization Algorithms Impact LLMs and Transformer Models for Binary Code Analysis", "https://arxiv.org/pdf/2511.03825.pdf"),
    ],
    "V. Long Context & Code-Specific Improvements Bonus": [
        ("49 Long-context LLMs Struggle with Long In-context Learning", "https://arxiv.org/pdf/2404.02060.pdf"),
        ("50 Advancing Transformer Architecture in Long-Context Large Language Models", "https://arxiv.org/pdf/2311.12351.pdf"),
        ("51 Lost in the Middle How Language Models Use Long Contexts", "https://arxiv.org/pdf/2307.03172.pdf"),
        ("52 GSM-Infinite How Do Your LLMs Behave over Infinitely Increasing Context Length", "https://arxiv.org/pdf/2502.05252.pdf"),
        ("53 BABILong Testing the Limits of LLMs with Long Context Reasoning", "https://arxiv.org/pdf/2406.10149.pdf")
    ]
}


# ===============================
# UTILITIES
# ===============================

def sanitize_filename(name):
    return "".join(c for c in name if c not in r'\/:*?"<>|').strip()


def download_file(session, url, filepath):
    temp_path = filepath + ".part"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, stream=True, headers=headers, timeout=30)
            response.raise_for_status()

            total = int(response.headers.get("content-length", 0))

            with open(temp_path, "wb") as file:
                if total == 0:
                    # Unknown size
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                else:
                    with tqdm(
                        total=total,
                        unit="iB",
                        unit_scale=True,
                        desc=os.path.basename(filepath),
                    ) as bar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                file.write(chunk)
                                bar.update(len(chunk))

            os.replace(temp_path, filepath)
            print(f"✔ Downloaded: {os.path.basename(filepath)}")
            return True

        except Exception as e:
            print(f"⚠ Attempt {attempt+1}/{MAX_RETRIES} failed: {e}")

            if os.path.exists(temp_path):
                os.remove(temp_path)

            if attempt < MAX_RETRIES - 1:
                sleep_time = 2 ** attempt
                print(f"   Retrying in {sleep_time}s...")
                time.sleep(sleep_time)

    print(f"❌ Failed permanently: {url}")
    return False


# ===============================
# MAIN
# ===============================

def main():
    os.makedirs(BASE_DIR, exist_ok=True)

    total_downloaded = 0
    total_failed = 0
    total_skipped = 0
    total_unavailable = 0

    session = requests.Session()

    print("🚀 Starting paper download process...")
    print(f"📁 Target directory: {BASE_DIR}\n")

    for category, paper_list in papers.items():
        category_path = os.path.join(BASE_DIR, sanitize_filename(category))
        os.makedirs(category_path, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"📂 Category: {category}")
        print(f"{'='*60}")

        for idx, (title, url) in enumerate(paper_list, start=1):
            # Strip first 3 characters (manual number + space)
            clean_title = title[3:].strip()
            safe_title = sanitize_filename(clean_title)

            # Loop numbering for the filename
            filename = f"{idx:02d}. {safe_title}.pdf"
            filepath = os.path.join(category_path, filename)

            # Skip if no valid URL provided
            if not url or url.strip() == "":
                print(f"⊘ No URL available: {filename}")
                total_unavailable += 1
                continue

            if os.path.exists(filepath):
                print(f"✔ Already exists: {filename}")
                total_skipped += 1
                continue

            print(f"⬇ Downloading: {filename}")

            success = download_file(session, url, filepath)

            if success:
                total_downloaded += 1
            else:
                total_failed += 1

            time.sleep(DELAY_BETWEEN_DOWNLOADS)

    print("\n" + "="*60)
    print("📊 DOWNLOAD SUMMARY")
    print("="*60)
    print(f"✅ Downloaded        : {total_downloaded}")
    print(f"⏭️ Skipped (exists)  : {total_skipped}")
    print(f"⊘ Not available      : {total_unavailable}")
    print(f"❌ Failed            : {total_failed}")
    print(f"📄 Total attempted   : {total_downloaded + total_failed}")
    print("="*60 + "\n")

    if total_unavailable > 0:
        print("\nℹ️  Some papers don't have public arXiv PDFs available.")
        print("   These may be behind paywalls or not yet published.")


if __name__ == "__main__":
    main()
