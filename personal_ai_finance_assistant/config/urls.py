from apps.analytics.admin_views import analytics_dashboard
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/analytics/dashboard/", admin.site.admin_view(analytics_dashboard), name="analytics-dashboard"),
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
]
