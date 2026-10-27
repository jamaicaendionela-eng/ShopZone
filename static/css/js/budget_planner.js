/* =========================================
   SHOPZONE ADVANCED BUDGET PLANNER
========================================= */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const budgetInput = document.getElementById("budgetInput");
    const setBudgetButton = document.getElementById("setBudgetButton");
    const budgetMessage = document.getElementById("budgetMessage");

    const totalBudgetElement = document.getElementById("totalBudget");
    const totalExpensesElement = document.getElementById("totalExpenses");
    const remainingBalanceElement = document.getElementById("remainingBalance");

    const budgetPercentageElement = document.getElementById("budgetPercentage");
    const budgetProgress = document.getElementById("budgetProgress");
    const progressTrack = document.getElementById("progressTrack");
    const budgetStatus = document.getElementById("budgetStatus");

    const productSearch = document.getElementById("productSearch");
    const categoryFilter = document.getElementById("categoryFilter");
    const priceFilter = document.getElementById("priceFilter");
    const productGrid = document.getElementById("budgetProductGrid");
    const productCount = document.getElementById("productCount");

    const shoppingListBody = document.getElementById("shoppingListBody");
    const shoppingListTotal = document.getElementById("shoppingListTotal");
    const shoppingMessage = document.getElementById("shoppingMessage");
    const clearShoppingListButton = document.getElementById("clearShoppingList");
    const compareAlternativesButton = document.getElementById("compareAlternatives");
    const alternativesContainer = document.getElementById("alternativesContainer");

    if (
        !budgetInput ||
        !setBudgetButton ||
        !productGrid ||
        !shoppingListBody
    ) {
        console.error("Budget Planner initialization failed: required elements are missing.");
        return;
    }

    const MAX_COMPARE_PRODUCTS = 4;
    const WARNING_THRESHOLD = 80;

    let budget = 0;
    let shoppingList = new Map();

    /*
     * Read product information rendered by Flask.
     * Prices and IDs come from the existing Supabase product data.
     */
    const productCards = Array.from(
        productGrid.querySelectorAll(".budget-product-card")
    );

    const products = productCards.map((card) => ({
        id: String(card.dataset.productId),
        name: card.dataset.name || "Unnamed Product",
        category: card.dataset.category || "Other",
        price: Number(card.dataset.price),
        rating: Number(card.dataset.rating) || 0,
        card: card
    })).filter((product) => {
        return product.id && Number.isFinite(product.price) && product.price >= 0;
    });

    const productsById = new Map(
        products.map((product) => [product.id, product])
    );

    /*
     * Utility functions
     */

    function formatCurrency(amount) {
        return new Intl.NumberFormat("en-PH", {
            style: "currency",
            currency: "PHP",
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    }

    function escapeHTML(value) {
        return String(value).replace(/[&<>"']/g, (character) => {
            const entities = {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            };

            return entities[character];
        });
    }

    function setMessage(element, message, type = "") {
        if (!element) return;

        element.textContent = message;
        element.classList.remove("error", "success");

        if (type) {
            element.classList.add(type);
        }
    }

    function getTotalExpenses() {
        let total = 0;

        shoppingList.forEach((item) => {
            total += item.product.price * item.quantity;
        });

        return total;
    }

    function getRemainingBalance() {
        return budget - getTotalExpenses();
    }

    function getBudgetUsage() {
        if (budget <= 0) return 0;

        return (getTotalExpenses() / budget) * 100;
    }

    /*
     * Budget setup
     */

    function setBudget() {
        const newBudget = Number(budgetInput.value);

        if (
            budgetInput.value.trim() === "" ||
            !Number.isFinite(newBudget) ||
            newBudget <= 0
        ) {
            setMessage(
                budgetMessage,
                "Please enter a valid budget greater than ₱0.",
                "error"
            );

            budgetInput.focus();
            return;
        }

        budget = Math.round((newBudget + Number.EPSILON) * 100) / 100;

        setMessage(
            budgetMessage,
            `Your budget is set to ${formatCurrency(budget)}.`,
            "success"
        );

        updateBudgetInterface();
        updateProductFilters();
        renderAlternatives();
    }

    setBudgetButton.addEventListener("click", setBudget);

    budgetInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            setBudget();
        }
    });

    /*
     * Budget summary and alerts
     */

    function updateBudgetInterface() {
        const expenses = getTotalExpenses();
        const remaining = budget - expenses;
        const actualUsage = getBudgetUsage();

        totalBudgetElement.textContent = formatCurrency(budget);
        totalExpensesElement.textContent = formatCurrency(expenses);
        remainingBalanceElement.textContent = formatCurrency(remaining);

        remainingBalanceElement.classList.toggle("negative", remaining < 0);
        remainingBalanceElement.classList.toggle("positive", remaining >= 0);

        /*
         * Cap the visual progress bar at 100%.
         * The displayed percentage can exceed 100% when over budget.
         */
        const visualProgress = Math.min(100, Math.max(0, actualUsage));

        budgetProgress.style.width = `${visualProgress}%`;
        budgetPercentageElement.textContent = `${actualUsage.toFixed(1)}%`;

        progressTrack.setAttribute(
            "aria-valuenow",
            String(Math.min(100, Math.round(actualUsage)))
        );

        budgetProgress.classList.remove("warning", "danger");
        budgetStatus.classList.remove("success", "warning", "danger");

        if (budget <= 0) {
            budgetStatus.textContent = "Set a budget to begin.";
            return;
        }

        if (remaining < 0) {
            budgetProgress.classList.add("danger");
            budgetStatus.classList.add("danger");

            budgetStatus.textContent =
                `You are over budget by ${formatCurrency(Math.abs(remaining))}.`;
        } else if (actualUsage >= WARNING_THRESHOLD) {
            budgetProgress.classList.add("warning");
            budgetStatus.classList.add("warning");

            budgetStatus.textContent =
                `You are nearing your budget limit. ${formatCurrency(remaining)} remaining.`;
        } else {
            budgetStatus.classList.add("success");

            budgetStatus.textContent =
                `You are within budget. ${formatCurrency(remaining)} remaining.`;
        }
    }

    /*
     * Product filtering
     */

    function updateProductFilters() {
        const searchTerm = (productSearch?.value || "")
            .trim()
            .toLowerCase();

        const selectedCategory = (categoryFilter?.value || "all")
            .trim()
            .toLowerCase();

        const selectedPrice = priceFilter?.value || "all";

        let visibleCount = 0;

        products.forEach((product) => {
            const matchesSearch =
                product.name.toLowerCase().includes(searchTerm) ||
                product.category.toLowerCase().includes(searchTerm);

            const matchesCategory =
                selectedCategory === "all" ||
                product.category.toLowerCase() === selectedCategory;

            const matchesPrice =
                selectedPrice !== "budget" ||
                (budget > 0 && product.price <= budget);

            const visible =
                matchesSearch && matchesCategory && matchesPrice;

            product.card.hidden = !visible;

            if (visible) visibleCount++;
        });

        if (productCount) {
            productCount.textContent =
                `${visibleCount} product${visibleCount === 1 ? "" : "s"} found`;
        }
    }

    productSearch?.addEventListener("input", updateProductFilters);
    categoryFilter?.addEventListener("change", updateProductFilters);
    priceFilter?.addEventListener("change", updateProductFilters);

    /*
     * Shopping list operations
     */

    function addProduct(productId) {
        const product = productsById.get(String(productId));

        if (!product) {
            setMessage(shoppingMessage, "Product not found.", "error");
            return;
        }

        const existingItem = shoppingList.get(product.id);

        if (existingItem) {
            if (existingItem.quantity >= 99) {
                setMessage(
                    shoppingMessage,
                    "Maximum quantity is 99 per product.",
                    "error"
                );
                return;
            }

            existingItem.quantity += 1;
        } else {
            shoppingList.set(product.id, {
                product: product,
                quantity: 1
            });
        }

        setMessage(
            shoppingMessage,
            `${product.name} added to your shopping list.`,
            "success"
        );

        renderShoppingList();
        updateBudgetInterface();
        updateProductButtons();
        renderAlternatives();
    }

    function changeQuantity(productId, change) {
        const item = shoppingList.get(String(productId));

        if (!item) return;

        const newQuantity = item.quantity + change;

        if (newQuantity <= 0) {
            shoppingList.delete(String(productId));
        } else if (newQuantity <= 99) {
            item.quantity = newQuantity;
        } else {
            setMessage(
                shoppingMessage,
                "Maximum quantity is 99 per product.",
                "error"
            );
            return;
        }

        renderShoppingList();
        updateBudgetInterface();
        updateProductButtons();
        renderAlternatives();
    }

    function removeProduct(productId) {
        const item = shoppingList.get(String(productId));

        if (!item) return;

        shoppingList.delete(String(productId));

        setMessage(
            shoppingMessage,
            `${item.product.name} removed from your shopping list.`,
            "success"
        );

        renderShoppingList();
        updateBudgetInterface();
        updateProductButtons();
        renderAlternatives();
    }

    /*
     * Render shopping list.
     * User-controlled text is escaped before inserting HTML.
     */

    function renderShoppingList() {
        if (shoppingList.size === 0) {
            shoppingListBody.innerHTML = `
                <tr>
                    <td colspan="5" class="empty-state">
                        Your shopping list is empty.
                    </td>
                </tr>
            `;

            shoppingListTotal.textContent = formatCurrency(0);
            compareAlternativesButton.disabled = true;
            return;
        }

        const rows = [];

        shoppingList.forEach((item, productId) => {
            const product = item.product;
            const subtotal = product.price * item.quantity;

            rows.push(`
                <tr>
                    <td>${escapeHTML(product.name)}</td>

                    <td>${formatCurrency(product.price)}</td>

                    <td>
                        <div class="quantity-control">
                            <button
                                type="button"
                                data-action="decrease"
                                data-product-id="${escapeHTML(productId)}"
                                aria-label="Decrease quantity of ${escapeHTML(product.name)}"
                            >−</button>

                            <span class="quantity-value">${item.quantity}</span>

                            <button
                                type="button"
                                data-action="increase"
                                data-product-id="${escapeHTML(productId)}"
                                aria-label="Increase quantity of ${escapeHTML(product.name)}"
                            >+</button>
                        </div>
                    </td>

                    <td><strong>${formatCurrency(subtotal)}</strong></td>

                    <td>
                        <button
                            type="button"
                            class="remove-product"
                            data-action="remove"
                            data-product-id="${escapeHTML(productId)}"
                        >
                            Remove
                        </button>
                    </td>
                </tr>
            `);
        });

        shoppingListBody.innerHTML = rows.join("");
        shoppingListTotal.textContent = formatCurrency(getTotalExpenses());

        compareAlternativesButton.disabled =
            shoppingList.size < 2 || shoppingList.size > MAX_COMPARE_PRODUCTS;
    }

    /*
     * Event delegation for quantity and remove controls.
     */

    shoppingListBody.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-action]");

        if (!button) return;

        const productId = button.dataset.productId;
        const action = button.dataset.action;

        if (action === "increase") {
            changeQuantity(productId, 1);
        } else if (action === "decrease") {
            changeQuantity(productId, -1);
        } else if (action === "remove") {
            removeProduct(productId);
        }
    });

    /*
     * Add-to-list buttons.
     */

    productGrid.addEventListener("click", (event) => {
        const button = event.target.closest(".add-budget-product");

        if (!button) return;

        addProduct(button.dataset.productId);
    });

    /*
     * Clear shopping list.
     */

    clearShoppingListButton.addEventListener("click", () => {
        if (shoppingList.size === 0) {
            setMessage(shoppingMessage, "Your shopping list is already empty.");
            return;
        }

        const confirmed = window.confirm(
            "Are you sure you want to clear your entire shopping list?"
        );

        if (!confirmed) return;

        shoppingList.clear();

        setMessage(shoppingMessage, "Shopping list cleared.", "success");

        renderShoppingList();
        updateBudgetInterface();
        updateProductButtons();
        renderAlternatives();
    });

    /*
     * Update product buttons to show which products are in the list.
     */

    function updateProductButtons() {
        document.querySelectorAll(".add-budget-product").forEach((button) => {
            const productId = String(button.dataset.productId);
            const isInList = shoppingList.has(productId);

            button.classList.toggle("in-list", isInList);
            button.textContent = isInList
                ? "Add Another"
                : "Add to Shopping List";
        });
    }

    /*
     * Affordable alternatives:
     * Recommend products in the same category with a lower price.
     * These are recommendations, not claims of exact technical equivalence.
     */

    function renderAlternatives() {
        if (shoppingList.size === 0) {
            alternativesContainer.innerHTML = `
                <p class="empty-state">
                    Add a product to your shopping list to see alternatives.
                </p>
            `;
            return;
        }

        const recommendations = [];

        shoppingList.forEach((item) => {
            const selectedProduct = item.product;

            const alternatives = products
                .filter((candidate) => {
                    return (
                        candidate.id !== selectedProduct.id &&
                        candidate.category.toLowerCase() ===
                            selectedProduct.category.toLowerCase() &&
                        candidate.price < selectedProduct.price
                    );
                })
                .sort((a, b) => {
                    /*
                     * Prefer the highest-rated cheaper option.
                     * Break ties by lower price.
                     */
                    return b.rating - a.rating || a.price - b.price;
                })
                .slice(0, 2);

            alternatives.forEach((alternative) => {
                recommendations.push({
                    selectedProduct: selectedProduct,
                    alternative: alternative,
                    savings:
                        selectedProduct.price - alternative.price
                });
            });
        });

        const uniqueRecommendations = new Map();

        recommendations.forEach((recommendation) => {
            const key = `${recommendation.selectedProduct.id}:${recommendation.alternative.id}`;

            if (!uniqueRecommendations.has(key)) {
                uniqueRecommendations.set(key, recommendation);
            }
        });

        if (uniqueRecommendations.size === 0) {
            alternativesContainer.innerHTML = `
                <p class="empty-state">
                    No lower-priced products in the same category were found.
                </p>
            `;
            return;
        }

        alternativesContainer.innerHTML = Array.from(
            uniqueRecommendations.values()
        ).map(({ selectedProduct, alternative, savings }) => `
            <article class="alternative-card">
                <span class="product-category">
                    ${escapeHTML(alternative.category)}
                </span>

                <h3>${escapeHTML(alternative.name)}</h3>

                <p>
                    Lower-priced alternative to
                    ${escapeHTML(selectedProduct.name)}
                </p>

                <p class="alternative-price">
                    ${formatCurrency(alternative.price)}
                </p>

                <p>
                    Potential savings per item:
                    <strong>${formatCurrency(savings)}</strong>
                </p>

                <button
                    type="button"
                    class="add-budget-product"
                    data-product-id="${escapeHTML(alternative.id)}"
                >
                    Add Alternative
                </button>
            </article>
        `).join("");
    }

    /*
     * Comparison integration.
     * The existing Flask /compare route accepts 2–4 distinct IDs.
     */

    compareAlternativesButton.addEventListener("click", () => {
        const selectedIds = Array.from(shoppingList.keys());

        if (selectedIds.length < 2 || selectedIds.length > MAX_COMPARE_PRODUCTS) {
            setMessage(
                shoppingMessage,
                "Select between 2 and 4 different products to compare.",
                "error"
            );
            return;
        }

        const queryString = selectedIds
            .map((id) => `id=${encodeURIComponent(id)}`)
            .join("&");

        window.location.href = `/compare?${queryString}`;
    });

    /*
     * Initialize interface.
     */

    updateProductFilters();
    renderShoppingList();
    updateBudgetInterface();
    updateProductButtons();
    renderAlternatives();

    console.log("ShopZone Budget Planner initialized.");
});