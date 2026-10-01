let quantity = 1;


/* =========================================================
   QUANTITY
   ========================================================= */

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

    const quantityInput =
        document.getElementById("quantityInput");


    if (quantityElement) {

        quantityElement.textContent =
            quantity;

    }


    if (quantityInput) {

        quantityInput.value =
            quantity;

    }

}


/* =========================================================
   CART NOTIFICATION
   ========================================================= */

function showCartNotification() {

    const cartLink =
        document.querySelector(".cart-link");


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
   ADD TO CART WITHOUT RELOADING PAGE
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        updateQuantity();


        const form =
            document.getElementById("addToCartForm");


        const button =
            document.getElementById("addCartButton");


        if (!form || !button) {
            return;
        }


        form.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();


                const originalText =
                    button.innerHTML;


                button.disabled = true;


                try {

                    const response =
                        await fetch(
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
                     * Flask has successfully
                     * added the product.
                     */

                    showCartNotification();


                    /*
                     * Button feedback.
                     */

                    button.classList.add("added");

                    button.innerHTML =
                        "✓ Added to Cart";


                    /*
                     * Restore button.
                     */

                    setTimeout(
                        function () {

                            button.classList.remove(
                                "added"
                            );

                            button.innerHTML =
                                originalText;

                            button.disabled =
                                false;

                        },
                        1000
                    );


                } catch (error) {

                    console.error(
                        "Add to cart error:",
                        error
                    );


                    button.innerHTML =
                        "⚠ Try Again";


                    button.disabled =
                        false;


                    setTimeout(
                        function () {

                            button.innerHTML =
                                originalText;

                        },
                        1500
                    );

                }

            }
        );

    }
);