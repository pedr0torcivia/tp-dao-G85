from django.http import JsonResponse


def api_root(request):
    return JsonResponse(
        {
            "name": "Biblioteca - API Grupo 85",
            "version": "0.1.0",
            "health": "/api/health/",
            "docs": "/api/docs/",
        }
    )


def health(request):
    return JsonResponse({"status": "ok"})
