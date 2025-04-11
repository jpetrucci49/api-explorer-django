from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
import requests
from django.conf import settings
import redis
import json
from typing import Dict

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT), 
    password=settings.REDIS_PASSWORD, 
    decode_responses=True
)

common_headers = {
    "Content-Type": "application/json",
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
    "Access-Control-Allow-Origin": "http://localhost:3000",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Expose-Headers": "X-Cache",
}

def fetch_github(url: str) -> Dict:
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {settings.GITHUB_TOKEN}"}
    )
    response.raise_for_status()
    return response.json()

def analyze_profile(username: str) -> Dict:
    user_data = fetch_github(f"{settings.GITHUB_API_URL}/users/{username}")
    repos = fetch_github(f"{user_data['repos_url']}?per_page=100")
    languages = [fetch_github(repo["languages_url"]) for repo in repos]

    lang_stats = {}
    for lang_data in languages:
        if isinstance(lang_data, dict):
            for lang, bytes in lang_data.items():
                lang_stats[lang] = lang_stats.get(lang, 0) + bytes

    top_languages = [
        {"lang": lang, "bytes": bytes}
        for lang, bytes in sorted(lang_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    return {
        "login": user_data["login"],
        "publicRepos": user_data["public_repos"],
        "topLanguages": top_languages
    }

@api_view(['GET'])
def get_github_user(request):
    username = request.query_params.get('username')
    if not username:
        return Response({"detail": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    cache_key = f"github:{username}"
    cached = redis_client.get(cache_key)
    if cached:
        return Response(
            json.loads(cached),
            headers={**common_headers, "X-Cache": "HIT"}
        )
    try:
        data = fetch_github(f"{settings.GITHUB_API_URL}/users/{username}")
        redis_client.setex(cache_key, 1800, json.dumps(data))
        return Response(
            data,
            headers={**common_headers, "X-Cache": "MISS"}
        )
    except requests.HTTPError as e:
        return Response({"detail": "GitHub API error"}, status=e.response.status_code, headers=common_headers)
    except requests.RequestException as e:
        return Response({"detail": "Failed to reach GitHub"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=common_headers)

@api_view(["GET"])
def analyze(request):
    username = request.query_params.get("username")
    if not username:
        return Response({"detail": "Username is required"}, status=status.HTTP_400_BAD_REQUEST, headers=common_headers)

    cache_key = f"analyze:{username}"
    cached = redis_client.get(cache_key)
    if cached:
        return Response(
            json.loads(cached),
            headers={**common_headers, "X-Cache": "HIT"}
        )

    try:
        analysis = analyze_profile(username)
        redis_client.setex(cache_key, 1800, json.dumps(analysis))
        return Response(
            analysis,
            headers={**common_headers, "X-Cache": "MISS"}
        )
    except requests.HTTPError as e:
        return Response({"detail": "GitHub API error"}, status=e.response.status_code, headers=common_headers)
    except requests.RequestException as e:
        return Response({"detail": "Failed to analyze profile"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=common_headers)

@api_view(['POST'])
def clear_cache(request):
    try:
        redis_client.flushdb()
        return Response({"detail": "Cache cleared successfully"}, headers=common_headers)
    except redis.RedisError as e:
        return Response({"detail": "Failed to clear cache"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=common_headers)
