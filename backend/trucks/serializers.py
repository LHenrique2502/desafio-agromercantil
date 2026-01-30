from __future__ import annotations

import re
from decimal import Decimal

from django.db import IntegrityError
from rest_framework import serializers

from .models import Truck
from .services.fipe import FipeClient, FipeValidationError


_LICENSE_PLATE_RE = re.compile(r"^(?:[A-Z]{3}-?\d{4}|[A-Z]{3}\d[A-Z]\d{2})$")


def _normalize_plate(value: str) -> str:
    return value.strip().upper().replace(" ", "")


class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = ["id", "license_plate", "brand", "model", "manufacturing_year", "fipe_price"]
        read_only_fields = ["id", "fipe_price"]


class TruckCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = ["id", "license_plate", "brand", "model", "manufacturing_year", "fipe_price"]
        read_only_fields = ["id", "fipe_price"]

    def validate_license_plate(self, value: str) -> str:
        value = _normalize_plate(value)
        if not _LICENSE_PLATE_RE.match(value):
            raise serializers.ValidationError("Placa inválida. Use AAA-1234 ou AAA1A23.")
        return value

    def create(self, validated_data):
        fipe = FipeClient()
        try:
            canonical_brand, canonical_model, canonical_year, price = fipe.validate_and_get_price(
                brand=validated_data["brand"],
                model=validated_data["model"],
                year=int(validated_data["manufacturing_year"]),
            )
        except FipeValidationError as e:
            raise serializers.ValidationError({"fipe": str(e)})

        validated_data["brand"] = canonical_brand
        validated_data["model"] = canonical_model
        validated_data["manufacturing_year"] = canonical_year
        validated_data["fipe_price"] = Decimal(price)

        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"license_plate": "Já existe um caminhão com esta placa."})


class TruckUpdateSerializer(serializers.ModelSerializer):
    license_plate = serializers.CharField(read_only=True)

    class Meta:
        model = Truck
        fields = ["id", "license_plate", "brand", "model", "manufacturing_year", "fipe_price"]
        read_only_fields = ["id", "license_plate", "fipe_price"]

    def update(self, instance: Truck, validated_data):
        # Somente brand/model/year podem ser atualizados, e recalculamos preço FIPE
        brand = validated_data.get("brand", instance.brand)
        model = validated_data.get("model", instance.model)
        year = int(validated_data.get("manufacturing_year", instance.manufacturing_year))

        fipe = FipeClient()
        try:
            canonical_brand, canonical_model, canonical_year, price = fipe.validate_and_get_price(
                brand=brand,
                model=model,
                year=year,
            )
        except FipeValidationError as e:
            raise serializers.ValidationError({"fipe": str(e)})

        instance.brand = canonical_brand
        instance.model = canonical_model
        instance.manufacturing_year = canonical_year
        instance.fipe_price = Decimal(price)
        instance.save(update_fields=["brand", "model", "manufacturing_year", "fipe_price"])
        return instance

