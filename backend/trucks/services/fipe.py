from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache


class FipeError(Exception):
    pass


class FipeUpstreamError(FipeError):
    pass


class FipeValidationError(FipeError):
    pass


def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


@dataclass(frozen=True)
class FipeRefItem:
    code: str
    name: str


class FipeClient:
    def __init__(self):
        self.base_url = getattr(settings, "FIPE_BASE_URL", "https://fipe.parallelum.com.br/api/v2").rstrip("/")
        self.vehicle_type = getattr(settings, "FIPE_VEHICLE_TYPE", "trucks")
        self.timeout = getattr(settings, "FIPE_HTTP_TIMEOUT_SECONDS", 8)
        self.cache_ttl = getattr(settings, "FIPE_CACHE_TTL_SECONDS", 60 * 30)

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = requests.get(url, params=params or {}, timeout=self.timeout)
        except requests.RequestException as e:
            raise FipeUpstreamError(f"Falha ao acessar FIPE: {e}") from e

        if resp.status_code >= 400:
            raise FipeUpstreamError(f"FIPE retornou {resp.status_code}")
        try:
            return resp.json()
        except ValueError as e:
            raise FipeUpstreamError("Resposta inválida da FIPE (JSON).") from e

    def list_brands(self) -> list[FipeRefItem]:
        cache_key = f"fipe:{self.vehicle_type}:brands"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._get_json(f"{self.vehicle_type}/brands")
        items = [FipeRefItem(code=str(x["code"]), name=str(x["name"])) for x in data]
        cache.set(cache_key, items, timeout=self.cache_ttl)
        return items

    def list_models(self, brand_code: str) -> list[FipeRefItem]:
        cache_key = f"fipe:{self.vehicle_type}:brands:{brand_code}:models"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._get_json(f"{self.vehicle_type}/brands/{brand_code}/models")
        items = [FipeRefItem(code=str(x["code"]), name=str(x["name"])) for x in data]
        cache.set(cache_key, items, timeout=self.cache_ttl)
        return items

    def list_years(self, brand_code: str, model_code: str) -> list[FipeRefItem]:
        cache_key = f"fipe:{self.vehicle_type}:brands:{brand_code}:models:{model_code}:years"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._get_json(f"{self.vehicle_type}/brands/{brand_code}/models/{model_code}/years")
        items = [FipeRefItem(code=str(x["code"]), name=str(x["name"])) for x in data]
        cache.set(cache_key, items, timeout=self.cache_ttl)
        return items

    def get_vehicle_details(self, brand_code: str, model_code: str, year_code: str) -> dict[str, Any]:
        # Esse endpoint retorna detalhes incluindo preço (ex.: "price": "R$ 500.000,00")
        return self._get_json(f"{self.vehicle_type}/brands/{brand_code}/models/{model_code}/years/{year_code}")

    def _find_by_name(self, items: list[FipeRefItem], name: str, label: str) -> FipeRefItem:
        wanted = _normalize_name(name)
        for item in items:
            if _normalize_name(item.name) == wanted:
                return item
        raise FipeValidationError(f"{label} não encontrado na FIPE: {name}")

    def validate_and_get_price(self, *, brand: str, model: str, year: int) -> tuple[str, str, int, str]:
        brand_item = self._find_by_name(self.list_brands(), brand, "Marca")
        model_item = self._find_by_name(self.list_models(brand_item.code), model, "Modelo")

        years = self.list_years(brand_item.code, model_item.code)
        # O name costuma ser "2020 Diesel" etc. Validamos pelo ano inicial.
        year_item = None
        for y in years:
            m = re.match(r"^(\d{4})", y.name.strip())
            if m and int(m.group(1)) == int(year):
                year_item = y
                break
        if year_item is None:
            raise FipeValidationError(f"Ano não encontrado na FIPE: {year}")

        details = self.get_vehicle_details(brand_item.code, model_item.code, year_item.code)
        price = details.get("price") or details.get("Price") or details.get("valor") or details.get("Valor")
        if not price:
            raise FipeUpstreamError("FIPE não retornou o campo de preço.")

        return brand_item.name, model_item.name, int(year), _parse_brl_price_to_decimal_str(str(price))


def _parse_brl_price_to_decimal_str(value: str) -> str:
    # Ex.: "R$ 500.000,00" -> "500000.00"
    v = value.strip()
    v = v.replace("R$", "").strip()
    v = v.replace(".", "").replace(",", ".")
    v = re.sub(r"[^\d.]", "", v)
    if not v:
        raise FipeUpstreamError(f"Preço inválido retornado pela FIPE: {value}")
    return v

