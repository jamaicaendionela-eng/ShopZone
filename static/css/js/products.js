let currentCategory = "all";


/* =========================================================
   PRODUCT FILTERING
   ========================================================= */

function updateProducts() {

    const searchInput = document.getElementById("searchInput");

    const searchTerm = searchInput
        ? searchInput.value.trim().toLowerCase()
        : "";

    const productCards = document.querySelectorAll(".product-card");

    productCards.forEach(function (product) {

        const productName =
            (product.getAttribute("data-name") || "").toLowerCase();

        const productCategory =
            (product.getAttribute("data-category") || "").toLowerCase();

        const categoryMatches =
            currentCategory === "all" ||
            productCategory === currentCategory.toLowerCase();

        const searchMatches =
            productName.includes(searchTerm);

        if (categoryMatches && searchMatches) {
            product.style.display = "";
        } else {
            product.style.display = "none";
        }

    });
}


function searchProducts() {
    updateProducts();
}


function filterProducts(category, button) {

    currentCategory = category;

    document
        .querySelectorAll(".category-btn")
        .forEach(function (categoryButton) {

            categoryButton.classList.remove("active");

        });

    if (button) {
        button.classList.add("active");
    }

    updateProducts();
}


/* =========================================================
   CART NOTIFICATION
   ========================================================= */

function showCartNotification() {

    const cartLink = document.querySelector(".cart-link");

    if (!cartLink) {
        return;
    }

    let notification =
        cartLink.querySelector(".cart-notification");

    if (!notification) {

        notification =
            document.createElement("span");

        notification.className =
            "cart-notification";

        cartLink.appendChild(notification);
    }
}


/* =========================================================
   ADD TO CART WITHOUT PAGE RELOAD
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const forms =
        document.querySelectorAll(".add-to-cart-form");

    forms.forEach(function (form) {

        form.addEventListener("submit", async function (event) {

            event.preventDefault();

            const button =
                form.querySelector(".add-cart-button");

            const originalText =
                button.innerHTML;

            button.disabled = true;

            try {

                const response = await fetch(
                    form.action,
                    {
                        method: "POST",
                        body: new FormData(form),
                        credentials: "same-origin"
                    }
                );

                if (!response.ok) {
                    throw new Error(
                        "Unable to add product to cart."
                    );
                }


                /*
                 * Flask has already updated the
                 * session/cart on the server.
                 */

                showCartNotification();


                /*
                 * Give the user visual feedback
                 * without showing an alert.
                 */

                button.classList.add("added");

                button.innerHTML =
                    "✓ Added";


                /*
                 * Return the button to normal
                 * after a short moment.
                 */

                setTimeout(function () {

                    button.classList.remove("added");

                    button.innerHTML =
                        originalText;

                    button.disabled = false;

                }, 1000);


            } catch (error) {

                console.error(
                    "Add to cart error:",
                    error
                );

                button.innerHTML =
                    "⚠ Try Again";

                button.disabled = false;


                setTimeout(function () {

                    button.innerHTML =
                        originalText;

                }, 1500);

            }

        });

    });

});