from django.contrib import admin

from .models import (
    AdCopy,
    CopyJob,
    FunnelTemplate,
    PageImage,
    PageTemplate,
    SystemFunnelAssociation,
    SystemTemplate,
)


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
    list_display = ("page", "order")
    list_filter = ("page",)
    ordering = ("order",)
    readonly_fields = ("image_content",)


@admin.register(CopyJob)
class CopyJobAdmin(admin.ModelAdmin):
    list_display = ("system", "status", "user")
    list_filter = ("status", "system", "user")
    search_fields = ("system__name", "user__username")
    readonly_fields = ("client_file",)


@admin.register(AdCopy)
class AdCopyAdmin(admin.ModelAdmin):
    list_display = ("copy_job", "funnel", "page")
    list_filter = ("copy_job", "funnel", "page")
    search_fields = ("copy_job__uuid", "funnel__name", "page__name")
    readonly_fields = ("copy_text", "copy_json")
