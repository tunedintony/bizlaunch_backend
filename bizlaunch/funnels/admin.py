from django.contrib import admin

from .models import (
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
    list_display = ("page", "order", "image_content")
    list_filter = ("page",)
    ordering = ("order",)
    readonly_fields = ("image_content",)
