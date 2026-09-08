from marketplace.category_utils import (
    detect_category_from_query,
    is_pure_category_query
)

CE_THRESHOLD = 0.25

_bi_encoder = None
_cross_encoder = None

def _get_models():
    global _bi_encoder, _cross_encoder
    if _bi_encoder is None or _cross_encoder is None:
        from sentence_transformers import SentenceTransformer, CrossEncoder
        _bi_encoder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _bi_encoder, _cross_encoder

def rank_marketplace_items(query, items, top_k=10):
    if not items or not query.strip():
        return []

    query = query.lower().strip()

    query_category = detect_category_from_query(query)
    pure_category_query = (
        query_category is not None and
        is_pure_category_query(query, query_category)
    )

    if query_category:
        items = [i for i in items if i.category == query_category]

    if not items:
        return []

    texts = [
        f"{i.description}. Category: {i.category}. Marketplace product."
        for i in items
    ]

    bi_encoder, cross_encoder = _get_models()
    from sentence_transformers import util

    q_emb = bi_encoder.encode(query, convert_to_tensor=True)
    i_embs = bi_encoder.encode(texts, convert_to_tensor=True)

    cos_scores = util.cos_sim(q_emb, i_embs)[0]
    TOP_N = min(20, len(items))
    top_results = cos_scores.topk(k=TOP_N)

    candidates = []
    for idx in top_results.indices:
        candidates.append({
            "item": items[int(idx)],
            "text": texts[int(idx)]
        })

    cross_inputs = [(query, c["text"]) for c in candidates]
    cross_scores = cross_encoder.predict(cross_inputs)

    results = []
    for c, score in zip(candidates, cross_scores):
        ce_score = float(score)
        if not pure_category_query and ce_score < CE_THRESHOLD:
            continue

        item = c["item"]
        results.append({
            "id": item.id,
            "description": item.description,
            "category": item.category,
            "image_url": item.image_url,
            "contact_info": item.contact_info,
            "price": item.price,
            "status": item.status,
            "seller_id": item.seller_id,
            "semantic_score": ce_score
        })

    results.sort(key=lambda x: -x["semantic_score"])
    return results[:top_k]
