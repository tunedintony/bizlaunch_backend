from django.db import models

from bizlaunch.core.models import CoreModel


class SystemTemplate(CoreModel):
    """
    High-level grouping of funnels, e.g. “Done-With-You,”
    “VSL Call Engine,” “Funnel Automation,” etc.
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class FunnelTemplate(CoreModel):
    """
    Each system can have multiple funnels. For example, under
    'VSL Call Engine' you might have:
    - High Ticket Funnel
    - Low Ticket Funnel
    """

    system = models.ForeignKey(
        SystemTemplate, on_delete=models.CASCADE, related_name="funnels"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    order_in_system = models.PositiveIntegerField(
        default=1, help_text="Order in which this funnel appears under the system."
    )

    def __str__(self):
        return f"{self.system.name} - {self.name}"


class PageTemplate(CoreModel):
    """
    Represents a single page in a funnel (Opt-in, Sales, Upsell, etc.).
    Stores:
    - Layout info (optional)
    - A JSON field that defines all the textual components/sections
      for this page (e.g., headlines, subheadings, CTA placeholders).
    """

    funnel = models.ForeignKey(
        FunnelTemplate, on_delete=models.CASCADE, related_name="pages"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    layout = models.CharField(
        max_length=50, help_text="e.g., 'optin', 'sales', 'thankyou'"
    )
    order_in_funnel = models.PositiveIntegerField(
        default=1, help_text="Order in which this page appears within the funnel."
    )
    components = models.JSONField(
        default=dict,
        help_text="JSON structure defining components like headlines, "
        "subheadings, CTAs, forms, etc.",
    )

    def __str__(self):
        return f"{self.funnel.name} - {self.name}"


class PageImage(CoreModel):
    """
    Dedicated model to store images associated with a PageTemplate.
    You can reference these images within the PageTemplate.components JSON
    if needed, using an identifier or a direct URL.
    """

    page = models.ForeignKey(
        PageTemplate, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="page_images/")
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Short description for accessibility.",
    )
    reference_key = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Use this key to reference the image in the components JSON.",
    )

    def __str__(self):
        return f"Image for {self.page.name} ({self.reference_key or self.id})"
