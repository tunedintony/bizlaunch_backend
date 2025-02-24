from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from bizlaunch.users.models import (
    InviteStatus,
    Profile,
    Team,
    TeamInvite,
    TeamMember,
    UserRole,
)
from bizlaunch.users.tasks import send_invite_email, send_joined_email

User = get_user_model()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, data):
        if data["new_password1"] != data["new_password2"]:
            raise serializers.ValidationError(
                {"new_password2": "Passwords do not match."},
            )
        return data

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password1"])
        user.save()

        # Blacklist all outstanding tokens for the user
        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            try:
                # Blacklist the token
                BlacklistedToken.objects.get_or_create(token=token)
            except Exception as e:
                raise serializers.ValidationError(
                    {
                        "detail": f"An error occurred while blacklisting the token: {str(e)}"
                    }
                )

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user
        try:
            EmailAddress.objects.get(user=user, verified=True)
        except EmailAddress.DoesNotExist:
            raise AuthenticationFailed("Email not verified")

        return data


# class UserDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = (
#             "uuid",
#             "email",
#             "created_at",
#             "updated_at",
#             "last_login",
#         )
#         read_only_fields = ("email", "created_at", "updated_at", "last_login")


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["uuid", "bio", "profile_picture"]
        read_only_fields = ["user"]


class TeamSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    members = serializers.SerializerMethodField()
    invites = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            "uuid",
            "name",
            "owner",
            "members",
            "invites",
            "created_at",
            "updated_at",
        ]

    def get_members(self, obj):
        # Fetch all accepted members of the team
        accepted_members = TeamMember.objects.filter(team=obj)
        return TeamMemberSerializer(accepted_members, many=True).data

    def get_invites(self, obj):
        # Fetch all pending invites for the team
        pending_invites = TeamInvite.objects.filter(
            team=obj, status=InviteStatus.PENDING
        )
        return TeamInviteSerializer(pending_invites, many=True).data


class TeamMemberSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = TeamMember
        fields = ["uuid", "user", "email", "created_at", "updated_at"]

    def get_email(self, obj):
        return obj.user.email


class TeamInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamInvite
        fields = [
            "uuid",
            "email",
            "team",
            "status",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "uuid",
            "team",
            "status",
            "expires_at",
            "created_at",
            "updated_at",
        ]

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if EmailAddress.objects.is_verified(email):
            raise serializers.ValidationError(
                _("A user is already registered with this e-mail address."),
            )
        return email

    def validate(self, data):
        # Ensure the team exists, create one if it doesn't
        user = self.context["request"].user
        team = getattr(user, "owned_team", None)
        if not team:
            if user.role == UserRole.ADMIN:
                team = Team.objects.create(owner=user, name=f"{user.name}'s Team")
            else:
                raise serializers.ValidationError("You are not authorized to own a team.")
        data["team"] = team
        return data

    def create(self, validated_data):
        inviter = self.context["request"].user
        team = inviter.owned_team

        # Check for existing invite with PENDING or EXPIRED status
        existing_invite = (
            TeamInvite.objects.filter(email=validated_data["email"], team=team)
            .filter(status__in=[InviteStatus.PENDING, InviteStatus.EXPIRED])
            .first()
        )

        if existing_invite:
            # Update the expiration date and resend the invite
            existing_invite.expires_at = timezone.now() + timezone.timedelta(days=7)
            existing_invite.status = (
                InviteStatus.PENDING
            )  # Reset status to PENDING if it was EXPIRED
            existing_invite.save(update_fields=["expires_at", "status", "updated_at"])

            # Resend the invitation email
            send_invite_email.delay(existing_invite.uuid)

            return existing_invite

        # Create the team invite
        invite = TeamInvite.objects.create(
            email=validated_data["email"], inviter=inviter, team=team
        )

        # Send invitation email
        send_invite_email.delay(invite.uuid)

        return invite


class MemberRegisterSerializer(serializers.Serializer):
    token = serializers.CharField()
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate_token(self, value):
        try:
            invite = TeamInvite.objects.get(token=value, status=InviteStatus.PENDING)
            if invite.expires_at < timezone.now():
                raise serializers.ValidationError("This invitation has expired.")
            # Store the invite in the serializer context for later use
            self.context["invite"] = invite
        except TeamInvite.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired invitation token.")
        return value

    def validate_password1(self, password1):
        return get_adapter().clean_password(password1)

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError("The two password fields didn't match.")
        return data

    def create(self, validated_data):
        password = validated_data.pop("password1")

        try:
            with transaction.atomic():
                # Retrieve the invite from the context instead of querying again
                invite = self.context.get("invite")
                if not invite:
                    raise serializers.ValidationError(
                        "Invalid or expired invitation token."
                    )

                # Create the user with role MEMBER
                email_prefix = invite.email.split("@")[
                    0
                ]  # Extract the first part of the email
                user = User.objects.create(
                    email=invite.email,
                    is_active=True,
                    name=email_prefix,  # Use the email prefix as the username
                    role=UserRole.MEMBER,  # Set the role to MEMBER
                )
                user.set_password(password)
                user.save()

                # Create and verify the email address using allauth
                EmailAddress.objects.create(
                    user=user, email=user.email, verified=True, primary=True
                )

                # Add the user to the team and update the team's members
                team_member = TeamMember.objects.create(team=invite.team, user=user)
                invite.team.team_members.add(team_member)

                # Mark the invite as accepted
                invite.status = InviteStatus.ACCEPTED
                invite.save()

                # Send notification email
                send_joined_email.delay(user.uuid, invite.team.uuid)

                return user
        except Exception as e:
            import traceback

            traceback.print_exc()
            raise e


class UserProfileSerializerForDetail(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["bio", "profile_picture"]


class UserTeamSerializerForDetail(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["uuid", "name"]


class UserDetailsSerializer(serializers.ModelSerializer):
    team = serializers.SerializerMethodField()
    profile = UserProfileSerializerForDetail()

    class Meta:
        model = User
        fields = [
            "uuid",
            "name",
            "email",
            "role",
            "team",
            "profile",
            "created_at",
            "updated_at",
            "last_login",
        ]

    def get_team(self, obj):
        # Fetch the user's team (if any)
        team = Team.objects.filter(owner=obj).first()
        if team:
            return UserTeamSerializerForDetail(team).data
        return None
