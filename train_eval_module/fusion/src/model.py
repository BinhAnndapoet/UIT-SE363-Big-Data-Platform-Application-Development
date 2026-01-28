"""
Late Fusion Model - Đơn giản hóa.
Text đã là 1 string concat, không cần CommentAggregator.
"""

import torch
import torch.nn as nn
from transformers import AutoModel


class LateFusionModel(nn.Module):
    def __init__(self, config):
        super().__init__()
        text_path = config["text_model_path"]
        video_path = config["video_model_path"]

        print(f"🏗️ Init Fusion Model (Text: {text_path}, Video: {video_path})")

        # 1. Load Backbones
        self.text_backbone = AutoModel.from_pretrained(text_path)
        self.video_backbone = AutoModel.from_pretrained(video_path)

        # 2. Unfreeze strategy - Unfreeze last N layers
        unfreeze_text_layers = config.get("unfreeze_text_layers", 0)  # 0 = full freeze
        unfreeze_video_layers = config.get("unfreeze_video_layers", 0)

        # Freeze all first
        for p in self.text_backbone.parameters():
            p.requires_grad = False
        for p in self.video_backbone.parameters():
            p.requires_grad = False

        # Unfreeze last N layers of text backbone
        if unfreeze_text_layers > 0:
            if hasattr(self.text_backbone, "encoder"):
                text_layers = self.text_backbone.encoder.layer
            elif hasattr(self.text_backbone, "transformer"):
                text_layers = self.text_backbone.transformer.layer
            else:
                text_layers = []

            if len(text_layers) > 0:
                for layer in text_layers[-unfreeze_text_layers:]:
                    for p in layer.parameters():
                        p.requires_grad = True
                print(f"🔓 Unfroze last {unfreeze_text_layers} TEXT layers")

        # Unfreeze last N layers of video backbone
        if unfreeze_video_layers > 0:
            if hasattr(self.video_backbone, "encoder"):
                video_layers = self.video_backbone.encoder.layer
            else:
                video_layers = []

            if len(video_layers) > 0:
                for layer in video_layers[-unfreeze_video_layers:]:
                    for p in layer.parameters():
                        p.requires_grad = True
                print(f"🔓 Unfroze last {unfreeze_video_layers} VIDEO layers")

        # 3. Fusion Strategy
        self.fusion_type = config.get(
            "fusion_type", "concat"
        )  # "concat" or "attention"

        text_dim = config["text_feat_dim"]
        video_dim = config["video_feat_dim"]
        fusion_hidden = config["fusion_hidden"]

        if self.fusion_type == "attention":
            # Cross-Modal Attention Fusion
            print("🔥 Using ATTENTION-BASED Fusion")

            # Project to same dimension
            self.text_proj = nn.Linear(text_dim, fusion_hidden)
            self.video_proj = nn.Linear(video_dim, fusion_hidden)

            # Cross-Attention: Text attend to Video
            self.cross_attn_t2v = nn.MultiheadAttention(
                embed_dim=fusion_hidden, num_heads=4, dropout=0.1, batch_first=True
            )

            # Cross-Attention: Video attend to Text
            self.cross_attn_v2t = nn.MultiheadAttention(
                embed_dim=fusion_hidden, num_heads=4, dropout=0.1, batch_first=True
            )

            # Gating mechanism
            self.gate = nn.Sequential(
                nn.Linear(fusion_hidden * 2, fusion_hidden), nn.Sigmoid()
            )

            # Classifier
            self.classifier = nn.Sequential(
                nn.Linear(fusion_hidden, fusion_hidden // 2),
                nn.LayerNorm(fusion_hidden // 2),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(fusion_hidden // 2, 2),
            )
        else:
            # Simple Concat Fusion (original)
            print("📦 Using CONCAT Fusion")
            input_dim = text_dim + video_dim
            self.classifier = nn.Sequential(
                nn.Linear(input_dim, fusion_hidden),
                nn.BatchNorm1d(fusion_hidden),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(fusion_hidden, 2),
            )

        self.v_weight = config["video_weight"]
        self.t_weight = config["text_weight"]

        self.is_videomae = "videomae" in video_path.lower()

    def forward(
        self,
        text_input_ids,
        text_attention_mask,
        video_pixel_values,
        labels=None,
        **kwargs,  # Ignore các params không dùng (num_comments, etc.)
    ):
        """
        Args:
            text_input_ids: (B, L) - Text đã concat
            text_attention_mask: (B, L)
            video_pixel_values: (B, C, T, H, W)
            labels: (B,)
        """
        # A. Text Features - Đơn giản, 1 forward pass
        t_outputs = self.text_backbone(
            input_ids=text_input_ids,
            attention_mask=text_attention_mask,
        )
        t_feat = t_outputs.last_hidden_state[:, 0, :]  # CLS token (B, hidden)

        # B. Video Features
        v_outputs = self.video_backbone(video_pixel_values)

        if self.is_videomae:
            v_feat = v_outputs.last_hidden_state.mean(dim=1)
        else:
            v_feat = v_outputs.last_hidden_state[:, 0, :]

        # C. Fusion
        if self.fusion_type == "attention":
            # Project to same dimension
            t_proj = self.text_proj(t_feat).unsqueeze(1)  # (B, 1, H)
            v_proj = self.video_proj(v_feat).unsqueeze(1)  # (B, 1, H)

            # Cross-attention
            t_attended, _ = self.cross_attn_t2v(
                t_proj, v_proj, v_proj
            )  # Text attends to Video
            v_attended, _ = self.cross_attn_v2t(
                v_proj, t_proj, t_proj
            )  # Video attends to Text

            # Squeeze back
            t_attended = t_attended.squeeze(1)  # (B, H)
            v_attended = v_attended.squeeze(1)  # (B, H)

            # Weighted combination
            t_weighted = t_attended * self.t_weight
            v_weighted = v_attended * self.v_weight

            # Gating mechanism
            concat_feat = torch.cat([t_weighted, v_weighted], dim=1)  # (B, 2H)
            gate = self.gate(concat_feat)  # (B, H)

            # Fused output
            combined = gate * t_weighted + (1 - gate) * v_weighted  # (B, H)
        else:
            # Simple concat (original)
            combined = torch.cat(
                (t_feat * self.t_weight, v_feat * self.v_weight), dim=1
            )

        # D. Classification
        logits = self.classifier(combined)

        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, 2), labels.view(-1))

        return (
            {"loss": loss, "logits": logits} if loss is not None else {"logits": logits}
        )
