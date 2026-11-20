import secrets
from datetime import datetime, timezone
import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from dotenv import load_dotenv
from supabase import create_client


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be set in the .env file."
    )


# =========================================================
# SUPABASE CONNECTION
# =========================================================

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "shopzone-development-secret-key"
)


# =========================================================
# PRODUCT FUNCTIONS
# =========================================================

def get_products():
    """
    Get all products from Supabase, including product images.
    """

    try:
        response = (
            supabase
            .table("products")
            .select("*")
            .order("id")
            .execute()
        )

        print("SUPABASE RESPONSE:", response.data)
        print("NUMBER OF PRODUCTS:", len(response.data or []))

        products = {}

        for product in response.data or []:

            product_id = product["id"]

            products[product_id] = {
                "name": product.get("name", ""),
                "category": product.get("category", ""),
                "price": float(product.get("price") or 0),
                "image_url": product.get("image_url") or "",
                "rating": float(product.get("rating") or 0),
                "description": product.get("description", ""),
                "ram": product.get("ram", "N/A"),
                "storage": product.get("storage", "N/A"),
                "processor": product.get("processor", "N/A")
            }

        return products

    except Exception as e:
        print("Products database error:", e)
        return {}


def get_product(product_id):
    """
    Get one product from Supabase, including its image.
    """

    try:
        response = (
            supabase
            .table("products")
            .select("*")
            .eq("id", product_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        product = response.data[0]

        return {
            "name": product.get("name", ""),
            "category": product.get("category", ""),
            "price": float(product.get("price") or 0),
            "image_url": product.get("image_url") or "",
            "rating": float(product.get("rating") or 0),
            "description": product.get("description", ""),
            "ram": product.get("ram", "N/A"),
            "storage": product.get("storage", "N/A"),
            "processor": product.get("processor", "N/A")
        }

    except Exception as e:
        print("Product database error:", e)
        return None

# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    recent_products = []
    recommended_products = []
    popular_products = []

    user = session.get("user")

    try:
        # GET ALL PRODUCTS
        all_products = get_products()

        # =============================================
        # RECENTLY VIEWED AND RECOMMENDED FOR YOU
        # =============================================

        if user:

            views_response = (
                supabase
                .table("product_views")
                .select("product_id, viewed_at")
                .eq("user_id", user["id"])
                .order("viewed_at", desc=True)
                .limit(30)
                .execute()
            )

            seen_product_ids = set()
            category_counts = {}

            for view in views_response.data or []:

                product_id = view.get("product_id")

                if product_id is None:
                    continue

                product_id = int(product_id)
                seen_product_ids.add(product_id)

                product = all_products.get(product_id)

                if not product:
                    continue

                category = product.get("category", "")

                if category:
                    category_counts[category] = (
                        category_counts.get(category, 0) + 1
                    )

                # RECENTLY VIEWED
                if not any(
                    item["id"] == product_id
                    for item in recent_products
                ):

                    recent_item = product.copy()
                    recent_item["id"] = product_id

                    recent_products.append(recent_item)

            recent_products = recent_products[:4]

            # RECOMMENDED FOR YOU
            if category_counts:

                sorted_categories = sorted(
                    category_counts.items(),
                    key=lambda item: item[1],
                    reverse=True
                )

                category_ranking = {
                    category: index
                    for index, (category, count)
                    in enumerate(sorted_categories)
                }

                for product_id, product in all_products.items():

                    if int(product_id) in seen_product_ids:
                        continue

                    category = product.get("category", "")

                    if category in category_ranking:

                        item = product.copy()
                        item["id"] = int(product_id)

                        recommended_products.append(item)

                recommended_products.sort(
                    key=lambda item: (
                        category_ranking.get(
                            item.get("category", ""), 999
                        ),
                        -float(item.get("rating") or 0)
                    )
                )

                recommended_products = recommended_products[:4]

        # =============================================
        # POPULAR PICKS
        # =============================================

        popular_response = (
            supabase
            .table("product_views")
            .select("product_id")
            .execute()
        )

        product_view_counts = {}

        for view in popular_response.data or []:

            product_id = view.get("product_id")

            if product_id is None:
                continue

            product_id = int(product_id)

            product_view_counts[product_id] = (
                product_view_counts.get(product_id, 0) + 1
            )

        # Sort products by total number of views.
        # Use rating as a secondary sorting factor.
        sorted_popular = sorted(
            product_view_counts.items(),
            key=lambda item: (
                -item[1],
                -float(
                    all_products.get(item[0], {}).get("rating") or 0
                )
            )
        )

        for product_id, view_count in sorted_popular:

            product = all_products.get(product_id)

            if product:

                item = product.copy()
                item["id"] = product_id
                item["view_count"] = view_count

                popular_products.append(item)

            if len(popular_products) == 4:
                break

    except Exception as e:

        print("Personalized product feed error:", e)

    return render_template(
        "index.html",
        recent_products=recent_products,
        recommended_products=recommended_products,
        popular_products=popular_products,
        logged_in=bool(user)
    )

    # =========================================================
# TRUST PROFILE
# =========================================================

@app.route("/trust-profile", methods=["GET", "POST"])
def trust_profile():

    user = session.get("user")

    if not user:
        return redirect(url_for("login"))

    error = ""
    submitted = False

    # =============================================
    # SUBMIT CUSTOMER REVIEW
    # =============================================

    if request.method == "POST":

        order_id = request.form.get("order_id", "").strip()
        rating = request.form.get("rating", "").strip()
        review = request.form.get("review", "").strip()

        if not order_id or not rating or not review:
            return redirect(
                url_for("trust_profile", error="required")
            )

        try:
            order_id = int(order_id)
            rating = int(rating)

        except (TypeError, ValueError):
            return redirect(
                url_for("trust_profile", error="invalid")
            )

        if rating < 1 or rating > 5:
            return redirect(
                url_for("trust_profile", error="invalid")
            )

        if len(review) > 1000:
            return redirect(
                url_for("trust_profile", error="too_long")
            )

        try:
            # Verify that this order belongs to the logged-in user
            # and has already been delivered.
            order_response = (
                supabase
                .table("orders")
                .select("id, user_id, status")
                .eq("id", order_id)
                .eq("user_id", user["id"])
                .eq("status", "Delivered")
                .limit(1)
                .execute()
            )

            if not order_response.data:
                return redirect(
                    url_for("trust_profile", error="not_eligible")
                )

            # Prevent duplicate reviews for the same order.
            existing_review = (
                supabase
                .table("store_reviews")
                .select("id")
                .eq("order_id", order_id)
                .limit(1)
                .execute()
            )

            if existing_review.data:
                return redirect(
                    url_for("trust_profile", error="duplicate")
                )

            # Save the verified purchase review.
            supabase.table("store_reviews").insert({
                "user_id": user["id"],
                "order_id": order_id,
                "rating": rating,
                "review": review
            }).execute()

            return redirect(
                url_for("trust_profile", submitted="1")
            )

        except Exception as e:
            print("Trust Profile review error:", e)

            return redirect(
                url_for("trust_profile", error="submit_failed")
            )

    # =============================================
    # LOAD TRUST PROFILE DATA
    # =============================================

    total_orders = 0
    delivered_orders = 0
    completion_rate = 0
    average_rating = 0
    total_reviews = 0
    trust_score = None

    reviews = []
    available_orders = []

    try:
        # Get store orders.
        orders_response = (
            supabase
            .table("orders")
            .select("id, user_id, status, created_at")
            .execute()
        )

        orders_data = orders_response.data or []

        total_orders = len(orders_data)

        delivered_orders = sum(
            1 for order in orders_data
            if order.get("status") == "Delivered"
        )

        if total_orders > 0:
            completion_rate = round(
                (delivered_orders / total_orders) * 100,
                1
            )

        # Get all customer reviews.
        reviews_response = (
            supabase
            .table("store_reviews")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        reviews_data = reviews_response.data or []

        total_reviews = len(reviews_data)

        if total_reviews > 0:
            average_rating = round(
                sum(
                    int(review.get("rating") or 0)
                    for review in reviews_data
                ) / total_reviews,
                1
            )

            satisfaction_score = (
                average_rating / 5
            ) * 100

            trust_score = round(
                (completion_rate * 0.60)
                + (satisfaction_score * 0.40)
            )

        # Get reviewer names.
        reviewer_ids = list({
            review["user_id"]
            for review in reviews_data
            if review.get("user_id") is not None
        })

        reviewer_names = {}

        if reviewer_ids:
            users_response = (
                supabase
                .table("users")
                .select("id, name")
                .in_("id", reviewer_ids)
                .execute()
            )

            reviewer_names = {
                item["id"]: item.get("name", "Customer")
                for item in (users_response.data or [])
            }

        # Attach reviewer names to reviews.
        for review_item in reviews_data:

            review_item["reviewer_name"] = (
                reviewer_names.get(
                    review_item.get("user_id"),
                    "Customer"
                )
            )

            reviews.append(review_item)

        # Get delivered orders belonging to the logged-in user.
        user_delivered_orders = (
            supabase
            .table("orders")
            .select("id, created_at, total")
            .eq("user_id", user["id"])
            .eq("status", "Delivered")
            .order("created_at", desc=True)
            .execute()
        )

        # Find which orders have already been reviewed.
        reviewed_order_ids = {
            review.get("order_id")
            for review in reviews_data
        }

        for order in user_delivered_orders.data or []:

            if order["id"] not in reviewed_order_ids:
                available_orders.append(order)

    except Exception as e:
        print("Trust Profile database error:", e)

        error = "Unable to load Trust Profile information. Please try again."

    return render_template(
        "trust_profile.html",
        user=user,
        total_orders=total_orders,
        delivered_orders=delivered_orders,
        completion_rate=completion_rate,
        average_rating=average_rating,
        total_reviews=total_reviews,
        trust_score=trust_score,
        reviews=reviews,
        available_orders=available_orders,
        submitted=request.args.get("submitted") == "1",
        error=request.args.get("error") or error
    )


# =========================================================
# EDIT CUSTOMER REVIEW
# =========================================================

@app.route(
    "/trust-profile/review/<int:review_id>/edit",
    methods=["POST"]
)
def edit_trust_review(review_id):

    user = session.get("user")

    if not user:
        return redirect(url_for("login"))

    rating = request.form.get("rating", "").strip()
    review = request.form.get("review", "").strip()

    try:
        rating = int(rating)

    except (TypeError, ValueError):
        return redirect(
            url_for("trust_profile", error="invalid")
        )

    if rating < 1 or rating > 5 or not review:
        return redirect(
            url_for("trust_profile", error="invalid")
        )

    if len(review) > 1000:
        return redirect(
            url_for("trust_profile", error="too_long")
        )

    try:
        # Update only the review owned by the logged-in user.
        response = (
            supabase
            .table("store_reviews")
            .update({
                "rating": rating,
                "review": review
            })
            .eq("id", review_id)
            .eq("user_id", user["id"])
            .execute()
        )

        if not response.data:
            return redirect(
                url_for("trust_profile", error="edit_failed")
            )

        return redirect(
            url_for("trust_profile", updated_review="1")
        )

    except Exception as e:
        print("Trust review edit error:", e)

        return redirect(
            url_for("trust_profile", error="edit_failed")
        )


# =========================================================
# DELETE CUSTOMER REVIEW
# =========================================================

@app.route(
    "/trust-profile/review/<int:review_id>/delete",
    methods=["POST"]
)
def delete_trust_review(review_id):

    user = session.get("user")

    if not user:
        return redirect(url_for("login"))

    try:
        # Delete only the review owned by the logged-in user.
        response = (
            supabase
            .table("store_reviews")
            .delete()
            .eq("id", review_id)
            .eq("user_id", user["id"])
            .execute()
        )

        if not response.data:
            return redirect(
                url_for("trust_profile", error="delete_failed")
            )

        return redirect(
            url_for("trust_profile", deleted_review="1")
        )

    except Exception as e:
        print("Trust review delete error:", e)

        return redirect(
            url_for("trust_profile", error="delete_failed")
        )


# =========================================================
# PRODUCTS
# =========================================================

@app.route("/products")
def products_page():

    print("PRODUCTS ROUTE ACCESSED")

    products = get_products()

    print("PRODUCTS RECEIVED:", len(products))

    return render_template(
        "products.html",
        products=products
    )

# =========================================================
# ADVANCED BUDGET PLANNER
# =========================================================

@app.route("/budget-planner")
def budget_planner():

    products = get_products()

    return render_template(
        "budget_planner.html",
        products=products
    )


# =========================================================
# COMPARE PRODUCTS
# =========================================================

@app.route("/compare")
def compare_products():

    raw_ids = request.args.getlist("id")
    # Require 2 to 4 distinct product IDs.
    if not 2 <= len(raw_ids) <= 4:
        return render_template(
            "compare.html",
            products=[],
            error="Please select between 2 and 4 products to compare."
        ), 400

    try:
        product_ids = [int(product_id) for product_id in raw_ids]
    except (TypeError, ValueError):
        return render_template(
            "compare.html",
            products=[],
            error="Invalid product selection. Please select your products again."
        ), 400

    if len(set(product_ids)) != len(product_ids):
        return render_template(
            "compare.html",
            products=[],
            error="Duplicate products are not allowed."
        ), 400

    try:
        response = (
            supabase
            .table("products")
            .select("*")
            .in_("id", product_ids)
            .execute()
        )

        products_by_id = {
            int(product["id"]): product
            for product in (response.data or [])
        }

    except Exception as e:
        print("Compare products database error:", e)

        return render_template(
            "compare.html",
            products=[],
            error="Unable to load products for comparison. Please try again."
        ), 500

    if len(products_by_id) != len(product_ids):
        return render_template(
            "compare.html",
            products=[],
            error="One or more products could not be found. Please return to the product catalog."
        ), 404

    selected_products = [
        products_by_id[product_id]
        for product_id in product_ids
    ]


    # Check whether all selected products belong to the same category.
    categories = {
        (product.get("category") or "").strip().casefold()
        for product in selected_products
    }

    same_category = len(categories) == 1

    category_warning = None

    if not same_category:
        category_warning = (
            "The selected products belong to different categories. "
            "For a more accurate comparison, please choose products "
            "from the same category."
        )
    # Calculate a Best Value score using rating and affordability.
    # A higher rating and lower price contribute to a higher score.
    max_price = max(
        (float(p.get("price") or 0) for p in selected_products),
        default=0
    )

    for product in selected_products:
        try:
            price = float(product.get("price") or 0)
        except (TypeError, ValueError):
            price = 0

        try:
            rating = float(product.get("rating") or 0)
        except (TypeError, ValueError):
            rating = 0

        rating_score = max(0, min(rating, 5)) / 5

        if max_price > 0:
            affordability_score = 1 - (price / max_price)
        else:
            affordability_score = 0

        product["best_value_score"] = (
            rating_score * 0.70
            + affordability_score * 0.30
        ) * 100

    # Choose the product with the highest calculated score.
    best_value_product_id = max(
        selected_products,
        key=lambda p: p["best_value_score"]
    )["id"]

    return render_template(
        "compare.html",
        products=selected_products,
        best_value_product_id=best_value_product_id,
        same_category=same_category,
        category_warning=category_warning,
        error=None
    )




# =========================================================
# PRODUCT VIEW TRACKING
# =========================================================

def record_product_view(product_id):
    """
    Record product views in Supabase.
    """

    try:
        user = session.get("user")

        view_data = {
            "product_id": product_id,
            "user_id": user.get("id") if isinstance(user, dict) else None
        }

        supabase.table("product_views").insert(
            view_data
        ).execute()

        print("PRODUCT VIEW RECORDED:", product_id)

    except Exception as e:
        print("Product view tracking error:", e)


# =========================================================
# PRODUCT DETAILS AND PRODUCT REVIEWS
# =========================================================

@app.route(
    "/product/<int:product_id>",
    methods=["GET", "POST"]
)
def product_details(product_id):

    user = session.get("user")

    product = get_product(product_id)

    if product is None:
        return "Product not found", 404

    # =============================================
    # SUBMIT PRODUCT REVIEW
    # =============================================

    if request.method == "POST":

        if not user:
            return redirect(url_for("login"))

        order_id = request.form.get("order_id", "").strip()
        rating = request.form.get("rating", "").strip()
        review = request.form.get("review", "").strip()

        if not order_id or not rating or not review:
            return redirect(
                url_for(
                    "product_details",
                    product_id=product_id,
                    error="required"
                ) + "#product-reviews"
            )

        try:
            order_id = int(order_id)
            rating = int(rating)

        except (TypeError, ValueError):
            return redirect(
                url_for(
                    "product_details",
                    product_id=product_id,
                    error="invalid"
                ) + "#product-reviews"
            )

        if rating < 1 or rating > 5:
            return redirect(
                url_for(
                    "product_details",
                    product_id=product_id,
                    error="invalid"
                ) + "#product-reviews"
            )

        if len(review) > 1000:
            return redirect(
                url_for(
                    "product_details",
                    product_id=product_id,
                    error="too_long"
                ) + "#product-reviews"
            )

        try:

            # -----------------------------------------
            # VERIFY ORDER OWNERSHIP AND DELIVERY
            # -----------------------------------------

            order_response = (
                supabase
                .table("orders")
                .select("id, user_id, status")
                .eq("id", order_id)
                .eq("user_id", user["id"])
                .eq("status", "Delivered")
                .limit(1)
                .execute()
            )

            if not order_response.data:

                return redirect(
                    url_for(
                        "product_details",
                        product_id=product_id,
                        error="not_eligible"
                    ) + "#product-reviews"
                )

            # -----------------------------------------
            # VERIFY PRODUCT EXISTS IN THAT ORDER
            # -----------------------------------------

            order_item_response = (
                supabase
                .table("order_items")
                .select("id, product_id")
                .eq("order_id", order_id)
                .eq("product_id", product_id)
                .limit(1)
                .execute()
            )

            if not order_item_response.data:

                return redirect(
                    url_for(
                        "product_details",
                        product_id=product_id,
                        error="product_not_purchased"
                    ) + "#product-reviews"
                )

            # -----------------------------------------
            # PREVENT DUPLICATE PRODUCT REVIEWS
            # -----------------------------------------

            existing_review = (
                supabase
                .table("product_reviews")
                .select("id")
                .eq("order_id", order_id)
                .eq("product_id", product_id)
                .limit(1)
                .execute()
            )

            if existing_review.data:

                return redirect(
                    url_for(
                        "product_details",
                        product_id=product_id,
                        error="duplicate"
                    ) + "#product-reviews"
                )

            # -----------------------------------------
            # SAVE PRODUCT REVIEW
            # -----------------------------------------

            supabase.table("product_reviews").insert({
                "user_id": user["id"],
                "product_id": product_id,
                "order_id": order_id,
                "rating": rating,
                "review": review
            }).execute()

            print(
                "PRODUCT REVIEW SUBMITTED:",
                product_id,
                "BY USER:",
                user["id"]
            )

            return redirect(
                url_for(
                    "product_details",
                    product_id=product_id,
                    submitted="1"
                ) + "#product-reviews"
            )

        except Exception as e:

            print("Product review submission error:", e)

            return redirect(
                url_for(
                    "product_details",
                    product_id=product_id,
                    error="submit_failed"
                ) + "#product-reviews"
            )

    # =============================================
    # RECORD PRODUCT VIEW
    # =============================================

    record_product_view(product_id)

    # =============================================
    # LOAD PRODUCT REVIEWS
    # =============================================

    product_reviews = []
    product_review_count = 0
    average_product_rating = product.get("rating", 0)

    try:

        reviews_response = (
            supabase
            .table("product_reviews")
            .select("*")
            .eq("product_id", product_id)
            .order("created_at", desc=True)
            .execute()
        )

        product_reviews = reviews_response.data or []

        product_review_count = len(product_reviews)

        # Calculate average rating from actual reviews.
        if product_reviews:

            total_rating = sum(
                int(item.get("rating") or 0)
                for item in product_reviews
            )

            average_product_rating = round(
                total_rating / product_review_count,
                1
            )

        # -----------------------------------------
        # GET REVIEWER NAMES
        # -----------------------------------------

        reviewer_ids = list({
            item["user_id"]
            for item in product_reviews
            if item.get("user_id") is not None
        })

        reviewer_names = {}

        if reviewer_ids:

            users_response = (
                supabase
                .table("users")
                .select("id, name")
                .in_("id", reviewer_ids)
                .execute()
            )

            reviewer_names = {
                item["id"]: item.get("name", "Customer")
                for item in (users_response.data or [])
            }

        # Attach customer names to product reviews.
        for item in product_reviews:

            item["reviewer_name"] = reviewer_names.get(
                item.get("user_id"),
                "ShopZone Customer"
            )

    except Exception as e:

        print("Product reviews loading error:", e)

        product_reviews = []
        product_review_count = 0

    # =============================================
    # FIND ELIGIBLE ORDERS FOR PRODUCT REVIEW
    # =============================================

    eligible_orders = []

    if user:

        try:

            # Get only delivered orders belonging to this user.
            delivered_orders_response = (
                supabase
                .table("orders")
                .select("id, created_at")
                .eq("user_id", user["id"])
                .eq("status", "Delivered")
                .order("created_at", desc=True)
                .execute()
            )

            delivered_orders = (
                delivered_orders_response.data or []
            )

            delivered_order_ids = [
                order["id"]
                for order in delivered_orders
            ]

            if delivered_order_ids:

                # Find orders containing this exact product.
                order_items_response = (
                    supabase
                    .table("order_items")
                    .select("order_id, product_id")
                    .in_("order_id", delivered_order_ids)
                    .eq("product_id", product_id)
                    .execute()
                )

                purchased_order_ids = {
                    item["order_id"]
                    for item in (order_items_response.data or [])
                }

                # Get existing reviews for this product.
                reviewed_response = (
                    supabase
                    .table("product_reviews")
                    .select("order_id")
                    .eq("product_id", product_id)
                    .in_("order_id", delivered_order_ids)
                    .execute()
                )

                reviewed_order_ids = {
                    item["order_id"]
                    for item in (reviewed_response.data or [])
                }

                # Only orders that:
                # 1. Belong to the logged-in user.
                # 2. Are Delivered.
                # 3. Contain this product.
                # 4. Have not reviewed this product yet.

                for order in delivered_orders:

                    order_id = order["id"]

                    if (
                        order_id in purchased_order_ids
                        and order_id not in reviewed_order_ids
                    ):

                        eligible_orders.append(order)

        except Exception as e:

            print("Eligible product orders error:", e)

    # =============================================
    # GET SIMILAR PRODUCTS
    # =============================================

    all_products = get_products()
    similar_products = []

    current_category = str(
        product.get("category", "")
    ).strip().lower()

    for similar_id, similar_product in all_products.items():

        if int(similar_id) == product_id:
            continue

        similar_category = str(
            similar_product.get("category", "")
        ).strip().lower()

        if similar_category == current_category:

            item = similar_product.copy()
            item["id"] = int(similar_id)

            similar_products.append(item)

    # Show higher-rated products first.
    similar_products.sort(
        key=lambda item: item.get("rating", 0),
        reverse=True
    )

    similar_products = similar_products[:4]

    # =============================================
    # REVIEW MESSAGES
    # =============================================

    review_error_messages = {
        "required": "Please complete all review fields.",
        "invalid": "Invalid rating or review information.",
        "too_long": "Your review must not exceed 1,000 characters.",
        "not_eligible": "Only customers with a delivered order can review.",
        "product_not_purchased": "This product was not found in your selected order.",
        "duplicate": "You have already reviewed this product for that order.",
        "submit_failed": "Unable to submit your review. Please try again."
    }

    review_error = review_error_messages.get(
        request.args.get("error"),
        ""
    )

    # =============================================
    # DISPLAY PRODUCT DETAILS
    # =============================================

    return render_template(
        "product_details.html",
        product=product,
        product_id=product_id,
        similar_products=similar_products,

        product_reviews=product_reviews,
        product_review_count=product_review_count,
        average_product_rating=average_product_rating,

        eligible_orders=eligible_orders,

        review_error=review_error,
        review_submitted=request.args.get("submitted") == "1"
    )

# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    error = ""

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            error = "Please fill in all required fields."

            return render_template(
                "login.html",
                error=error
            )

        try:

            response = (
                supabase
                .table("users")
                .select("id, name, email, password")
                .eq("email", email)
                .limit(1)
                .execute()
            )

            user = (
                response.data[0]
                if response.data
                else None
            )

        except Exception as e:

            print(
                "Login database error:",
                e
            )

            error = (
                "Unable to connect to the database."
            )

            return render_template(
                "login.html",
                error=error
            )

        if user is None:

            error = "Invalid email or password."

            return render_template(
                "login.html",
                error=error
            )

        if not check_password_hash(
            user["password"],
            password
        ):

            error = "Invalid email or password."

            return render_template(
                "login.html",
                error=error
            )

        session["user"] = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }

        return redirect(
            url_for("home")
        )

    return render_template(
        "login.html",
        error=error
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    error = ""

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if (
            not name
            or not email
            or not password
            or not confirm_password
        ):

            error = (
                "Please fill in all required fields."
            )

            return render_template(
                "register.html",
                error=error
            )

        if password != confirm_password:

            error = "Passwords do not match."

            return render_template(
                "register.html",
                error=error
            )

        if len(password) < 6:

            error = (
                "Password must be at least 6 characters."
            )

            return render_template(
                "register.html",
                error=error
            )

        try:

            existing_user = (
                supabase
                .table("users")
                .select("id")
                .eq("email", email)
                .limit(1)
                .execute()
            )

            if existing_user.data:

                error = (
                    "An account with this email already exists."
                )

                return render_template(
                    "register.html",
                    error=error
                )

            hashed_password = (
                generate_password_hash(password)
            )

            supabase.table("users").insert({
                "name": name,
                "email": email,
                "password": hashed_password
            }).execute()

        except Exception as e:

            print(
                "Registration database error:",
                e
            )

            error = (
                "Unable to create your account. "
                "Please try again."
            )

            return render_template(
                "register.html",
                error=error
            )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html",
        error=error
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.pop(
        "user",
        None
    )

    return redirect(
        url_for("home")
    )


# =========================================================
# MY PROFILE
# =========================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if not session.get("user"):
        return redirect(url_for("login"))

    user_id = session["user"]["id"]
    error = ""

    # =========================================
    # LOAD USER PROFILE
    # =========================================

    try:
        response = (
            supabase
            .table("users")
            .select(
                "id, name, email, password, phone, address_line, "
                "barangay, city, province, postal_code, created_at"
            )
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

        user_data = response.data[0] if response.data else None

        if not user_data:
            session.pop("user", None)
            return redirect(url_for("login"))

    except Exception as e:
        print("Profile loading error:", e)
        return "Unable to load profile. Please try again."

    # =========================================
    # UPDATE PROFILE / CHANGE PASSWORD / REDEEM
    # =========================================

    if request.method == "POST":

        action = request.form.get("action", "update_profile")

        # UPDATE PERSONAL INFORMATION
        if action == "update_profile":

            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            address_line = request.form.get("address_line", "").strip()
            barangay = request.form.get("barangay", "").strip()
            city = request.form.get("city", "").strip()
            province = request.form.get("province", "").strip()
            postal_code = request.form.get("postal_code", "").strip()

            if not name:
                error = "Name is required."

            elif len(name) > 100:
                error = "Name is too long."

            else:
                try:
                    (
                        supabase
                        .table("users")
                        .update({
                            "name": name,
                            "phone": phone,
                            "address_line": address_line,
                            "barangay": barangay,
                            "city": city,
                            "province": province,
                            "postal_code": postal_code,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        })
                        .eq("id", user_id)
                        .execute()
                    )

                    session["user"]["name"] = name

                    return redirect(
                        url_for("profile", updated="1")
                    )

                except Exception as e:
                    print("Profile update error:", e)
                    error = "Unable to update profile."

        # CHANGE PASSWORD
        elif action == "change_password":

            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not current_password or not new_password or not confirm_password:
                error = "Please fill in all password fields."

            elif not check_password_hash(
                user_data["password"],
                current_password
            ):
                error = "Current password is incorrect."

            elif len(new_password) < 8:
                error = "New password must be at least 8 characters."

            elif new_password != confirm_password:
                error = "New passwords do not match."

            else:
                try:
                    (
                        supabase
                        .table("users")
                        .update({
                            "password": generate_password_hash(new_password),
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        })
                        .eq("id", user_id)
                        .execute()
                    )

                    return redirect(
                        url_for("profile", password_changed="1")
                    )

                except Exception as e:
                    print("Password update error:", e)
                    error = "Unable to change password."

        # REDEEM REWARD POINTS
        elif action == "redeem_rewards":

            try:
                redeem_points = int(
                    request.form.get("redeem_points", "0")
                )

                if redeem_points < 100:
                    error = "Minimum redemption is 100 points."

                elif redeem_points % 100 != 0:
                    error = "You can only redeem points in multiples of 100."

                else:
                    # Get latest reward transactions.
                    balance_response = (
                        supabase
                        .table("reward_transactions")
                        .select("transaction_type, points")
                        .eq("user_id", user_id)
                        .execute()
                    )

                    current_earned = 0
                    current_redeemed = 0

                    for transaction in balance_response.data or []:

                        transaction_type = str(
                            transaction.get("transaction_type", "")
                        ).lower()

                        points = abs(
                            int(transaction.get("points") or 0)
                        )

                        if transaction_type == "earn":
                            current_earned += points

                        elif transaction_type in [
                            "redeem",
                            "redeemed",
                            "spend",
                            "spent"
                        ]:
                            current_redeemed += points

                    current_balance = (
                        current_earned - current_redeemed
                    )

                    if redeem_points > current_balance:
                        error = "Insufficient reward points."

                    else:
                        discount_amount = redeem_points // 10

                        voucher_code = (
                            "SHOPZONE-" +
                            secrets.token_hex(4).upper()
                        )

                        # Record redemption.
                        (
                            supabase
                            .table("reward_transactions")
                            .insert({
                                "user_id": user_id,
                                "order_id": None,
                                "transaction_type": "redeem",
                                "points": redeem_points,
                                "voucher_code": voucher_code
                            })
                            .execute()
                        )

                        return redirect(
                            url_for(
                                "profile",
                                redeemed="1",
                                voucher=voucher_code,
                                discount=discount_amount
                            )
                        )

            except ValueError:
                error = "Please enter a valid number of points."

            except Exception as e:
                print("Reward redemption error:", e)
                error = "Unable to redeem points. Please try again."

    # =========================================
    # REFRESH PROFILE DATA
    # =========================================

    try:
        response = (
            supabase
            .table("users")
            .select(
                "id, name, email, phone, address_line, "
                "barangay, city, province, postal_code, created_at"
            )
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

        user_data = response.data[0]

    except Exception as e:
        print("Profile refresh error:", e)
        return "Unable to load profile."

    # =========================================
    # LOAD REWARD TRANSACTIONS
    # =========================================

    reward_transactions = []

    total_earned = 0
    total_redeemed = 0
    reward_balance = 0

    try:
        reward_response = (
            supabase
            .table("reward_transactions")
            .select(
                "id, user_id, order_id, transaction_type, "
                "points, voucher_code, created_at"
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        reward_transactions = reward_response.data or []

        for transaction in reward_transactions:

            transaction_type = str(
                transaction.get("transaction_type", "")
            ).lower()

            points = abs(
                int(transaction.get("points") or 0)
            )

            if transaction_type == "earn":
                total_earned += points

            elif transaction_type in [
                "redeem",
                "redeemed",
                "spend",
                "spent"
            ]:
                total_redeemed += points

        reward_balance = total_earned - total_redeemed

    except Exception as e:
        print("Reward loading error:", e)

    # =========================================
    # LOAD PURCHASE HISTORY
    # =========================================

    orders = []

    try:
        order_response = (
            supabase
            .table("orders")
            .select(
                "id, user_id, full_name, email, phone, "
                "address, payment_method, total, status, created_at"
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        orders = order_response.data or []

        order_ids = [
            order["id"]
            for order in orders
        ]

        if order_ids:

            items_response = (
                supabase
                .table("order_items")
                .select(
                    "id, order_id, product_id, "
                    "product_name, price, quantity"
                )
                .in_("order_id", order_ids)
                .execute()
            )

            all_order_items = items_response.data or []

            for order in orders:

                order["items"] = []

                for item in all_order_items:

                    if item["order_id"] == order["id"]:

                        item["subtotal"] = (
                            float(item.get("price") or 0)
                            * int(item.get("quantity") or 0)
                        )

                        order["items"].append(item)

        else:

            for order in orders:
                order["items"] = []

    except Exception as e:
        print("Purchase history loading error:", e)

    # =========================================
    # RENDER PROFILE
    # =========================================

    return render_template(
        "profile.html",
        profile=user_data,

        updated=request.args.get("updated"),
        password_changed=request.args.get("password_changed"),

        redeemed=request.args.get("redeemed"),
        redeemed_voucher=request.args.get("voucher"),
        redeemed_discount=request.args.get("discount"),

        error=error,

        reward_balance=reward_balance,
        total_earned=total_earned,
        total_redeemed=total_redeemed,
        reward_transactions=reward_transactions,

        orders=orders
    )



# =========================================================
# ADD TO CART
# =========================================================

@app.route(
    "/add-to-cart/<int:product_id>",
    methods=["POST"]
)
def add_to_cart(product_id):

    product = get_product(
        product_id
    )

    if product is None:
        return "Product not found", 404

    try:

        quantity = int(
            request.form.get(
                "quantity",
                1
            )
        )

    except ValueError:

        quantity = 1

    if quantity < 1:
        quantity = 1

    cart = session.get(
        "cart",
        {}
    )

    product_key = str(
        product_id
    )

    if product_key in cart:

        cart[product_key] += quantity

    else:

        cart[product_key] = quantity

    session["cart"] = cart

    # Show notification dot on Cart.
    session["cart_notification"] = True

    session.modified = True

    # Stay on the current page.
    return redirect(
        request.referrer
        or url_for("products_page")
    )


# =========================================================
# UPDATE CART
# =========================================================

@app.route(
    "/update-cart/<int:product_id>",
    methods=["POST"]
)
def update_cart(product_id):

    cart = session.get(
        "cart",
        {}
    )

    product_key = str(
        product_id
    )

    try:

        quantity = int(
            request.form.get(
                "quantity",
                1
            )
        )

    except ValueError:

        quantity = 1

    if quantity < 1:
        quantity = 1

    if product_key in cart:

        cart[product_key] = quantity

    session["cart"] = cart

    session.modified = True

    return redirect(
        url_for("cart")
    )


# =========================================================
# REMOVE FROM CART
# =========================================================

@app.route(
    "/remove-from-cart/<int:product_id>",
    methods=["POST"]
)
def remove_from_cart(product_id):

    cart = session.get(
        "cart",
        {}
    )

    product_key = str(
        product_id
    )

    if product_key in cart:

        del cart[product_key]

    session["cart"] = cart

    session.modified = True

    return redirect(
        url_for("cart")
    )

# =========================================================
# VIEW CART
# =========================================================

@app.route("/cart")
def cart():

    cart = session.get("cart", {})
    cart_items = []

    for product_id, quantity in cart.items():

        product_id = int(product_id)

        product = get_product(product_id)

        if product:

            item = product.copy()
            item["id"] = product_id
            item["quantity"] = quantity
            item["subtotal"] = (
                product["price"] * quantity
            )

            cart_items.append(item)

    cart_total = sum(
        item["subtotal"]
        for item in cart_items
    )

    cart_count = sum(
        item["quantity"]
        for item in cart_items
    )

    session["cart_notification"] = False

    return render_template(
        "cart.html",
        cart_items=cart_items,
        cart_total=cart_total,
        cart_count=cart_count
    )

@app.route("/bundle-builder", methods=["GET", "POST"])
def bundle_builder():
    products = get_products()

    if request.method == "POST":
        selected_ids = request.form.getlist("product_ids")

        if not selected_ids:
            return render_template(
                "bundle_builder.html",
                products=products,
                error="Please select at least one product."
            )

        cart = session.get("cart", {})
        added_count = 0

        for product_id in selected_ids:
            try:
                product_id_int = int(product_id)
            except (TypeError, ValueError):
                continue

            if product_id_int not in products:
                continue

            product_key = str(product_id_int)
            cart[product_key] = cart.get(product_key, 0) + 1
            added_count += 1

        if added_count == 0:
            return render_template(
                "bundle_builder.html",
                products=products,
                error="No valid products were selected."
            )

        session["cart"] = cart
        session["cart_notification"] = True
        session.modified = True

        return redirect(url_for("cart"))

    return render_template(
        "bundle_builder.html",
        products=products
    )


# =========================================================
# CHECKOUT
# =========================================================

@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    if not session.get("user"):
        return redirect(url_for("login"))

    user_id = session["user"]["id"]

    cart_items = []
    cart = session.get("cart", {})

    # BUILD CART ITEMS
    for product_id, quantity in cart.items():

        product_id = int(product_id)
        product = get_product(product_id)

        if product:
            item = product.copy()
            item["id"] = product_id
            item["quantity"] = quantity
            item["subtotal"] = product["price"] * quantity
            cart_items.append(item)

    cart_total = sum(item["subtotal"] for item in cart_items)
    cart_count = sum(item["quantity"] for item in cart_items)

    if not cart_items:
        return render_template(
            "checkout.html",
            cart_items=[],
            cart_total=0,
            cart_count=0,
            error="Your cart is empty."
        )

    # LOAD CUSTOMER PROFILE
    try:
        profile_response = (
            supabase
            .table("users")
            .select(
                "id, name, email, phone, address_line, "
                "barangay, city, province, postal_code"
            )
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

        customer = (
            profile_response.data[0]
            if profile_response.data
            else None
        )

        if not customer:
            raise Exception("Customer profile not found.")

    except Exception as e:
        print("Checkout profile loading error:", e)

        return render_template(
            "checkout.html",
            cart_items=cart_items,
            cart_total=cart_total,
            cart_count=cart_count,
            error="Unable to load your profile. Please try again."
        )

    # BUILD COMPLETE DELIVERY ADDRESS
    address_parts = [
        customer.get("address_line"),
        customer.get("barangay"),
        customer.get("city"),
        customer.get("province"),
        customer.get("postal_code")
    ]

    delivery_address = ", ".join(
        str(part).strip()
        for part in address_parts
        if part and str(part).strip()
    )

    customer_info = {
        "full_name": customer.get("name") or "",
        "email": customer.get("email") or "",
        "phone": customer.get("phone") or "",
        "address": delivery_address
    }

    # PLACE ORDER
    if request.method == "POST":

        payment_method = request.form.get(
            "payment_method", ""
        ).strip()

        if not all(customer_info.values()):
            return render_template(
                "checkout.html",
                cart_items=cart_items,
                cart_total=cart_total,
                cart_count=cart_count,
                customer=customer_info,
                error=(
                    "Please complete your personal information "
                    "and delivery address in My Profile first."
                )
            )

        if payment_method not in ["Cash on Delivery", "GCash"]:
            return render_template(
                "checkout.html",
                cart_items=cart_items,
                cart_total=cart_total,
                cart_count=cart_count,
                customer=customer_info,
                error="Please select a valid payment method."
            )

        try:

            order_data = {
                "user_id": user_id,
                "full_name": customer_info["full_name"],
                "email": customer_info["email"],
                "phone": customer_info["phone"],
                "address": customer_info["address"],
                "payment_method": payment_method,
                "total": cart_total,
                "status": "Pending"
            }

            order_response = (
                supabase
                .table("orders")
                .insert(order_data)
                .execute()
            )

            if not order_response.data:
                raise Exception("Order was not created.")

            order_id = order_response.data[0]["id"]

            order_items = []

            for item in cart_items:
                order_items.append({
                    "order_id": order_id,
                    "product_id": item["id"],
                    "product_name": item["name"],
                    "price": item["price"],
                    "quantity": item["quantity"],
                    "subtotal": item["subtotal"]
                })

            (
                supabase
                .table("order_items")
                .insert(order_items)
                .execute()
            )

            session.pop("cart", None)
            session["last_order_id"] = order_id

            return redirect(url_for("orders"))

        except Exception as e:

            print("Checkout database error:", e)

            return render_template(
                "checkout.html",
                cart_items=cart_items,
                cart_total=cart_total,
                cart_count=cart_count,
                customer=customer_info,
                error=(
                    "Unable to place your order. "
                    "Please try again."
                )
            )

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        cart_total=cart_total,
        cart_count=cart_count,
        customer=customer_info
    )


# =========================================================
# ORDERS
# =========================================================

@app.route("/orders")
def orders():

    # REQUIRE LOGIN
    if not session.get("user"):
        return redirect(url_for("login"))

    orders_list = []
    error = ""

    user_id = session["user"]["id"]

    try:

        # GET ONLY THE LOGGED-IN USER'S ORDERS
        response = (
            supabase
            .table("orders")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .execute()
        )

        user_orders = response.data or []

        # ASSIGN ORDER NUMBER PER USER
        for index, order in enumerate(user_orders, start=1):

            order["display_order_number"] = index

            # GET ORDER ITEMS
            items_response = (
                supabase
                .table("order_items")
                .select("*")
                .eq("order_id", order["id"])
                .execute()
            )

            order["items"] = (
                items_response.data
                if items_response.data
                else []
            )

            orders_list.append(order)

        # DISPLAY NEWEST ORDERS FIRST
        orders_list.reverse()

    except Exception as e:

        print("Orders database error:", e)

        error = (
            "Unable to load your orders. "
            "Please try again."
        )

    return render_template(
        "orders.html",
        orders=orders_list,
        error=error
    )

#
# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin_dashboard():

    total_products = 0
    total_orders = 0

    pending_orders = 0
    processing_orders = 0
    shipped_orders = 0
    delivered_orders = 0
    cancelled_orders = 0

    total_sales = 0.0
    recent_orders = []
    sales_data = []

    try:

        # GET PRODUCTS
        products_response = (
            supabase
            .table("products")
            .select("id")
            .execute()
        )

        products = products_response.data or []
        total_products = len(products)

        # GET ALL ORDERS
        orders_response = (
            supabase
            .table("orders")
            .select(
                "id, full_name, total, status, created_at"
            )
            .order("created_at", desc=True)
            .execute()
        )

        orders_data = orders_response.data or []
        total_orders = len(orders_data)

        # CALCULATE STATISTICS AND SALES DATA
        for order in orders_data:

            status = order.get("status", "")

            if status == "Pending":
                pending_orders += 1
            elif status == "Processing":
                processing_orders += 1
            elif status == "Shipped":
                shipped_orders += 1
            elif status == "Delivered":
                delivered_orders += 1
            elif status == "Cancelled":
                cancelled_orders += 1

            # Calculate total recorded order amounts
            try:
                order_total = float(order.get("total") or 0)
            except (TypeError, ValueError):
                order_total = 0.0

            total_sales += order_total

            # Add order to Sales Overview
            created_at = order.get("created_at") or ""

            sales_data.append({
                "order_id": order.get("id"),
                "date": created_at[:10] if created_at else "N/A",
                "total": order_total
            })

        # Latest five orders
        recent_orders = orders_data[:5]

    except Exception as e:
        print("Admin dashboard database error:", e)

    return render_template(
        "admin/dashboard.html",
        total_products=total_products,
        total_orders=total_orders,
        pending_orders=pending_orders,
        processing_orders=processing_orders,
        shipped_orders=shipped_orders,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders,
        total_sales=total_sales,
        recent_orders=recent_orders,
        sales_data=sales_data
    )


# =========================================================
# ADMIN PRODUCTS
# =========================================================

@app.route("/admin/products")
def admin_products():

    products = get_products()

    return render_template(
        "admin/products.html",
        products=products
    )


# =========================================================
# ADD ADMIN PRODUCT
# =========================================================

@app.route("/admin/products/add", methods=["POST"])
def admin_add_product():

    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price = request.form.get("price", "").strip()
    rating = request.form.get("rating", "0").strip()

    image_url = request.form.get(
        "image_url",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    ram = request.form.get("ram", "N/A").strip()
    storage = request.form.get("storage", "N/A").strip()
    processor = request.form.get("processor", "N/A").strip()

    if not name or not category or not price:
        return redirect(url_for("admin_products"))

    try:

        price = float(price)
        rating = float(rating or 0)

        if price < 0:
            price = 0

        rating = max(0, min(rating, 5))

        product_data = {
            "name": name,
            "category": category,
            "price": price,
            "image_url": image_url,
            "rating": rating,
            "description": description,
            "ram": ram or "N/A",
            "storage": storage or "N/A",
            "processor": processor or "N/A"
        }

        (
            supabase
            .table("products")
            .insert(product_data)
            .execute()
        )

        print("PRODUCT ADDED SUCCESSFULLY:", name)

    except Exception as e:

        print("Admin add product error:", e)

    return redirect(url_for("admin_products"))

# =========================================================
# EDIT ADMIN PRODUCT
# =========================================================

@app.route(
    "/admin/products/<int:product_id>/edit",
    methods=["POST"]
)
def admin_edit_product(product_id):

    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price = request.form.get("price", "").strip()
    rating = request.form.get("rating", "0").strip()

    image_url = request.form.get(
        "image_url",
        ""
    ).strip()

    description = request.form.get("description", "").strip()
    ram = request.form.get("ram", "N/A").strip()
    storage = request.form.get("storage", "N/A").strip()
    processor = request.form.get("processor", "N/A").strip()

    if not name or not category or not price:
        return redirect(url_for("admin_products"))

    try:

        price = float(price)
        rating = float(rating or 0)

        if price < 0:
            price = 0

        rating = max(0, min(rating, 5))

        product_data = {
            "name": name,
            "category": category,
            "price": price,
            "image_url": image_url,
            "rating": rating,
            "description": description,
            "ram": ram or "N/A",
            "storage": storage or "N/A",
            "processor": processor or "N/A"
        }

        (
            supabase
            .table("products")
            .update(product_data)
            .eq("id", product_id)
            .execute()
        )

        print("PRODUCT UPDATED SUCCESSFULLY:", product_id)

    except Exception as e:

        print("Admin edit product error:", e)

    return redirect(url_for("admin_products"))

# =========================================================
# DELETE ADMIN PRODUCT
# =========================================================

@app.route(
    "/admin/products/<int:product_id>/delete",
    methods=["POST"]
)
def admin_delete_product(product_id):

    try:

        (
            supabase
            .table("products")
            .delete()
            .eq(
                "id",
                product_id
            )
            .execute()
        )

    except Exception as e:

        print(
            "Admin delete product error:",
            e
        )

    return redirect(
        url_for("admin_products")
    )


# =========================================================
# ADMIN ORDERS
# =========================================================

@app.route("/admin/orders")
def admin_orders():

    orders_list = []

    error = ""

    try:

        # Get all orders.
        response = (
            supabase
            .table("orders")
            .select("*")
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )

        # Get order items.
        if response.data:

            for order in response.data:

                items_response = (
                    supabase
                    .table("order_items")
                    .select("*")
                    .eq(
                        "order_id",
                        order["id"]
                    )
                    .execute()
                )

                order["items"] = (
                    items_response.data
                    if items_response.data
                    else []
                )

                orders_list.append(
                    order
                )

    except Exception as e:

        print(
            "Admin orders database error:",
            e
        )

        error = (
            "Unable to load orders. "
            "Please try again."
        )

    return render_template(
        "admin/orders.html",
        orders=orders_list,
        error=error
    )


# =========================================================
# UPDATE ORDER STATUS
# =========================================================


@app.route(
    "/admin/orders/<int:order_id>/status",
    methods=["POST"]
)
def update_order_status(order_id):

    status = request.form.get(
        "status",
        ""
    ).strip()

    allowed_statuses = [
        "Pending",
        "Processing",
        "Shipped",
        "Delivered",
        "Cancelled"
    ]

    if status not in allowed_statuses:
        return redirect(
            url_for("admin_orders")
        )

    try:

        # Get order information.
        order_response = (
            supabase
            .table("orders")
            .select("id, user_id, total")
            .eq("id", order_id)
            .limit(1)
            .execute()
        )

        if not order_response.data:
            return redirect(
                url_for("admin_orders")
            )

        order = order_response.data[0]

        # Update order status.
        (
            supabase
            .table("orders")
            .update({
                "status": status
            })
            .eq("id", order_id)
            .execute()
        )

        # Award points only when Delivered.
        if status == "Delivered" and order.get("user_id"):

            total = float(
                order.get("total") or 0
            )

            points = int(
                total // 100
            )

            if points > 0:

                # Check if points were already awarded.
                existing_reward = (
                    supabase
                    .table("reward_transactions")
                    .select("id")
                    .eq("order_id", order_id)
                    .eq("transaction_type", "earn")
                    .limit(1)
                    .execute()
                )

                if not existing_reward.data:

                    # Insert reward transaction.
                    (
                        supabase
                        .table("reward_transactions")
                        .insert({
                            "user_id": order["user_id"],
                            "order_id": order_id,
                            "transaction_type": "earn",
                            "points": points
                        })
                        .execute()
                    )

                    print(
                        f"Reward credited: {points} points"
                    )

    except Exception as e:

        print(
            "Order status update error:",
            e
        )

    return redirect(
        url_for("admin_orders")
    )

@app.route('/categories')
def categories_page():

    products = get_products()

    return render_template(
        'categories.html',
        products=products
    )

# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )