import torch
from torch import nn
from transformers import AutoTokenizer, AutoModel, AutoConfig
import pandas as pd 

from functions.functions_preprocessing import( 
    extract_paragraphs_and_sections
    , extract_title_fixed
    , clean_sections_and_paragraphs
)

class CosineMapper(nn.Module):
    def __init__(
        self,
        model_name,  # e.g. best_model["model_url"]
        label_embeddings,  # e.g. label_embeddings
        pooling,  # e.g. best_model["pooling_strategy"]
        threshold,  # e.g. best_model["optimal_threshold"]
    ):
        """
        Initializes the CosineMapper model.

        Parameters:
        - model_name: HuggingFace model name or path
        - label_embeddings: Precomputed label embeddings (Tensor)
        - pooling: Pooling strategy ('cls', 'max', or 'mean')
        - threshold: Threshold for classification decisions
        """
        super().__init__()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        config = AutoConfig.from_pretrained(model_name)
        self.bert = AutoModel.from_pretrained(model_name, config=config)
        self.pooling = pooling
        self.threshold = threshold

        self.label_embeddings = nn.Parameter(label_embeddings, requires_grad=False)
        self.activation = nn.GELU()  # Use 'gelu' as activation function

        self.dropout = nn.Dropout(0.5)

    def forward(self, texts, return_embedding=False):
        """
        Encodes input texts and computes cosine similarity with label embeddings.

        Parameters:
        - texts: A string or list of strings to encode
        - return_embedding: If True, returns the pooled embedding instead of similarity

        Returns:
        - Tensor of cosine similarities or embeddings
        """
        if isinstance(texts, str):
            texts = [texts]

        inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        outputs = self.bert(**inputs)
        token_embeddings = outputs.last_hidden_state  # (B, T, H)

        # Pooling
        if self.pooling == "cls":
            pooled = token_embeddings[:, 0]
        elif self.pooling == "max":
            mask = inputs["attention_mask"].unsqueeze(-1).expand(token_embeddings.shape).float()
            token_embeddings[mask == 0] = -1e9
            pooled = torch.max(token_embeddings, dim=1)[0]
        elif self.pooling == "mean":
            mask = inputs["attention_mask"].unsqueeze(-1).expand(token_embeddings.shape).float()
            summed = torch.sum(token_embeddings * mask, dim=1)
            counts = mask.sum(dim=1).clamp(min=1e-9)
            pooled = summed / counts
        else:
            raise ValueError("Unknown pooling method")

        pooled = self.dropout(pooled)
        if return_embedding:
            return pooled 

        # Cosine similarity with all label embeddings
        normalized_input = nn.functional.normalize(pooled, dim=1)
        normalized_labels = nn.functional.normalize(self.label_embeddings, dim=1)

        cosine_sim = torch.matmul(normalized_input, normalized_labels.T)  # (B, num_labels)
        return cosine_sim

    def predict(self, texts, top_k: int = 1, return_scores: bool = False):
        """
        Predicts the most similar labels for given texts.

        Parameters:
        - texts: A string or list of strings
        - top_k: Number of top predictions to return
        - return_scores: If True, returns the scores with the predictions

        Returns:
        - List of top-k (label_index, score) tuples if return_scores is True
        - Otherwise, returns the predicted label index (+1)
        """
        with torch.no_grad():
            scores = self.forward(texts)

        if return_scores:
            # Return top-k indices (+1) and scores
            topk_scores, topk_indices = torch.topk(scores, k=top_k, dim=1)
            results = []
            for indices, values in zip(topk_indices, topk_scores):
                results.append([(i.item(), round(s.item(), 4)) for i, s in zip(indices, values)])
            return results if len(results) > 1 else results[0]

        else:
            # Return only index (+1) of the best class
            preds = torch.argmax(scores, dim=1)
            result = (preds + 1).tolist()
            return result[0] if len(result) == 1 else result
