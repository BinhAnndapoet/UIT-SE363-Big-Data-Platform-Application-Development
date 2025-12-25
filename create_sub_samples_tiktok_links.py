# %%
import os
import pandas as pd
import matplotlib.pyplot as plt

# ---------------- CONFIG ----------------
# Số lượng mẫu mong muốn
TARGET_HARMFUL = 650
TARGET_NOT_HARMFUL = 350

# --- Tự động tìm đường dẫn ---
ROOT_DIR = (
    os.path.dirname(os.path.abspath(__file__))
    if "__file__" in globals()
    else os.getcwd()
)
CRAWL_DIR = os.path.join(ROOT_DIR, "data", "crawl")

# File Input (File master lớn 4000 dòng)
INPUT_CSV_BIG = os.path.join(CRAWL_DIR, "tiktok_links.csv")

# File Output (File mẫu 1000 dòng)
OUTPUT_CSV_SMALL = os.path.join(CRAWL_DIR, "sub_tiktok_links.csv")

# Dùng một số cố định (42) để đảm bảo script luôn lấy
# cùng một mẫu ngẫu nhiên mỗi khi chạy.
RANDOM_SEED = 42

print("ROOT_DIR: ", ROOT_DIR)
print("CRAWL_DIR: ", CRAWL_DIR)
print("INPUT_CSV_BIG: ", INPUT_CSV_BIG)
print("OUTPUT_CSV_SMALL: ", OUTPUT_CSV_SMALL)


# %% [markdown]
# # EDA function

# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def eda_tiktok_advanced_labelwise(df, top_n_per_label=5, random_seed=42):
    """
    Hàm EDA nâng cao cho dataset TikTok với top hashtags riêng theo label.

    Args:
        df (pd.DataFrame): DataFrame có các cột ['hashtag', 'link', 'label']
        top_n_per_label (int): số lượng hashtag hàng đầu cho mỗi label
        random_seed (int): để cố định khi cần shuffle
    """
    print("=== Thông tin cơ bản ===")
    display(df.info())
    print("\n=== 10 dòng đầu tiên ===")
    display(df.head(10))

    print("\n=== Thống kê mô tả ===")
    display(df.describe(include="all"))

    # --- Phân bố nhãn ---
    print("\n=== Phân bố nhãn (label) ===")
    label_counts = df["label"].value_counts()
    print(label_counts)

    plt.figure(figsize=(6, 6))
    label_counts.plot(
        kind="pie", autopct="%1.1f%%", startangle=90, colors=["#66b3ff", "#ff9999"]
    )
    plt.title("Phân bố nhãn (label)")
    plt.ylabel("")
    plt.show()

    # --- Top hashtags riêng cho từng label ---
    # --- Top hashtags riêng cho từng label ---
    print(f"\n=== Top {top_n_per_label} hashtags cho từng label ===")
    top_hashtags_list = []
    for lbl in df["label"].unique():
        top_lbl = df[df["label"] == lbl]["hashtag"].value_counts().head(top_n_per_label)
        print(f"\nLabel = {lbl}:")
        display(top_lbl)
        top_hashtags_list.extend(top_lbl.index.tolist())

    # Lấy unique hashtags từ cả 2 label
    top_hashtags_list = list(set(top_hashtags_list))

    # --- Chuẩn bị data cho barplot theo label ---
    df_top_plot = df[df["hashtag"].isin(top_hashtags_list)]
    # Tạo bảng count theo hashtag và label
    top_counts = (
        df_top_plot.groupby(["hashtag", "label"]).size().reset_index(name="count")
    )

    # --- Bar chart với 2 màu cho 2 label ---
    plt.figure(figsize=(10, 6))
    sns.barplot(
        x="count",
        y="hashtag",
        hue="label",
        data=top_counts,
        palette=["#66b3ff", "#ff9999"],
    )
    plt.xlabel("Số lượng")
    plt.ylabel("Hashtag")
    plt.title(f"Tổng số lượng hashtags top {top_n_per_label} mỗi label")
    plt.legend(title="Label")
    plt.show()

    # --- Mối quan hệ label vs top hashtags ---
    df_top = df[df["hashtag"].isin(top_hashtags_list)]
    pivot = df_top.pivot_table(
        index="hashtag", columns="label", aggfunc="size", fill_value=0
    )
    print("\n=== Pivot table label vs hashtag ===")
    display(pivot)

    # Stacked bar chart với legend
    ax = pivot.plot(kind="bar", stacked=True, figsize=(12, 6), colormap="viridis")
    plt.title(f"Label vs Top {top_n_per_label} hashtags mỗi label")
    plt.ylabel("Số lượng")
    plt.xlabel("Hashtag")
    plt.xticks(rotation=45)
    plt.legend(title="Label")
    plt.show()


# %% [markdown]
# # 1. Đọc file

# %%
print(f"Đang đọc file sample lớn: {INPUT_CSV_BIG}...")


try:
    df = pd.read_csv(INPUT_CSV_BIG)
    eda_tiktok_advanced_labelwise(df, top_n_per_label=10)
except FileNotFoundError:
    print(f"LỖI: Không tìm thấy file {INPUT_CSV_BIG}")
    print("Bạn cần chạy script 'find_tiktok_links.py' trước để tạo file này.")
except Exception as e:
    print(f"Lỗi khi đọc file CSV: {e}")

print(f"Đã tải {len(df)} link.")

# %% [markdown]
# # 2. Phân loại

# %%
# --- Chỉ lấy link video ---
df = df[df["link"].str.contains("/video/")]


# --- Lọc theo label ---
df_harmful = df[df["label"] == "harmful"]
df_not_harmful = df[df["label"] == "not_harmful"]

print(f"-> Tìm thấy {len(df_harmful)} harmful và {len(df_not_harmful)} not_harmful.")

# %%
print("Harmful label")
display(df_harmful.head(5))

print("Not harmful label")
display(df_not_harmful.head(5))

# %%
# 3. Xử lý nếu không đủ mẫu
# (Ví dụ: file master chỉ có 300 'harmful' dù ta muốn 450)
n_harmful = min(TARGET_HARMFUL, len(df_harmful))
n_not_harmful = min(TARGET_NOT_HARMFUL, len(df_not_harmful))

print(f"-> Sẽ lấy {n_harmful} harmful và {n_not_harmful} not_harmful.")

# %%
# 4. Lấy mẫu (sample)
df_harmful_sample = df_harmful.sample(n=n_harmful, random_state=RANDOM_SEED)
df_not_harmful_sample = df_not_harmful.sample(n=n_not_harmful, random_state=RANDOM_SEED)
print("df_harmful_sample:")
display(df_harmful_sample.describe(include="all"))
print("df_not_harmful_sample:")
display(df_not_harmful_sample.describe(include="all"))

# %% [markdown]
# # 5. Gộp lại

# %%
df_final = pd.concat([df_harmful_sample, df_not_harmful_sample], ignore_index=True)

# %% [markdown]
# # 6. TRỘN LẪN (SHUFFLE) - Rất quan trọng

# %%
# Trộn các dòng harmful và not_harmful với nhau
df_shuffled = df_final.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)

print("df_final:")
display(df_final.head(5))
display(df_final.info())
display(df_final.describe(include="all"))

# %% [markdown]
# # 7. Lưu file CSV

# %%

try:
    df_shuffled.to_csv(OUTPUT_CSV_SMALL, index=False, encoding="utf-8-sig")
    print(f"\n✅ HOÀN TẤT!")
    print(f"Đã lưu {len(df_shuffled)} mẫu (đã trộn) vào file:")
    print(f"{OUTPUT_CSV_SMALL}")
except Exception as e:
    print(f"\nLỖI khi lưu file CSV: {e}")


# %% [markdown]
# # 8. KIỂM TRA DỮ LIỆU

# %%
print("\n" + "=" * 40)
print("GIAI ĐOẠN 8: KIỂM TRA DỮ LIỆU (VERIFICATION)")
print("=" * 40)
try:
    print(f"Đang đọc lại file vừa lưu: {os.path.basename(OUTPUT_CSV_SMALL)}...\n")
    df_verify = pd.read_csv(OUTPUT_CSV_SMALL)
    eda_tiktok_advanced_labelwise(df=df_verify, top_n_per_label=10)

    print("\n✅ Kiểm tra hoàn tất.")

except Exception as e:
    print(f"Lỗi khi kiểm tra dữ liệu: {e}")
