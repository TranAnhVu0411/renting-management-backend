(function () {
    "use strict";

    function initRoomConditions() {
        const container = document.getElementById("room-conditions");
        const roomInput = document.getElementById("id_room");

        if (!container || !roomInput) return;

        const message = document.getElementById(
            "room-conditions-message"
        );
        const details = document.getElementById(
            "room-conditions-details"
        );
        const allowValue = document.getElementById(
            "room-allow-cotenant"
        );
        const maximumValue = document.getElementById(
            "room-cotenant-maximum"
        );
        const waterMeterValue = document.getElementById(
            "room-has-water-meter"
        );

        const urlTemplate = container.dataset.urlTemplate;
        let requestController = null;

        async function updateRoomConditions() {
            const roomId = roomInput.value;

            if (requestController) {
                requestController.abort();
                requestController = null;
            }

            details.hidden = true;

            if (!roomId) {
                message.textContent =
                    "Vui lòng chọn phòng để xem điều kiện ở ghép.";
                return;
            }

            message.textContent = "Đang tải điều kiện phòng...";

            requestController = new AbortController();

            const url = urlTemplate.replace(
                "00000000-0000-0000-0000-000000000000",
                encodeURIComponent(roomId)
            );

            try {
                const response = await fetch(url, {
                    method: "GET",
                    credentials: "same-origin",
                    headers: {
                        Accept: "application/json",
                    },
                    signal: requestController.signal,
                });

                if (!response.ok) {
                    throw new Error("Không thể tải điều kiện phòng.");
                }

                const data = await response.json();

                allowValue.textContent = data.allow_co_tenant
                    ? "Có"
                    : "Không";

                maximumValue.textContent = data.co_tenant_maximum;
                waterMeterValue.textContent = data.has_water_meter ? "Có" : "Không";
                details.hidden = false;
                message.textContent = "";
            } catch (error) {
                if (error.name === "AbortError") return;

                message.textContent =
                    "Không thể tải điều kiện phòng. Vui lòng thử lại.";
            }
        }

        roomInput.addEventListener("change", updateRoomConditions);

        // Hiển thị điều kiện ngay khi mở trang sửa Tenancy.
        updateRoomConditions();
    }

    function initContractDates() {
        const contractStartDateInput = document.getElementById(
            "id_contract_start_date"
        );

        const contractEndDateInput = document.getElementById(
            "id_contract_end_date"
        );

        const billingStartDateInput = document.getElementById(
            "id_billing_start_date"
        );

        if (
            !contractStartDateInput ||
            !contractEndDateInput ||
            !billingStartDateInput
        ) {
            return;
        }

        /**
         * Parse a date using Django's localized DATE_INPUT_FORMATS.
         */
        function parseDate(value) {
            if (!value) return null;

            const formats = get_format("DATE_INPUT_FORMATS");

            for (const format of formats) {
                const tokens = [];
                const pattern = format.replace(
                    /%([dmyY])/g,
                    (_, token) => {
                        tokens.push(token);

                        switch (token) {
                            case "d":
                                return "(\\d{1,2})";
                            case "m":
                                return "(\\d{1,2})";
                            case "Y":
                                return "(\\d{4})";
                            case "y":
                                return "(\\d{2})";
                            default:
                                return "";
                        }
                    }
                );

                const match = value.match(
                    new RegExp(`^${pattern}$`)
                );

                if (!match) continue;

                const parts = {};

                tokens.forEach((token, index) => {
                    parts[token] = Number(match[index + 1]);
                });

                const year = parts.Y ?? (
                    parts.y >= 69
                        ? 1900 + parts.y
                        : 2000 + parts.y
                );

                const month = parts.m;
                const day = parts.d;

                if (
                    !year ||
                    !month ||
                    !day ||
                    month < 1 ||
                    month > 12 ||
                    day < 1 ||
                    day > 31
                ) {
                    continue;
                }

                const date = new Date(year, month - 1, day);

                // Reject invalid dates such as 31/02/2026.
                if (
                    date.getFullYear() !== year ||
                    date.getMonth() !== month - 1 ||
                    date.getDate() !== day
                ) {
                    continue;
                }

                return date;
            }

            return null;
        }

        /**
         * Format a date using Django's localized date format.
         */
        function formatDate(date) {
            const format = get_format("DATE_INPUT_FORMATS")[0];

            const values = {
                d: String(date.getDate()).padStart(2, "0"),
                m: String(date.getMonth() + 1).padStart(2, "0"),
                Y: String(date.getFullYear()),
                y: String(date.getFullYear()).slice(-2),
            };

            return format.replace(
                /%([dmyY])/g,
                (_, token) => values[token] ?? token
            );
        }

        function addOneYear(date) {
            const year = date.getFullYear() + 1;
            const month = date.getMonth();
            const day = date.getDate();

            const result = new Date(year, month, day);

            // Handle February 29 in a leap year.
            if (result.getMonth() !== month) {
                result.setDate(0);
            }

            return result;
        }

        function updateContractDates() {
            const startDateValue = contractStartDateInput.value.trim();

            if (!startDateValue) return;

            const startDate = parseDate(startDateValue);

            if (!startDate) return;

            // Only populate empty fields.
            if (!billingStartDateInput.value.trim()) {
                billingStartDateInput.value = formatDate(startDate);
            }

            if (!contractEndDateInput.value.trim()) {
                const endDate = addOneYear(startDate);

                contractEndDateInput.value = formatDate(endDate);
            }
        }

        contractStartDateInput.addEventListener(
            "blur",
            updateContractDates
        );

        contractStartDateInput.addEventListener(
            "change",
            updateContractDates
        );
    }

    function initTenancyMeterInline() {
        const roomInput = document.getElementById("id_room");
        const table = document.querySelector("#meters-data");
        const totalForms = document.querySelector(
            "#id_meters-TOTAL_FORMS"
        );

        if (!roomInput || !table || !totalForms) {
            return;
        }

        const emptyForm = table.querySelector(
            "tbody.template.empty-form"
        );

        if (!emptyForm) {
            console.error("TenancyMeter empty form not found.");
            return;
        }
        
        // Insert placeholder for meters information when no room is selected.
        const placeholder = document.createElement("div");
        placeholder.id = "meters-placeholder";
        placeholder.className = `
            flex flex-col items-center justify-center
            rounded-lg border border-dashed border-base-300
            bg-base-50 dark:bg-base-900
            px-6 py-10 text-center
        `;

        placeholder.innerHTML = `
            <div class="
                flex items-center justify-center
                w-12 h-12 rounded-xl
                bg-base-100 dark:bg-base-800
                text-base-500 dark:text-base-400
                mb-4 meter-placeholder
            ">
                <span class="material-symbols-outlined p-2 text-4xl">
                    gas_meter
                </span>
            </div>

            <h3 class="
                text-sm font-semibold
                text-font-default-light dark:text-font-default-dark
                mb-1
            ">
                Chưa có thông tin đồng hồ
            </h3>

            <p class="
                max-w-md text-sm
                text-font-subtle-light dark:text-font-subtle-dark
            ">
                Vui lòng chọn phòng để hiển thị danh sách
                đồng hồ đo điện và nước của phòng.
            </p>
        `;
        table.parentElement.insertBefore(placeholder, table);

        /**
         * Update the placeholder message for meters information.
         */
        function showPlaceholder({title, description,}) {
            placeholder.classList.remove("hidden");

            placeholder.querySelector("h3").textContent = title;
            placeholder.querySelector("p").textContent = description;

            table.hidden = true;
        }

        function hidePlaceholder() {
            placeholder.classList.add("hidden");
            table.hidden = false;
        }

        let requestController = null;
        let requestSequence = 0;

        /**
         * Remove all dynamically generated meter forms.
         *
         * This implementation is intended for the Add Tenancy form,
         * where INITIAL_FORMS is 0.
         */
        function resetMeterForms() {
            const forms = table.querySelectorAll(
                "tbody.form-group:not(.template)"
            );

            forms.forEach((form) => form.remove());

            totalForms.value = "0";
        }

        /**
         * Replace Django's __prefix__ placeholder with
         * the actual form index.
         */
        function replaceFormIndex(element, index) {
            const elements = [
                element,
                ...element.querySelectorAll("*"),
            ];

            elements.forEach((item) => {
                Array.from(item.attributes).forEach((attr) => {
                    if (attr.value.includes("__prefix__")) {
                        item.setAttribute(
                            attr.name,
                            attr.value.replaceAll("__prefix__", index)
                        );
                    }
                });
            });
        }

        /**
         * Create one meter form from Django's empty form.
         */
        function addMeterForm(meter, index) {
            const form = emptyForm.cloneNode(true);

            form.classList.remove("template", "empty-form");

            replaceFormIndex(form, index);

            // Populate meter select.
            const meterField = form.querySelector(
                `[name="meters-${index}-meter"]`
            );

            meterField.innerHTML = "";

            const option = document.createElement("option");

            option.value = meter.id;
            option.textContent = meter.label;

            option.selected = true;

            meterField.appendChild(option);

            // Make meter select read-only.
            meterField.setAttribute("tabindex", "-1");
            meterField.setAttribute("aria-disabled", "true");
            meterField.classList.add("meter-select-readonly");

            // Reset meter reading.
            const readingField = form.querySelector(
                `[name="meters-${index}-meter_reading"]`
            );

            readingField.value = "";

            // Add form to table.
            table.querySelector("tfoot").before(form);

            totalForms.value = String(index + 1);
        }

        /**
         * Fetch meters belonging to the selected room.
         */
        async function fetchRoomMeters(url, signal) {
            const response = await fetch(url, {
                method: "GET",
                credentials: "same-origin",
                headers: {
                    Accept: "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
                signal,
            });

            if (!response.ok) {
                throw new Error(
                    `Unable to fetch room meters: ${response.status}`
                );
            }

            return response.json();
        }

        /**
         * Update meter forms whenever Room changes.
         */
        async function updateRoomMeters() {
            const currentSequence = ++requestSequence;

            if (requestController) {
                requestController.abort();
            }

            resetMeterForms();
            const url = roomInput.selectedOptions[0]?.dataset.roomMetersUrl;
            if (!url) {
                showPlaceholder({
                    title: "Chưa có thông tin đồng hồ",
                    description:
                        "Vui lòng chọn phòng để hiển thị danh sách đồng hồ đo điện và nước của phòng.",
                });
                return;
            }

            showPlaceholder({
                title: "Đang tải thông tin đồng hồ",
                description:
                    "Vui lòng đợi trong giây lát.",
            });

            requestController = new AbortController();

            try {
                const data = await fetchRoomMeters(
                    url,
                    requestController.signal
                );

                // Ignore outdated responses.
                if (currentSequence !== requestSequence) {
                    return;
                }

                if (data.length === 0) {
                    showPlaceholder({
                        title: "Phòng chưa có đồng hồ",
                        description:
                            "Phòng này chưa được thiết lập đồng hồ đo. Bạn cần thêm đồng hồ cho phòng trước khi tạo hợp đồng.",
                    });
                    return;
                }

                data.forEach((meter, index) => {
                    addMeterForm(meter, index);
                });
                hidePlaceholder();
            } catch (error) {
                if (error.name === "AbortError") {
                    return;
                }

                console.error(error);

                showPlaceholder({
                    title: "Không thể tải thông tin đồng hồ",
                    description:
                        "Đã xảy ra lỗi khi tải dữ liệu. Vui lòng thử chọn lại phòng.",
                });
            }
        }

        roomInput.addEventListener("change", updateRoomMeters);
    }

    function init() {
        initRoomConditions();
        initContractDates();
        initTenancyMeterInline();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init, {
            once: true,
        });
    } else {
        init();
    }
})();
