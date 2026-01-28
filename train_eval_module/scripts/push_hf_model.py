#!/usr/bin/env python3
"""
Push TikTok Safety Models to HuggingFace Hub

Usage:
    # Interactive mode
    python push_hf_model.py

    # CLI mode
    python push_hf_model.py --model-type text --model-path path/to/checkpoint --repo-id username/repo-name

Requirements:
    pip install huggingface_hub transformers torch
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_available_checkpoints(model_type: str) -> list:
    """Find available checkpoints for a model type."""
    output_dir = PROJECT_ROOT / model_type / "output"
    checkpoints = []
    
    if not output_dir.exists():
        return checkpoints
    
    # Search for best_checkpoint folders
    for model_dir in output_dir.iterdir():
        if model_dir.is_dir():
            # Check for train/best_checkpoint structure
            checkpoint_path = model_dir / "train" / "best_checkpoint"
            if checkpoint_path.exists():
                checkpoints.append(str(checkpoint_path))
            # Check for direct best_checkpoint
            checkpoint_path = model_dir / "best_checkpoint"
            if checkpoint_path.exists():
                checkpoints.append(str(checkpoint_path))
    
    return checkpoints


def push_text_model(model_path: str, repo_id: str, private: bool = False):
    """Push text classification model to HuggingFace Hub."""
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    from huggingface_hub import HfApi
    
    print(f"📦 Loading text model from: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    
    print(f"🚀 Pushing to HuggingFace Hub: {repo_id}")
    
    # Push model and tokenizer
    model.push_to_hub(repo_id, private=private)
    tokenizer.push_to_hub(repo_id, private=private)
    
    # Create model card
    model_card = f"""---
language:
- vi
- en
tags:
- text-classification
- content-moderation
- tiktok
- pytorch
license: mit
datasets:
- custom
metrics:
- f1
- accuracy
---

# TikTok Content Safety - Text Classifier

This model classifies TikTok video text content (captions, comments) as **safe** or **harmful**.

## Usage

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("{repo_id}")
model = AutoModelForSequenceClassification.from_pretrained("{repo_id}")

text = "your text here"
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
outputs = model(**inputs)
prediction = outputs.logits.argmax(-1).item()  # 0=safe, 1=harmful
```

## Model Details
- **Base Model**: XLM-RoBERTa / CafeBERT
- **Task**: Binary classification (safe/harmful)
- **Training Data**: TikTok video metadata (Vietnamese + English)
"""
    
    api = HfApi()
    api.upload_file(
        path_or_fileobj=model_card.encode(),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="model",
    )
    
    print(f"✅ Model pushed successfully: https://huggingface.co/{repo_id}")
    return True


def push_video_model(model_path: str, repo_id: str, private: bool = False):
    """Push video classification model to HuggingFace Hub."""
    from transformers import AutoImageProcessor, VideoMAEForVideoClassification
    from huggingface_hub import HfApi
    
    print(f"📦 Loading video model from: {model_path}")
    processor = AutoImageProcessor.from_pretrained(model_path)
    model = VideoMAEForVideoClassification.from_pretrained(model_path)
    
    print(f"🚀 Pushing to HuggingFace Hub: {repo_id}")
    
    model.push_to_hub(repo_id, private=private)
    processor.push_to_hub(repo_id, private=private)
    
    # Create model card
    model_card = f"""---
language:
- vi
- en
tags:
- video-classification
- content-moderation
- tiktok
- videomae
- pytorch
license: mit
datasets:
- custom
metrics:
- f1
- accuracy
---

# TikTok Content Safety - Video Classifier

This model classifies TikTok video frames as **safe** or **harmful**.

## Usage

```python
from transformers import AutoImageProcessor, VideoMAEForVideoClassification
from decord import VideoReader, cpu
import numpy as np

processor = AutoImageProcessor.from_pretrained("{repo_id}")
model = VideoMAEForVideoClassification.from_pretrained("{repo_id}")

# Load video and sample 16 frames
vr = VideoReader("video.mp4", ctx=cpu(0))
indices = np.linspace(0, len(vr) - 1, 16).astype(int)
frames = list(vr.get_batch(indices).asnumpy())

inputs = processor(frames, return_tensors="pt")
outputs = model(**inputs)
prediction = outputs.logits.argmax(-1).item()  # 0=safe, 1=harmful
```

## Model Details
- **Base Model**: VideoMAE (MCG-NJU/videomae-base-finetuned-kinetics)
- **Task**: Binary classification (safe/harmful)
- **Input**: 16 frames, 224x224
"""
    
    api = HfApi()
    api.upload_file(
        path_or_fileobj=model_card.encode(),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="model",
    )
    
    print(f"✅ Model pushed successfully: https://huggingface.co/{repo_id}")
    return True


def push_fusion_model(model_path: str, repo_id: str, private: bool = False):
    """Push fusion (multimodal) model to HuggingFace Hub."""
    from huggingface_hub import HfApi
    import shutil
    import json
    
    print(f"📦 Preparing fusion model from: {model_path}")
    
    api = HfApi()
    
    # Create repo if not exists
    try:
        api.create_repo(repo_id=repo_id, private=private, exist_ok=True)
    except Exception as e:
        print(f"⚠️ Repo creation note: {e}")
    
    # Upload all files in checkpoint
    for file in Path(model_path).iterdir():
        if file.is_file():
            print(f"   Uploading: {file.name}")
            api.upload_file(
                path_or_fileobj=str(file),
                path_in_repo=file.name,
                repo_id=repo_id,
                repo_type="model",
            )
    
    # Upload fusion config
    fusion_config = {
        "model_type": "late_fusion",
        "fusion_type": "attention",
        "text_feat_dim": 768,
        "video_feat_dim": 768,
        "fusion_hidden": 256,
        "text_weight": 0.5,
        "video_weight": 0.5,
        "num_labels": 2,
        "label2id": {"safe": 0, "harmful": 1},
        "id2label": {0: "safe", 1: "harmful"},
    }
    
    api.upload_file(
        path_or_fileobj=json.dumps(fusion_config, indent=2).encode(),
        path_in_repo="fusion_config.json",
        repo_id=repo_id,
        repo_type="model",
    )
    
    # Create model card
    model_card = f"""---
language:
- vi
- en
tags:
- multimodal
- text-video-fusion
- content-moderation
- tiktok
- pytorch
license: mit
datasets:
- custom
metrics:
- f1
- accuracy
---

# TikTok Content Safety - Multimodal Fusion Model

This model combines **text** and **video** features using **Late Fusion with Cross-Attention** to classify TikTok content as **safe** or **harmful**.

## Architecture

```
Text Backbone (XLM-RoBERTa) → Text Features (768-dim)
Video Backbone (VideoMAE)    → Video Features (768-dim)
                                  ↓
                         Cross-Attention Fusion
                                  ↓
                         Gating Mechanism
                                  ↓
                        Classifier (2 classes)
```

## Usage

This is a custom model. You need to download and use the `LateFusionModel` class:

```python
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file
import torch.nn as nn

# Download model weights
weights_path = hf_hub_download(repo_id="{repo_id}", filename="model.safetensors")
config_path = hf_hub_download(repo_id="{repo_id}", filename="fusion_config.json")

# Load config
import json
with open(config_path) as f:
    config = json.load(f)

# Initialize and load model (using LateFusionModel class from your codebase)
# model = LateFusionModel(config)
# model.load_state_dict(load_file(weights_path))
```

## Model Details
- **Text Backbone**: XLM-RoBERTa-base
- **Video Backbone**: VideoMAE-base
- **Fusion**: Cross-Attention with Gating
- **Task**: Binary classification (safe/harmful)
"""
    
    api.upload_file(
        path_or_fileobj=model_card.encode(),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="model",
    )
    
    print(f"✅ Fusion model pushed successfully: https://huggingface.co/{repo_id}")
    return True


def interactive_menu():
    """Interactive menu for selecting and pushing models."""
    from huggingface_hub import login
    
    print("=" * 50)
    print("   TikTok Safety - Push Model to HuggingFace Hub")
    print("=" * 50)
    
    # Check for HF token
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        login(token=hf_token)
        print("✅ Logged in using HF_TOKEN environment variable")
    else:
        print("\n⚠️ No HF_TOKEN found. You may need to login first.")
        print("   Run: huggingface-cli login")
        print("   Or set HF_TOKEN environment variable\n")
        proceed = input("Continue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            return
    
    # Select model type
    print("\nSelect model type:")
    print("  1) Text (CafeBERT / XLM-RoBERTa)")
    print("  2) Video (VideoMAE)")
    print("  3) Fusion (Multimodal)")
    print("  q) Quit")
    
    choice = input("\nEnter choice [1-3/q]: ").strip()
    
    model_type_map = {"1": "text", "2": "video", "3": "fusion"}
    if choice == "q":
        return
    if choice not in model_type_map:
        print("❌ Invalid choice!")
        return
    
    model_type = model_type_map[choice]
    
    # Find available checkpoints
    checkpoints = get_available_checkpoints(model_type)
    
    if not checkpoints:
        print(f"\n❌ No checkpoints found for {model_type} in {PROJECT_ROOT / model_type / 'output'}")
        manual_path = input("Enter manual path (or q to quit): ").strip()
        if manual_path == "q":
            return
        checkpoints = [manual_path]
    
    print(f"\nAvailable checkpoints for {model_type}:")
    for i, cp in enumerate(checkpoints, 1):
        print(f"  {i}) {cp}")
    
    cp_choice = input(f"\nSelect checkpoint [1-{len(checkpoints)}]: ").strip()
    try:
        model_path = checkpoints[int(cp_choice) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid selection!")
        return
    
    # Get repo ID
    default_repo = f"KhoiBui/tiktok-{model_type}-classifier"
    repo_id = input(f"\nEnter HuggingFace repo ID [{default_repo}]: ").strip()
    if not repo_id:
        print("❌ Repo ID is required!")
        return
    
    # Private?
    private = input("Make repo private? (y/n) [n]: ").strip().lower() == 'y'
    
    # Confirm
    print(f"\n--- Summary ---")
    print(f"  Model Type: {model_type}")
    print(f"  Model Path: {model_path}")
    print(f"  Repo ID:    {repo_id}")
    print(f"  Private:    {private}")
    
    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Push
    try:
        if model_type == "text":
            push_text_model(model_path, repo_id, private)
        elif model_type == "video":
            push_video_model(model_path, repo_id, private)
        elif model_type == "fusion":
            push_fusion_model(model_path, repo_id, private)
    except Exception as e:
        print(f"❌ Error pushing model: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Push TikTok Safety Models to HuggingFace Hub")
    parser.add_argument("--model-type", choices=["text", "video", "fusion"], help="Model type")
    parser.add_argument("--model-path", help="Path to model checkpoint")
    parser.add_argument("--repo-id", help="HuggingFace repo ID (e.g., username/model-name)")
    parser.add_argument("--private", action="store_true", help="Make repo private")
    
    args = parser.parse_args()
    
    # If all args provided, run CLI mode
    if args.model_type and args.model_path and args.repo_id:
        from huggingface_hub import login
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            login(token=hf_token)
        
        if args.model_type == "text":
            push_text_model(args.model_path, args.repo_id, args.private)
        elif args.model_type == "video":
            push_video_model(args.model_path, args.repo_id, args.private)
        elif args.model_type == "fusion":
            push_fusion_model(args.model_path, args.repo_id, args.private)
    else:
        # Interactive mode
        interactive_menu()


if __name__ == "__main__":
    main()
