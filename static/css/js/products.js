let currentCategory = "all";


function updateProducts() {

    const searchInput =
        document.getElementById("searchInput");

    const searchTerm =
        searchInput
            ? searchInput.value.trim().toLowerCase()
            : "";


    const productCards =
        document.querySelectorAll(".product-card");


    productCards.forEach(function (product) {

        const productName =
            (
                product.getAttribute("data-name") || ""
            ).toLowerCase();


        const productCategory =
            (
                product.getAttribute("data-category") || ""
            ).toLowerCase();


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


function addToCart(productName) {

    alert(productName + " added to cart!");

}