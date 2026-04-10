from datetime import timedelta

from django.db.models import FloatField, Prefetch
from django.db.models.expressions import RawSQL
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.response import Response

from rides.models import Ride, RideEvent
from rides.serializers import RideSerializer
from rides.permissions import IsAdminRole
from rides.pagination import StandardPagination


class RideViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RideSerializer
    permission_classes = [IsAdminRole]
    pagination_class = StandardPagination

    def get_queryset(self):
        last_24h = timezone.now() - timedelta(hours=24)
        todays_events = Prefetch(
            "ride_events",
            queryset=RideEvent.objects.filter(created_at__gte=last_24h),
            to_attr="todays_ride_events",
        )
        qs = (
            Ride.objects
            .select_related("id_rider", "id_driver")
            .prefetch_related(todays_events)
        )
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        rider_email = self.request.query_params.get("rider_email")
        if rider_email:
            qs = qs.filter(id_rider__email=rider_email)

        sort_by = self.request.query_params.get("sort_by")
        if sort_by == "pickup_time":
            qs = qs.order_by("pickup_time")
        elif sort_by == "distance":
            lat = float(self.request.query_params.get("latitude"))
            lng = float(self.request.query_params.get("longitude"))
            qs = self._annotate_haversine(qs, lat, lng).order_by("distance")
        return qs

    def list(self, request, *args, **kwargs):
        if request.query_params.get("sort_by") == "distance":
            lat = request.query_params.get("latitude")
            lng = request.query_params.get("longitude")
            if not lat or not lng:
                return Response(
                    {"error": "latitude and longitude are required for distance sorting"},
                    status=400,
                )
            try:
                float(lat)
                float(lng)
            except (ValueError, TypeError):
                return Response(
                    {"error": "latitude and longitude must be valid numbers"},
                    status=400,
                )
        return super().list(request, *args, **kwargs)

    @staticmethod
    def _annotate_haversine(qs, lat, lng):
        """
        Haversine at DB level so ORDER BY + LIMIT (pagination) work on full
        dataset. Loading all rides into Python would break pagination and
        require O(n) memory — unacceptable for large tables per spec.
        """
        haversine = """
            6371 * 2 * ASIN(SQRT(
                POWER(SIN(RADIANS(pickup_latitude - %s) / 2), 2) +
                COS(RADIANS(%s)) * COS(RADIANS(pickup_latitude)) *
                POWER(SIN(RADIANS(pickup_longitude - %s) / 2), 2)
            ))
        """
        return qs.annotate(
            distance=RawSQL(haversine, (lat, lat, lng), output_field=FloatField())
        )
