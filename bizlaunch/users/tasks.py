from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from bizlaunch.users.models import InviteStatus, Team, TeamInvite, User


@shared_task(name="expire_team_invite")
def expire_team_invite_task(invite_uuid):
    try:
        invite = TeamInvite.objects.get(uuid=invite_uuid, status=InviteStatus.PENDING)
        if timezone.now() >= invite.expires_at:
            invite.status = InviteStatus.EXPIRED
            invite.save(update_fields=["status", "updated_at"])
            return f"Successfully expired invite for {invite.email}"
        return f"Invite for {invite.email} has not expired yet"
    except TeamInvite.DoesNotExist:
        return f"No pending invite found with UUID: {invite_uuid}"
    except Exception as e:
        return f"Error expiring invite: {str(e)}"


@shared_task(name="send_invite_email")
def send_invite_email(invite_uuid):
    invite = TeamInvite.objects.get(uuid=invite_uuid)
    subject = "You've been invited to join a team"
    message = f"""Join our team by registering here:
{settings.FRONTEND_BASE_URL}/register/{invite.token}/"""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [invite.email])


@shared_task(name="send_joined_email")
def send_joined_email(user_uuid, team_uuid):
    user = User.objects.get(uuid=user_uuid)
    team = Team.objects.get(uuid=team_uuid)
    subject = "New team member joined"
    message = f"{user.email} has joined your team {team.name}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [team.owner.email])
