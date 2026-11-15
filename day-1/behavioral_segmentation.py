"""Day 1 — Behavioral Segmentation: K-Means / GMM.

Single self-contained script. Run after feature engineering:

    python day-1/feature_engineering.py
    python day-1/behavioral_segmentation.py

Clusters users (anonymous_id) from user-level features. Writes:

    day-1/output/audience_segments.csv
    day-1/output/segment_profiles_kmeans.csv
    day-1/output/segment_profiles_gmm.csv
    day-1/output/segmentation_metrics.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
USER_FEATURES = OUTPUT / "user_features.csv"

# Keep in sync with day-1/feature_engineering.py user feature rates.
FEATURE_COLUMNS = [
    "n_sessions",
    "mean_duration_sec",
    "mean_behavior_events",
    "mean_content",
    "mean_furthest_rank",
    "share_deep",
    "share_intent",
    "share_engaged",
    "share_landing_or_scroll",
    "page_view_rate",
    "scroll_rate",
    "engaged_read_rate",
    "share_rate",
    "login_rate",
    "register_start_rate",
    "subscription_view_rate",
    "subscribe_click_rate",
    "checkout_start_rate",
    "payment_success_rate",
    "conversion_rate",
]
K_CANDIDATES = range(3, 9)
SEED = 42


# ---------------------------------------------------------------------------
# Load features
# ---------------------------------------------------------------------------


def load_user_features() -> pd.DataFrame:
    """Load user_features.csv from feature_engineering.py; rebuild if needed."""
    if USER_FEATURES.exists():
        features = pd.read_csv(USER_FEATURES)
        return _ensure_feature_columns(features)

    from feature_engineering import enrich_session_features, load_sessions, user_features

    print("user_features.csv missing — rebuilding from sessions")
    return _ensure_feature_columns(user_features(enrich_session_features(load_sessions())))


def _ensure_feature_columns(features: pd.DataFrame) -> pd.DataFrame:
    if "anonymous_id" not in features.columns:
        raise RuntimeError(f"{USER_FEATURES.name} missing anonymous_id")
    missing = [column for column in FEATURE_COLUMNS if column not in features.columns]
    if missing:
        raise RuntimeError(
            f"user features missing columns: {', '.join(missing)}. "
            "Re-run python day-1/feature_engineering.py after sessionize."
        )
    out = features.copy()
    for column in FEATURE_COLUMNS:
        out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0.0)
    # Cap extreme session lengths so a few outliers do not dominate distance metrics.
    duration_cap = float(out["mean_duration_sec"].quantile(0.995))
    if np.isfinite(duration_cap) and duration_cap > 0:
        out["mean_duration_sec"] = out["mean_duration_sec"].clip(upper=duration_cap)
    return out.dropna(subset=["anonymous_id"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Fit
# ---------------------------------------------------------------------------


def fit_segmentation(features: pd.DataFrame, seed: int = SEED) -> dict:
    """Scale audience features and fit K-Means and GMM."""
    matrix = features[FEATURE_COLUMNS].to_numpy(dtype=float)
    if not np.isfinite(matrix).all():
        matrix = np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)

    k, k_scores = _choose_k(scaled, seed=seed)
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=seed)
    kmeans_labels = kmeans.fit_predict(scaled)

    gmm = GaussianMixture(n_components=k, covariance_type="full", random_state=seed, n_init=3)
    gmm_labels = gmm.fit_predict(scaled)

    labeled = features.copy()
    labeled["kmeans_segment"] = kmeans_labels
    labeled["gmm_segment"] = gmm_labels
    kmeans_names = _name_segments(labeled, "kmeans_segment")
    gmm_names = _name_segments(labeled, "gmm_segment")
    labeled["kmeans_label"] = labeled["kmeans_segment"].map(kmeans_names)
    labeled["gmm_label"] = labeled["gmm_segment"].map(gmm_names)

    profiles = {
        "kmeans": _profile_table(labeled, "kmeans_segment", "kmeans_label"),
        "gmm": _profile_table(labeled, "gmm_segment", "gmm_label"),
    }
    metrics = {
        "readers": int(len(features)),
        "features": FEATURE_COLUMNS,
        "kmeans": {
            "n_clusters": int(k),
            "inertia": round(float(kmeans.inertia_), 2),
            "silhouette": _safe_silhouette(scaled, kmeans_labels),
            "k_selection": k_scores,
        },
        "gmm": {
            "n_components": int(k),
            "bic": round(float(gmm.bic(scaled)), 2),
            "aic": round(float(gmm.aic(scaled)), 2),
            "silhouette": _safe_silhouette(scaled, gmm_labels),
        },
    }
    return {"audience": labeled, "profiles": profiles, "metrics": metrics}


def _choose_k(scaled: np.ndarray, seed: int) -> tuple[int, list[dict]]:
    sample_size = min(12000, len(scaled))
    rng = np.random.default_rng(seed)
    take = rng.choice(len(scaled), size=sample_size, replace=False)
    sample = scaled[take]
    scores = []
    for k in K_CANDIDATES:
        labels = KMeans(n_clusters=k, n_init=10, random_state=seed).fit_predict(sample)
        score = float(silhouette_score(sample, labels))
        scores.append({"k": int(k), "silhouette": round(score, 4)})
    best = max(scores, key=lambda row: row["silhouette"])
    return int(best["k"]), scores


def _safe_silhouette(scaled: np.ndarray, labels: np.ndarray) -> float | None:
    labels = np.asarray(labels)
    if len(scaled) < 2 or len(np.unique(labels)) < 2:
        return None
    if len(scaled) > 20000:
        rng = np.random.default_rng(SEED)
        take = rng.choice(len(scaled), size=20000, replace=False)
        scaled = scaled[take]
        labels = labels[take]
        if len(np.unique(labels)) < 2:
            return None
    return round(float(silhouette_score(scaled, labels)), 4)


def _name_segments(frame: pd.DataFrame, segment_column: str) -> dict[int, str]:
    names: dict[int, str] = {}
    used: set[str] = set()
    for segment, part in frame.groupby(segment_column, sort=True):
        segment = int(segment)
        depth = float(part["mean_furthest_rank"].mean())
        convert = float(part["conversion_rate"].mean())
        plan_view = (
            float(part["subscription_view_rate"].mean()) if "subscription_view_rate" in part.columns else 0.0
        )
        sessions = float(part["n_sessions"].mean())
        # Ranks: landing=1, scroll=2, engaged=3, intent=4, deep=5
        if convert >= 0.03:
            label = "converters"
        elif depth >= 4.5:
            label = "deep_checkout"
        elif depth >= 3.8 and plan_view >= 0.08:
            label = "intent_engaged"
        elif depth >= 3.0:
            label = "regular_readers"
        elif sessions >= 3 and depth < 2.0:
            label = "repeat_browsers"
        elif depth <= 1.5:
            label = "bouncers"
        else:
            label = "casual_browsers"
        base = label
        suffix = 2
        while label in used:
            label = f"{base}_{suffix}"
            suffix += 1
        used.add(label)
        names[segment] = label
    return names


def _profile_table(frame: pd.DataFrame, segment_column: str, label_column: str) -> pd.DataFrame:
    rows = []
    for segment, part in frame.groupby(segment_column, sort=True):
        rows.append(
            {
                "segment": int(segment),
                "label": part[label_column].iloc[0],
                "readers": int(len(part)),
                "share_of_readers": round(float(len(part) / len(frame)), 4),
                "mean_sessions": round(float(part["n_sessions"].mean()), 2),
                "mean_duration_sec": round(float(part["mean_duration_sec"].mean()), 1),
                "mean_behavior_events": round(float(part["mean_behavior_events"].mean()), 2),
                "mean_furthest_rank": round(float(part["mean_furthest_rank"].mean()), 2),
                "conversion_rate": round(float(part["conversion_rate"].mean()), 4),
                "share_deep": round(float(part["share_deep"].mean()), 4),
                "share_intent": round(
                    float(part["share_intent"].mean()) if "share_intent" in part.columns else 0.0,
                    4,
                ),
                "subscription_view_rate": round(
                    float(part["subscription_view_rate"].mean()) if "subscription_view_rate" in part.columns else 0.0,
                    4,
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("readers", ascending=False).reset_index(drop=True)


def save_segmentation(result: dict) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    audience = result["audience"]
    keep = [
        "anonymous_id",
        "n_sessions",
        "mean_duration_sec",
        "mean_behavior_events",
        "mean_furthest_rank",
        "conversion_rate",
        "subscription_view_rate",
        "checkout_start_rate",
        "kmeans_segment",
        "kmeans_label",
        "gmm_segment",
        "gmm_label",
    ]
    keep = [column for column in keep if column in audience.columns]
    audience[keep].to_csv(OUTPUT / "audience_segments.csv", index=False)
    for method, table in result["profiles"].items():
        table.to_csv(OUTPUT / f"segment_profiles_{method}.csv", index=False)
    stale = OUTPUT / "segment_profiles_hdbscan.csv"
    if stale.exists():
        stale.unlink()
    (OUTPUT / "segmentation_metrics.json").write_text(json.dumps(result["metrics"], indent=2))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


def main() -> None:
    print("6. Behavioral Segmentation — K-Means / GMM")
    features = load_user_features()
    result = fit_segmentation(features)
    save_segmentation(result)

    metrics = result["metrics"]
    print(f"   readers: {metrics['readers']:,}")
    print(
        f"   K-Means k={metrics['kmeans']['n_clusters']}, "
        f"silhouette {metrics['kmeans']['silhouette']}"
    )
    print(
        f"   GMM components={metrics['gmm']['n_components']}, "
        f"BIC {metrics['gmm']['bic']}, silhouette {metrics['gmm']['silhouette']}"
    )
    print("\nK-Means profiles")
    print(result["profiles"]["kmeans"].to_string(index=False))
    print("\nGMM profiles")
    print(result["profiles"]["gmm"].to_string(index=False))
    print(f"\nwrote files under {OUTPUT}")


if __name__ == "__main__":
    main()
