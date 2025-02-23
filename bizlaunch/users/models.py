import os
import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from bizlaunch.core.models import CoreModel
from bizlaunch.users.managers import CustomUserManager


def get_profile_picture_path(instance, filename):
    """Generate file path for profile pictures: user_uuid/profile/image_name"""
    ext = filename.split(".")[-1]
    filename = f"profile_photo.{ext}"
    return os.path.join(f"{instance.user.uuid}/profile", filename)


class User(AbstractUser, CoreModel):
    username = None
    email = models.EmailField(_("email address"), unique=True)
    # First and last name do not cover name patterns around the globe
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class Profile(CoreModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to=get_profile_picture_path, blank=True, null=True
    )

    def __str__(self):
        return f"Profile of {self.user.email}"


class Team(CoreModel):
    name = models.CharField(max_length=255, unique=True)
    owner = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="owned_team"
    )
    members = models.ManyToManyField(User, through="TeamMember", related_name="teams")

    def __str__(self):
        return self.name


class TeamMember(CoreModel):
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="team_members"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="team_memberships"
    )

    def __str__(self):
        return f"{self.user.email} in {self.team.name}"


class InviteStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    EXPIRED = "EXPIRED", "Expired"


class TeamInvite(CoreModel):
    email = models.EmailField()
    inviter = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name="sent_invites"
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="invites")
    status = models.CharField(
        max_length=10, choices=InviteStatus.choices, default=InviteStatus.PENDING
    )
    token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invite to {self.email} for {self.team.name}"
