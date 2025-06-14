#!/usr/bin/env python3
import os

import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

# --- Configuration ---
DATA_PATH = "data/train.csv"
MODEL_DIR = "models"
BATCH_SIZE = 32
EPOCHS = 10
LR = 1e-3

# Ensure model directory exists
os.makedirs(MODEL_DIR, exist_ok=True)

def preprocess(df):
    # Basic preprocessing for Titanic dataset
    df = df.copy()
    # Fill missing values
    df["Age"].fillna(df["Age"].median(), inplace=True)
    df["Embarked"].fillna(df["Embarked"].mode()[0], inplace=True)
    df["Fare"].fillna(df["Fare"].median(), inplace=True)

    # Encode categorical features
    df["Sex"] = df["Sex"].map({"male": 0, "female": 1}).astype(int)
    df["Embarked"] = df["Embarked"].map({"S": 0, "C": 1, "Q": 2}).astype(int)

    # Select features and target
    features = df[["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"]].values
    target = df["Survived"].values
    return torch.tensor(features, dtype=torch.float32), torch.tensor(target, dtype=torch.float32)

class TitanicDataset(Dataset):
    def __init__(self, features, targets):
        self.X = features
        self.y = targets

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

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
        return self.model(x).squeeze(-1)


def train():
    # Device configuration
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load and preprocess data
    df = pd.read_csv(DATA_PATH)
    X, y = preprocess(df)

    # Dataset and DataLoader
    dataset = TitanicDataset(X, y)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    # Model, loss, optimizer
    model = SimpleNet(input_dim=X.shape[1]).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=LR)

    # Training loop
    model.train()
    for epoch in range(1, EPOCHS + 1):
        total_loss = 0.0
        for batch_X, batch_y in loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)

            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * batch_X.size(0)

        avg_loss = total_loss / len(dataset)
        print(f"Epoch [{epoch}/{EPOCHS}], Loss: {avg_loss:.4f}")

    # Save model weights
    save_path = os.path.join(MODEL_DIR, "titanic_model.pth")
    torch.save(model.state_dict(), save_path)
    print(f"Model saved to {save_path}")

if __name__ == "__main__":
    train()
