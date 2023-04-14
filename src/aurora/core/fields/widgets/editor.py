from django import forms
from django.conf import settings

from aurora.core.version_media import VersionMedia


class JavascriptEditor(forms.Textarea):
    template_name = "admin/core/widgets/editor.html"

    def __init__(self, *args, **kwargs):
        theme = kwargs.pop("theme", "midnight")
        toolbar = kwargs.pop("toolbar", True)
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "js-editor"
        self.attrs["theme"] = theme
        self.attrs["toolbar"] = toolbar

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        CM_VERSION = "6.65.7"
        return base + VersionMedia(
            css={
                "all": (
                    f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/codemirror.min.css",
                    f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/theme/midnight.min.css",
                    f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/display/fullscreen.min.css",
                    f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/fold/foldgutter.min.css",
                    f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/lint/lint.min.css",
                    # "codemirror/codemirror.css",
                    # "codemirror/fullscreen.css",
                    # "codemirror/midnight.css",
                    "cm.css",
                )
            },
            js=[
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/codemirror.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/display/fullscreen.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/display/placeholder.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/edit/closebrackets.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/edit/trailingspace.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/fold/brace-fold.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/fold/foldcode.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/fold/foldgutter.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/fold/indent-fold.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/fold/indent-fold.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/hint/javascript-hint.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/lint/javascript-lint.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/lint/lint.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/addon/selection/active-line.min.js",
                f"https://cdnjs.cloudflare.com/ajax/libs/codemirror/{CM_VERSION}/mode/javascript/javascript.min.js",
                "https://cdnjs.cloudflare.com/ajax/libs/jshint/2.13.6/jshint.min.js",
                "cm%s.js" % extra,
            ],
        )
