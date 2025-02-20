# from celery import shared_task
# from django.utils import timezone

# from bizlaunch.users.choices import InviteStatus
# from bizlaunch.users.models import TeamInvite


# @shared_task(name="expire_team_invite")
# def expire_team_invite_task(invite_uuid):
#     try:
#         invite = TeamInvite.objects.get(uuid=invite_uuid, status=InviteStatus.PENDING)
#         if timezone.now() >= invite.expires_at:
#             invite.status = InviteStatus.EXPIRED
#             invite.save(update_fields=["status", "updated_at"])
#             return f"Successfully expired invite for {invite.email}"
#         return f"Invite for {invite.email} has not expired yet"
#     except TeamInvite.DoesNotExist:
#         return f"No pending invite found with UUID: {invite_uuid}"
#     except Exception as e:
#         return f"Error expiring invite: {str(e)}"
