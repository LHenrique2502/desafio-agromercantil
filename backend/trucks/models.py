from django.db import models


class Truck(models.Model):
    license_plate = models.CharField(max_length=10, unique=True)
    brand = models.CharField(max_length=120)
    model = models.CharField(max_length=160)
    manufacturing_year = models.IntegerField()
    fipe_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.license_plate} - {self.brand} {self.model} ({self.manufacturing_year})"
