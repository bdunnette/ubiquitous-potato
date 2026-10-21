from django.urls import include, path
from rest_framework import routers
from rest_framework.reverse import reverse

from . import api_views


class DemoAPIRootView(routers.APIRootView):
    """
    Root entry point for the Demo REST API.
    Provides discoverable hyperlinks to all exposed endpoints.
    """

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.data["info"] = reverse("api_info", request=request)
        return response


class DemoDefaultRouter(routers.DefaultRouter):
    APIRootView = DemoAPIRootView


router = DemoDefaultRouter()
router.register(r"items", api_views.ItemViewSet, basename="item")

urlpatterns = [
    path("info/", api_views.api_info, name="api_info"),
    path("", include(router.urls)),
]
