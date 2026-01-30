from __future__ import annotations

from decimal import Decimal

import responses
from django.conf import settings
from rest_framework.test import APITestCase


def _fipe_url(path: str) -> str:
    base = getattr(settings, "FIPE_BASE_URL", "https://fipe.parallelum.com.br/api/v2").rstrip("/")
    return f"{base}/{path.lstrip('/')}"


def _mock_fipe_happy_path(
    *,
    brand_code: str = "102",
    brand_name: str = "AGRALE",
    model_code: str = "5986",
    model_name: str = "10000 / 10000 S  2p (diesel) (E5)",
    year_code: str = "2022-3",
    year_name: str = "2022",
    price: str = "R$ 243.652,00",
):
    responses.add(
        responses.GET,
        _fipe_url("trucks/brands"),
        json=[{"code": brand_code, "name": brand_name}],
        status=200,
    )
    responses.add(
        responses.GET,
        _fipe_url(f"trucks/brands/{brand_code}/models"),
        json=[{"code": model_code, "name": model_name}],
        status=200,
    )
    responses.add(
        responses.GET,
        _fipe_url(f"trucks/brands/{brand_code}/models/{model_code}/years"),
        json=[{"code": year_code, "name": year_name}],
        status=200,
    )
    responses.add(
        responses.GET,
        _fipe_url(f"trucks/brands/{brand_code}/models/{model_code}/years/{year_code}"),
        json={"price": price},
        status=200,
    )


class TruckApiTests(APITestCase):
    @responses.activate
    def test_create_truck_persists_fipe_price_and_lists(self):
        _mock_fipe_happy_path()

        payload = {
            "license_plate": "ABC1D23",
            "brand": "Agrale",
            "model": "10000 / 10000 S  2p (diesel) (E5)",
            "manufacturing_year": 2022,
        }
        res = self.client.post("/api/trucks/", payload, format="json")
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["license_plate"], "ABC1D23")
        self.assertEqual(Decimal(res.data["fipe_price"]), Decimal("243652.00"))

        res_list = self.client.get("/api/trucks/")
        self.assertEqual(res_list.status_code, 200, res_list.data)
        self.assertEqual(len(res_list.data), 1)

    @responses.activate
    def test_duplicate_license_plate_is_rejected(self):
        _mock_fipe_happy_path()

        payload = {
            "license_plate": "ABC1D23",
            "brand": "AGRALE",
            "model": "10000 / 10000 S  2p (diesel) (E5)",
            "manufacturing_year": 2022,
        }
        res1 = self.client.post("/api/trucks/", payload, format="json")
        self.assertEqual(res1.status_code, 201, res1.data)

        # repetir mocks (o fluxo chama FIPE novamente)
        _mock_fipe_happy_path()
        res2 = self.client.post("/api/trucks/", payload, format="json")
        self.assertEqual(res2.status_code, 400, res2.data)
        self.assertIn("license_plate", res2.data)

    @responses.activate
    def test_patch_updates_brand_model_year_and_recalculates_price(self):
        _mock_fipe_happy_path(price="R$ 243.652,00")

        create_payload = {
            "license_plate": "AAA-1234",
            "brand": "AGRALE",
            "model": "10000 / 10000 S  2p (diesel) (E5)",
            "manufacturing_year": 2022,
        }
        created = self.client.post("/api/trucks/", create_payload, format="json").data

        # novo preço após update
        _mock_fipe_happy_path(price="R$ 200.000,00")
        res = self.client.patch(
            f"/api/trucks/{created['id']}/",
            {"brand": "AGRALE", "model": "10000 / 10000 S  2p (diesel) (E5)", "manufacturing_year": 2022},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(Decimal(res.data["fipe_price"]), Decimal("200000.00"))

    @responses.activate
    def test_invalid_plate_format_is_rejected(self):
        _mock_fipe_happy_path()
        res = self.client.post(
            "/api/trucks/",
            {
                "license_plate": "123",
                "brand": "AGRALE",
                "model": "10000 / 10000 S  2p (diesel) (E5)",
                "manufacturing_year": 2022,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400, res.data)
        self.assertIn("license_plate", res.data)

    @responses.activate
    def test_fipe_validation_error_is_returned(self):
        # FIPE sem a marca/modelo informados
        responses.add(
            responses.GET,
            _fipe_url("trucks/brands"),
            json=[{"code": "1", "name": "OUTRA"}],
            status=200,
        )

        res = self.client.post(
            "/api/trucks/",
            {
                "license_plate": "ABC1D23",
                "brand": "INEXISTENTE",
                "model": "QUALQUER",
                "manufacturing_year": 2022,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400, res.data)
        self.assertIn("fipe", res.data)
