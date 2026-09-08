from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from marketplace.model import MarketplaceItem
from marketplace.image_upload import save_image
from marketplace.marketplace_ranker import rank_marketplace_items
from osm.osm_service import fetch_nearby_places
from ml.bert_shop_ranker import rank_shops_bert

marketplace_bp = Blueprint("marketplace", __name__)

# --------------------------------------------------
# GET ALL ITEMS
# --------------------------------------------------
@marketplace_bp.route("/api/marketplace", methods=["GET"])
@jwt_required(optional=True)
def get_items():
    items = MarketplaceItem.query.order_by(
        MarketplaceItem.created_at.desc()
    ).all()

    return jsonify([
        {
            "id": i.id,
            "description": i.description,
            "price": i.price,
            "image_url": i.image_url,
            "contact_info": i.contact_info,
            "status": i.status,
            "seller_id": i.seller_id,
            "category": i.category
        } for i in items
    ])


# --------------------------------------------------
# POST ITEM
# --------------------------------------------------
@marketplace_bp.route("/api/marketplace", methods=["POST"])
@jwt_required()
def post_item():
    seller_id = int(get_jwt_identity())

    description = request.form.get("description")
    category = request.form.get("category")
    contact = request.form.get("contact")
    price = request.form.get("price")

    image = request.files.get("image")
    image_url = save_image(image) if image else None

    item = MarketplaceItem(
        seller_id=seller_id,
        description=description,
        category=category,
        contact_info=contact,
        price=price,
        image_url=image_url,
        status="available"
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({"success": True})


# --------------------------------------------------
# UPDATE STATUS
# --------------------------------------------------
@marketplace_bp.route("/api/marketplace/<int:item_id>/status", methods=["PATCH"])
@jwt_required()
def update_status(item_id):
    user_id = int(get_jwt_identity())
    item = MarketplaceItem.query.get_or_404(item_id)

    if item.seller_id != user_id:
        return jsonify({"error": "Not allowed"}), 403

    status = request.json.get("status")
    if status not in ["available", "sold"]:
        return jsonify({"error": "Invalid status"}), 400

    item.status = status
    db.session.commit()

    return jsonify({"success": True, "status": status})


# --------------------------------------------------
# SEARCH MARKETPLACE (SAFE VERSION)
# --------------------------------------------------
@marketplace_bp.route("/api/marketplace/search", methods=["POST"])
@jwt_required(optional=True)
def search_marketplace():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({
            "items": [],
            "nearby_shops": []
        })

    # -----------------------------
    # Fetch DB items
    # -----------------------------
    items = MarketplaceItem.query.all()

    # -----------------------------
    # SAFE ITEM RANKING
    # -----------------------------
    try:
        ranked_items = rank_marketplace_items(query, items)
    except Exception as e:
        print("Marketplace ML ranking failed:", e)
        ranked_items = [
            {
                "id": i.id,
                "description": i.description,
                "category": i.category,
                "image_url": i.image_url,
                "contact_info": i.contact_info,
                "price": i.price,
                "status": i.status,
                "seller_id": i.seller_id,
                "semantic_score": 0.0
            }
            for i in items
            if query.lower() in i.description.lower()
        ]

    # -----------------------------
    # SAFE SHOP SEARCH
    # -----------------------------
    try:
        places = fetch_nearby_places()
        nearby_shops = rank_shops_bert(query, places)
    except Exception as e:
        print("Nearby shop ranking failed:", e)
        nearby_shops = []

    return jsonify({
        "items": ranked_items,
        "nearby_shops": nearby_shops
    })
