import re
import secrets
from functools import wraps

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST, require_http_methods

API_URL = settings.SLS_API_URL if hasattr(settings, 'SLS_API_URL') else 'http://localhost:8789'
API_KEY = settings.SLS_API_KEY if hasattr(settings, 'SLS_API_KEY') else ''

API_STREAM_IDS_ENDPOINT = '/api/stream-ids'
INDEX_ROUTE = 'streams:index'
LOGIN_ROUTE = 'streams:login'
CREATE_STREAM_TEMPLATE = 'create_stream.html'
ADD_PLAYER_TEMPLATE = 'add_player.html'

# Stream keys are used as path segments when calling the SLS API, so they must be
# restricted to a safe character set to prevent path traversal (e.g. "../").
STREAM_KEY_RE = re.compile(r'^[A-Za-z0-9_.-]{1,200}$')
# Only allow API endpoints below the fixed /api/ root and reject traversal sequences.
API_ENDPOINT_RE = re.compile(r'^/api/[A-Za-z0-9_./-]*$')


def conditional_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if getattr(settings, 'REQUIRE_LOGIN', True):
            if not request.user.is_authenticated:
                return redirect(LOGIN_ROUTE)
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def _is_valid_stream_key(key):
    return (
        isinstance(key, str)
        and bool(STREAM_KEY_RE.match(key))
        and '..' not in key
    )


def _is_safe_endpoint(endpoint):
    if not isinstance(endpoint, str) or not API_ENDPOINT_RE.match(endpoint):
        return False
    return '..' not in endpoint and '//' not in endpoint


def call_api(method, endpoint, data=None):
    if not _is_safe_endpoint(endpoint):
        return None, "Invalid endpoint"
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
    except requests.RequestException as e:
        return None, str(e)


def _fetch_stream_entries():
    _, res = call_api('GET', API_STREAM_IDS_ENDPOINT)
    if res and isinstance(res, dict) and "data" in res:
        return res.get("data") or []
    return []


def _group_by_publisher(entries):
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
    return publisher_map


@require_http_methods(["GET", "POST"])
def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(INDEX_ROUTE)
        else:
            error = _("Invalid credentials")
    return render(request, 'login.html', {'error': error})


@require_GET
def logout_view(request):
    request.session.flush()
    return redirect(LOGIN_ROUTE)


@require_GET
@conditional_login_required
def index(request):
    entries = _fetch_stream_entries()
    streams = list(_group_by_publisher(entries).values())

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
        'sls_stats_scheme': getattr(settings, 'SLS_STATS_SCHEME', 'http'),
    }
    return render(request, 'index.html', context)


@require_GET
@conditional_login_required
def streams_status_json(request):
    entries = _fetch_stream_entries()
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


@require_GET
@conditional_login_required
def sls_stats(request, player_key):
    if not _is_valid_stream_key(player_key):
        return JsonResponse({"error": "Invalid player key", "status": "error"}, status=400)

    scheme = getattr(settings, 'SLS_STATS_SCHEME', 'http')
    try:
        url = f"{scheme}://{settings.SLS_STATS_DOMAIN_IP}:{settings.SLS_STATS_PORT}/stats/{player_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return JsonResponse(data)
    except requests.RequestException:
        return JsonResponse({"error": "Failed to fetch stats", "status": "error"}, status=500)


@require_http_methods(["GET", "POST"])
@conditional_login_required
def create_stream(request):
    if request.method == "POST":
        publisher_key = request.POST.get("publisher")
        if not publisher_key:
            publisher_key = 'live_' + secrets.token_hex(16)
        player_key = request.POST.get("player")
        if not player_key:
            player_key = 'play_' + secrets.token_hex(16)
        if not (_is_valid_stream_key(publisher_key) and _is_valid_stream_key(player_key)):
            return render(request, CREATE_STREAM_TEMPLATE, {'error': _("Invalid stream key")})
        description = request.POST.get("description", "")
        data = {
            "publisher": publisher_key,
            "player": player_key,
            "description": description,
        }
        code, _ = call_api('POST', API_STREAM_IDS_ENDPOINT, data)
        if code and 200 <= code < 300:
            return redirect(INDEX_ROUTE)
        else:
            return render(request, CREATE_STREAM_TEMPLATE, {'error': _("API error"), 'data': data})
    return render(request, CREATE_STREAM_TEMPLATE)


@require_http_methods(["GET", "POST"])
@conditional_login_required
def add_player(request):
    if request.method == "POST":
        publisher_key = request.POST.get("publisher_key")
        description = request.POST.get("description", "")
        if not _is_valid_stream_key(publisher_key):
            return HttpResponseBadRequest(_("Invalid publisher key"))
        if 'confirm' in request.POST:
            player_key = request.POST.get("player_key")
            if not _is_valid_stream_key(player_key):
                return HttpResponseBadRequest(_("Invalid player key"))
            data = {"publisher": publisher_key, "player": player_key, "description": description}
            code, _ = call_api('POST', API_STREAM_IDS_ENDPOINT, data)
            if code and 200 <= code < 300:
                return redirect(INDEX_ROUTE)
            else:
                return render(request, ADD_PLAYER_TEMPLATE, {
                    'error': _("API error"),
                    'publisher_key': publisher_key,
                    'player_key': player_key,
                    'description': description,
                })
        else:
            player_key = 'play_' + secrets.token_hex(16)
            return render(request, ADD_PLAYER_TEMPLATE, {
                'publisher_key': publisher_key,
                'player_key': player_key,
                'description': description,
            })

    publisher_key = request.GET.get("publisher_key", "")
    player_key = 'play_' + secrets.token_hex(16)
    return render(request, ADD_PLAYER_TEMPLATE, {
        "publisher_key": publisher_key,
        "player_key": player_key,
        "description": ""
    })


@require_POST
@conditional_login_required
def delete_stream(request, publisher_key):
    if not _is_valid_stream_key(publisher_key):
        return HttpResponseBadRequest(_("Invalid publisher key"))

    entries = _fetch_stream_entries()
    player_keys = [entry["player"] for entry in entries if entry.get("publisher") == publisher_key and entry.get("player")]
    for play_key in player_keys:
        call_api('DELETE', f'{API_STREAM_IDS_ENDPOINT}/{play_key}')
    return redirect(INDEX_ROUTE)


@require_POST
@conditional_login_required
def delete_player(request, player_key):
    if not _is_valid_stream_key(player_key):
        return HttpResponseBadRequest(_("Invalid player key"))

    call_api('DELETE', f'{API_STREAM_IDS_ENDPOINT}/{player_key}')
    return redirect(INDEX_ROUTE)
