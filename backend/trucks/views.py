from __future__ import annotations

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Truck
from .serializers import TruckCreateSerializer, TruckSerializer, TruckUpdateSerializer
from .services.fipe import FipeClient, FipeUpstreamError, FipeValidationError


class TruckListCreateView(generics.ListCreateAPIView):
    queryset = Truck.objects.all().order_by("id")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TruckCreateSerializer
        return TruckSerializer


class TruckUpdateView(generics.UpdateAPIView):
    queryset = Truck.objects.all()
    serializer_class = TruckUpdateSerializer
    http_method_names = ["patch"]


class FipeBrandsView(APIView):
    def get(self, request):
        fipe = FipeClient()
        try:
            items = fipe.list_brands()
        except FipeUpstreamError as e:
            return Response({"error": str(e)}, status=503)
        return Response([{"code": x.code, "name": x.name} for x in items])


class FipeModelsView(APIView):
    def get(self, request):
        brand = (request.query_params.get("brand") or "").strip()
        if not brand:
            return Response({"error": "Parâmetro obrigatório: brand"}, status=400)

        fipe = FipeClient()
        try:
            if brand.isdigit():
                brand_code = brand
            else:
                brand_item = fipe._find_by_name(fipe.list_brands(), brand, "Marca")
                brand_code = brand_item.code
            items = fipe.list_models(brand_code)
        except (FipeUpstreamError, FipeValidationError) as e:
            return Response({"error": str(e)}, status=400 if isinstance(e, FipeValidationError) else 503)

        return Response([{"code": x.code, "name": x.name} for x in items])


class FipeYearsView(APIView):
    def get(self, request):
        brand = (request.query_params.get("brand") or "").strip()
        model = (request.query_params.get("model") or "").strip()
        if not brand or not model:
            return Response({"error": "Parâmetros obrigatórios: brand, model"}, status=400)

        fipe = FipeClient()
        try:
            if brand.isdigit():
                brand_code = brand
            else:
                brand_item = fipe._find_by_name(fipe.list_brands(), brand, "Marca")
                brand_code = brand_item.code

            if model.isdigit():
                model_code = model
            else:
                model_item = fipe._find_by_name(fipe.list_models(brand_code), model, "Modelo")
                model_code = model_item.code

            items = fipe.list_years(brand_code, model_code)
        except (FipeUpstreamError, FipeValidationError) as e:
            return Response({"error": str(e)}, status=400 if isinstance(e, FipeValidationError) else 503)

        return Response([{"code": x.code, "name": x.name} for x in items])
