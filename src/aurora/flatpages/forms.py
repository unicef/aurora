from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib.flatpages.models import FlatPage
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


def get_page_css():
    return (
        Path(settings.PACKAGE_DIR / "flatpages" / "static" / "flatpages" / "flatpages.css").read_text(),
        Path(settings.PACKAGE_DIR / "web" / "static" / "base.css").read_text(),
    )


class FlatPageForm(forms.ModelForm):
    title = forms.CharField()
    content = forms.CharField(widget=forms.Textarea)
    # content = forms.CharField(
    #     widget=AdminTinyMCE(
    #         attrs={"rows": "24", "cols": "100"},
    #         mce_attrs={
    #             "setup": "initTinyMCE",
    #             "useDarkMode": False,
    #             "branding": False,
    #             "deprecation_warnings": True,
    #             "force_p_newlines": False,
    #             "force_br_newlines": True,
    #             "urlconverter_callback": "tinyURLConverter",
    #             "relative_urls": False,
    #             "forced_root_block": "",
    #             "content_style": get_page_css(),
    #             "plugins": [
    #                 "advlist",
    #                 "charmap",
    #                 "code",
    #                 "fullscreen",
    #                 "help",
    #                 "image",
    #                 "insertdatetime",
    #                 "link",
    #                 "lists",
    #             ],
    #             "toolbar": [
    #                 "undo redo code source | fullscreen help"
    #                 "| bold italic underline strikethrough blockformats "
    #                 "| alignleft aligncenter alignright alignjustify | bullist numlist"
    #                 "| forecolor backcolor "
    #                 "| formatselect "
    #                 "| image link charmap insertdatetime | buttonPrimary",
    #             ],
    #             "toolbar_sticky": True,
    #             "toolbar_mode": "sliding",
    #             # toolbar_sticky_offset: isSmallScreen ? 102: 108,
    #             "block_formats": "Paragraph=p; Header 1=h1; Header 2=h2; Header 3=h3; Header 4=h4",
    #             "formats": {
    #                 "h1": {"block": "h1", "attributes": {"class": "text-5xl leading-1"}},
    #                 "h2": {"block": "h2", "attributes": {"class": "text-4xl leading-1"}},
    #                 "h3": {"block": "h3", "attributes": {"class": "text-3xl leading-1"}},
    #                 "h4": {"block": "h4", "attributes": {"class": "text-2xl leading-1"}},
    #             },
    #         },
    #     ),
    #     help_text="",
    #     required=False,
    # )

    url = forms.RegexField(
        label=_("URL"),
        required=False,
        max_length=100,
        regex=r"^[-a-z/\.~]+$",
        help_text=_("Example: “/about/contact/”. Leading and trailing slashes will be added."),
        error_messages={
            "invalid": _(
                "This value must contain only letters, numbers, dots, " "underscores, dashes, slashes or tildes."
            ),
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields["content"].widget.mce_attrs["content_css"] = [static("bob/mailing.css")]
        # self.fields["html"].widget.mce_attrs["document_base_url"] = get_server_url()

    class Media:
        js = ("flatpages/tinymce_init.js",)

    class Meta:
        model = FlatPage
        fields = ("title", "url", "content", "sites")

    def save(self, commit=True):
        return super().save(commit)

    def clean_url(self):
        value = self.cleaned_data.get("url", "")
        if not value:
            value = slugify(self.cleaned_data.get("title", ""))
        if not value.startswith("/"):
            value = "/" + value
        if not value.endswith("/"):
            value = value + "/"
        return value

    def clean(self):
        url = self.cleaned_data.get("url")
        sites = self.cleaned_data.get("sites")

        same_url = FlatPage.objects.filter(url=url)
        if self.instance.pk:
            same_url = same_url.exclude(pk=self.instance.pk)

        if sites and same_url.filter(sites__in=sites).exists():
            for site in sites:
                if same_url.filter(sites=site).exists():
                    raise ValidationError(
                        _("Flatpage with url %(url)s already exists for site %(site)s"),
                        code="duplicate_url",
                        params={"url": url, "site": site},
                    )
        # self.cleaned_data["url"] = url
        return super().clean()
