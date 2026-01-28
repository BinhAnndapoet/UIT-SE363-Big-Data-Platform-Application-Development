import numpy as np
import random
import cv2

try:
    from decord import VideoReader, cpu
except ImportError:
    raise ImportError("Hãy cài đặt decord: pip install decord")


def extract_frames(video_path, num_frames=16, resize=224):
    """
    Trích xuất frames sử dụng DECORD.
    Uniform Sampling -> Batch Read -> Fallback Loop -> Padding.
    """
    try:
        vr = VideoReader(video_path, ctx=cpu(0), width=-1, height=-1)
        v_len = len(vr)

        if v_len <= 0:
            return None

        indices = np.linspace(0, v_len - 1, num_frames).astype(int)
        frames_list = []

        try:
            frames_decord = vr.get_batch(indices).asnumpy()
            for frame in frames_decord:
                frames_list.append(frame)
        except Exception:
            for i in indices:
                try:
                    frame = vr[i].asnumpy()
                    frames_list.append(frame)
                except:
                    continue

        if len(frames_list) == 0:
            return None

        processed_frames = []
        for frame in frames_list:
            frame_resized = cv2.resize(frame, (resize, resize))
            processed_frames.append(frame_resized)

        while len(processed_frames) < num_frames:
            if len(processed_frames) > 0:
                processed_frames.append(processed_frames[-1].copy())
            else:
                processed_frames.append(np.zeros((resize, resize, 3), dtype=np.uint8))

        return processed_frames

    except Exception as e:
        return None


def augment_frames(frames):
    """
    Data Augmentation: Random Crop, Flip, Color Jitter.
    """
    augmented = []
    do_flip = random.random() > 0.5
    h, w, _ = frames[0].shape
    scale = random.uniform(0.8, 1.0)
    new_h, new_w = int(h * scale), int(w * scale)
    top = random.randint(0, h - new_h)
    left = random.randint(0, w - new_w)
    brightness = random.uniform(0.7, 1.3)
    contrast = random.uniform(0.7, 1.3)

    for frame in frames:
        frame = frame[top : top + new_h, left : left + new_w]
        frame = cv2.resize(frame, (224, 224))
        if do_flip:
            frame = np.fliplr(frame)
        frame = frame.astype(np.float32)
        frame = frame * brightness
        frame = (frame - 128) * contrast + 128
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        augmented.append(frame)

    return augmented
