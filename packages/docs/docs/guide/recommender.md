# Recommender System

The recommender uses a LightGBM learning-to-rank model to rerank retrieved documents.

## Features

The model uses six features for ranking:

1. **Embedding Similarity**: Cosine similarity between query and document embeddings
2. **Temporal Decay**: Exponential decay based on document age
3. **Protocol Match**: Jaccard similarity for ICS protocol overlap
4. **Asset Type Match**: Jaccard similarity for asset type overlap
5. **Popularity Score**: Log-scaled interaction count
6. **Recency Boost**: Bonus for recently published content

## Training

```bash
# Train on synthetic data
make train-recommender

# Or programmatically
from recommender.trainer import RecommenderTrainer

trainer = RecommenderTrainer(n_estimators=100)
trainer.train_from_synthetic(n_queries=200)
trainer.save("models/recommender.joblib")
```

## Inference

```python
from recommender.predictor import RecommenderPredictor

predictor = RecommenderPredictor.from_path("models/recommender.joblib")
ranked = predictor.rank_documents(query_embedding, candidates, top_k=5)
```
