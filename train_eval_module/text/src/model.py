"""
Text Classification Model - Dùng AutoModelForSequenceClassification chuẩn HuggingFace.

Phương pháp đơn giản nhưng hiệu quả:
1. Input: 1 chuỗi text dài (các comment đã được gộp bằng [SEP])
2. Tokenizer tự động truncate về max_length (512)
3. Model pretrained được fine-tune trực tiếp
4. Giữ nguyên 100% pretrained weights, chỉ train classification head
"""

from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig


def get_text_model_and_tokenizer(model_name, dropout_rate=0.1, num_labels=2):
    """
    Load model và tokenizer chuẩn HuggingFace.

    Args:
        model_name: Tên model pretrained (e.g., "uitnlp/CafeBERT", "xlm-roberta-base")
        dropout_rate: Dropout rate cho classifier head
        num_labels: Số class (2 cho binary classification)

    Returns:
        model: AutoModelForSequenceClassification
        tokenizer: AutoTokenizer
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Load config để xác định loại model
    config = AutoConfig.from_pretrained(model_name, num_labels=num_labels)

    # DistilBERT dùng các tham số dropout khác
    if "distilbert" in model_name.lower():
        config.dropout = dropout_rate
        config.seq_classif_dropout = dropout_rate
    else:
        # BERT, RoBERTa, XLM-R, CafeBERT
        config.hidden_dropout_prob = dropout_rate
        config.attention_probs_dropout_prob = dropout_rate

    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        config=config,
    )

    return model, tokenizer
