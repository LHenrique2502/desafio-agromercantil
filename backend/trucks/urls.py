from django.urls import path

from . import views

urlpatterns = [
    # Trucks
    path("trucks/", views.TruckListCreateView.as_view(), name="truck-list-create"),
    path("trucks/<int:pk>/", views.TruckUpdateView.as_view(), name="truck-update"),
    # FIPE helpers (via backend)
    path("fipe/brands/", views.FipeBrandsView.as_view(), name="fipe-brands"),
    path("fipe/models/", views.FipeModelsView.as_view(), name="fipe-models"),
    path("fipe/years/", views.FipeYearsView.as_view(), name="fipe-years"),
]

