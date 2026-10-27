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
    Get all products from Supabase and convert them
    into the same dictionary structure used by the
    existing ShopZone templates.
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
                "price": float(product.get("price", 0)),
                "icon": product.get("icon", "🛍️"),
                "rating": float(product.get("rating", 0)),
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
    Get one product from Supabase.
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
            "price": float(product.get("price", 0)),
            "icon": product.get("icon", "🛍️"),
            "rating": float(product.get("rating", 0)),
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
    return render_template("index.html")


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
# PRODUCT DETAILS
# =========================================================

@app.route("/product/<int:product_id>")
def product_details(product_id):

    product = get_product(product_id)

    if product is None:
        return "Product not found", 404

    return render_template(
        "product_details.html",
        product=product,
        product_id=product_id
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
# CART
# =========================================================

@app.route("/cart")
def cart():

    # Remove notification when Cart is opened.
    session.pop(
        "cart_notification",
        None
    )

    cart_items = []

    cart = session.get(
        "cart",
        {}
    )

    for product_id, quantity in cart.items():

        product_id = int(product_id)

        product = get_product(
            product_id
        )

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

    return render_template(
        "cart.html",
        cart_items=cart_items,
        cart_total=cart_total,
        cart_count=cart_count
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
# CHECKOUT
# =========================================================

@app.route(
    "/checkout",
    methods=["GET", "POST"]
)
def checkout():

    cart_items = []

    cart = session.get(
        "cart",
        {}
    )

    # Build cart items.
    for product_id, quantity in cart.items():

        product_id = int(product_id)

        product = get_product(
            product_id
        )

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

    # Empty cart.
    if not cart_items:

        return render_template(
            "checkout.html",
            cart_items=[],
            cart_total=0,
            cart_count=0,
            error="Your cart is empty."
        )

    # Place order.
    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        payment_method = request.form.get(
            "payment_method",
            ""
        ).strip()

        if (
            not full_name
            or not email
            or not phone
            or not address
            or not payment_method
        ):

            error = (
                "Please fill in all required fields."
            )

            return render_template(
                "checkout.html",
                cart_items=cart_items,
                cart_total=cart_total,
                cart_count=cart_count,
                error=error
            )

        user_id = None

        if session.get("user"):

            user_id = session[
                "user"
            ].get("id")

        try:

            # Insert order.
            order_data = {
                "user_id": user_id,
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "address": address,
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

                raise Exception(
                    "Order was not created."
                )

            order_id = (
                order_response
                .data[0]["id"]
            )

            # Insert order items.
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

            # Clear cart.
            session.pop(
                "cart",
                None
            )

            session["last_order_id"] = (
                order_id
            )

            return redirect(
                url_for("orders")
            )

        except Exception as e:

            print(
                "Checkout database error:",
                e
            )

            error = (
                "Unable to place your order. "
                "Please try again."
            )

            return render_template(
                "checkout.html",
                cart_items=cart_items,
                cart_total=cart_total,
                cart_count=cart_count,
                error=error
            )

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        cart_total=cart_total,
        cart_count=cart_count
    )


# =========================================================
# ORDERS
# =========================================================

@app.route("/orders")
def orders():

    orders_list = []

    error = ""

    try:

        user = session.get(
            "user"
        )

        # Logged-in user.
        if user:

            response = (
                supabase
                .table("orders")
                .select("*")
                .eq(
                    "user_id",
                    user["id"]
                )
                .order(
                    "created_at",
                    desc=True
                )
                .execute()
            )

        # Guest user.
        else:

            last_order_id = session.get(
                "last_order_id"
            )

            if last_order_id:

                response = (
                    supabase
                    .table("orders")
                    .select("*")
                    .eq(
                        "id",
                        last_order_id
                    )
                    .limit(1)
                    .execute()
                )

            else:

                response = None

        # Process orders.
        if response and response.data:

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
            "Orders database error:",
            e
        )

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

@app.route(
    "/admin/products/add",
    methods=["POST"]
)
def admin_add_product():

    name = request.form.get(
        "name",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    price = request.form.get(
        "price",
        ""
    ).strip()

    rating = request.form.get(
        "rating",
        "0"
    ).strip()

    icon = request.form.get(
        "icon",
        "🛍️"
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    ram = request.form.get(
        "ram",
        "N/A"
    ).strip()

    storage = request.form.get(
        "storage",
        "N/A"
    ).strip()

    processor = request.form.get(
        "processor",
        "N/A"
    ).strip()

    if not name or not category or not price:

        return redirect(
            url_for("admin_products")
        )

    try:

        price = float(price)

        rating = float(rating or 0)

        if price < 0:
            price = 0

        if rating < 0:
            rating = 0

        if rating > 5:
            rating = 5

        product_data = {
            "name": name,
            "category": category,
            "price": price,
            "rating": rating,
            "icon": icon or "🛍️",
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

    except Exception as e:

        print(
            "Admin add product error:",
            e
        )

    return redirect(
        url_for("admin_products")
    )


# =========================================================
# EDIT ADMIN PRODUCT
# =========================================================

@app.route(
    "/admin/products/<int:product_id>/edit",
    methods=["POST"]
)
def admin_edit_product(product_id):

    name = request.form.get(
        "name",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    price = request.form.get(
        "price",
        ""
    ).strip()

    rating = request.form.get(
        "rating",
        "0"
    ).strip()

    icon = request.form.get(
        "icon",
        "🛍️"
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    ram = request.form.get(
        "ram",
        "N/A"
    ).strip()

    storage = request.form.get(
        "storage",
        "N/A"
    ).strip()

    processor = request.form.get(
        "processor",
        "N/A"
    ).strip()

    if not name or not category or not price:

        return redirect(
            url_for("admin_products")
        )

    try:

        price = float(price)

        rating = float(rating or 0)

        if price < 0:
            price = 0

        if rating < 0:
            rating = 0

        if rating > 5:
            rating = 5

        product_data = {
            "name": name,
            "category": category,
            "price": price,
            "rating": rating,
            "icon": icon or "🛍️",
            "description": description,
            "ram": ram or "N/A",
            "storage": storage or "N/A",
            "processor": processor or "N/A"
        }

        (
            supabase
            .table("products")
            .update(product_data)
            .eq(
                "id",
                product_id
            )
            .execute()
        )

    except Exception as e:

        print(
            "Admin edit product error:",
            e
        )

    return redirect(
        url_for("admin_products")
    )


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

        (
            supabase
            .table("orders")
            .update({
                "status": status
            })
            .eq(
                "id",
                order_id
            )
            .execute()
        )

    except Exception as e:

        print(
            "Order status update error:",
            e
        )

    return redirect(
        url_for("admin_orders")
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
