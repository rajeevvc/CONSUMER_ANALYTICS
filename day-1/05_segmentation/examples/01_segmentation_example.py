"""Segmentation example — K-Means + GMM on toy audience features.

Question: Which audience group does each cookie belong to?

Run:
    python day-1/05_segmentation/examples/01_segmentation_example.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

_DAY1 = Path(__file__).resolve().parents[2]
_SHARED = _DAY1 / "_shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

TOY_AUDIENCE_CSV = _SHARED / "data" / "toy_audience.csv"

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
    """12 cookies in 3 obvious groups from day-1/_shared/data/toy_audience.csv."""
    if not TOY_AUDIENCE_CSV.exists():
        raise FileNotFoundError(
            f"missing {TOY_AUDIENCE_CSV}. Run: python day-1/_shared/generate_toy_data.py"
        )
    return pd.read_csv(TOY_AUDIENCE_CSV)


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


def _section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    _section("SEGMENTATION — K-Means + GMM")
    print("Goal: raw user features → named audience segment per cookie.")
    users = toy_audience()

    _section("RAW — toy audience features")
    print(
        users[
            ["anonymous_id", "persona", "mean_furthest_rank", "conversion_rate", "share_deep"]
        ].to_string(index=False)
    )

    labeled = fit_segmentation(users)
    _section("PROCESSED — segment assignments")
    print(labeled[["anonymous_id", "persona", "kmeans_label", "gmm_label"]].to_string(index=False))
    print(f"\nNote: chosen k={labeled.attrs['k']}; "
          "toy recovers bouncers / regular_readers / converters (K-Means and GMM agree).")


if __name__ == "__main__":
    main()