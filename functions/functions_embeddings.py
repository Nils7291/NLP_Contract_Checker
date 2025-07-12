
import pandas as pd
import torch
from tqdm import tqdm



def add_embed_text_column(df, text_column, model, target_column, batch_size=16):
    """
    Computes SentenceTransformer embeddings column-wise in batches, optimized for CPU performance.
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