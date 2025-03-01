import os

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from bizlaunch.core.models import CoreModel

User = get_user_model()


class SystemTemplate(CoreModel):
    """
    High-level grouping of funnels, e.g. “Done-With-You,”
    “VSL Call Engine,” “Funnel Automation,” etc.
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(null=True, blank=True)
    # Many-to-many link to FunnelTemplate using a through model
    funnels = models.ManyToManyField(
        "FunnelTemplate",
        through="SystemFunnelAssociation",
        related_name="systems",
    )

    def __str__(self):
        return self.name


class FunnelTemplate(CoreModel):
    """
    A funnel template is a reusable funnel flow (e.g., VSL Call Engine, Low Ticket Funnel).
    It can be linked to multiple SystemTemplates.
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name}"


class SystemFunnelAssociation(CoreModel):
    """
    Intermediary model to associate SystemTemplate and FunnelTemplate.
    This allows a funnel to belong to multiple systems with additional data (like order).
    """

    system = models.ForeignKey(SystemTemplate, on_delete=models.CASCADE)
    funnel = models.ForeignKey(FunnelTemplate, on_delete=models.CASCADE)
    order_in_system = models.PositiveIntegerField(
        default=1,
        help_text="Order in which this funnel appears under the system.",
    )

    class Meta:
        unique_together = ("system", "funnel")
        ordering = ["order_in_system"]

    def __str__(self):
        return f"{self.system.name} - {self.funnel.name}"


class PageTemplate(CoreModel):
    """
    Represents a single page in a funnel (Opt-in, Sales, Upsell, etc.).
    Stores:
    - Layout info (optional)
    - A JSON field that defines all the textual components/sections
      for this page (e.g., headlines, subheadings, CTA placeholders).
    """

    funnel = models.ForeignKey(
        FunnelTemplate,
        on_delete=models.CASCADE,
        related_name="pages",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    layout = models.CharField(
        max_length=50,
        help_text="e.g., 'optin', 'sales', 'thankyou'",
    )
    order_in_funnel = models.PositiveIntegerField(
        default=1,
        help_text="Order in which this page appears within the funnel.",
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
        PageTemplate,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image_content = models.TextField(null=True, blank=True)
    components = models.JSONField(
        default=dict,
        help_text="JSON structure defining components like headlines, "
        "subheadings, CTAs, forms, etc.",
    )
    order = models.PositiveIntegerField(
        default=1,
        help_text="Order in which this image appears in the page.",
    )

    def __str__(self):
        return f"Image for {self.page.name}"


class Status(models.TextChoices):
    PENDING = "pending", _("Pending")
    PROCESSING = "processing", _("Processing")
    PARTIALLY_COMPLETED = "partially_completed", _("Partially Completed")
    COMPLETED = "completed", _("Completed")
    FAILED = "failed", _("Failed")


def copy_job_file_upload_path(instance, filename):
    """
    Generate the file upload path for CopyJob files.
    Path format: user_uuid/copy_jobs/job_uuid/file_name.csv
    """
    return os.path.join(f"{instance.user.uuid}/copy_jobs/{instance.pk}/{filename}")


class CopyJob(CoreModel):
    """
    Stores client data and tracks the status of the ad copy generation process.
    """

    system = models.ForeignKey(
        SystemTemplate,
        on_delete=models.CASCADE,
        related_name="copy_jobs",
    )
    client_data = models.JSONField(help_text="Client input data for copy generation")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    client_file = models.FileField(
        upload_to=copy_job_file_upload_path,
        null=True,
        blank=True,
        help_text="Any supporting file from client",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="copy_jobs",
        help_text="User initiating the job",
    )

    def __str__(self):
        return f"Copy Job {self.pk} - {self.status}"


class AdCopy(CoreModel):
    """
    Stores the generated ad copy results.
    """

    copy_job = models.ForeignKey(
        CopyJob,
        on_delete=models.CASCADE,
        related_name="generated_copies",
    )
    funnel = models.ForeignKey(FunnelTemplate, on_delete=models.CASCADE, null=True)
    page = models.ForeignKey(PageTemplate, on_delete=models.CASCADE)
    copy_text = models.TextField(help_text="Generated ad copy text")
    copy_json = models.JSONField(
        default=dict,
        help_text="Generated ad copy in JSON format",
    )

    def __str__(self):
        return f"Ad Copy for Job {self.job.pk}"
