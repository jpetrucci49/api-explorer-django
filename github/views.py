from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests

GITHUB_API_URL = "https://api.github.com/users"

@api_view(['GET'])
def get_github_user(request):
    username = request.query_params.get('username')
    if not username:
        return Response({"detail": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        response = requests.get(f"{GITHUB_API_URL}/{username}")
        if response.status_code != 200:
            return Response({"detail": "GitHub API error"}, status=response.status_code)
        return Response(response.json())
    except requests.RequestException:
        return Response({"detail": "Failed to reach GitHub"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)