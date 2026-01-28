import logging
import os
import sys
from datetime import datetime
from transformers import TrainerCallback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs.paths import LOG_DIR


def setup_logger(name, sub_dir=None):
    """
    Khởi tạo Logger.
    Args:
        name: Tên logger/file log.
        sub_dir: Đường dẫn con (vd: 'video/logs').
                 Nếu sub_dir là đường dẫn tuyệt đối thì dùng luôn.
                 Nếu là tương đối thì nối với LOG_DIR gốc.
    """
    if sub_dir:
        if os.path.isabs(sub_dir):
            final_log_dir = sub_dir
        else:
            final_log_dir = os.path.join(LOG_DIR, sub_dir)
    else:
        final_log_dir = LOG_DIR

    # Tự động tạo toàn bộ cây thư mục cha nếu chưa tồn tại
    os.makedirs(final_log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(final_log_dir, f"{name}_{timestamp}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    print(f"📄 Log file created at: {log_file}")
    return logger


class FileLoggingCallback(TrainerCallback):
    """Callback đẩy log từ Trainer vào file .log"""

    def __init__(self, logger):
        self.logger = logger

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            log_items = []
            for k, v in logs.items():
                if isinstance(v, float):
                    if "learning_rate" in k or v < 0.0001:
                        log_items.append(f"{k}: {v:.2e}")
                    else:
                        log_items.append(f"{k}: {v:.4f}")
                else:
                    log_items.append(f"{k}: {v}")
            message = f"Step {state.global_step} | " + " | ".join(log_items)
            self.logger.info(message)
