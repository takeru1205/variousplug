#!/usr/bin/env python3
import os

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

# --- Configuration ---
TEST_PATH  = "data/test.csv"
MODEL_DIR  = "models"
BATCH_SIZE = 32

# デバイス設定
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # fillna の inplace を避ける
    df["Age"]      = df["Age"].fillna(df["Age"].median())
    df["Fare"]     = df["Fare"].fillna(df["Fare"].median())
    df["Embarked"] = df["Embarked"].fillna(df["Embarked"].mode()[0])
    # カテゴリ変換
    df["Sex"]      = df["Sex"].map({"male": 0, "female": 1}).astype(int)
    df["Embarked"] = df["Embarked"].map({"S": 0, "C": 1, "Q": 2}).astype(int)
    # 特徴量抽出
    return df[["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"]]

class TitanicTestDataset(Dataset):
    def __init__(self, features: pd.DataFrame):
        arr = features.to_numpy(dtype=np.float32)
        self.X = torch.from_numpy(arr)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx]

# 学習時と同じモデル定義をコピペ
class SimpleNet(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        # BCEWithLogitsLoss で学習しているので、出力は logit
        return self.model(x).squeeze(-1)

def main():
    # テストデータ読み込み
    test_df = pd.read_csv(TEST_PATH)
    passenger_ids = test_df["PassengerId"]

    # 前処理
    X_test = preprocess(test_df)

    # DataLoader
    test_ds = TitanicTestDataset(X_test)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)

    # モデル準備
    input_dim = X_test.shape[1]
    model = SimpleNet(input_dim).to(device)

    # 重み読み込み
    model_path = os.path.join(MODEL_DIR, "titanic_model.pth")
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    print(f"Loaded model weights from {model_path}")

    # 推論
    preds = []
    with torch.no_grad():
        for X in test_loader:
            X = X.to(device)
            logits = model(X)
            probs = torch.sigmoid(logits)            # ロジット → 確率
            preds.extend((probs >= 0.5).long().cpu().tolist())

    # 結果保存
    submission = pd.DataFrame({
        "PassengerId": passenger_ids,
        "Survived":     preds
    })
    os.makedirs("results", exist_ok=True)
    output_path = "results/submission.csv"
    submission.to_csv(output_path, index=False)
    print(f"Predictions saved to {output_path}")

if __name__ == "__main__":
    main()

