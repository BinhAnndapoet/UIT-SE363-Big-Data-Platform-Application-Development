import os
import glob


def find_latest_checkpoint(output_dir):
    """
    Tìm checkpoint mới nhất trong thư mục output.
    """
    if not os.path.exists(output_dir):
        return None

    checkpoints = glob.glob(os.path.join(output_dir, "checkpoint-*"))
    if not checkpoints:
        return None

    # Sắp xếp theo số step (checkpoint-100, checkpoint-200)
    checkpoints.sort(key=lambda x: int(x.split("-")[-1]))
    return checkpoints[-1]


def find_best_checkpoint(output_dir):
    """
    Tìm folder 'best_checkpoint'
    """
    best_path = os.path.join(output_dir, "best_checkpoint")
    if os.path.exists(best_path):
        return best_path
    return None
