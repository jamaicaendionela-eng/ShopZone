let quantity = 1;


function increaseQuantity() {

    quantity++;

    updateQuantity();

}


function decreaseQuantity() {

    if (quantity > 1) {

        quantity--;

    }

    updateQuantity();

}


function updateQuantity() {

    const quantityElement =
        document.getElementById("quantity");


    if (quantityElement) {

        quantityElement.textContent = quantity;

    }

}


function addToCart() {

    alert(
        "Product added to cart! Quantity: " + quantity
    );

}