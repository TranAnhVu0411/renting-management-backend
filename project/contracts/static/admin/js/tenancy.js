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

    function init() {
        initRoomConditions();
        initContractDates();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init, {
            once: true,
        });
    } else {
        init();
    }
})();
