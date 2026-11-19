
// ShopZone Global JavaScript

document.addEventListener("DOMContentLoaded", function () {

    // SMOOTH SCROLLING
    document.querySelectorAll('a[href^="#"]').forEach(function (link) {

        link.addEventListener("click", function (event) {

            const targetId = this.getAttribute("href");

            if (targetId === "#") {
                return;
            }

            const target = document.querySelector(targetId);

            if (target) {
                event.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth"
                });
            }
        });

    });


    // LOGOUT CONFIRMATION MODAL

    const logoutStyle = document.createElement("style");

    logoutStyle.textContent = `
        .logout-overlay {
            position: fixed;
            inset: 0;
            background: rgba(5, 3, 12, 0.78);
            backdrop-filter: blur(7px);
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            z-index: 99999;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.25s ease, visibility 0.25s ease;
        }

        .logout-overlay.show {
            opacity: 1;
            visibility: visible;
        }

        .logout-modal {
            width: 100%;
            max-width: 420px;
            background: linear-gradient(145deg, #211631, #130d20);
            border: 1px solid #50336f;
            border-radius: 18px;
            padding: 35px 30px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            transform: translateY(20px) scale(0.96);
            transition: transform 0.25s ease;
        }

        .logout-overlay.show .logout-modal {
            transform: translateY(0) scale(1);
        }

        .logout-icon {
            width: 75px;
            height: 75px;
            margin: 0 auto 20px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            background: rgba(168, 85, 247, 0.15);
            border: 1px solid rgba(192, 132, 252, 0.35);
            color: #c084fc;
            font-size: 34px;
        }

        .logout-modal h2 {
            color: #ffffff;
            font-size: 23px;
            margin-bottom: 12px;
        }

        .logout-modal p {
            color: #b6a9ca;
            font-size: 14px;
            line-height: 1.7;
            margin-bottom: 27px;
        }

        .logout-actions {
            display: flex;
            justify-content: center;
            gap: 12px;
        }

        .logout-actions button {
            flex: 1;
            padding: 12px 15px;
            border: none;
            border-radius: 9px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.2s ease;
        }

        .logout-cancel {
            background: #30213f;
            color: #e9d5ff;
            border: 1px solid #50336f !important;
        }

        .logout-cancel:hover {
            background: #402b55;
        }

        .logout-confirm {
            background: linear-gradient(135deg, #a855f7, #7e22ce);
            color: white;
        }

        .logout-confirm:hover {
            background: linear-gradient(135deg, #c084fc, #9333ea);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(168, 85, 247, 0.3);
        }

        @media (max-width: 450px) {
            .logout-modal {
                padding: 28px 20px;
            }

            .logout-modal h2 {
                font-size: 20px;
            }

            .logout-actions {
                flex-direction: column-reverse;
            }
        }
    `;

    document.head.appendChild(logoutStyle);


    // CREATE MODAL

    const logoutOverlay = document.createElement("div");

    logoutOverlay.className = "logout-overlay";

    logoutOverlay.innerHTML = `
        <div class="logout-modal" role="dialog"
             aria-modal="true"
             aria-labelledby="logoutTitle">

            <div class="logout-icon">
                ↪
            </div>

            <h2 id="logoutTitle">
                Confirm Logout
            </h2>

            <p>
                Are you sure you want to log out of your
                ShopZone account?
                <br>
                You can log in again anytime.
            </p>

            <div class="logout-actions">

                <button type="button" class="logout-cancel">
                    Cancel
                </button>

                <button type="button" class="logout-confirm">
                    Yes, Logout
                </button>

            </div>

        </div>
    `;

    document.body.appendChild(logoutOverlay);


    const cancelButton = logoutOverlay.querySelector(".logout-cancel");
    const confirmButton = logoutOverlay.querySelector(".logout-confirm");

    let logoutUrl = null;


    // OPEN MODAL FOR ALL LOGOUT LINKS

    document.addEventListener("click", function (event) {

        const logoutLink = event.target.closest("a[href]");

        if (!logoutLink) {
            return;
        }

        const linkUrl = new URL(logoutLink.href, window.location.origin);

        if (
            linkUrl.origin === window.location.origin &&
            linkUrl.pathname.replace(/\/+$/, "").endsWith("/logout")
        ) {
            event.preventDefault();

            logoutUrl = logoutLink.href;

            logoutOverlay.classList.add("show");

            cancelButton.focus();
        }

    });


    // CLOSE MODAL

    function closeLogoutModal() {
        logoutOverlay.classList.remove("show");
        logoutUrl = null;
    }

    cancelButton.addEventListener("click", closeLogoutModal);


    // CLICK OUTSIDE MODAL

    logoutOverlay.addEventListener("click", function (event) {

        if (event.target === logoutOverlay) {
            closeLogoutModal();
        }

    });


    // ESCAPE KEY

    document.addEventListener("keydown", function (event) {

        if (
            event.key === "Escape" &&
            logoutOverlay.classList.contains("show")
        ) {
            closeLogoutModal();
        }

    });


    // CONFIRM LOGOUT

    confirmButton.addEventListener("click", function () {

        if (logoutUrl) {
            window.location.href = logoutUrl;
        }

    });

});
