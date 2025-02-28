from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bizlaunch.funnels.models import SystemTemplate
from bizlaunch.funnels.serializers import SystemTemplateSerializer


class FunnelSystemsAPIView(APIView):
    """
    Returns the UUIDs of all funnel systems.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        systems = SystemTemplate.objects.all()
        serializer = SystemTemplateSerializer(systems, many=True)
        return Response(serializer.data)
