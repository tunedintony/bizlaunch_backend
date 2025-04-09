from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AdCopy,
    CopyJob,
    FunnelTemplate,
    PageImage,
    PageTemplate,
    SystemFunnelAssociation,
    SystemTemplate,
)


class TemporaryImageUploadForm(forms.ModelForm):
    """
    Custom form for temporary image upload in the admin.
    """

    temp_image_file = forms.ImageField(
        required=False,
        help_text="Upload an image file to encode its content to base64. The image will not be saved.",
    )

    class Meta:
        model = PageImage
        fields = "__all__"

    def clean_temp_image_file(self):
        """
        Process the uploaded image file and store it temporarily.
        """
        temp_image = self.cleaned_data.get("temp_image_file")
        if temp_image:
            # Attach the temporary image file to the instance for processing
            self.instance._temp_image_file = temp_image
        return temp_image


@admin.register(SystemTemplate)
class SystemTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "image")
    search_fields = ("name", "description")


@admin.register(FunnelTemplate)
class FunnelTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


@admin.register(SystemFunnelAssociation)
class SystemFunnelAssociationAdmin(admin.ModelAdmin):
    list_display = ("system", "funnel", "order_in_system")
    list_filter = ("system", "funnel")
    ordering = ("order_in_system",)


@admin.register(PageTemplate)
class PageTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "funnel", "layout", "order_in_funnel")
    list_filter = ("funnel", "layout")
    search_fields = ("name", "description")
    ordering = ("order_in_funnel",)


@admin.register(PageImage)
class PageImageAdmin(admin.ModelAdmin):
    form = TemporaryImageUploadForm
    list_display = ("page", "order", "base64_preview")
    list_filter = ("page",)
    ordering = ("order",)
    readonly_fields = ("image_content", "base64_preview")

    def base64_preview(self, obj):
        """
        Display a preview of the base64-encoded string in the admin.
        """
        if obj.image_content:
            # Display the first 100 characters for preview
            return format_html(
                "<pre>{}</pre>",
                obj.image_content[:100] + "..." if len(obj.image_content) > 100 else obj.image_content
            )
        return "No base64 content available"

    base64_preview.short_description = "Base64 Content Preview"

@admin.register(CopyJob)
class CopyJobAdmin(admin.ModelAdmin):
    list_display = ("system", "status", "user")
    list_filter = ("status", "system", "user")
    search_fields = ("system__name", "user__username")
    readonly_fields = ("client_file",)


@admin.register(AdCopy)
class AdCopyAdmin(admin.ModelAdmin):
    list_display = ("copy_job", "funnel")
    list_filter = ("copy_job", "funnel")
    search_fields = ("copy_job__uuid", "funnel__name")
    readonly_fields = ("copy_text", "copy_json")
