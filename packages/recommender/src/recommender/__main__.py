"""CLI entry point for training the recommender model."""

from pathlib import Path

from recommender.trainer import RecommenderTrainer


def main() -> None:
    """Train the LightGBM recommender and save to disk."""
    trainer = RecommenderTrainer()
    trainer.train_from_synthetic()
    importance = trainer.get_feature_importance()
    print("Feature importance:")  # noqa: T201
    for name, score in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {score:.1f}")  # noqa: T201
    model_path = Path("models/recommender.joblib")
    trainer.save(model_path)
    print(f"Model saved to {model_path}")  # noqa: T201


if __name__ == "__main__":
    main()
