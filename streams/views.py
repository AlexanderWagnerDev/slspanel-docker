from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.utils.translation import gettext as _
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from functools import wraps
import requests
import secrets

API_URL = settings.SLS_API_URL if hasattr(settings, 'SLS_API_URL') else 'http://localhost:8789'
API_KEY = settings.SLS_API_KEY if hasattr(settings, 'SLS_API_KEY') else ''

def conditional_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if getattr(settings, 'REQUIRE_LOGIN', True):
            if not request.user.is_authenticated:
                return redirect('streams:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

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

@conditional_login_required
def index(request):
    code, res = call_api('GET', '/api/stream-ids')
    entries = res.get("data") if res and isinstance(res, dict) and "data" in res else []
    publisher_map = {}
    
    for entry in entries:
        pub = entry.get("publisher")
        player = entry.get("player")
        desc = entry.get("description", "")
        if not pub:
            continue
            
        if pub not in publisher_map:
            publisher_map[pub] = {"publisher": pub, "player": [], "description": ""}
        
        if player:
            player_obj = {"key": player, "description": desc}
            if player_obj not in publisher_map[pub]["player"]:
                publisher_map[pub]["player"].append(player_obj)
        
        if not publisher_map[pub]["description"] and desc:
            publisher_map[pub]["description"] = desc
    
    streams = list(publisher_map.values())
    
    for s in streams:
        if s["player"]:
            s["main_player"] = s["player"][0]["key"]
            s["main_description"] = s["player"][0]["description"]
        else:
            s["main_player"] = None
            s["main_description"] = ""

    context = {
        'streams': streams,
        'srt_publish_port': settings.SRT_PUBLISH_PORT,
        'srt_player_port': settings.SRT_PLAYER_PORT,
        'srtla_publish_port': settings.SRTLA_PUBLISH_PORT,
        'sls_domain_ip': settings.SLS_DOMAIN_IP,
        'sls_stats_port': settings.SLS_STATS_PORT,
    }
    return render(request, 'index.html', context)

@conditional_login_required
def streams_status_json(request):
    code, res = call_api('GET', '/api/stream-ids')
    entries = res.get("data") if res and isinstance(res, dict) and "data" in res else []
    publisher_map = {}
    for entry in entries:
        pub = entry.get("publisher")
        player = entry.get("player")
        desc = entry.get("description", "")
        if not pub:
            continue
        if pub not in publisher_map:
            publisher_map[pub] = {"publisher": pub, "player": [], "description": desc}
        if desc:
            publisher_map[pub]["description"] = desc
        if player and player not in publisher_map[pub]["player"]:
            publisher_map[pub]["player"].append(player)
    streams = list(publisher_map.values())
    return JsonResponse({"streams": streams})

@conditional_login_required
def sls_stats(request, player_key):
    try:
        url = f"http://{settings.SLS_STATS_DOMAIN_IP}:{settings.SLS_STATS_PORT}/stats/{player_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return JsonResponse(data)
    except:
        return JsonResponse({"error": "Failed to fetch stats", "status": "error"}, status=500)

@conditional_login_required
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

@conditional_login_required
def add_player(request):
    if request.method == "POST":
        if 'confirm' in request.POST:
            publisher_key = request.POST.get("publisher_key")
            player_key = request.POST.get("player_key")
            description = request.POST.get("description")
            data = {"publisher": publisher_key, "player": player_key, "description": description}
            code, res = call_api('POST', '/api/stream-ids', data)
            if code and 200 <= code < 300:
                return redirect('streams:index')
            else:
                return render(request, 'add_player.html', {
                    'error': _("API error"),
                    'publisher_key': publisher_key,
                    'player_key': player_key,
                    'description': description,
                })
        else:
            publisher_key = request.POST.get("publisher_key")
            player_key = 'play_' + secrets.token_hex(16)
            description = request.POST.get("description", "")
            return render(request, 'add_player.html', {
                'publisher_key': publisher_key,
                'player_key': player_key,
                'description': description,
            })

    publisher_key = request.GET.get("publisher_key", "")
    player_key = 'play_' + secrets.token_hex(16)
    return render(request, 'add_player.html', {
        "publisher_key": publisher_key,
        "player_key": player_key,
        "description": ""
    })
    
@conditional_login_required
def delete_stream(request, publisher_key):
    code, res = call_api('GET', '/api/stream-ids')
    entries = res.get("data") if res and isinstance(res, dict) and "data" in res else []
    player_keys = [entry["player"] for entry in entries if entry.get("publisher") == publisher_key and entry.get("player")]
    for play_key in player_keys:
        call_api('DELETE', f'/api/stream-ids/{play_key}')
    return redirect('streams:index')

@conditional_login_required
def delete_player(request, player_key):
    code, res = call_api('DELETE', f'/api/stream-ids/{player_key}')
    return redirect('streams:index')