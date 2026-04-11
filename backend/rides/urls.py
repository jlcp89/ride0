from django.urls import path
from rest_framework.routers import DefaultRouter

from rides.auth_views import LoginView, LogoutView, MeView, RefreshView
from rides.report_views import TripsOverHourReportView
from rides.views import RideViewSet

router = DefaultRouter()
router.register(r"rides", RideViewSet, basename="ride")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path(
        "reports/trips-over-hour/",
        TripsOverHourReportView.as_view(),
        name="reports-trips-over-hour",
    ),
    *router.urls,
]
