from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """
    Centraliza o formato de erros e permite mapear erros de integração externa.
    """
    response = exception_handler(exc, context)
    if response is None:
        return None

    # Padroniza o payload de erro (sem quebrar o default do DRF)
    if isinstance(response.data, dict) and "detail" in response.data:
        response.data = {"error": response.data["detail"]}

    return Response(response.data, status=response.status_code)

