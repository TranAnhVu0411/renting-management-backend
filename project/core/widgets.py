from decimal import Decimal, InvalidOperation
from unfold.widgets import UnfoldAdminTextInputWidget, UnfoldAdminDateWidget


class ThousandsInput(UnfoldAdminTextInputWidget):
    def __init__(self, attrs=None):
        super().__init__(
            attrs={"inputmode": "decimal", "data-thousands": "1", **(attrs or {})}
        )

    class Media:
        js = ("core/js/thousands_input.js",)

    def format_value(self, value):
        if value in (None, ""):
            return ""
        try:
            return f"{Decimal(str(value).replace(',', '')):,}"
        except InvalidOperation:
            return str(value)

    def value_from_datadict(self, data, files, name):
        value = super().value_from_datadict(data, files, name)
        return value.replace(",", "") if isinstance(value, str) else value


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
