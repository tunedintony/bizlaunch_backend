from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from bizlaunch.users.models import (
    InviteStatus,
    Profile,
    Team,
    TeamInvite,
    TeamMember,
    UserRole,
)
from bizlaunch.users.permissions import IsProfileOwner
from bizlaunch.users.serializers import (
    ChangePasswordSerializer,
    MemberRegisterSerializer,
    ProfileSerializer,
    TeamInviteSerializer,
    TeamMemberSerializer,
    TeamSerializer,
)


def email_confirm_redirect(request, key):
    return HttpResponseRedirect(f"{settings.EMAIL_CONFIRM_REDIRECT_BASE_URL}{key}/")


def password_reset_confirm_redirect(request, uidb64, token):
    return HttpResponseRedirect(
        f"{settings.PASSWORD_RESET_CONFIRM_REDIRECT_BASE_URL}{uidb64}/{token}/",
    )


class ProfileView(APIView):
    permission_classes = [IsAuthenticated, IsProfileOwner]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Retrieve the authenticated user's profile",
        responses={
            200: ProfileSerializer,
            404: openapi.Response(description="Profile not found"),
        },
    )
    def get(self, request, *args, **kwargs):
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Partially update the authenticated user's profile",
        manual_parameters=[
            openapi.Parameter(
                "bio",
                openapi.IN_FORM,
                description="User bio",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "profile_picture",
                openapi.IN_FORM,
                description="Profile picture file upload",
                type=openapi.TYPE_FILE,
            ),
        ],
        consumes=["multipart/form-data"],  # Specify the content type for file uploads
        responses={
            200: ProfileSerializer,
            400: openapi.Response(description="Invalid input"),
            404: openapi.Response(description="Profile not found"),
        },
    )
    def patch(self, request, *args, **kwargs):
        profile = get_object_or_404(Profile, user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        return Response(
            {"detail": "Delete not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class TeamViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def get_queryset(self):
        return Team.objects.filter(owner=self.request.user)

    @swagger_auto_schema(
        operation_description="Retrieve the authenticated user's team. If no team exists, one will be created automatically. The response includes team details, pending invites, and accepted members.",
        responses={status.HTTP_200_OK: TeamSerializer},
    )
    def get(self, request):
        # Check if the user owns a team
        team = self.get_queryset().first()
        if not team:
            # Automatically create a team for the user if they are an admin
            if request.user.role == UserRole.ADMIN:
                team = Team.objects.create(
                    owner=request.user, name=f"{request.user.name}'s Team"
                )
            else:
                return Response(
                    {"detail": "You are not authorized to own a team."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Serialize the team, including members and invites
        serializer = TeamSerializer(team)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update the authenticated user's team",
        request_body=TeamSerializer,
        responses={status.HTTP_200_OK: TeamSerializer},
    )
    def partial_update(self, request, uuid=None):
        team = self.get_queryset().first()
        if not team:
            return Response(
                {"detail": "You do not own a team."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = TeamSerializer(team, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="members")
    def list_members(self, request):
        team = self.get_queryset().first()
        if not team:
            return Response(
                {"detail": "You do not own a team."}, status=status.HTTP_404_NOT_FOUND
            )

        # Segregate members by invite status
        pending_invites = TeamInvite.objects.filter(team=team, status="PENDING")
        accepted_members = TeamMember.objects.filter(team=team)

        data = {
            "pending_invites": TeamInviteSerializer(pending_invites, many=True).data,
            "accepted_members": TeamMemberSerializer(accepted_members, many=True).data,
        }
        return Response(data)

    @swagger_auto_schema(
        operation_description="Invite a new team member",
        request_body=TeamInviteSerializer,
        responses={status.HTTP_201_CREATED: TeamInviteSerializer},
    )
    @action(detail=False, methods=["post"], url_path="invite-member")
    def invite_member(self, request):
        if request.user.role != UserRole.ADMIN:
            return Response(
                {"detail": "Only team admins can invite members."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = TeamInviteSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        invite = serializer.save()
        return Response(
            TeamInviteSerializer(invite).data, status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_description="Delete a team member or team invite by UUID",
        responses={status.HTTP_204_NO_CONTENT: "No Content"},
    )
    @action(detail=False, methods=["delete"], url_path="member/(?P<uuid>[^/.]+)")
    def delete_member_or_invite(self, request, uuid=None):
        if request.user.role != UserRole.ADMIN:
            return Response(
                {"detail": "Only team admins can remove members or invites."},
                status=status.HTTP_403_FORBIDDEN,
            )

        team = self.get_queryset().first()
        if not team:
            return Response(
                {"detail": "You do not own a team."}, status=status.HTTP_404_NOT_FOUND
            )

        # Attempt to delete a team member
        try:
            member = TeamMember.objects.get(uuid=uuid, team=team)
            member.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TeamMember.DoesNotExist:
            pass  # If not found, proceed to check for invites

        # Attempt to delete a pending or expired team invite
        try:
            invite = TeamInvite.objects.get(uuid=uuid, team=team)
            if invite.status in [InviteStatus.PENDING, InviteStatus.EXPIRED]:
                invite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {"detail": "Only pending or expired invites can be deleted."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except TeamInvite.DoesNotExist:
            return Response(
                {"detail": "Team member or invite not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class MemberRegisterView(APIView):
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Register a new team member using an invite token",
        request_body=MemberRegisterSerializer,
        responses={
            201: openapi.Response(
                description="Account created successfully",
                examples={
                    "application/json": {
                        "detail": "Account created successfully",
                        "email": "user@example.com",
                        "uuid": "123e4567-e89b-12d3-a456-426614174000",
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    }
                },
            ),
            400: openapi.Response(description="Invalid input"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = MemberRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response(
            {
                "detail": "Account created successfully",
                "email": user.email,
                "uuid": str(user.uuid),
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
            status=status.HTTP_201_CREATED,
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Change the password of the authenticated user",
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password updated successfully",
                examples={
                    "application/json": {"detail": "Password updated successfully."}
                },
            ),
            400: openapi.Response(description="Invalid input"),
            401: openapi.Response(
                description="Authentication credentials were not provided."
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password updated successfully."}, status=status.HTTP_200_OK
        )
