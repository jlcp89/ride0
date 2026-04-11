from datetime import timedelta

from django.db.models import FloatField, Prefetch
from django.db.models.expressions import RawSQL
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.response import Response

from rides.models import Ride, RideEvent, User
from rides.pagination import StandardPagination
from rides.serializers import RideReadSerializer, RideWriteSerializer, UserSerializer


class RideViewSet(viewsets.ModelViewSet):
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return RideWriteSerializer
        return RideReadSerializer

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
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
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

    def create(self, request, *args, **kwargs):
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        write_serializer.save()
        instance = self._hydrate(write_serializer.instance.pk)
        return Response(
            RideReadSerializer(instance).data, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        write_serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        write_serializer.is_valid(raise_exception=True)
        write_serializer.save()
        hydrated = self._hydrate(write_serializer.instance.pk)
        return Response(RideReadSerializer(hydrated).data)

    def _hydrate(self, pk):
        """Reload a ride through the view queryset so select_related and
        the todays_ride_events Prefetch are populated, keeping write
        responses identical in shape to GET responses."""
        return (
            Ride.objects
            .select_related("id_rider", "id_driver")
            .prefetch_related(
                Prefetch(
                    "ride_events",
                    queryset=RideEvent.objects.filter(
                        created_at__gte=timezone.now() - timedelta(hours=24)
                    ),
                    to_attr="todays_ride_events",
                )
            )
            .get(pk=pk)
        )

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


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list of users for the admin UI's rider/driver pickers.

    Returns all users regardless of role — the frontend shows `role` next to
    each name and `RideWriteSerializer`'s cross-field validator enforces that
    rider != driver. Inherits `JWTAuthentication` + `IsAdminRole` from the
    global DRF defaults, so non-admins get 403 automatically.
    """

    queryset = User.objects.all().order_by("id_user")
    serializer_class = UserSerializer
    pagination_class = StandardPagination
