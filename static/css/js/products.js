
/* =====================================
   SHOPZONE PRODUCT COMPARISON
===================================== */

const MAX_COMPARE_PRODUCTS = 4;

let selectedCompareProducts = [];

let currentCategory = "all";


/* =====================================
   SEARCH AND CATEGORY FILTERS
===================================== */

function updateProducts() {
    const searchInput = document.getElementById("searchInput");

    const searchTerm = searchInput
        ? searchInput.value.toLowerCase().trim()
        : "";

    const productCards = document.querySelectorAll(".product-card");

    productCards.forEach((card) => {
        const productName = (
            card.dataset.name || ""
        ).toLowerCase();

        const productCategory = (
            card.dataset.category || ""
        ).toLowerCase();

        const matchesSearch =
            productName.includes(searchTerm) ||
            productCategory.includes(searchTerm);

        const matchesCategory =
            currentCategory === "all" ||
            productCategory === currentCategory.toLowerCase();

        card.style.display =
            matchesSearch && matchesCategory ? "" : "none";
    });
}


function searchProducts() {
    updateProducts();
}


function filterProducts(category, button) {
    currentCategory = category;

    document.querySelectorAll(".category-btn").forEach((btn) => {
        btn.classList.remove("active");
    });

    if (button) {
        button.classList.add("active");
    }

    updateProducts();
}


/* =====================================
   SELECT / DESELECT PRODUCTS
===================================== */

function toggleCompareProduct(button) {
    const productId = String(button.dataset.compareId);

    const selectedIndex = selectedCompareProducts.indexOf(productId);

    // Remove product if it is already selected.
    if (selectedIndex !== -1) {
        selectedCompareProducts.splice(selectedIndex, 1);

        updateCompareInterface();
        return;
    }

    // Prevent selecting more than four products.
    if (selectedCompareProducts.length >= MAX_COMPARE_PRODUCTS) {
        alert("You can compare a maximum of 4 products.");
        return;
    }

    selectedCompareProducts.push(productId);

    updateCompareInterface();
}


/* =====================================
   UPDATE SELECTION BAR AND BUTTONS
===================================== */

function updateCompareInterface() {
    const compareBar = document.getElementById("compareBar");
    const compareStatus = document.getElementById("compareStatus");
    const compareButton = document.getElementById("openCompareButton");

    const selectedCount = selectedCompareProducts.length;

    // Show the selection bar when at least one product is selected.
    if (compareBar) {
        compareBar.classList.toggle(
            "visible",
            selectedCount > 0
        );
    }

    // Update the selection counter.
    if (compareStatus) {
        compareStatus.textContent =
            `${selectedCount} of ${MAX_COMPARE_PRODUCTS} products selected`;
    }

    // Enable comparison only when at least two products are selected.
    if (compareButton) {
        compareButton.disabled = selectedCount < 2;
    }

    // Update each product's Compare button.
    document.querySelectorAll(".compare-button").forEach((button) => {
        const productId = String(button.dataset.compareId);

        const isSelected =
            selectedCompareProducts.includes(productId);

        button.classList.toggle("selected", isSelected);

        button.setAttribute(
            "aria-pressed",
            String(isSelected)
        );

        button.textContent = isSelected
            ? "✓ Selected — Remove"
            : "⇄ Compare";

        // Disable unselected products when the maximum is reached.
        button.disabled =
            !isSelected &&
            selectedCount >= MAX_COMPARE_PRODUCTS;
    });
}


/* =====================================
   CLEAR ALL SELECTED PRODUCTS
===================================== */

function clearCompareProducts() {
    selectedCompareProducts = [];

    updateCompareInterface();
}


/* =====================================
   OPEN COMPARISON PAGE
===================================== */

function openProductComparison() {
    if (selectedCompareProducts.length < 2) {
        alert("Please select at least 2 products to compare.");
        return;
    }

    if (selectedCompareProducts.length > MAX_COMPARE_PRODUCTS) {
        return;
    }

    const queryString = selectedCompareProducts
        .map((id) => `id=${encodeURIComponent(id)}`)
        .join("&");

    // The Flask comparison route will be added in a later step.
    window.location.href = `/compare?${queryString}`;
}


/* =====================================
   CART NOTIFICATION
===================================== */

function showCartNotification() {
    const cartLink = document.querySelector(".cart-link");

    if (!cartLink) {
        return;
    }

    let notification = cartLink.querySelector(".cart-notification");

    if (!notification) {
        notification = document.createElement("span");
        notification.className = "cart-notification";

        cartLink.appendChild(notification);
    }
}


/* =====================================
   ADD TO CART
===================================== */

document.addEventListener("DOMContentLoaded", () => {
    // Initialize the comparison interface.
    updateCompareInterface();

    // Preserve the existing AJAX Add to Cart behavior.
    document.querySelectorAll(".add-to-cart-form").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const button = form.querySelector(".add-cart-button");

            if (!button || button.disabled) {
                return;
            }

            const originalText = button.textContent;

            button.disabled = true;

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: new FormData(form),
                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    }
                });

                if (!response.ok) {
                    throw new Error("Unable to add product to cart.");
                }

                button.textContent = "✓ Added";
                button.classList.add("added");

                showCartNotification();

                // Restore the button after a short delay.
                setTimeout(() => {
                    button.textContent = originalText;
                    button.classList.remove("added");
                    button.disabled = false;
                }, 1500);

            } catch (error) {
                console.error("Add to Cart error:", error);

                alert(
                    "Unable to add this product to your cart. Please try again."
                );

                button.textContent = originalText;
                button.disabled = false;
            }
        });
    });
});
