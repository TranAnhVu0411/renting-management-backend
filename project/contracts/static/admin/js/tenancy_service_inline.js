(function () {
    "use strict";

    const SERVICE_FIELDS = [
        { toggle: "laundry", price: "laundry_price" },
        { toggle: "parking", price: "parking_price" },
        { toggle: "internet", price: "internet_price" },
        { toggle: "cleaner", price: "cleaner_price" },
    ];

    /**
     * Show the price field only when its corresponding service is enabled.
     * The grouped fields are rendered inside the same .form-row.field-row.
     */
    function updateServicePrice(toggleName, priceName, toggleInput) {
        const row = toggleInput.closest(".form-row.field-row");

        if (!row) return;

        const priceField = row.querySelector(`.field-${priceName}`);

        if (!priceField) return;

        const isEnabled = toggleInput.checked;
        const isLargeScreen = window.matchMedia("(min-width: 1024px)").matches;

        if (isEnabled) {
            priceField.style.display = "";
            priceField.style.visibility = "";
        } else if (isLargeScreen) {
            priceField.style.display = "";
            priceField.style.visibility = "hidden";
        } else {
            priceField.style.display = "none";
            priceField.style.visibility = "";
        }
    }

    function updateAllServicePrices(root = document) {
        SERVICE_FIELDS.forEach(({ toggle, price }) => {
            root.querySelectorAll(
                `.field-${toggle} input[type="checkbox"]`
            ).forEach((input) => {
                updateServicePrice(toggle, price, input);
            });
        });
    }

    function handleChange(event) {
        const input = event.target;

        if (
            !(input instanceof HTMLInputElement) ||
            input.type !== "checkbox"
        ) {
            return;
        }

        const service = SERVICE_FIELDS.find(({ toggle }) =>
            input.closest(`.field-${toggle}`)
        );

        if (service) {
            updateServicePrice(
                service.toggle,
                service.price,
                input
            );
        }
    }

    function init() {
        // Apply the initial state when the page loads.
        updateAllServicePrices();

        // Handle checkbox changes, including dynamically added inline forms.
        document.addEventListener("change", handleChange);

        // Handle inline rows added dynamically by Django Admin.
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        updateAllServicePrices(node);
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
        });
        
        // Update service prices when the screen size changes.
        const mediaQuery = window.matchMedia("(min-width: 1024px)");

        mediaQuery.addEventListener("change", () => {
            updateAllServicePrices();
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init, {
            once: true,
        });
    } else {
        init();
    }
})();