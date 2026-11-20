
/* =====================================
   SHOPZONE PRODUCT COMPARISON
===================================== */

const MAX_COMPARE_PRODUCTS = 4;

let selectedCompareProducts = [];
let currentCategory = "all";


/* =====================================
   DYNAMIC CATEGORY GENERATION
===================================== */

function generateCategoryButtons() {
    const categoryContainer = document.getElementById("categoryContainer");

    if (!categoryContainer) return;

    const productCards = document.querySelectorAll(".product-card");
    const categories = new Set();

    productCards.forEach((card) => {
        const category = (card.dataset.category || "").trim();

        if (category) {
            categories.add(category);
        }
    });

    const sortedCategories = Array.from(categories).sort((a, b) =>
        a.localeCompare(b)
    );

    categoryContainer.innerHTML = "";

    const allButton = document.createElement("button");

    allButton.type = "button";
    allButton.className = "category-btn";
    allButton.dataset.category = "all";
    allButton.textContent = "All";

    allButton.addEventListener("click", () => {
        filterProducts("all", allButton);
    });

    categoryContainer.appendChild(allButton);

    sortedCategories.forEach((category) => {
        const button = document.createElement("button");

        button.type = "button";
        button.className = "category-btn";
        button.dataset.category = category;
        button.textContent = category;

        button.addEventListener("click", () => {
            filterProducts(category, button);
        });

        categoryContainer.appendChild(button);
    });
}


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
        ).trim().toLowerCase();

        const matchesSearch =
            productName.includes(searchTerm) ||
            productCategory.includes(searchTerm);

        const matchesCategory =
            currentCategory === "all" ||
            productCategory === currentCategory.trim().toLowerCase();

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
   CATEGORY FROM URL
===================================== */

function applyCategoryFromURL() {
    const params = new URLSearchParams(window.location.search);
    const requestedCategory = params.get("category");

    if (!requestedCategory) return;

    const categoryButton = Array.from(
        document.querySelectorAll(".category-btn")
    ).find((button) =>
        button.dataset.category.toLowerCase() ===
        requestedCategory.trim().toLowerCase()
    );

    if (categoryButton) {
        filterProducts(requestedCategory, categoryButton);
    }
}


/* =====================================
   SELECT / DESELECT PRODUCTS
===================================== */

function toggleCompareProduct(button) {
    const productId = String(button.dataset.compareId);

    const selectedIndex = selectedCompareProducts.indexOf(productId);

    if (selectedIndex !== -1) {
        selectedCompareProducts.splice(selectedIndex, 1);
        updateCompareInterface();
        return;
    }

    if (selectedCompareProducts.length >= MAX_COMPARE_PRODUCTS) {
        alert("You can compare a maximum of 4 products.");
        return;
    }

    selectedCompareProducts.push(productId);

    updateCompareInterface();
}


/* =====================================
   UPDATE COMPARISON INTERFACE
===================================== */

function updateCompareInterface() {
    const compareBar = document.getElementById("compareBar");
    const compareStatus = document.getElementById("compareStatus");
    const compareButton = document.getElementById("openCompareButton");

    const selectedCount = selectedCompareProducts.length;

    if (compareBar) {
        compareBar.classList.toggle("visible", selectedCount > 0);
    }

    if (compareStatus) {
        compareStatus.textContent =
            `${selectedCount} of ${MAX_COMPARE_PRODUCTS} products selected`;
    }

    if (compareButton) {
        compareButton.disabled = selectedCount < 2;
    }

    document.querySelectorAll(".compare-button").forEach((button) => {
        const productId = String(button.dataset.compareId);

        const isSelected =
            selectedCompareProducts.includes(productId);

        button.classList.toggle("selected", isSelected);

        button.setAttribute("aria-pressed", String(isSelected));

        button.textContent = isSelected
            ? "✓ Selected — Remove"
            : "⇄ Compare";

        button.disabled =
            !isSelected &&
            selectedCount >= MAX_COMPARE_PRODUCTS;
    });
}


/* =====================================
   CLEAR SELECTED PRODUCTS
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

    window.location.href = `/compare?${queryString}`;
}


/* =====================================
   CART NOTIFICATION
===================================== */

function showCartNotification() {
    const cartLink = document.querySelector(".cart-link");

    if (!cartLink) return;

    let notification = cartLink.querySelector(".cart-notification");

    if (!notification) {
        notification = document.createElement("span");
        notification.className = "cart-notification";

        cartLink.appendChild(notification);
    }
}


/* =====================================
   AJAX ADD TO CART
===================================== */

document.addEventListener("DOMContentLoaded", () => {

    generateCategoryButtons();

    updateProducts();

    applyCategoryFromURL();

    updateCompareInterface();

    document.querySelectorAll(".add-to-cart-form").forEach((form) => {

        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const button = form.querySelector(".add-cart-button");

            if (!button || button.disabled) return;

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
