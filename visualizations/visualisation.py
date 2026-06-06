import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from collections import Counter
import re
import os

DATA_PATH = "data/clean_articles.csv"
OUTPUT_DIR = "visualizations"

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

DISEASE_NAMES = {
    "cancer", "diabetes", "alzheimer", "heart disease",
    "neurological diseases", "respiratory diseases",
    "eye diseases", "digestive diseases",
    "infectious diseases", "autoimmune diseases",
    "pubmed", "europe pmc", "who", "clinicaltrials", "medlineplus",
}

plt.style.use("dark_background")
COLORS = [
    "#60a5fa", "#4ade80", "#c084fc", "#fb923c", "#f472b6",
    "#34d399", "#fbbf24", "#a78bfa", "#38bdf8", "#f87171",
]


def save(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# 1. Articles by disease (horizontal bar)
print("1. Articles by disease...")
disease_counts = df["maladie"].value_counts()
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(disease_counts.index, disease_counts.values,
               color=COLORS[:len(disease_counts)], edgecolor="none", height=0.6)
ax.set_xlabel("Number of articles", color="#94a3b8")
ax.set_title("Articles by Disease", fontsize=14, color="white", pad=15)
ax.tick_params(colors="#94a3b8")
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
for bar, val in zip(bars, disease_counts.values):
    ax.text(val + 1, bar.get_y() + bar.get_height() / 2,
            str(val), va="center", color="#94a3b8", fontsize=9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
save(fig, "1_articles_by_disease.png")


# 2. Articles by source (pie chart)
print("2. Articles by source...")
source_counts = df["source"].value_counts()
fig, ax = plt.subplots(figsize=(8, 6))
wedges, texts, autotexts = ax.pie(
    source_counts.values,
    labels=source_counts.index,
    colors=COLORS[:len(source_counts)],
    autopct="%1.1f%%",
    startangle=140,
    pctdistance=0.82,
    wedgeprops={"edgecolor": "#0f1117", "linewidth": 2},
)
for text in texts:
    text.set_color("#94a3b8")
for autotext in autotexts:
    autotext.set_color("white")
    autotext.set_fontsize(9)
ax.set_title("Articles by Source", fontsize=14, color="white", pad=15)
save(fig, "2_articles_by_source.png")


# 3. Publication timeline (line chart)
print("3. Publication timeline...")
years = []
for date in df["date_publication"].dropna():
    match = re.search(r"(19|20)\d{2}", str(date))
    if match:
        years.append(int(match.group()))

year_counts = Counter(years)
sorted_years = sorted(year_counts.items())
if sorted_years:
    x = [y for y, _ in sorted_years]
    y = [c for _, c in sorted_years]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(x, y, color="#60a5fa", linewidth=2, marker="o", markersize=4)
    ax.fill_between(x, y, alpha=0.15, color="#60a5fa")
    ax.set_xlabel("Year", color="#94a3b8")
    ax.set_ylabel("Number of articles", color="#94a3b8")
    ax.set_title("Publication Timeline", fontsize=14, color="white", pad=15)
    ax.tick_params(colors="#94a3b8")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    save(fig, "3_publication_timeline.png")


# 4. Top 20 keywords (horizontal bar)
print("4. Top keywords...")
keyword_counts = Counter()
for raw in df["mots_cles"].dropna():
    for kw in str(raw).split("|"):
        kw = kw.strip().lower()
        if kw and kw not in DISEASE_NAMES and len(kw) > 3:
            keyword_counts[kw] += 1

top_kw = keyword_counts.most_common(20)
kw_labels = [k for k, _ in top_kw]
kw_values = [v for _, v in top_kw]

fig, ax = plt.subplots(figsize=(10, 7))
ax.barh(kw_labels[::-1], kw_values[::-1],
        color="#c084fc", edgecolor="none", height=0.65)
ax.set_xlabel("Occurrences", color="#94a3b8")
ax.set_title("Top 20 Keywords", fontsize=14, color="white", pad=15)
ax.tick_params(colors="#94a3b8")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
save(fig, "4_top_keywords.png")


# 5. Disease vs Source heatmap (stacked bar)
print("5. Disease vs Source coverage...")
matrix = df.groupby(["maladie", "source"]).size().unstack(fill_value=0)
fig, ax = plt.subplots(figsize=(12, 7))
bottom = pd.Series([0] * len(matrix), index=matrix.index)
for i, source in enumerate(matrix.columns):
    ax.bar(matrix.index, matrix[source], bottom=bottom,
           label=source, color=COLORS[i % len(COLORS)], edgecolor="none")
    bottom += matrix[source]
ax.set_xlabel("Disease", color="#94a3b8")
ax.set_ylabel("Number of articles", color="#94a3b8")
ax.set_title("Coverage by Disease and Source", fontsize=14, color="white", pad=15)
ax.tick_params(axis="x", rotation=30, colors="#94a3b8")
ax.tick_params(axis="y", colors="#94a3b8")
ax.legend(fontsize=9, framealpha=0.2)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
save(fig, "5_disease_source_coverage.png")


# 6. Content type distribution (bar)
print("6. Content type distribution...")
type_counts = df["type_contenu"].value_counts()
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(type_counts.index, type_counts.values,
       color=COLORS[:len(type_counts)], edgecolor="none", width=0.5)
ax.set_ylabel("Number of articles", color="#94a3b8")
ax.set_title("Content Type Distribution", fontsize=14, color="white", pad=15)
ax.tick_params(axis="x", rotation=20, colors="#94a3b8")
ax.tick_params(axis="y", colors="#94a3b8")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
save(fig, "6_content_types.png")


print(f"\nDone. All charts saved in '{OUTPUT_DIR}/'")
print(f"Total articles: {len(df)}")
print(f"Sources: {df['source'].nunique()}")
print(f"Diseases: {df['maladie'].nunique()}")