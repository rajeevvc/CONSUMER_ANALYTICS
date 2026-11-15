"""Segmentation example — K-Means + GMM on toy audience features.

Question: Which audience group does each cookie belong to?

Run:
    python day-1/examples/05_segmentation/01_segmentation_example.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

FEATURE_COLUMNS = [
    "n_sessions",
    "mean_duration_sec",
    "mean_furthest_rank",
    "share_intent",
    "share_deep",
    "subscription_view_rate",
    "conversion_rate",
]


def toy_audience() -> pd.DataFrame:
    """12 cookies in 3 obvious groups (clearer than 4 single-session toys)."""
    rows = []
    # Bouncers — shallow, short, no convert
    for i in range(4):
        rows.append(
            {
                "anonymous_id": f"B{i+1}",
                "persona": "bouncer_truth",
                "n_sessions": 1,
                "mean_duration_sec": 20 + i * 5,
                "mean_furthest_rank": 1.0,
                "share_intent": 0.0,
                "share_deep": 0.0,
                "subscription_view_rate": 0.0,
                "conversion_rate": 0.0,
            }
        )
    # Regular readers — mid depth, some intent
    for i in range(4):
        rows.append(
            {
                "anonymous_id": f"R{i+1}",
                "persona": "reader_truth",
                "n_sessions": 2 + i,
                "mean_duration_sec": 180 + i * 20,
                "mean_furthest_rank": 3.0 + 0.2 * i,
                "share_intent": 0.1,
                "share_deep": 0.0,
                "subscription_view_rate": 0.05,
                "conversion_rate": 0.0,
            }
        )
    # Converters — deep + intent + convert
    for i in range(4):
        rows.append(
            {
                "anonymous_id": f"C{i+1}",
                "persona": "converter_truth",
                "n_sessions": 3 + i,
                "mean_duration_sec": 400 + i * 30,
                "mean_furthest_rank": 4.5 + 0.1 * i,
                "share_intent": 0.4,
                "share_deep": 0.3,
                "subscription_view_rate": 0.25,
                "conversion_rate": 0.4 + 0.1 * i,
            }
        )
    return pd.DataFrame(rows)


def name_segment(part: pd.DataFrame) -> str:
    convert = float(part["conversion_rate"].mean())
    depth = float(part["mean_furthest_rank"].mean())
    if convert >= 0.2:
        return "converters"
    if depth >= 2.5:
        return "regular_readers"
    return "bouncers"


def fit_segmentation(users: pd.DataFrame) -> pd.DataFrame:
    matrix = users[FEATURE_COLUMNS].to_numpy(dtype=float)
    scaled = StandardScaler().fit_transform(matrix)

    # Choose k with silhouette on this tiny set (k=3 is the designed truth).
    scores = []
    for k in range(2, 5):
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(scaled)
        scores.append((k, float(silhouette_score(scaled, labels))))
    best_k = max(scores, key=lambda item: item[1])[0]

    kmeans = KMeans(n_clusters=best_k, n_init=10, random_state=42)
    gmm = GaussianMixture(n_components=best_k, covariance_type="full", random_state=42, n_init=3)
    out = users.copy()
    out["kmeans_segment"] = kmeans.fit_predict(scaled)
    out["gmm_segment"] = gmm.fit_predict(scaled)

    k_names = {
        seg: name_segment(out.loc[out["kmeans_segment"] == seg])
        for seg in sorted(out["kmeans_segment"].unique())
    }
    g_names = {
        seg: name_segment(out.loc[out["gmm_segment"] == seg])
        for seg in sorted(out["gmm_segment"].unique())
    }
    # Deduplicate labels if needed
    def unique_map(mapping: dict[int, str]) -> dict[int, str]:
        used: set[str] = set()
        fixed = {}
        for seg, label in mapping.items():
            base = label
            n = 2
            while label in used:
                label = f"{base}_{n}"
                n += 1
            used.add(label)
            fixed[seg] = label
        return fixed

    k_names = unique_map(k_names)
    g_names = unique_map(g_names)
    out["kmeans_label"] = out["kmeans_segment"].map(k_names)
    out["gmm_label"] = out["gmm_segment"].map(g_names)
    out.attrs["k"] = best_k
    out.attrs["silhouette_scores"] = scores
    out.attrs["gmm_bic"] = float(gmm.bic(scaled))
    return out


def profile(frame: pd.DataFrame, segment_col: str, label_col: str) -> pd.DataFrame:
    rows = []
    for seg, part in frame.groupby(segment_col, sort=True):
        rows.append(
            {
                "segment": int(seg),
                "label": part[label_col].iloc[0],
                "readers": len(part),
                "mean_furthest_rank": round(float(part["mean_furthest_rank"].mean()), 2),
                "conversion_rate": round(float(part["conversion_rate"].mean()), 3),
                "share_deep": round(float(part["share_deep"].mean()), 3),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    print("=" * 60)
    print("SEGMENTATION — K-Means + GMM")
    print("=" * 60)
    users = toy_audience()

    print("\nWhat the algorithm does")
    print("  1. Take user-level numeric features")
    print("  2. StandardScaler (so seconds and rates are comparable)")
    print("  3. Pick k via silhouette (here designed truth is 3 groups)")
    print("  4. Fit K-Means (hard clusters) and GMM (soft mixture → argmax)")
    print("  5. Name segments from profile means (converters / readers / bouncers)")

    print("\nToy audience (ground-truth personas)")
    print(users[["anonymous_id", "persona", "mean_furthest_rank", "conversion_rate"]].to_string(index=False))

    labeled = fit_segmentation(users)
    print(f"\nChosen k = {labeled.attrs['k']}")
    print("Silhouette by k:", labeled.attrs["silhouette_scores"])
    print(f"GMM BIC = {labeled.attrs['gmm_bic']:.1f}")

    print("\nAssignments")
    print(
        labeled[["anonymous_id", "persona", "kmeans_label", "gmm_label"]].to_string(index=False)
    )

    print("\nK-Means profiles")
    print(profile(labeled, "kmeans_segment", "kmeans_label").to_string(index=False))
    print("\nGMM profiles")
    print(profile(labeled, "gmm_segment", "gmm_label").to_string(index=False))

    print("\nTeaching takeaway")
    print("  Segmentation answers: 'What kind of audience is this cookie?'")
    print("  Needs feature engineering first; HMM modes are optional extras.")


if __name__ == "__main__":
    main()
