from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from app.text import normalize

DOCUMENT_TYPES = [
    "certidao_transito_julgado",
    "sentenca",
    "acordao",
    "calculos",
    "substabelecimento",
    "certidao_obito",
    "procuracao",
    "peticao",
    "despacho",
]


@dataclass
class Prediction:
    label: str
    confidence: float
    top_terms: list[str]


def build_pipeline() -> Pipeline:
    features = FeatureUnion(
        [
            (
                "words",
                TfidfVectorizer(
                    preprocessor=normalize,
                    ngram_range=(1, 2),
                    min_df=2,
                    sublinear_tf=True,
                ),
            ),
            (
                "chars",
                TfidfVectorizer(
                    preprocessor=normalize,
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=3,
                    sublinear_tf=True,
                    max_features=30000,
                ),
            ),
        ]
    )
    model = LogisticRegression(max_iter=3000, C=4.0, class_weight="balanced")
    return Pipeline([("features", features), ("model", model)])


class DocumentClassifier:
    def __init__(self, pipeline: Pipeline, metadata: dict | None = None):
        self.pipeline = pipeline
        self.metadata = metadata or {}

    @classmethod
    def load(cls, path: Path) -> "DocumentClassifier":
        bundle = joblib.load(path)
        return cls(bundle["pipeline"], bundle.get("metadata"))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"pipeline": self.pipeline, "metadata": self.metadata}, path)

    @property
    def version(self) -> str:
        return self.metadata.get("version", "unknown")

    def predict(self, texts: list[str], n_terms: int = 5) -> list[Prediction]:
        probabilities = self.pipeline.predict_proba(texts)
        classes = self.pipeline.classes_
        vectors = self.pipeline.named_steps["features"].transform(texts)
        word_vectorizer = self.pipeline.named_steps["features"].transformer_list[0][1]
        vocabulary = word_vectorizer.get_feature_names_out()
        n_words = len(vocabulary)
        coefficients = self.pipeline.named_steps["model"].coef_

        predictions = []
        for row, probs in enumerate(probabilities):
            best = int(np.argmax(probs))
            word_weights = vectors[row, :n_words].toarray().ravel() * coefficients[best, :n_words]
            top = np.argsort(word_weights)[::-1][:n_terms]
            terms = [vocabulary[i] for i in top if word_weights[i] > 0]
            predictions.append(Prediction(str(classes[best]), float(probs[best]), terms))
        return predictions
