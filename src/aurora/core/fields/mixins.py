# from django.utils.translation import get_language
#
# from aurora.core.utils import oneline
# from aurora.state import state
#
#
# class TailWindMixin:
#     def __init__(self, attrs=None, **kwargs):
#         attrs = {
#             "class": "shadow appearance-none border rounded w-full py-2 px-3 my-1 cursor-pointer"
#             "text-gray-700 leading-tight focus:outline-none focus:shadow-outline ",
#             **(attrs or {}),
#         }
#         super().__init__(attrs=attrs, **kwargs)
#
#
# class SmartWidgetMixin:
#     def get_context(self, name, value, attrs):
#         ret = super().get_context(name, value, attrs)
#         ret["LANGUAGE_CODE"] = get_language()
#         ret["request"] = state.request
#         ret["user"] = state.request.user
#         return ret


class SmartFieldMixin:
    NONE = None
    PRIMARY = 1
    BLOB = 2
    storage = PRIMARY

    def __init__(self, *args, **kwargs) -> None:
        self.flex_field = kwargs.pop("flex_field")
        # self.smart_attrs = kwargs.pop("smart_attrs", kwargs.pop("smart", {}))
        # self.field_attrs = kwargs.pop("field_attrs", {})
        # self.data_attrs = kwargs.pop("data", {})
        self.widget_kwargs = kwargs.pop("widget_kwargs", {})
        # self.smart_events = kwargs.pop("smart_events", {})
        # self.datasource = kwargs.pop("datasource", None)
        super().__init__(*args, **kwargs)

    def is_stored(self):
        return self.storage in [self.PRIMARY, self.BLOB]

    def get_advanced(self, target, dafault=None):
        ret = self.flex_field.advanced
        for part in target.split("."):
            ret = ret.get(part)
        return ret

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs.update({k: v for k, v in self.widget_kwargs.items() if v is not None})
        #
        # for k, v in self.smart_attrs.items():
        #     if k.startswith("data-") or k.startswith("on") and v:
        #         attrs[k] = v
        #
        # for k, v in self.widget_kwargs.items():
        #     if k.startswith("data-") or k.startswith("on") and v:
        #         attrs[k] = v
        #
        # for k, v in self.data_attrs.items():
        #     attrs[f"data-{k}"] = v
        #
        # if self.flex_field.validator:
        #     attrs["data-smart-validator"] = self.flex_field.validator.name
        #
        # if not self.flex_field.required:
        #     attrs.pop("required", "")
        # attrs["flex_field"] = self.flex_field
        # attrs["data-flex-name"] = self.flex_field.name
        # for attr in [
        #     "onblur",
        #     "onchange",
        #     "onkeyup",
        # ]:
        #     if attr in self.smart_events:
        #         if self.smart_events[attr]:
        #             attrs[attr] = oneline(self.smart_events[attr])
        #
        # for attr in [
        #     "onload",
        # ]:
        #     if attr in self.smart_events:
        #         if self.smart_events[attr]:
        #             attrs[f"data-{attr}"] = oneline(self.smart_events[attr])
        #
        # if validation := self.smart_events.get("validation", None):
        #     attrs["data-validation"] = oneline(validation)
        # widget.smart_attrs = self.smart_attrs
        widget.field = self
        widget.flex_field = self.flex_field
        return attrs
