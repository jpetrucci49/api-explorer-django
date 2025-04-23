from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
import requests
from django.conf import settings
import redis
import json
from typing import Dict
from .exceptions import CustomAPIException

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
    "Access-Control-Allow-Methods": "GET, POST",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Expose-Headers": "X-Cache",
}

def fetch_github(url: str) -> Dict:
    if "test429" in url:
        raise CustomAPIException(429, "GitHub rate limit exceeded", {"remaining": "0"})
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {settings.GITHUB_TOKEN}"},
            timeout=10
        )
        if not response.ok:
            status_code = response.status_code
            detail = "GitHub API error"
            extra = {}
            if status_code == 404:
                detail = "GitHub user not found"
            elif status_code == 429:
                detail = "GitHub rate limit exceeded"
                extra["remaining"] = response.headers.get("x-ratelimit-remaining", "0")
            elif status_code == 400:
                detail = "Invalid GitHub API request"
            raise CustomAPIException(status_code, detail, extra)
        return response.json()
    except requests.RequestException:
        raise CustomAPIException(500, "Failed to reach GitHub", {})

def analyze_profile(username: str) -> Dict:
    user_data = fetch_github(f"{settings.GITHUB_API_URL}/users/{username}")
    repos = fetch_github(f"{user_data['repos_url']}?per_page=100")
    languages = []
    for repo in repos:
        try:
            lang_data = fetch_github(repo["languages_url"])
            languages.append(lang_data)
        except CustomAPIException as e:
            if e.status_code == 404:
                continue
            raise

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
        raise CustomAPIException(400, "Username is required")
    
    cache_key = f"github:{username}"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return Response(
                json.loads(cached),
                headers={**common_headers, "X-Cache": "HIT"}
            )
    except redis.RedisError:
        pass

    data = fetch_github(f"{settings.GITHUB_API_URL}/users/{username}")
    try:
        redis_client.setex(cache_key, 1800, json.dumps(data))
    except redis.RedisError:
        pass
    return Response(
        data,
        headers={**common_headers, "X-Cache": "MISS"}
    )

@api_view(["GET"])
def analyze(request):
    username = request.query_params.get("username")
    if not username:
        raise CustomAPIException(400, "Username is required")

    cache_key = f"analyze:{username}"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return Response(
                json.loads(cached),
                headers={**common_headers, "X-Cache": "HIT"}
            )
    except redis.RedisError:
        pass

    analysis = analyze_profile(username)
    try:
        redis_client.setex(cache_key, 1800, json.dumps(analysis))
    except redis.RedisError:
        pass
    return Response(
        analysis,
        headers={**common_headers, "X-Cache": "MISS"}
    )

@api_view(['POST'])
def clear_cache(request):
    try:
        redis_client.flushdb()
        return Response({"detail": "Cache cleared successfully"}, headers=common_headers)
    except redis.RedisError:
        raise CustomAPIException(500, "Failed to clear cache")