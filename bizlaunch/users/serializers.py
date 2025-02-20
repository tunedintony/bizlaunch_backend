from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from dj_rest_auth.registration.serializers import (
    RegisterSerializer,
    SocialLoginSerializer,
)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from bizlaunch.clients.models import Client, ClientUserProfile
from bizlaunch.core.helpers import get_user_profile

# from grid.clients.models import Client, ClientUserProfile
from bizlaunch.recruiters.serializers import AgencySerializer
from bizlaunch.site_settings.serializers import CountrySerializer, CurrencySerializer
from bizlaunch.users.choices import InviteStatus, InviteType, Roles
from bizlaunch.users.models import TeamInvite, TeamMember, User
from bizlaunch.users.signup_router import Router


# from dj_rest_auth.serializers import PasswordResetSerializer as DefaultPasswordResetSerializer


class ClientMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["uuid", "company_name"]
        read_only_fields = ["uuid", "company_name"]


class UserDetailSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    profile_photo = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    user_type_guide = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    profile_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "uuid",
            "role",
            "email",
            "is_active",
            "is_staff",
            "is_client",
            "is_admin",
            "is_recruiter",
            "first_name",
            "last_name",
            "profile_photo",
            "user_type",
            "user_type_guide",
            "country",
            "currency",
            "company",
            "profile_id",
        ]

    def get_country(self, obj):
        if obj.is_recruiter and hasattr(obj.recruiter, "address"):
            return CountrySerializer(obj.recruiter.address.country).data
        elif obj.is_client and hasattr(obj, "clientuserprofile") and obj.clientuserprofile.client and obj.clientuserprofile.client.country:
            return CountrySerializer(obj.clientuserprofile.client.country).data
        return None

    def get_currency(self, obj):
        if obj.is_recruiter and hasattr(obj.recruiter, "address"):
            return CurrencySerializer(obj.recruiter.address.country.currency).data
        elif obj.is_client and hasattr(obj, "clientuserprofile") and obj.clientuserprofile.client and obj.clientuserprofile.client.country:
            return CurrencySerializer(obj.clientuserprofile.client.country.currency).data
        return None

    def get_company(self, obj):
        if obj.is_recruiter and hasattr(obj, "recruiter") and obj.recruiter.agency:
            return AgencySerializer(obj.recruiter.agency).data
        elif obj.is_client and hasattr(obj, "clientuserprofile") and obj.clientuserprofile.client:
            return ClientMiniSerializer(obj.clientuserprofile.client).data
        return None

    def get_user_type(self, obj):
        profile = get_user_profile(obj)

        if profile:
            if obj.is_recruiter:
                if obj.recruiter.superuser:
                    return "SUPERUSER"
                else:
                    return "MEMBER"
            else:
                return profile.get_user_type_display()

        return None

    def get_user_type_guide(self, obj):
        if obj.is_admin:
            return {
                "admin_user_types": {"1": "SUPERADMIN", "2": "ADMIN", "3": "EDITOR", "4": "VIEWER", "5": "ACCOUNTANT"}
            }

        if obj.is_client:
            return {"client_user_types": {"0": "SUPERUSER", "1": "ADMIN", "2": "MEMBER"}}

        if obj.is_recruiter:
            return {"recruiter_user_types": {"superuser - TRUE": "SUPERUSER", "superuser - FALSE": "MEMBER"}}

        return None

    def get_profile_photo(self, obj):
        profile = get_user_profile(obj)
        if profile and profile.profile_photo:
            # Convert to a URL if it's a FileField or ImageField
            if hasattr(profile.profile_photo, 'url'):
                return profile.profile_photo.url  # Return the URL of the profile photo
            else:
                # Handle cases where the file might not have a URL
                return default_storage.url(profile.profile_photo.name)
        return None

    def get_first_name(self, obj):
        profile = get_user_profile(obj)
        if profile and profile.first_name:
            return profile.first_name
        return None

    def get_last_name(self, obj):
        profile = get_user_profile(obj)
        if profile and profile.last_name:
            return profile.last_name
        return None

    def get_profile_id(self, obj):
        profile = get_user_profile(obj)
        if profile:
            return profile.uuid
        return None


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, data):
        if data["new_password1"] != data["new_password2"]:
            raise serializers.ValidationError({"new_password2": "Passwords do not match."})
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
        return user



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user
        try:
            EmailAddress.objects.get(user=user, verified=True)
        except EmailAddress.DoesNotExist:
            raise AuthenticationFailed("Email not verified")

        # Get route, message, and profile (custom logic)
        route, message, profile = Router.get_route(user)

        # Default values
        first_name = None
        last_name = None
        country = None

        # Determine user's role and fetch first_name, last_name, and country
        if user.is_client and hasattr(user, "clientuserprofile"):
            first_name = user.clientuserprofile.first_name
            last_name = user.clientuserprofile.last_name
            if hasattr(user.clientuserprofile, "client") and hasattr(user.clientuserprofile.client, "country"):
                country = user.clientuserprofile.client.country.two_letter_code

        elif user.is_recruiter and hasattr(user, "recruiter"):
            first_name = user.recruiter.first_name
            last_name = user.recruiter.last_name
            if hasattr(user.recruiter, "address") and hasattr(user.recruiter.address, "country"):
                country = user.recruiter.address.country.two_letter_code

        elif user.is_admin:
            first_name = user.adminuserprofile.first_name if hasattr(user, "adminuserprofile") else None
            last_name = user.adminuserprofile.last_name if hasattr(user, "adminuserprofile") else None
            country = "US"  # Default to "US" for admin

        # Add additional data
        data["route"] = route
        data["message"] = message
        data["role"] = user.role
        data["user_uuid"] = user.uuid
        data["email"] = user.email
        data["is_member"] = user.is_team_member
        data["first_name"] = first_name
        data["last_name"] = last_name
        data["country"] = country

        return data


class CustomUserRegisterSerializer(RegisterSerializer):
    username = None
    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(choices=Roles.choices, default=Roles.CLIENT)

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(_("A user is already registered with this e-mail address."))
        return email

    def validate(self, data):
        validated_data = super().validate(data)
        return validated_data

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data.update(
            {
                "role": self.validated_data.get("role", Roles.CLIENT),
            }
        )
        return data

    def save(self, request):
        user = super().save(request)
        role = self.validated_data.get("role", Roles.CLIENT)
        user.role = role
        user.save(update_fields=["role"])
        return user


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "uuid",
            "email",
            "role",
            "created_at",
            "updated_at",
            "last_login",
        )
        read_only_fields = ("email", "created_at", "updated_at", "last_login")


class RouteResponseSerializer(serializers.Serializer):
    route = serializers.CharField()
    message = serializers.CharField()
    role = serializers.CharField()
    uuid = serializers.UUIDField(allow_null=True, required=False)
    is_member = serializers.BooleanField()


class TeamInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamInvite
        fields = ["email", "uuid", "created_at", "updated_at", "inviter", "invite_type", "invitee_sub_type"]
        read_only_fields = ["uuid", "created_at", "updated_at", "inviter", "invite_type"]
        extra_kwargs = {"email": {"help_text": "Email address of the person to invite"}}

    def validate_invitee_sub_type(self, value):
        """
        Validate invitee_sub_type based on user role. Admin users do not have any subrole.
        """
        user = self.context["request"].user
        valid_types = []

        if user.is_admin:
            raise serializers.ValidationError("Admin users cannot invite members")
        elif user.is_client:
            valid_types = list(TeamInvite.InviteeSubType)
        elif user.is_recruiter:
            valid_types = [TeamInvite.InviteeSubType.MEMBER, TeamInvite.InviteeSubType.SUPERUSER]
        else:
            raise serializers.ValidationError("Invalid user role")

        if value not in valid_types:
            role = "client" if user.is_client else "recruiter"
            valid_types_str = ", ".join(str(t) for t in valid_types)
            raise serializers.ValidationError(
                f"Invalid user type for {role} team invite. Must be one of: {valid_types_str}"
            )

        return value

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if EmailAddress.objects.is_verified(email):
            raise serializers.ValidationError(
                _("A user is already registered with this e-mail address."),
            )
        return email

    def validate(self, data):
        user = self.context["request"].user

        # Determine invite type based on inviter's role
        if user.is_client:
            data["invite_type"] = InviteType.CLIENT

        elif user.is_recruiter:
            data["invite_type"] = InviteType.RECRUITER

        else:
            raise serializers.ValidationError("Invalid user role for sending invites")

        return data

    def create(self, validated_data):
        inviter = self.context["request"].user
        return TeamInvite.objects.create(**validated_data, inviter=inviter)


class MemberRegisterSerializer(serializers.Serializer):
    token = serializers.CharField()
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate_token(self, value):
        if not TeamInvite.objects.filter(token=value, status=InviteStatus.PENDING).exists():
            raise serializers.ValidationError("Invalid or expired invitation token")
        return value

    def validate_password1(self, password1):
        return get_adapter().clean_password(password1)

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError(_("The two password fields didn't match."))
        return data

    def _create_team_member(self, user, inviter):
        """Helper method to create team member based on inviter type"""
        if inviter.is_client:
            TeamMember.objects.create(
                user=user,
                client=inviter.clientuserprofile.client,
            )
        elif inviter.is_recruiter:
            TeamMember.objects.create(
                user=user,
                agency=inviter.recruiter.agency,
            )

    def create(self, validated_data):
        token = validated_data.pop("token")
        password1 = validated_data.pop("password1")
        invite = TeamInvite.objects.get(token=token)

        with transaction.atomic():
            try:
                # Create user based on invite type
                user = User.objects.create(
                    email=invite.email,
                    role=Roles.CLIENT if invite.invite_type == InviteType.CLIENT else Roles.RECRUITER,
                    is_active=True,
                    is_staff=False,
                    is_superuser=False,
                )
                user.password = make_password(password1)
                user.save()

                # Create and verify email address using allauth
                EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)

                # Update invite status
                invite.status = InviteStatus.ACCEPTED
                invite.save()

                # Create team member
                self._create_team_member(user, invite.inviter)

                return user
            except Exception as e:
                import traceback

                traceback.print_exc()
                raise e


class TeamInviteItemSerializer(serializers.ModelSerializer):
    inviter_name = serializers.SerializerMethodField()
    invitee_user_role = serializers.SerializerMethodField()
    invitee_subrole = serializers.SerializerMethodField()

    class Meta:
        model = TeamInvite
        fields = [
            "uuid",
            "email",
            "status",
            "invitee_user_role",
            "inviter_name",
            "invitee_subrole",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_inviter_name(self, obj):
        if obj.inviter.is_client:
            return f"{obj.inviter.clientuserprofile.first_name} {obj.inviter.clientuserprofile.last_name}"
        return f"{obj.inviter.recruiter.first_name} {obj.inviter.recruiter.last_name}"

    def get_invitee_subrole(self, obj):
        return obj.invitee_sub_type

    def get_invitee_user_role(self, obj):
        return obj.invite_type


class TeamInviteListResponseSerializer(serializers.Serializer):
    accepted = TeamInviteItemSerializer(many=True, read_only=True)
    invited = TeamInviteItemSerializer(many=True, read_only=True)


class TeamMemberSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.company_name", read_only=True)
    agency_name = serializers.CharField(source="agency.agency_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    profile_id = serializers.SerializerMethodField()
    user_is_active = serializers.SerializerMethodField()

    class Meta:
        model = TeamMember
        fields = [
            "uuid",
            "client",
            "client_name",  # Read-only client name
            "agency",
            "agency_name",  # Read-only agency name
            "profile_id",
            "user",
            "user_is_active",  # New field for user active status
            "user_email",  # Read-only user email
            "first_name",
            "last_name",
            "photo",
            "user_type",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
        ]

    def get_user_is_active(self, obj):
        """
        Get the active status of the user.
        """
        return obj.user.is_active

    def get_profile_id(self, obj):
        if obj.client:
            return obj.user.clientuserprofile.uuid if hasattr(obj.user, "clientuserprofile") else None
        elif obj.agency:
            return obj.user.recruiter.uuid if hasattr(obj.user, "recruiter") else None

    def get_first_name(self, obj):
        """
        Get the first name based on the team type (client or agency).
        """
        if obj.client:
            return obj.user.clientuserprofile.first_name if hasattr(obj.user, "clientuserprofile") else None
        elif obj.agency:
            return obj.user.recruiter.first_name if hasattr(obj.user, "recruiter") else None
        return None

    def get_photo(self, obj):
        """
        Get the photo URL based on the team type (client or agency).
        """
        if obj.client and hasattr(obj.user, "clientuserprofile"):
            profile_photo = obj.user.clientuserprofile.profile_photo
            return profile_photo.url if profile_photo and profile_photo.name else None
        elif obj.agency and hasattr(obj.user, "recruiter"):
            profile_photo = obj.user.recruiter.profile_photo
            return profile_photo.url if profile_photo and profile_photo.name else None
        return None

    def get_last_name(self, obj):
        """
        Get the last name based on the team type (client or agency).
        """
        if obj.client:
            return obj.user.clientuserprofile.last_name if hasattr(obj.user, "clientuserprofile") else None
        elif obj.agency:
            return obj.user.recruiter.last_name if hasattr(obj.user, "recruiter") else None
        return None

    def get_user_type(self, obj):
        """
        Determine the user type based on whether the user is a client or a recruiter.
        """
        if obj.client and hasattr(obj.user, "clientuserprofile"):
            user_type = obj.user.clientuserprofile.user_type
            return dict(ClientUserProfile.UserType.choices).get(user_type, "Unknown")
        elif obj.agency and hasattr(obj.user, "recruiter"):
            return "SUPERUSER" if obj.user.recruiter.superuser else "MEMBER"
        return "Unknown"

    def validate(self, attrs):
        # Ensure only one of `client` or `agency` is provided
        if not (attrs.get("client") or attrs.get("agency")):
            raise serializers.ValidationError("Either 'client' or 'agency' must be provided.")
        if attrs.get("client") and attrs.get("agency"):
            raise serializers.ValidationError("You cannot provide both 'client' and 'agency'.")

        return attrs


class EmailVerificationResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    refresh = serializers.CharField()
    access = serializers.CharField()
    route = serializers.CharField()
    message = serializers.CharField()
    role = serializers.CharField()
    user_uuid = serializers.UUIDField()
    email = serializers.EmailField()
    is_member = serializers.BooleanField()
