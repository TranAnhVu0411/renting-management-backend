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
                "ROOM_ID_PLACEHOLDER",
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

        function addOneYear(dateValue) {
            const date = new Date(`${dateValue}T00:00:00`);

            if (Number.isNaN(date.getTime())) {
                return "";
            }

            const originalMonth = date.getMonth();

            date.setFullYear(date.getFullYear() + 1);

            // Handle February 29 in a leap year.
            if (date.getMonth() !== originalMonth) {
                date.setDate(0);
            }

            return [
                date.getFullYear(),
                String(date.getMonth() + 1).padStart(2, "0"),
                String(date.getDate()).padStart(2, "0"),
            ].join("-");
        }

        function updateContractDates() {
            const startDate = contractStartDateInput.value;

            if (!startDate) return;

            // Only populate empty fields.
            if (!billingStartDateInput.value) {
                billingStartDateInput.value = startDate;
            }

            if (!contractEndDateInput.value) {
                contractEndDateInput.value = addOneYear(startDate);
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
