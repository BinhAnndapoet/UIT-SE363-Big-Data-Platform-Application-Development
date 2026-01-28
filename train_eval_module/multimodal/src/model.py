import torch
import torch.nn as nn
from transformers import XCLIPModel


class XCLIPClassificationModel(nn.Module):
    def __init__(self, model_name="microsoft/xclip-base-patch32", num_labels=2):
        super().__init__()
        print(f"🏗️ Initializing X-CLIP: {model_name}")
        self.xclip = XCLIPModel.from_pretrained(model_name)

        # Freeze XCLIP backbone (optional)
        # for param in self.xclip.parameters():
        #     param.requires_grad = False

        hidden_dim = self.xclip.config.projection_dim

        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 256),  # Combine Text + Video features
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_labels),
        )

    def forward(self, input_ids, attention_mask, pixel_values, labels=None):
        # 1. Text Features
        text_features = self.xclip.get_text_features(
            input_ids=input_ids, attention_mask=attention_mask
        )
        # 2. Video Features
        video_features = self.xclip.get_video_features(pixel_values=pixel_values)

        # 3. Concatenate
        combined_features = torch.cat((text_features, video_features), dim=1)
        logits = self.classifier(combined_features)

        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, 2), labels.view(-1))

        return (
            {"loss": loss, "logits": logits} if loss is not None else {"logits": logits}
        )
