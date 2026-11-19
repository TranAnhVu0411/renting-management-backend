from decimal import Decimal, InvalidOperation
from django.utils.formats import get_format
from unfold.widgets import UnfoldAdminTextInputWidget, UnfoldAdminDateWidget


class ThousandsInput(UnfoldAdminTextInputWidget):
    def __init__(self, attrs=None):
        super().__init__(
            attrs={"inputmode": "decimal", "data-thousands": "1", **(attrs or {})}
        )

    class Media:
        js = ("core/js/thousands_input.js",)

    @staticmethod
    def _seps():
        return (
            get_format("THOUSAND_SEPARATOR", use_l10n=True),
            get_format("DECIMAL_SEPARATOR", use_l10n=True),
        )

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        thousand, decimal = self._seps()
        attrs["data-thousand-sep"] = thousand
        attrs["data-decimal-sep"] = decimal
        return attrs

    def format_value(self, value):
        if value in (None, ""):
            return ""
        thousand, decimal = self._seps()
        try:
            text = f"{Decimal(str(value)):,}"  # dạng chuẩn: 1,234.5
        except InvalidOperation:
            return str(value)
        return text.translate(str.maketrans({",": thousand, ".": decimal}))

    def value_from_datadict(self, data, files, name):
        value = super().value_from_datadict(data, files, name)
        if not isinstance(value, str):
            return value
        thousand, decimal = self._seps()
        return value.replace(thousand, "").replace(decimal, ".")


class LocalizedDateInputWidget(UnfoldAdminDateWidget):
    """
    Date input widget with localized placeholder
    and automatic date formatting.
    """

    def __init__(self, attrs=None, format=None):
        attrs = {
            **(attrs or {}),
            "data-date-input-mask": "true",
        }

        super().__init__(
            attrs=attrs,
            format=format,
        )

    class Media(UnfoldAdminDateWidget.Media):
        js = [
            *UnfoldAdminDateWidget.Media.js,
            "core/js/localized_date_input.js",
        ]
