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


# =========================
# LOAD ENVIRONMENT VARIABLES
# =========================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be set in the .env file."
    )


# =========================
# SUPABASE CONNECTION
# =========================

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================
# FLASK APP
# =========================

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "shopzone-development-secret-key"
)


# =========================
# PRODUCT DATA
# =========================

products = {
    1: {
        "name": "Programming Laptop",
        "category": "Electronics",
        "price": 24000,
        "icon": "💻",
        "rating": 4.8,
        "description": (
            "A reliable laptop for programming, school projects, "
            "and everyday tasks."
        ),
        "ram": "16GB",
        "storage": "512GB SSD",
        "processor": "AMD Ryzen 5"
    },

    2: {
        "name": "Mechanical Keyboard",
        "category": "Accessories",
        "price": 1500,
        "icon": "⌨️",
        "rating": 4.7,
        "description": (
            "A mechanical keyboard suitable for programming "
            "and everyday typing."
        ),
        "ram": "N/A",
        "storage": "N/A",
        "processor": "N/A"
    },

    3: {
        "name": "Wireless Mouse",
        "category": "Accessories",
        "price": 800,
        "icon": "🖱️",
        "rating": 4.6,
        "description": (
            "A comfortable wireless mouse for students "
            "and computer users."
        ),
        "ram": "N/A",
        "storage": "N/A",
        "processor": "N/A"
    },

    4: {
        "name": "Student Backpack",
        "category": "School",
        "price": 899,
        "icon": "🎒",
        "rating": 4.5,
        "description": (
            "A practical backpack suitable for students, "
            "school supplies, and everyday use."
        ),
        "ram": "N/A",
        "storage": "Multiple Compartments",
        "processor": "N/A"
    }
}


# =========================
# MAIN PAGES
# =========================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/products")
def products_page():
    return render_template(
        "products.html",
        products=products
    )


@app.route("/product/<int:product_id>")
def product_details(product_id):

    product = products.get(product_id)

    if product is None:
        return "Product not found", 404

    return render_template(
        "product_details.html",
        product=product
    )


# =========================
# LOGIN
# =========================

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

        # Required fields

        if not email or not password:

            error = "Please fill in all required fields."

            return render_template(
                "login.html",
                error=error
            )

        try:

            # Find user in Supabase

            response = (
                supabase
                .table("users")
                .select("id, name, email, password")
                .eq("email", email)
                .limit(1)
                .execute()
            )

            user = response.data[0] if response.data else None

        except Exception as e:

            print("Login database error:", e)

            error = "Unable to connect to the database."

            return render_template(
                "login.html",
                error=error
            )

        # User does not exist

        if user is None:

            error = "Invalid email or password."

            return render_template(
                "login.html",
                error=error
            )

        # Check password

        if not check_password_hash(
            user["password"],
            password
        ):

            error = "Invalid email or password."

            return render_template(
                "login.html",
                error=error
            )

        # Create login session

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


# =========================
# REGISTER
# =========================

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

        # Required fields

        if not name or not email or not password or not confirm_password:

            error = "Please fill in all required fields."

            return render_template(
                "register.html",
                error=error
            )

        # Password confirmation

        if password != confirm_password:

            error = "Passwords do not match."

            return render_template(
                "register.html",
                error=error
            )

        # Basic password requirement

        if len(password) < 6:

            error = "Password must be at least 6 characters."

            return render_template(
                "register.html",
                error=error
            )

        try:

            # Check if email already exists

            existing_user = (
                supabase
                .table("users")
                .select("id")
                .eq("email", email)
                .limit(1)
                .execute()
            )

            if existing_user.data:

                error = "An account with this email already exists."

                return render_template(
                    "register.html",
                    error=error
                )

            # Hash password before saving

            hashed_password = generate_password_hash(
                password
            )

            # Insert new user into Supabase

            supabase.table("users").insert({
                "name": name,
                "email": email,
                "password": hashed_password
            }).execute()

        except Exception as e:

            print("Registration database error:", e)

            error = "Unable to create your account. Please try again."

            return render_template(
                "register.html",
                error=error
            )

        # Registration successful

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html",
        error=error
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.pop(
        "user",
        None
    )

    return redirect(
        url_for("home")
    )


# =========================
# CART
# =========================

@app.route("/cart")
def cart():
    return render_template("cart.html")


# =========================
# CHECKOUT
# =========================

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")


# =========================
# ORDERS
# =========================

@app.route("/orders")
def orders():
    return render_template("orders.html")


# =========================
# ADMIN PAGES
# =========================

@app.route("/admin")
def admin_dashboard():
    return render_template("admin/dashboard.html")


@app.route("/admin/products")
def admin_products():
    return render_template("admin/products.html")


@app.route("/admin/orders")
def admin_orders():
    return render_template("admin/orders.html")


# =========================
# ERROR HANDLER
# =========================

@app.errorhandler(404)
def page_not_found(error):
    return "Page not found", 404


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
    app.run(debug=True)