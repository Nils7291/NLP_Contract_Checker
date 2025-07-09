class CosineMapper(nn.Module):
    def __init__(
        self,
        model_name= best_model["model_url"],
        label_embeddings = label_embeddings,
        pooling= best_model["pooling_strategy"],
        threshold= best_model["optimal_threshold"]
    ):
        super().__init__()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        config = AutoConfig.from_pretrained(model_name)
        self.bert = AutoModel.from_pretrained(model_name,config = config)  # Verwende 'gelu' als Aktivierungsfunktion
        self.pooling = pooling
        self.threshold = threshold

        self.label_embeddings = nn.Parameter(label_embeddings, requires_grad=False)  # z. B. aus SentenceTransformer
        self.activation = nn.GELU()  # Verwende 'gelu' als Aktivierungsfunktion

        self.dropout = nn.Dropout(0.5)

    def forward(self, texts,return_embedding = False  ):
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

        # Cosine similarity zu allen Labels
        normalized_input = nn.functional.normalize(pooled, dim=1)
        normalized_labels = nn.functional.normalize(self.label_embeddings, dim=1)

        cosine_sim = torch.matmul(normalized_input, normalized_labels.T)  # (B, num_labels)
        return cosine_sim

    def predict(self, texts, top_k: int = 1, return_scores: bool = False):
        with torch.no_grad():
            scores = self.forward(texts)

        if return_scores:
            # Gib Top-k Indizes (+1) und Scores zurück
            topk_scores, topk_indices = torch.topk(scores, k=top_k, dim=1)
            results = []
            for indices, values in zip(topk_indices, topk_scores):
                results.append([(i.item(), round(s.item(), 4)) for i, s in zip(indices, values)])
            return results if len(results) > 1 else results[0]

        else:
            # Gib nur Index (+1) der besten Klasse zurück
            preds = torch.argmax(scores, dim=1)
            result = (preds+1 ).tolist()
            return result[0] if len(result) == 1 else result
