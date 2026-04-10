from rest_framework import viewsets, serializers as drf_serializers

from rides.models import Ride
from rides.permissions import IsAdminRole
from rides.pagination import StandardPagination


class _MinimalRideSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = ["id_ride"]


class RideViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = _MinimalRideSerializer
    permission_classes = [IsAdminRole]
    pagination_class = StandardPagination

    def get_queryset(self):
        return Ride.objects.none()
