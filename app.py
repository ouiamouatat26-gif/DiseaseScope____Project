from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from collections import Counter
import re

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]


def get_collection():
    return db["articles_tous"]


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/api/overview")
def overview():
    col = get_collection()
    total = col.count_documents({})
    sources = list(col.distinct("source"))
    diseases = list(col.distinct("maladie"))
    return jsonify({
        "total_articles": total,
        "total_sources": len(sources),
        "total_diseases": len(diseases),
    })


@app.route("/api/by_disease")
def by_disease():
    col = get_collection()
    pipeline = [
        {"$group": {"_id": "$maladie", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    results = list(col.aggregate(pipeline))
    return jsonify({
        "labels": [r["_id"] or "Unknown" for r in results],
        "values": [r["count"] for r in results],
    })


@app.route("/api/by_source")
def by_source():
    col = get_collection()
    pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    results = list(col.aggregate(pipeline))
    return jsonify({
        "labels": [r["_id"] or "Unknown" for r in results],
        "values": [r["count"] for r in results],
    })


@app.route("/api/by_content_type")
def by_content_type():
    col = get_collection()
    pipeline = [
        {"$group": {"_id": "$type_contenu", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    results = list(col.aggregate(pipeline))
    return jsonify({
        "labels": [r["_id"] or "non_classifie" for r in results],
        "values": [r["count"] for r in results],
    })


@app.route("/api/by_year")
def by_year():
    col = get_collection()
    articles = list(col.find({}, {"date_publication": 1, "_id": 0}))
    year_counts = Counter()
    for a in articles:
        date = str(a.get("date_publication", ""))
        match = re.search(r"(19|20)\d{2}", date)
        if match:
            year_counts[match.group()] += 1

    sorted_years = sorted(year_counts.items())
    return jsonify({
        "labels": [y for y, _ in sorted_years],
        "values": [c for _, c in sorted_years],
    })


@app.route("/api/top_keywords")
def top_keywords():
    col = get_collection()
    articles = list(col.find({}, {"mots_cles": 1, "_id": 0}))
    keyword_counts = Counter()
    disease_names = {
        "cancer", "diabetes", "alzheimer", "heart disease",
        "neurological diseases", "respiratory diseases",
        "eye diseases", "digestive diseases",
        "infectious diseases", "autoimmune diseases",
        "pubmed", "europe pmc", "who", "clinicaltrials", "medlineplus",
    }
    for a in articles:
        raw = a.get("mots_cles", "")
        if isinstance(raw, list):
            keywords = raw
        else:
            keywords = [k.strip() for k in str(raw).split("|") if k.strip()]
        for kw in keywords:
            kw_lower = kw.lower().strip()
            if kw_lower and kw_lower not in disease_names and len(kw_lower) > 3:
                keyword_counts[kw_lower] += 1

    top = keyword_counts.most_common(20)
    return jsonify({
        "labels": [k for k, _ in top],
        "values": [c for _, c in top],
    })


@app.route("/api/disease_source_matrix")
def disease_source_matrix():
    col = get_collection()
    pipeline = [
        {"$group": {"_id": {"disease": "$maladie", "source": "$source"}, "count": {"$sum": 1}}},
    ]
    results = list(col.aggregate(pipeline))

    diseases = sorted(col.distinct("maladie"))
    sources = sorted(col.distinct("source"))

    matrix = {d: {s: 0 for s in sources} for d in diseases}
    for r in results:
        d = r["_id"]["disease"]
        s = r["_id"]["source"]
        if d in matrix and s in matrix[d]:
            matrix[d][s] = r["count"]

    return jsonify({
        "diseases": diseases,
        "sources": sources,
        "matrix": [[matrix[d][s] for s in sources] for d in diseases],
    })


@app.route("/api/articles")
def articles():
    col = get_collection()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    disease = request.args.get("disease", "")
    source = request.args.get("source", "")
    search = request.args.get("search", "")

    query = {}
    if disease:
        query["maladie"] = disease
    if source:
        query["source"] = source
    if search:
        query["$or"] = [
            {"titre": {"$regex": search, "$options": "i"}},
            {"resume": {"$regex": search, "$options": "i"}},
        ]

    total = col.count_documents(query)
    docs = list(
        col.find(query, {"_id": 0, "titre": 1, "maladie": 1, "source": 1,
                         "date_publication": 1, "journal": 1, "lien": 1, "type_contenu": 1})
        .skip((page - 1) * per_page)
        .limit(per_page)
    )

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "articles": docs,
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
