#!/usr/bin/env python
"""
Analyze text data BEFORE and AFTER split to understand:
1. How many videos/comments are dropped
2. Text length distribution per video
3. Label distribution changes
4. Sample text content for debugging
"""

import os
import sys
import pandas as pd
import numpy as np
from collections import Counter

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from configs.paths import TEXT_LABEL_FILE, PROCESSED_DIR


def load_raw_text():
    """Load original text CSV (before any processing)"""
    if os.path.exists(TEXT_LABEL_FILE):
        df = pd.read_csv(TEXT_LABEL_FILE, dtype=str)
        return df
    else:
        print(f"❌ Raw text CSV not found: {TEXT_LABEL_FILE}")
        return None


def load_split_text(split="train"):
    """Load processed split CSV"""
    split_map = {
        "train": "train_split.csv",
        "val": "eval_split.csv",
        "test": "test_split.csv",
    }
    path = os.path.join(PROCESSED_DIR, "text", split_map[split])
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
        return df
    else:
        print(f"❌ Split CSV not found: {path}")
        return None


def analyze_raw_text(df):
    """Analyze raw text data"""
    print("\n" + "=" * 60)
    print("📊 RAW TEXT DATA ANALYSIS")
    print("=" * 60)

    print(f"\n📁 Total rows: {len(df)}")
    print(f"📁 Columns: {list(df.columns)}")

    # Check video_id column
    video_col = None
    for col in ["video_id", "Video ID", "videoID"]:
        if col in df.columns:
            video_col = col
            break

    if video_col:
        unique_videos = df[video_col].nunique()
        print(f"\n🎬 Unique video_ids: {unique_videos}")

        # Comments per video distribution
        comments_per_video = df.groupby(video_col).size()
        print(f"\n📝 Comments per video:")
        print(f"   - Min: {comments_per_video.min()}")
        print(f"   - Max: {comments_per_video.max()}")
        print(f"   - Mean: {comments_per_video.mean():.2f}")
        print(f"   - Median: {comments_per_video.median():.0f}")

    # Check text column
    text_col = None
    for col in ["text", "comment", "Comment", "content"]:
        if col in df.columns:
            text_col = col
            break

    if text_col:
        # Text length stats
        df["text_len"] = df[text_col].fillna("").apply(len)
        print(f"\n📏 Text length (characters):")
        print(f"   - Min: {df['text_len'].min()}")
        print(f"   - Max: {df['text_len'].max()}")
        print(f"   - Mean: {df['text_len'].mean():.2f}")

        # Empty texts
        empty_texts = (df[text_col].isna() | (df[text_col] == "")).sum()
        print(f"\n⚠️  Empty/null texts: {empty_texts} ({100*empty_texts/len(df):.2f}%)")

    # Check label column
    label_col = None
    for col in ["label", "Label", "harmful", "is_harmful"]:
        if col in df.columns:
            label_col = col
            break

    if label_col:
        label_counts = df[label_col].value_counts()
        print(f"\n🏷️  Label distribution:")
        for label, count in label_counts.items():
            print(f"   - {label}: {count} ({100*count/len(df):.2f}%)")

    return video_col, text_col, label_col


def analyze_split_text(df, split_name):
    """Analyze a split dataset"""
    print(f"\n" + "-" * 60)
    print(f"📊 {split_name.upper()} SPLIT ANALYSIS")
    print("-" * 60)

    print(f"\n📁 Total rows (videos): {len(df)}")
    print(f"📁 Columns: {list(df.columns)}")

    # video_id
    if "video_id" in df.columns:
        unique_videos = df["video_id"].nunique()
        print(f"🎬 Unique video_ids: {unique_videos}")

    # Text analysis
    if "text" in df.columns:
        df["text_len"] = df["text"].fillna("").apply(len)
        df["text_tokens_approx"] = df["text_len"] / 4  # rough token estimate

        print(f"\n📏 Aggregated text length (characters):")
        print(f"   - Min: {df['text_len'].min()}")
        print(f"   - Max: {df['text_len'].max()}")
        print(f"   - Mean: {df['text_len'].mean():.2f}")
        print(f"   - Median: {df['text_len'].median():.0f}")

        print(f"\n🔤 Approx tokens (chars/4):")
        print(f"   - Mean: {df['text_tokens_approx'].mean():.0f}")
        print(f"   - Max: {df['text_tokens_approx'].max():.0f}")

        # How many exceed 512 tokens?
        exceed_512 = (df["text_tokens_approx"] > 512).sum()
        print(
            f"   - Exceeding 512 tokens: {exceed_512} ({100*exceed_512/len(df):.2f}%)"
        )

        # Count [cmt] separators (comment boundaries)
        df["num_comments"] = df["text"].fillna("").apply(lambda x: x.count("[cmt]") + 1)
        print(f"\n💬 Comments per video (from [cmt] count):")
        print(f"   - Min: {df['num_comments'].min()}")
        print(f"   - Max: {df['num_comments'].max()}")
        print(f"   - Mean: {df['num_comments'].mean():.2f}")

    # Label distribution
    if "label" in df.columns:
        # Convert to int for counting
        df["label_int"] = (
            pd.to_numeric(df["label"], errors="coerce").fillna(-1).astype(int)
        )
        label_counts = df["label_int"].value_counts().sort_index()
        print(f"\n🏷️  Label distribution:")
        for label, count in label_counts.items():
            label_name = (
                "Harmful"
                if label == 1
                else ("Not Harmful" if label == 0 else "Unknown")
            )
            print(f"   - {label} ({label_name}): {count} ({100*count/len(df):.2f}%)")


def compare_raw_vs_splits(df_raw, video_col, df_train, df_val, df_test):
    """Compare raw data vs splits to see what's dropped"""
    print("\n" + "=" * 60)
    print("🔍 COMPARISON: RAW vs SPLITS")
    print("=" * 60)

    if df_raw is None or video_col is None:
        print("❌ Cannot compare - raw data not loaded properly")
        return

    raw_videos = set(df_raw[video_col].dropna().unique())
    print(f"\n📊 Raw unique videos: {len(raw_videos)}")

    split_videos = set()
    if df_train is not None and "video_id" in df_train.columns:
        train_videos = set(df_train["video_id"].dropna().unique())
        split_videos.update(train_videos)
        print(f"📊 Train videos: {len(train_videos)}")

    if df_val is not None and "video_id" in df_val.columns:
        val_videos = set(df_val["video_id"].dropna().unique())
        split_videos.update(val_videos)
        print(f"📊 Val videos: {len(val_videos)}")

    if df_test is not None and "video_id" in df_test.columns:
        test_videos = set(df_test["video_id"].dropna().unique())
        split_videos.update(test_videos)
        print(f"📊 Test videos: {len(test_videos)}")

    print(f"\n📊 Total videos in splits: {len(split_videos)}")

    # Find dropped videos
    dropped_videos = raw_videos - split_videos
    print(f"\n⚠️  Videos DROPPED (in raw but not in splits): {len(dropped_videos)}")

    if len(dropped_videos) > 0 and len(dropped_videos) <= 20:
        print(f"   Dropped video_ids: {list(dropped_videos)[:20]}")

    # Find added videos (shouldn't happen normally)
    added_videos = split_videos - raw_videos
    if len(added_videos) > 0:
        print(f"\n⚠️  Videos ADDED (in splits but not in raw): {len(added_videos)}")


def show_sample_texts(df, split_name, n=3):
    """Show sample texts from a split"""
    print(f"\n" + "-" * 60)
    print(f"📝 SAMPLE TEXTS FROM {split_name.upper()} (first {n})")
    print("-" * 60)

    if df is None or "text" not in df.columns:
        print("❌ No text column found")
        return

    for i, row in df.head(n).iterrows():
        video_id = row.get("video_id", "N/A")
        label = row.get("label", "N/A")
        text = row.get("text", "")[:500]  # First 500 chars

        print(f"\n[{i+1}] Video: {video_id} | Label: {label}")
        print(f"    Text ({len(row.get('text', ''))} chars): {text}...")


def main():
    print("🔬 TEXT DATA ANALYSIS TOOL")
    print("=" * 60)

    # Load raw text
    print("\n📂 Loading raw text data...")
    df_raw = load_raw_text()
    video_col, text_col, label_col = None, None, None
    if df_raw is not None:
        video_col, text_col, label_col = analyze_raw_text(df_raw)

    # Load splits
    print("\n📂 Loading split data...")
    df_train = load_split_text("train")
    df_val = load_split_text("val")
    df_test = load_split_text("test")

    # Analyze each split
    if df_train is not None:
        analyze_split_text(df_train, "train")
    if df_val is not None:
        analyze_split_text(df_val, "val")
    if df_test is not None:
        analyze_split_text(df_test, "test")

    # Compare raw vs splits
    compare_raw_vs_splits(df_raw, video_col, df_train, df_val, df_test)

    # Show sample texts
    if df_train is not None:
        show_sample_texts(df_train, "train", n=2)
    if df_test is not None:
        show_sample_texts(df_test, "test", n=2)

    print("\n" + "=" * 60)
    print("✅ Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
