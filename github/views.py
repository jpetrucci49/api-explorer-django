from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
import requests
from django.conf import settings
import redis
import json

redis_client = redis.Redis(host=f"{settings.REDIS_HOST}", port=F"{settings.REDIS_PORT}", password=f"{settings.REDIS_PASSWORD}", decode_responses=True)

@api_view(['GET'])
def get_github_user(request):
    username = request.query_params.get('username')
    if not username:
        return Response({"detail": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    cache_key = f"github:{username}"
    cached = redis_client.get(cache_key)
    if cached:
        response = JsonResponse(json.loads(cached))
        response['X-Cache'] = 'HIT'
        return response
    else:
        try:
            response = requests.get(
                f"{settings.GITHUB_API_URL}/{username}",
                headers={"Authorization": f"Bearer {settings.GITHUB_TOKEN}"},
            )
            if response.status_code != 200:
                return Response({"detail": "GitHub API error"}, status=response.status_code)
            data = response.json()
            redis_client.setex(cache_key, 1800, json.dumps(data))
            response = JsonResponse(data)
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