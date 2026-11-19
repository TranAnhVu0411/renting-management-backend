
(function () {
    "use strict";

    function getDateFormat() {
        if (typeof get_format !== "function") {
            return null;
        }

        const formats = get_format("DATE_INPUT_FORMATS");

        return formats?.[0] || null;
    }

    function getFormatParts(format) {
        const parts = [];
        const regex = /%([dmyY])/g;

        let previousIndex = 0;
        let match;

        while ((match = regex.exec(format)) !== null) {
            const token = match[1];

            parts.push({
                token,
                length: token === "Y" ? 4 : 2,
                separator: format.slice(previousIndex, match.index),
            });

            previousIndex = regex.lastIndex;
        }

        if (!parts.length) {
            return null;
        }

        return parts;
    }

    function getPlaceholder(parts) {
        const placeholders = {
            d: "dd",
            m: "mm",
            Y: "yyyy",
            y: "yy",
        };

        return parts
            .map((part, index) => {
                const separator = part.separator;
                return `${separator}${placeholders[part.token]}`;
            })
            .join("");
    }

    function formatPartialDate(value, parts) {
        const maxLength = parts.reduce(
            (total, part) => total + part.length,
            0
        );

        const digits = value
            .replace(/\D/g, "")
            .slice(0, maxLength);

        const hasTrailingSeparator = /[^\d]+$/.test(value);

        let result = "";
        let offset = 0;
        let lastCompletedIndex = -1;

        for (let index = 0; index < parts.length; index++) {
            const part = parts[index];

            if (offset >= digits.length) {
                break;
            }

            const segment = digits.slice(
                offset,
                offset + part.length
            );

            result += part.separator;
            result += segment;

            offset += segment.length;

            if (segment.length === part.length) {
                lastCompletedIndex = index;
            } else {
                break;
            }
        }

        // Preserve a separator explicitly entered by the user.
        if (
            hasTrailingSeparator &&
            lastCompletedIndex >= 0 &&
            lastCompletedIndex < parts.length - 1
        ) {
            result += parts[lastCompletedIndex + 1].separator;
        }

        return result;
    }

    function getCaretPosition(value, digitCount) {
        if (digitCount <= 0) {
            return 0;
        }

        let count = 0;

        for (let index = 0; index < value.length; index++) {
            if (/\d/.test(value[index])) {
                count++;

                if (count === digitCount) {
                    return index + 1;
                }
            }
        }

        return value.length;
    }

    function setFormattedValue(input, parts, rawValue, selectionStart, selectionEnd) {
        const formattedValue = formatPartialDate(rawValue, parts);

        const start = formatPartialDate(
            rawValue.slice(0, selectionStart),
            parts
        ).length;

        const end = formatPartialDate(
            rawValue.slice(0, selectionEnd),
            parts
        ).length;

        input.value = formattedValue;

        input.setSelectionRange(
            Math.min(start, formattedValue.length),
            Math.min(end, formattedValue.length)
        );
    }

    function removeAdjacentDigit(input, parts, direction) {
        const value = input.value;
        const start = input.selectionStart;
        const end = input.selectionEnd;

        if (start !== end) {
            return false;
        }

        const separatorIndex = direction === "backward"
            ? start - 1
            : start;

        if (
            separatorIndex < 0 ||
            separatorIndex >= value.length ||
            /\d/.test(value[separatorIndex])
        ) {
            return false;
        }

        let digitIndex = separatorIndex;

        while (
            digitIndex >= 0 &&
            digitIndex < value.length &&
            !/\d/.test(value[digitIndex])
        ) {
            digitIndex += direction === "backward" ? -1 : 1;
        }

        if (
            digitIndex < 0 ||
            digitIndex >= value.length
        ) {
            return false;
        }

        const digitsBefore = value
            .slice(0, digitIndex)
            .replace(/\D/g, "").length;

        const nextValue =
            value.slice(0, digitIndex) +
            value.slice(digitIndex + 1);

        const formattedValue = formatPartialDate(
            nextValue,
            parts
        );

        const caret = getCaretPosition(
            formattedValue,
            digitsBefore
        );

        input.value = formattedValue;
        input.setSelectionRange(caret, caret);

        return true;
    }

    function initDateInput(input) {
        if (
            input.dataset.dateInputInitialized === "true" ||
            input.disabled ||
            input.readOnly
        ) {
            return;
        }

        const format = getDateFormat();

        if (!format) {
            return;
        }

        const parts = getFormatParts(format);

        if (!parts) {
            return;
        }

        input.dataset.dateInputInitialized = "true";
        input.placeholder = getPlaceholder(parts);

        input.addEventListener("input", function () {
            const rawValue = input.value;

            const selectionStart = input.selectionStart;
            const selectionEnd = input.selectionEnd;

            setFormattedValue(
                input,
                parts,
                rawValue,
                selectionStart,
                selectionEnd
            );
        });

        input.addEventListener("keydown", function (event) {
            if (
                event.key === "Backspace" &&
                removeAdjacentDigit(input, parts, "backward")
            ) {
                event.preventDefault();
                return;
            }

            if (
                event.key === "Delete" &&
                removeAdjacentDigit(input, parts, "forward")
            ) {
                event.preventDefault();
            }
        });

        // Normalize values changed by other scripts or autofill.
        input.addEventListener("change", function () {
            const value = input.value;

            if (!value) return;

            setFormattedValue(
                input,
                parts,
                value,
                value.length,
                value.length
            );
        });
    }

    function init() {
        document
            .querySelectorAll(
                'input[data-date-input-mask="true"]'
            )
            .forEach(initDateInput);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init, {
            once: true,
        });
    } else {
        init();
    }
})();
