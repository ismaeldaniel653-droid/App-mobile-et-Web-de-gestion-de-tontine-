from django.contrib import admin
from django.urls import include, path
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.permissions import AllowAny
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


class VueSante(APIView):
	permission_classes = [AllowAny]

	@extend_schema(
		responses=inline_serializer(
			name="ReponseSante",
			fields={"statut": serializers.CharField()},
		)
	)
	def get(self, request):
		return Response({"statut": "ok"})


urlpatterns = [
	path("admin/", admin.site.urls),
	path("api/sante/", VueSante.as_view(), name="sante"),
	path("api/auth/", include("apps.utilisateurs.urls")),
	path("api/", include("apps.tontines.urls")),
	path("api/schema/", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"),
	path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[AllowAny]), name="swagger-ui"),
]
