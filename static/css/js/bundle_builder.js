/* =========================================
   SHOPZONE SMART BUNDLE BUILDER
========================================= */

document.addEventListener("DOMContentLoaded", () => {
    const budgetInput = document.getElementById("budgetInput");
    const goalOptions = document.querySelectorAll(".goal-option");
    const recommendButton = document.getElementById("recommendButton");

    const productCards = Array.from(
        document.querySelectorAll(".bundle-product")
    );

    const selectedCountElement = document.getElementById("selectedCount");
    const summaryBudget = document.getElementById("summaryBudget");
    const summaryTotal = document.getElementById("summaryTotal");
    const remainingBudget = document.getElementById("remainingBudget");
    const budgetProgress = document.getElementById("budgetProgress");
    const budgetPercentage = document.getElementById("budgetPercentage");
    const remainingBox = document.getElementById("remainingBox");
    const budgetMessage = document.getElementById("budgetMessage");

    const bundleForm = document.getElementById("bundleForm");
    const selectedProductsInputs = document.getElementById(
        "selectedProductsInputs"
    );

    const addBundleButton = document.getElementById("addBundleButton");
    const clearBundleButton = document.getElementById("clearBundleButton");

    const currencyFormatter = new Intl.NumberFormat("en-PH", {
        style: "currency",
        currency: "PHP",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    const selectedProducts = new Set();

    let currentGoal = "School Essentials";
    let recommendationApplied = false;

    /* =====================================
       PRODUCT DATA
    ===================================== */

    const products = productCards.map((card) => {
        const price = Number(card.dataset.price);

        return {
            id: String(card.dataset.productId),
            name: card.dataset.name || "",
            category: card.dataset.category || "",
            price: Number.isFinite(price) && price >= 0 ? price : 0,
            card: card,
            button: card.querySelector(".select-product-button")
        };
    });

    /* =====================================
       HELPERS
    ===================================== */

    function formatCurrency(amount) {
        return currencyFormatter.format(amount);
    }

    function getBudget() {
        const budget = Number(budgetInput.value);

        if (
            budgetInput.value.trim() === "" ||
            !Number.isFinite(budget) ||
            budget <= 0
        ) {
            return 0;
        }

        return budget;
    }

    function getSelectedProducts() {
        return products.filter((product) =>
            selectedProducts.has(product.id)
        );
    }

    function getBundleTotal() {
        return getSelectedProducts().reduce(
            (total, product) => total + product.price,
            0
        );
    }

    function normalizeText(value) {
        return String(value || "").toLowerCase().trim();
    }

    /* =====================================
       GOAL-BASED PRODUCT MATCHING
    ===================================== */

    const goalKeywords = {
        "School Essentials": {
            preferred: [
                "school",
                "student",
                "study",
                "education",
                "notebook",
                "pen",
                "paper",
                "backpack",
                "laptop",
                "tablet",
                "computer",
                "storage",
                "usb",
                "mouse",
                "keyboard",
                "headphone",
                "calculator",
                "printer",
                "flash drive"
            ],
            categories: [
                "school",
                "education"
            ]
        },

        "Gaming Setup": {
            preferred: [
                "gaming",
                "game",
                "gpu",
                "graphics",
                "monitor",
                "mechanical keyboard",
                "keyboard",
                "gaming mouse",
                "mouse",
                "headset",
                "headphone",
                "controller",
                "processor",
                "ram",
                "laptop",
                "computer",
                "ssd",
                "storage",
                "graphics card",
                "gaming chair"
            ],
            categories: [
                "gaming",
                "electronics",
                "accessories"
            ]
        },

        "Work-from-Home": {
            preferred: [
                "laptop",
                "computer",
                "monitor",
                "webcam",
                "headset",
                "headphone",
                "keyboard",
                "mouse",
                "desk",
                "office",
                "storage",
                "ssd",
                "printer",
                "processor",
                "ram",
                "workstation",
                "router"
            ],
            categories: [
                "office",
                "work",
                "productivity",
                "electronics",
                "accessories"
            ]
        },

        "Everyday Essentials": {
            preferred: [
                "accessory",
                "accessories",
                "charger",
                "power bank",
                "usb",
                "mouse",
                "keyboard",
                "headphone",
                "headset",
                "storage",
                "flash drive",
                "laptop",
                "tablet",
                "phone",
                "cable",
                "adapter",
                "earbuds"
            ],
            categories: [
                "everyday",
                "accessories",
                "electronics"
            ]
        }
    };

    function getGoalScore(product, goal) {
        const rules = goalKeywords[goal];

        if (!rules) {
            return 0;
        }

        const name = normalizeText(product.name);
        const category = normalizeText(product.category);

        let score = 0;

        rules.preferred.forEach((keyword) => {
            if (name.includes(keyword)) {
                score += 3;
            }
        });

        rules.categories.forEach((keyword) => {
            if (category.includes(keyword)) {
                score += 1;
            }
        });

        if (
            goal === "School Essentials" &&
            category.includes("school")
        ) {
            score += 4;
        }

        return score;
    }

    function isProductRelevant(product, goal) {
        return getGoalScore(product, goal) > 0;
    }

    /* =====================================
       PRODUCT VISIBILITY
    ===================================== */

    function showMatchingProducts(goal) {
        let visibleCount = 0;

        products.forEach((product) => {
            const matches = isProductRelevant(product, goal);

            product.card.hidden = !matches;

            if (!matches) {
                selectedProducts.delete(product.id);
                product.card.classList.remove("recommended");
            } else {
                visibleCount++;
            }
        });

        updateSummary();

        return visibleCount;
    }

    function showAllProducts() {
        products.forEach((product) => {
            product.card.hidden = false;
            product.card.classList.remove("recommended");
        });

        recommendationApplied = false;
        selectedProducts.clear();

        updateSummary();
    }

    /* =====================================
       UPDATE PRODUCT SELECTION INTERFACE
    ===================================== */

    function updateProductSelection() {
        productCards.forEach((card) => {
            const button = card.querySelector(
                ".select-product-button"
            );

            if (!button) {
                return;
            }

            const productId = String(card.dataset.productId);
            const isSelected = selectedProducts.has(productId);

            card.classList.toggle("selected", isSelected);
            button.classList.toggle("selected", isSelected);

            button.setAttribute(
                "aria-pressed",
                String(isSelected)
            );

            button.textContent = isSelected
                ? "✓ Remove from Bundle"
                : "+ Add to Bundle";
        });
    }

    /* =====================================
       UPDATE HIDDEN FORM INPUTS
    ===================================== */

    function updateFormInputs() {
        selectedProductsInputs.innerHTML = "";

        getSelectedProducts().forEach((product) => {
            const input = document.createElement("input");

            input.type = "hidden";
            input.name = "product_ids";
            input.value = product.id;

            selectedProductsInputs.appendChild(input);
        });
    }

    /* =====================================
       UPDATE BUDGET SUMMARY
    ===================================== */

    function updateSummary() {
        const budget = getBudget();
        const selected = getSelectedProducts();
        const total = getBundleTotal();
        const remaining = budget - total;

        const hasBudget = budget > 0;
        const isOverBudget = hasBudget && total > budget;
        const percentage = hasBudget
            ? (total / budget) * 100
            : 0;

        selectedCountElement.textContent =
            `${selected.length} ${selected.length === 1 ? "item" : "items"}`;

        summaryBudget.textContent = formatCurrency(budget);
        summaryTotal.textContent = formatCurrency(total);
        remainingBudget.textContent = formatCurrency(remaining);

        budgetProgress.style.width =
            `${Math.min(percentage, 100)}%`;

        budgetProgress.classList.toggle(
            "over-budget",
            isOverBudget
        );

        remainingBox.classList.toggle(
            "over-budget",
            isOverBudget
        );

        budgetPercentage.textContent = hasBudget
            ? `${percentage.toFixed(1)}% of budget used`
            : "Enter a valid budget to continue.";

        if (!hasBudget) {
            budgetMessage.textContent =
                "Enter a budget greater than zero.";
        } else if (selected.length === 0) {
            budgetMessage.textContent = recommendationApplied
                ? `No products have been selected for ${currentGoal}. Try another goal or budget.`
                : "Choose products to start building your bundle.";
        } else if (isOverBudget) {
            budgetMessage.textContent =
                "Your bundle exceeds your budget. Remove products or increase your budget.";
        } else if (remaining === 0) {
            budgetMessage.textContent =
                "Perfect! You have used your entire budget.";
        } else {
            budgetMessage.textContent =
                "Your bundle is within budget. You still have " +
                formatCurrency(remaining) +
                " available.";
        }

        addBundleButton.disabled =
            selected.length === 0 ||
            !hasBudget ||
            isOverBudget;

        updateProductSelection();
        updateFormInputs();
    }

    /* =====================================
       SELECT / DESELECT PRODUCTS
    ===================================== */

    productCards.forEach((card) => {
        const button = card.querySelector(
            ".select-product-button"
        );

        if (!button) {
            return;
        }

        button.addEventListener("click", () => {
            const productId = String(card.dataset.productId);
            const product = products.find((item) => item.id === productId);

            if (!product || card.hidden) {
                return;
            }

            if (selectedProducts.has(productId)) {
                selectedProducts.delete(productId);
            } else {
                const budget = getBudget();
                const newTotal = getBundleTotal() + product.price;

                if (budget <= 0) {
                    alert("Please enter a valid budget first.");
                    budgetInput.focus();
                    return;
                }

                if (newTotal > budget) {
                    alert("This product would exceed your budget.");
                    return;
                }

                selectedProducts.add(productId);
            }

            updateSummary();
        });
    });

    /* =====================================
       SELECT A GOAL
    ===================================== */

    goalOptions.forEach((button) => {
        button.setAttribute(
            "aria-pressed",
            String(button.dataset.goal === currentGoal)
        );

        button.addEventListener("click", () => {
            currentGoal = button.dataset.goal;

            goalOptions.forEach((option) => {
                const isActive = option === button;

                option.classList.toggle("active", isActive);
                option.setAttribute(
                    "aria-pressed",
                    String(isActive)
                );
            });

            // Changing the goal resets the previous recommendations.
            showAllProducts();
            budgetMessage.textContent =
                `You selected ${currentGoal}. Click "Find My Bundle" to see matching products.`;
        });
    });

    /* =====================================
       FIND MY BUNDLE
    ===================================== */

    recommendButton.addEventListener("click", () => {
        const budget = getBudget();

        if (budget <= 0) {
            alert("Please enter a budget greater than zero.");
            budgetInput.focus();
            return;
        }

        selectedProducts.clear();

        products.forEach((product) => {
            product.card.classList.remove("recommended");
        });

        // Only include products relevant to the selected goal.
        const matchingProducts = products
            .filter((product) => isProductRelevant(product, currentGoal))
            .sort((a, b) => {
                const scoreDifference =
                    getGoalScore(b, currentGoal) -
                    getGoalScore(a, currentGoal);

                if (scoreDifference !== 0) {
                    return scoreDifference;
                }

                return a.price - b.price;
            });

        // Hide products that do not match the selected goal.
        products.forEach((product) => {
            product.card.hidden = !isProductRelevant(
                product,
                currentGoal
            );
        });

        recommendationApplied = true;

        if (matchingProducts.length === 0) {
            updateSummary();

            budgetMessage.textContent =
                `No products currently match "${currentGoal}". Check your product names and categories, or add relevant products.`;

            return;
        }

        let total = 0;
        let selectedCount = 0;

        matchingProducts.forEach((product) => {
            if (
                product.price <= budget &&
                total + product.price <= budget
            ) {
                selectedProducts.add(product.id);
                total += product.price;
                selectedCount++;

                product.card.classList.add("recommended");
            }
        });

        updateSummary();

        if (selectedCount === 0) {
            budgetMessage.textContent =
                `Products for ${currentGoal} were found, but none fit your budget. Try increasing it.`;
        } else {
            budgetMessage.textContent =
                `Found ${matchingProducts.length} matching product(s) for ${currentGoal}. Selected ${selectedCount} within your budget. You can customize your bundle.`;
        }
    });

    /* =====================================
       CLEAR BUNDLE
    ===================================== */

    clearBundleButton.addEventListener("click", () => {
        selectedProducts.clear();

        products.forEach((product) => {
            product.card.classList.remove("recommended");
        });

        updateSummary();
    });

    /* =====================================
       BUDGET INPUT
    ===================================== */

    budgetInput.addEventListener("input", updateSummary);

    /* =====================================
       FORM VALIDATION
    ===================================== */

    bundleForm.addEventListener("submit", (event) => {
        const budget = getBudget();
        const total = getBundleTotal();
        const selected = getSelectedProducts();

        if (selected.length === 0) {
            event.preventDefault();
            alert("Please select at least one product.");
            return;
        }

        if (budget <= 0) {
            event.preventDefault();
            alert("Please enter a valid budget.");
            budgetInput.focus();
            return;
        }

        if (total > budget) {
            event.preventDefault();
            alert(
                "Your bundle exceeds your budget. Please adjust your selection."
            );
            return;
        }

        // Prevent submitting products hidden by the active goal filter.
        const hasInvalidSelection = selected.some(
            (product) => product.card.hidden
        );

        if (hasInvalidSelection) {
            event.preventDefault();
            alert("Please select products that match your chosen goal.");
        }
    });

    /* =====================================
       INITIALIZE
    ===================================== */

    // Show all products initially. Filtering begins after Find My Bundle.
    products.forEach((product) => {
        product.card.hidden = false;
    });

    updateSummary();
});