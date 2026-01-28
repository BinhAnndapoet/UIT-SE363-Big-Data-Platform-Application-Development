import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import re
import sys
import os

# Thêm đường dẫn để import config từ thư mục cha
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class AILabeler:
    def __init__(self):
        if not config.ENABLE_AI_LABELING:
            self.model = None
            return

        print(f"⏳ Loading AI Model ({config.MODEL_NAME})...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                config.MODEL_NAME, trust_remote_code=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                config.MODEL_NAME,
                torch_dtype="auto",
                device_map="auto",
                trust_remote_code=True,
            )
            print("✅ Model Loaded!")
        except Exception as e:
            print(f"⚠️ Model Load Failed: {e}")
            self.model = None

    def predict(self, text):
        """
        Dự đoán nhãn và độ tin cậy động bằng cách bóc tách JSON từ Output của LLM.
        """
        if not self.model or not text:
            # Mặc định confidence 0.0 nếu không có model
            return {"label": "safe", "confidence": 0.0}

        # Prompt yêu cầu JSON nghiêm ngặt
        prompt = f"""Phân loại nội dung sau là 'safe' (an toàn) hoặc 'harmful' (độc hại).
        Nội dung: "{text}"
        Yêu cầu trả về đúng định dạng JSON: {{"label": "safe/harmful", "confidence": <giá trị số thực từ 0 đến 1>}}"""

        messages = [{"role": "user", "content": prompt}]
        input_text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer([input_text], return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.1,  # Nhiệt độ thấp để output ổn định
                top_p=0.9,
            )

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[
            0
        ]

        # --- BÓC TÁCH JSON ĐỘNG (LOGIC MỚI) ---
        try:
            # Tìm khối JSON trong chuỗi phản hồi bằng Regex
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())

                # 1. Đồng bộ nhãn về lowercase chuẩn: safe/harmful
                raw_label = str(result.get("label", "safe")).lower()
                clean_label = "harmful" if "harm" in raw_label else "safe"

                # 2. Lấy confidence thực tế từ mô hình (Quan trọng)
                confidence = float(result.get("confidence", 0.5))

                return {"label": clean_label, "confidence": confidence}

            # Fallback thông minh: Nếu không tìm thấy JSON, kiểm tra từ khóa
            lower_res = response.lower()
            if "harmful" in lower_res or "độc hại" in lower_res:
                return {"label": "harmful", "confidence": 0.75}  # Confidence ước lượng

        except Exception as e:
            print(f"⚠️ Parsing Error: {e} | Response: {response}")

        # Fallback an toàn cuối cùng
        return {"label": "safe", "confidence": 0.5}
