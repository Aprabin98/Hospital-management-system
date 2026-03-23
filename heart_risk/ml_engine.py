import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.datasets import fetch_openml
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


APP_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = APP_DIR / 'model_artifacts'
MODEL_PATH = ARTIFACT_DIR / 'heart_risk_model.joblib'
META_PATH = ARTIFACT_DIR / 'heart_risk_model_meta.json'


def _to_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_features_from_openml() -> tuple[pd.DataFrame, pd.Series, dict]:
    """Fetch and normalize the OpenML heart-disease dataset for training."""
    dataset = fetch_openml(name='heart-disease', version=1, as_frame=True)
    data = dataset.data.copy()

    if 'target' not in data.columns and dataset.target is not None:
        data['target'] = dataset.target

    if 'target' not in data.columns:
        raise ValueError('OpenML heart-disease dataset did not provide target column.')

    model_df = pd.DataFrame(
        {
            'age': pd.to_numeric(data.get('age'), errors='coerce'),
            'sex': pd.to_numeric(data.get('sex'), errors='coerce'),
            'systolic_bp': pd.to_numeric(data.get('trestbps'), errors='coerce'),
            'total_cholesterol': pd.to_numeric(data.get('chol'), errors='coerce'),
            'high_fbs': pd.to_numeric(data.get('fbs'), errors='coerce'),
            'chest_pain': pd.to_numeric(data.get('cp'), errors='coerce').fillna(0).gt(0).astype(int),
            'exercise_angina': pd.to_numeric(data.get('exang'), errors='coerce').fillna(0),
        }
    )

    target = pd.to_numeric(data['target'], errors='coerce').fillna(0)
    target = target.gt(0).astype(int)

    mask = model_df.notna().all(axis=1)
    model_df = model_df[mask]
    target = target[mask]

    source_info = {
        'dataset_name': 'OpenML heart-disease v1',
        'openml_name': 'heart-disease',
        'version': 1,
        'samples_used': int(model_df.shape[0]),
    }
    return model_df, target, source_info


def train_and_save_model() -> dict:
    """Train and select strongest model on online real data, then persist artifacts."""
    X, y, source_info = _build_features_from_openml()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    candidates = {
        'LogisticRegression': Pipeline(
            steps=[
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler()),
                ('clf', LogisticRegression(max_iter=2000, class_weight='balanced')),
            ]
        ),
        'RandomForestClassifier': Pipeline(
            steps=[
                ('imputer', SimpleImputer(strategy='median')),
                (
                    'clf',
                    RandomForestClassifier(
                        n_estimators=400,
                        max_depth=8,
                        min_samples_split=4,
                        min_samples_leaf=2,
                        random_state=42,
                        class_weight='balanced',
                    ),
                ),
            ]
        ),
        'GradientBoostingClassifier': Pipeline(
            steps=[
                ('imputer', SimpleImputer(strategy='median')),
                (
                    'clf',
                    GradientBoostingClassifier(
                        n_estimators=300,
                        learning_rate=0.05,
                        max_depth=3,
                        random_state=42,
                    ),
                ),
            ]
        ),
    }

    best_model_name = None
    best_model = None
    best_metrics = None
    all_results = {}

    for model_name, model in candidates.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        metrics = {
            'roc_auc': float(roc_auc_score(y_test, y_prob)),
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, zero_division=0)),
            'recall': float(recall_score(y_test, y_pred, zero_division=0)),
            'f1': float(f1_score(y_test, y_pred, zero_division=0)),
            'train_size': int(X_train.shape[0]),
            'test_size': int(X_test.shape[0]),
        }
        all_results[model_name] = metrics

        if best_metrics is None or metrics['roc_auc'] > best_metrics['roc_auc']:
            best_metrics = metrics
            best_model = model
            best_model_name = model_name

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        'model': best_model,
        'feature_names': list(X.columns),
    }
    joblib.dump(payload, MODEL_PATH)

    metadata = {
        'trained_at': datetime.now(timezone.utc).isoformat(),
        'model_type': best_model_name,
        'selection_metric': 'roc_auc',
        'pipeline': str(best_model),
        'source': source_info,
        'metrics': best_metrics,
        'candidate_results': all_results,
    }
    META_PATH.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    return metadata


def model_available() -> bool:
    return MODEL_PATH.exists() and META_PATH.exists()


def load_model_payload() -> tuple[dict, dict]:
    if not model_available():
        raise FileNotFoundError('Model artifacts not found. Run train_heart_risk_model command first.')
    payload = joblib.load(MODEL_PATH)
    metadata = json.loads(META_PATH.read_text(encoding='utf-8'))
    return payload, metadata


def predict_probability(cleaned_data: dict) -> tuple[float, dict]:
    payload, metadata = load_model_payload()
    model = payload['model']

    sex_raw = str(cleaned_data.get('sex', 'F')).upper()
    sex_value = 1 if sex_raw == 'M' else 0
    high_fbs = 1 if (_to_int(cleaned_data.get('fasting_blood_sugar')) >= 120 or bool(cleaned_data.get('diabetic'))) else 0
    chest_pain = 1 if bool(cleaned_data.get('chest_pain')) else 0
    exercise_angina = 1 if bool(cleaned_data.get('sedentary_lifestyle')) else 0

    feature_df = pd.DataFrame(
        [
            {
                'age': _to_int(cleaned_data.get('age')),
                'sex': sex_value,
                'systolic_bp': _to_int(cleaned_data.get('systolic_bp')),
                'total_cholesterol': _to_int(cleaned_data.get('total_cholesterol')),
                'high_fbs': high_fbs,
                'chest_pain': chest_pain,
                'exercise_angina': exercise_angina,
            }
        ]
    )

    probability = float(model.predict_proba(feature_df)[:, 1][0])
    return probability, metadata
