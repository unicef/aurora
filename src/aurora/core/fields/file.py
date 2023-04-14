from django import forms

from aurora.core.fields.widgets import UploadFileWidget
from aurora.i18n.gettext import gettext as _


class SmartFileField(forms.FileField):
    widget = UploadFileWidget
    default_error_messages = {
        "invalid": _("No file was submitted. Check the encoding type on the form."),
        "missing": _("No file was submitted."),
        "empty": _("The submitted file is empty."),
        # 'max_length': ngettext_lazy(
        #     'Ensure this filename has at most %(max)d character (it has %(length)d).',
        #     'Ensure this filename has at most %(max)d characters (it has %(length)d).',
        #     'max'),
        "contradiction": _("Please either submit a file or check the clear checkbox, not both."),
    }

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        try:
            attrs["accept"] = self.flex_field.advanced["custom"]["accept"]
        except KeyError:
            attrs["accept"] = "*/*"
        except AttributeError:
            pass
        # if isinstance(widget, UploadFileWidget) and 'accept' not in widget.attrs:
        #     attrs.setdefault('accept', 'image/*')
        return attrs
