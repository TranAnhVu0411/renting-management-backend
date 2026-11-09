(function () {
    "use strict";

    /**
     * Update the water price help text based on the flat fee toggle.
     */
    function updateWaterPriceHelpText(toggleInput) {
        const field = toggleInput.closest(".form-row.field-row");

        if (!field) return;

        const waterPriceField = field.querySelector(".field-water_price");

        if (!waterPriceField) return;

        const helpText = waterPriceField.querySelector(
            ".leading-relaxed.mt-2.text-xs"
        );

        if (!helpText) return;

        helpText.textContent = toggleInput.checked
            ? "Giá nước (khoán)"
            : "Giá nước (theo m3)";
    }

    function updateAllWaterPriceHelpTexts(root = document) {
        root.querySelectorAll(
            '.field-is_water_flat_fee input[type="checkbox"]'
        ).forEach((input) => {
            updateWaterPriceHelpText(input);
        });
    }

    /**
     * Show the price field only when its corresponding service is enabled.
     * The grouped fields are rendered inside the same .form-row.field-row.
     */
    const SERVICE_FIELDS = [
        { toggle: "laundry", price: "laundry_price" },
        { toggle: "internet", price: "internet_price" },
        { toggle: "cleaner", price: "cleaner_price" },
    ];

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

    /**
     * Show the parking price field only when vehicle plate numbers exist.
     */
    function updateParkingPriceVisibility() {
        const vehiclePlateNumbersField = document.querySelector(
            ".field-vehicle_plate_numbers"
        );

        if (!vehiclePlateNumbersField) return;

        const hasVehicle = Array.from(
            vehiclePlateNumbersField.querySelectorAll(
                'input:not([type="hidden"]), textarea, select'
            )
        ).some((input) => input.value.trim() !== "");

        document.querySelectorAll(".field-parking_price").forEach((priceField) => {
            if (hasVehicle) {
                priceField.style.display = "";
            } else {
                priceField.style.display = "none";
            }
        });
    }

    function updateAllServicePrices(root = document) {
        SERVICE_FIELDS.forEach(({ toggle, price }) => {
            root.querySelectorAll(
                `.field-${toggle} input[type="checkbox"]`
            ).forEach((input) => {
                updateServicePrice(toggle, price, input);
            });
        });
        updateParkingPriceVisibility();
    }

    function handleVehiclePlateNumbersChange(event) {
        const input = event.target;

        if (
            !(
                input instanceof HTMLInputElement ||
                input instanceof HTMLTextAreaElement
            ) ||
            !input.closest(".field-vehicle_plate_numbers")
        ) {
            return;
        }

        updateParkingPriceVisibility();
    }

    /**
     * Show the button next to price field. When user click the button,
     * it will apply the default service price rule in the corresponding field.
     */
    const SERVICE_PRICE_FIELDS = [
        "electricity_price",
        "water_price",
        "laundry_price",
        "parking_price",
        "internet_price",
        "cleaner_price",
    ];

    let servicePriceRulesPromise = null;

    /**
     * Get the ServicePriceRule endpoint.
     *
     * Supports standard Django Admin add/change URLs.
     */
    function getServicePriceRuleUrl() {
        const path = window.location.pathname.replace(
            /(?:add|[^/]+\/change)\/?$/,
            "service-price-rule/"
        );

        return new URL(path, window.location.origin);
    }

    /**
     * Fetch default service prices.
     * Cache the request to avoid unnecessary API calls.
     */
    function getServicePriceRules() {
        if (!servicePriceRulesPromise) {
            servicePriceRulesPromise = fetch(
                getServicePriceRuleUrl(),
                {
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },
                }
            )
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(
                            "Unable to fetch service price rules."
                        );
                    }

                    return response.json();
                })
                .catch((error) => {
                    servicePriceRulesPromise = null;
                    throw error;
                });
        }

        return servicePriceRulesPromise;
    }

    /**
     * Get the corresponding price rule field.
     * Water price depends on the flat fee toggle.
     */
    function getServicePriceRuleField(input) {
        const fieldName = input.name.split("-").pop();

        if (fieldName !== "water_price") {
            return fieldName;
        }

        const row = input.closest(".form-row.field-row");

        const flatFeeToggle = row?.querySelector(
            '.field-is_water_flat_fee input[type="checkbox"]'
        );

        return flatFeeToggle?.checked
            ? "water_flat_fee"
            : "water_price";
    }

    /**
     * Handle the service price button click.
     */
    async function handleServicePriceClick(input, button) {
        try {
            button.disabled = true;

            const rules = await getServicePriceRules();
            const ruleField = getServicePriceRuleField(input);

            if (!ruleField || rules[ruleField] === undefined) {
                throw new Error(
                    `Service price rule "${ruleField}" not found.`
                );
            }

            input.value = rules[ruleField];

            // Notify other scripts and Django Admin about the change.
            input.dispatchEvent(
                new Event("input", { bubbles: true })
            );

            input.dispatchEvent(
                new Event("change", { bubbles: true })
            );
        } catch (error) {
            console.error("Service price rule error:", error);
            button.title = "Không thể lấy giá mặc định. Vui lòng thử lại.";
        } finally {
            button.disabled = false;
        }
    }

    /**
     * Create a button next to a service price input.
     */
    function createServicePriceButton(input) {
        if (input.dataset.servicePriceButtonInitialized) return;

        const button = document.createElement("button");

        button.type = "button";
        button.className = [
            // Layout
            "inline-flex",
            "items-center",
            "justify-center",
            "shrink-0",

            // Size
            "rounded-md",
            "px-2",
            "py-1",

            // Light mode
            "border",
            "border-base-300",
            "bg-base-100",
            "text-base-600",
            "hover:bg-base-200",

            // Dark mode
            "dark:border-base-700",
            "dark:bg-base-800",
            "dark:text-base-300",
            "dark:hover:bg-base-700",

            // Transition
            "transition-colors",
            "duration-150",

            // Focus
            "focus:outline-none",
            "focus:ring-2",
            "focus:ring-primary-500",
        ].join(" ");

        button.title = "Lấy giá mặc định";
        button.setAttribute("aria-label", "Lấy giá mặc định");

        button.innerHTML = `
            <span class="material-symbols-outlined text-base">
                download
            </span>
        `;

        button.addEventListener("click", () => {
            handleServicePriceClick(input, button);
        });

        // Wrap the input and button to control their layout.
        const wrapper = document.createElement("div");

        wrapper.className = "service-price-input-wrapper";

        input.parentNode.insertBefore(wrapper, input);

        wrapper.append(input, button);

        input.dataset.servicePriceButtonInitialized = "true";
    }

    /**
     * Initialize service price buttons.
     */
    function updateAllServicePriceButtons(root = document) {
        SERVICE_PRICE_FIELDS.forEach((fieldName) => {
            root.querySelectorAll(
                `.field-${fieldName} input:not([type="hidden"])`
            ).forEach((input) => {
                createServicePriceButton(input);
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

        if (input.closest(".field-is_water_flat_fee")) {
            updateWaterPriceHelpText(input);
        }
    }

    function init() {
        // Apply the initial state when the page loads.
        updateAllWaterPriceHelpTexts();
        updateAllServicePrices();
        updateAllServicePriceButtons();

        // Handle checkbox changes, including dynamically added inline forms.
        document.addEventListener("change", handleChange);
        
        // Handle changes to the vehicle plate numbers input to update parking price visibility.
        document.addEventListener("input", handleVehiclePlateNumbersChange);
        document.addEventListener("change", handleVehiclePlateNumbersChange);

        // Handle inline rows added dynamically by Django Admin.
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        updateAllWaterPriceHelpTexts(node);
                        updateAllServicePrices(node);
                        updateAllServicePriceButtons(node);
                    }
                });
            });

            updateParkingPriceVisibility();
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
        });
        
        // Update service prices when the screen size changes.
        const mediaQuery = window.matchMedia("(min-width: 1024px)");

        mediaQuery.addEventListener("change", () => {
            updateAllWaterPriceHelpTexts();
            updateAllServicePrices();
            updateAllServicePriceButtons();
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
