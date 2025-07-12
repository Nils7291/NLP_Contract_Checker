import pandas as pd
import torch
from tqdm import tqdm


def add_embed_text_column(df, text_column, model, target_column, batch_size=16):
    """
    Computes and adds a column of embeddings to a DataFrame using a SentenceTransformer-like model.

    Parameters:
    - df: The input pandas DataFrame
    - text_column: Name of the column containing text data
    - model: A model with a .encode() method (e.g., SentenceTransformer)
    - target_column: Name of the column to store the resulting embeddings
    - batch_size: Number of texts to process per batch (default: 16)

    Returns:
    - The input DataFrame with a new column containing embeddings as numpy arrays
    """
    texts = df[text_column].fillna("").tolist()
    all_embeddings = []

    for i in tqdm(range(0, len(texts), batch_size), desc=f"Embedding {text_column}"):
        batch = texts[i:i+batch_size]
        with torch.no_grad():
            emb = model.encode(batch, convert_to_tensor=True)
        all_embeddings.extend(emb.cpu().numpy())

    df[target_column] = all_embeddings
    return df
