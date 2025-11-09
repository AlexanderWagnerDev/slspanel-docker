from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.conf import settings
import requests
import secrets

API_URL = settings.SLS_API_URL if hasattr(settings, 'SLS_API_URL') else 'http://localhost:8080'
API_KEY = settings.SLS_API_KEY if hasattr(settings, 'SLS_API_KEY') else 'changeme'

def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('streams:index')
        else:
            error = _("Invalid credentials")
    return render(request, 'login.html', {'error': error})


def logout_view(request):
    request.session.flush()
    return redirect('streams:login')


def call_api(method, endpoint, data=None):
    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }
    url = f"{API_URL}{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=5)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=5)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=5)
        else:
            return None, "Unsupported method"
        return response.status_code, response.json() if response.content else {}
    except Exception as e:
        return None, str(e)

@login_required(login_url='streams:login')
def index(request):
    code, streams = call_api('GET', '/api/stream-ids')
    streams = response.get("data") if response else []
    if streams is None:
        streams = []
    context = {
        'streams': streams,
        'srt_publish_port': settings.SRT_PUBLISH_PORT,
        'srt_player_port': settings.SRT_PLAYER_PORT,
        'srtla_publish_port': settings.SRTLA_PUBLISH_PORT,
        'sls_domain_ip': settings.SLS_DOMAIN_IP,
        'sls_stats_port': settings.SLS_STATS_PORT,
    }
    return render(request, 'index.html', context)

@login_required(login_url='streams:login')
def sls_stats(request, player_key):
    try:
        url = f"http://{settings.SLS_STATS_DOMAIN_IP}:{settings.SLS_STATS_PORT}/stats/{player_key}"
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        data = response.json()
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": "Failed to fetch stats"}, status=500)

@login_required(login_url='streams:login')
def create_stream(request):
    if request.method == "POST":
        publisher_key = request.POST.get("publisher")
        if not publisher_key:
            publisher_key = 'live_' + secrets.token_hex(16)
        player_key = request.POST.get("player")
        if not player_key:
            player_key = 'play_' + secrets.token_hex(16)
        description = request.POST.get("description", "")
        data = {
            "publisher": publisher_key,
            "player": player_key,
            "description": description,
        }
        code, res = call_api('POST', '/api/stream-ids', data)
        if code and 200 <= code < 300:
            return redirect('streams:index')
        else:
            return render(request, 'create_stream.html', {'error': _("API error"), 'data': data})
    return render(request, 'create_stream.html')

@login_required(login_url='streams:login')
def add_player(request):
    if request.method == "POST":
        stream_id = request.POST.get("stream_id")
        player_key = request.POST.get("player_key")
        if not player_key:
            player_key = 'play_' + secrets.token_hex(16)
        description = request.POST.get("description", "")
        data = {
            "publisher": stream_id,
            "player": player_key,
            "description": description,
        }
        code, res = call_api('POST', '/api/stream-ids', data)
        if code and 200 <= code < 300:
            return redirect('streams:index')
        else:
            return render(request, 'add_player.html', {'error': _("API error"), 'data': data})

@login_required(login_url='streams:login')
def delete_stream(request, play_key):
    code, res = call_api('DELETE', f'/api/stream-ids/{play_key}')
    return redirect('streams:index')

@login_required(login_url='streams:login')
def delete_player(request, play_key):
    code, res = call_api('DELETE', f'/api/stream-ids/{play_key}')
    return redirect('streams:index')
