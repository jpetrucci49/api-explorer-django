from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
from django.conf import settings
from time import time

CACHE_TTL = 30 * 60  # 30 minutes in seconds
cache = {}  # {cache_key: {"data": data, "timestamp": time}}

@api_view(['GET'])
def get_github_user(request):
    username = request.query_params.get('username')
    if not username:
        return Response({"detail": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    cache_key = f"github:{username}"
    cached = cache.get(cache_key)
    if cached and (time() - cached["timestamp"]) < CACHE_TTL:
        response = Response(cached["data"])
        response["X-Cache"] = "HIT"
    else:
        try:
            response = requests.get(
                f"{settings.GITHUB_API_URL}/{username}",
                headers={"Authorization": f"Bearer {settings.GITHUB_TOKEN}"},
            )
            if response.status_code != 200:
                return Response({"detail": "GitHub API error"}, status=response.status_code)
            data = response.json()
            cache[cache_key] = {"data": data, "timestamp": time()}
            response = Response(data)
            response["X-Cache"] = "MISS"
        except requests.RequestException:
            return Response({"detail": "Failed to reach GitHub"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    response["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response["Access-Control-Allow-Methods"] = "GET"
    response["Access-Control-Allow-Headers"] = "*"
    return response