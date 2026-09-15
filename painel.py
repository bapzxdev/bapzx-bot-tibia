import html
import json
import os
import secrets
import time
from datetime import datetime, timedelta

import requests
from flask import Blueprint, jsonify, redirect, request, session

import rbac

bp = Blueprint("painel", __name__)

BRAND = "BAPZX"
VERSION = "2.1.0"
PORTFOLIO_URL = os.environ.get("PORTFOLIO_URL", "https://bapzxdev.github.io/bapzx-portfolio/")


def _env_master():
    for source in (
        os.environ,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gemini-cli", ".env"),
    ):
        lines = []
        if isinstance(source, dict):
            for var in ("MASTER_EMAILS", "ADMIN_EMAILS"):
                if source.get(var):
                    return source.get(var)
            continue
        try:
            with open(source, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            lines = []
        for line in lines:
            line = line.strip()
            for var in ("MASTER_EMAILS", "ADMIN_EMAILS"):
                if line.startswith(var + "=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip()
    return ""


MASTER_EMAILS = {e.strip().lower() for e in _env_master().split(",") if e.strip()}


def _env(var, default=""):
    value = os.environ.get(var)
    if value:
        return value
    for candidate in (
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gemini-cli", ".env"),
    ):
        if os.path.isfile(candidate):
            with open(candidate, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(var + "=") and not line.startswith("#"):
                        return line.split("=", 1)[1].strip()
    return default


SUPA_URL = _env("SUPABASE_URL").rstrip("/")
SUPA_KEY = _env("SUPABASE_KEY")
ADMIN_IP_ALLOWLIST = {
    item.strip()
    for item in _env("ADMIN_IP_ALLOWLIST").split(",")
    if item.strip()
}
if not SUPA_URL or not SUPA_KEY:
    raise RuntimeError("painel: SUPABASE_URL/SUPABASE_KEY obrigatorias")

_CSRF_PERMITTED_ORIGINS = {
    item.strip()
    for item in _env("ALLOWED_ORIGINS", PORTFOLIO_URL + ",https://bapzx-bot-tibia.onrender.com")
    .split(",")
    if item.strip()
}
_CSRF_PERMITTED_ORIGINS.add("http://localhost")
_CSRF_PERMITTED_ORIGINS.add("http://127.0.0.1")

_RATE = {}
_RATE_LIMIT_TRACK_PER_MIN = 20
_RATE_LIMIT_ADMIN_PER_MIN = 30


def _headers():
    return {
        "apikey": SUPA_KEY,
        "Authorization": f"Bearer {SUPA_KEY}",
        "Content-Type": "application/json",
    }


def _client_ip():
    return (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.remote_addr
        or "?"
    )


def _rate_limited(bucket, limit, window=60):
    ip = _client_ip()
    now = time.time()
    key = f"{bucket}:{ip}"
    hits = [t for t in _RATE.get(key, []) if now - t < window]
    hits.append(now)
    _RATE[key] = hits
    return len(hits) > limit


def _csrf_token():
    token = session.get("_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf"] = token
    return token


def _csrf_ok():
    sent = request.form.get("_csrf") or request.headers.get("X-CSRF-Token")
    token = session.get("_csrf")
    return bool(token) and bool(sent) and secrets.compare_digest(sent, token)


def _current_user():
    email = session.get("email")
    if not email:
        return None
    cargo = (session.get("cargo") or session.get("role") or "CLIENTE").upper()
    perms = session.get("perms") or []
    return {
        "email": email,
        "name": session.get("name") or email,
        "role": cargo,
        "cargo": cargo,
        "perms": set(perms or []),
    }


def _require_perm(*requeridas):
    user = _current_user()
    if not user:
        return None
    if ADMIN_IP_ALLOWLIST and _client_ip() not in ADMIN_IP_ALLOWLIST:
        return None
    if rbac.tem_perm(user.get("cargo"), user.get("perms"), *requeridas):
        user["perms"] = rbac.perms_efetivas(user.get("cargo"), user.get("perms"))
        return user
    return None


def _require_any_perm(*opcoes):
    user = _current_user()
    if not user:
        return None
    if ADMIN_IP_ALLOWLIST and _client_ip() not in ADMIN_IP_ALLOWLIST:
        return None
    if rbac.tem_qualquer_perm(user.get("cargo"), user.get("perms"), *opcoes):
        user["perms"] = rbac.perms_efetivas(user.get("cargo"), user.get("perms"))
        return user
    return None


def _audit(user, acao, detalhes=""):
    try:
        requests.post(
            f"{SUPA_URL}/rest/v1/audit_log",
            headers=_headers(),
            json={
                "email": user["email"] if isinstance(user, dict) else str(user),
                "acao": acao,
                "detalhes": detalhes[:500],
                "ip": _client_ip(),
            },
            timeout=10,
        )
    except Exception as error:
        print(f"[painel] audit falhou: {error}")


def _fetch(table, select="*", order="", query="", range_="0-999"):
    url = f"{SUPA_URL}/rest/v1/{table}?select={select}"
    if query:
        url += f"&{query}"
    if order:
        url += f"&order={order}"
    response = requests.get(
        url,
        headers={**_headers(), "Range": range_},
        timeout=15,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Supabase {response.status_code}: {response.text[:200]}")
    return response.json()


def _fetch_soft(table, select="*", order="", query="", range_="0-999"):
    """Como _fetch, mas retorna lista vazia se a tabela ainda não existir
    (PGRST205) para não derrubar o painel antes da migration ser rodada."""
    try:
        return _fetch(table, select=select, order=order, query=query, range_=range_)
    except Exception as error:
        if "PGRST205" in str(error):
            print(f"[painel] tabela '{table}' ainda não existe (migration pendente)")
            return []
        raise


def _count(table, query=""):
    response = requests.get(
        f"{SUPA_URL}/rest/v1/{table}?select=id{query}",
        headers={**_headers(), "Prefer": "count=exact", "Range": "0-0"},
        timeout=15,
    )
    total = response.headers.get("content-range", "").split("/")[-1]
    return int(total) if total.isdigit() else 0


def _count_since(table, iso_dt):
    response = requests.get(
        f"{SUPA_URL}/rest/v1/{table}?select=id&criado_em=gte.{iso_dt}",
        headers={**_headers(), "Prefer": "count=exact", "Range": "0-0"},
        timeout=15,
    )
    total = response.headers.get("content-range", "").split("/")[-1]
    return int(total) if total.isdigit() else 0


def _config_all():
    try:
        rows = _fetch("config", select="chave,valor")
        return {r.get("chave"): r.get("valor", "") for r in rows}
    except Exception:
        return {}


def _config_set(chave, valor):
    requests.post(
        f"{SUPA_URL}/rest/v1/config?on_conflict=chave",
        headers={**_headers(), "Prefer": "resolution=merge-duplicates"},
        json={"chave": chave, "valor": valor},
        timeout=10,
    )


DEFAULT_PRECOS = {
    "100": "R$ 9,00",
    "250": "R$ 22,50",
    "500": "R$ 45,00",
    "1000": "R$ 90,00",
    "2500": "R$ 225,00",
}


def _precos_atual():
    raw = _config_all().get("precos") or ""
    try:
        dados = json.loads(raw)
        if isinstance(dados, dict) and dados:
            return {str(k): str(v) for k, v in dados.items()}
    except Exception:
        pass
    return dict(DEFAULT_PRECOS)


def _precos_texto():
    return "\n".join(f"{k}={v}" for k, v in sorted(_precos_atual().items(), key=lambda kv: int(kv[0])))


def _parse_brl(value):
    if not value:
        return 0.0
    text = str(value).replace("R$", "").replace(" ", "")
    try:
        return float(text.replace(".", "").replace(",", "."))
    except Exception:
        return 0.0


def _fmt_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _iso_days_ago(days):
    moment = datetime.utcnow() - timedelta(days=days)
    return moment.isoformat() + "Z"


def _storage_upload(file_storage, folder="itens"):
    blob = file_storage.read()
    if not blob:
        return None, "Arquivo vazio."
    if len(blob) > 2 * 1024 * 1024:
        return None, "Imagem maior que 2 MB."
    name = file_storage.filename or ""
    ext = (os.path.splitext(name)[1] or ".png").lower().lstrip(".")
    if ext not in {"png", "jpg", "jpeg", "webp", "gif"}:
        return None, "Formato invalido (use png, jpg, jpeg, webp ou gif)."
    safe_name = f"{secrets.token_hex(8)}.{ext}"
    response = requests.post(
        f"{SUPA_URL}/storage/v1/object/{folder}/{safe_name}",
        headers={
            "apikey": SUPA_KEY,
            "Authorization": f"Bearer {SUPA_KEY}",
            "Content-Type": file_storage.mimetype or "image/png",
        },
        data=blob,
        timeout=30,
    )
    if response.status_code not in (200, 201):
        return None, f"Upload falhou ({response.status_code}): {response.text[:200]}"
    return f"{SUPA_URL}/storage/v1/object/public/{folder}/{safe_name}", None


from urllib.parse import urlsplit


def _origin_parts(origin):
    try:
        parsed = urlsplit(origin or "")
        host = (parsed.hostname or "").lower()
        port = parsed.port
        scheme = (parsed.scheme or "").lower()
        return scheme, host, port
    except Exception:
        return "", "", None


def _cors_ok():
    origin = request.headers.get("Origin") or ""
    scheme, host, port = _origin_parts(origin)
    for allowed in _CSRF_PERMITTED_ORIGINS:
        a_scheme, a_host, a_port = _origin_parts(allowed)
        if not a_host:
            continue
        if host and host == a_host and (not scheme or scheme == a_scheme) and (a_port is None or port == a_port):
            return True
    if not origin:
        req_host = (request.host or "").split(":")[0].lower()
        if any(a_host == req_host for _, a_host, _ in (_origin_parts(a) for a in _CSRF_PERMITTED_ORIGINS)):
            return True
    return False


_ICONS = {
    "grid": "<rect x='3' y='3' width='7' height='7'/><rect x='14' y='3' width='7' height='7'/><rect x='14' y='14' width='7' height='7'/><rect x='3' y='14' width='7' height='7'/>",
    "cart": "<circle cx='9' cy='21' r='1'/><circle cx='20' cy='21' r='1'/><path d='M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6'/>",
    "package": "<path d='M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z'/><polyline points='3.27 6.96 12 12.01 20.73 6.96'/><line x1='12' y1='22.08' x2='12' y2='12'/>",
    "users": "<path d='M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/><path d='M23 21v-2a4 4 0 0 0-3-3.87'/><path d='M16 3.13a4 4 0 0 1 0 7.75'/>",
    "wallet": "<path d='M21 12V7H5a2 2 0 0 1 0-4h14v4'/><path d='M3 5v14a2 2 0 0 0 2 2h16v-5'/><path d='M18 12a2 2 0 0 0 0 4h4v-4Z'/>",
    "support": "<circle cx='12' cy='12' r='10'/><path d='M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3'/><line x1='12' y1='17' x2='12.01' y2='17'/>",
    "gear": "<circle cx='12' cy='12' r='3'/><path d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'/>",
    "external": "<path d='M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6'/><polyline points='15 3 21 3 21 9'/><line x1='10' y1='14' x2='21' y2='3'/>",
    "swap": "<polyline points='16 3 21 3 21 8'/><line x1='4' y1='20' x2='21' y2='3'/><polyline points='21 16 21 21 16 21'/><line x1='15' y1='15' x2='21' y2='21'/><line x1='4' y1='4' x2='9' y2='9'/>",
    "logout": "<path d='M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4'/><polyline points='16 17 21 12 16 7'/><line x1='21' y1='12' x2='9' y2='12'/>",
    "search": "<circle cx='11' cy='11' r='8'/><line x1='21' y1='21' x2='16.65' y2='16.65'/>",
    "bell": "<path d='M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9'/><path d='M13.73 21a2 2 0 0 1-3.46 0'/>",
    "chevron": "<polyline points='6 9 12 15 18 9'/>",
    "menu": "<line x1='3' y1='12' x2='21' y2='12'/><line x1='3' y1='6' x2='21' y2='6'/><line x1='3' y1='18' x2='21' y2='18'/>",
    "dollar": "<line x1='12' y1='1' x2='12' y2='23'/><path d='M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'/>",
    "checks": "<path d='M22 11.08V12a10 10 0 1 1-5.93-9.14'/><polyline points='22 4 12 14.01 9 11.01'/>",
    "shield": "<path d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'/>",
    "brands": "<path d='M17 20h5v-2a3 3 0 0 0-5.36-1.86'/><path d='M3 20h5'/><path d='M16 15a3 3 0 1 0-2.12-5.12'/><path d='M8 4H3v5'/><circle cx='17' cy='4' r='2'/>",
    "clipboard": "<path d='M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2'/><rect x='8' y='2' width='8' height='4' rx='1'/>",
}


def _icon(name):
    return (
        "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' "
        "stroke-linecap='round' stroke-linejoin='round'>" + _ICONS.get(name, "") + "</svg>"
    )


LAYOUT_HEAD = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@500;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
* { box-sizing:border-box; }
body { font-family:'Inter',Arial,sans-serif; margin:0; background:#0b1120; color:#e2e8f0; }
.shell { display:flex; min-height:100vh; }
.sidebar { position:fixed; top:0; left:0; bottom:0; width:250px; background:#0e1626; border-right:1px solid #1e2c40; display:flex; flex-direction:column; z-index:50; }
.side-brand { display:flex; align-items:center; gap:11px; padding:18px 18px 16px; border-bottom:1px solid #1e2c40; }
.side-logo { width:36px; height:36px; border-radius:10px; background:linear-gradient(135deg,#34d399,#60a5fa); display:flex; align-items:center; justify-content:center; color:#04111b; font-weight:800; font-family:'Sora',sans-serif; font-size:12px; letter-spacing:1px; }
.brand-name { font-family:'Sora',sans-serif; font-weight:800; letter-spacing:2px; font-size:15px; color:#fff; }
.brand-name span { background:linear-gradient(135deg,#34d399,#60a5fa); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
.side-nav { flex:1; overflow-y:auto; padding:14px 10px 8px; }
.side-group { font-size:10px; letter-spacing:1.6px; text-transform:uppercase; color:#5b6b82; margin:18px 10px 6px; font-weight:600; }
.side-group:first-child { margin-top:2px; }
.side-item { display:flex; align-items:center; gap:11px; padding:9px 11px; border-radius:9px; color:#8ea0b8; text-decoration:none; font-size:14px; margin:2px 0; }
.side-item svg { width:18px; height:18px; flex:none; }
.side-item:hover { color:#fff; background:rgba(52,211,153,.08); }
.side-item.active { color:#fff; background:linear-gradient(135deg,rgba(52,211,153,.16),rgba(96,165,250,.14)); box-shadow:inset 0 0 0 1px rgba(52,211,153,.28); }
.side-item.active svg { color:#34d399; }
.side-foot { padding:12px 10px; border-top:1px solid #1e2c40; }
.side-foot .side-item { margin:0; }
.wrap { flex:1; margin-left:250px; min-width:0; display:flex; flex-direction:column; }
.topbar { position:sticky; top:0; z-index:40; background:rgba(11,17,32,.88); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); border-bottom:1px solid #1e2c40; display:flex; align-items:center; gap:14px; padding:12px 22px; }
.hamburger { display:none; background:transparent; border:1px solid #2a3a52; color:#e2e8f0; width:38px; height:38px; border-radius:9px; cursor:pointer; align-items:center; justify-content:center; padding:0; }
.hamburger svg { width:18px; height:18px; }
.top-title { flex:1; min-width:0; }
.crumb { font-size:12px; color:#5b6b82; margin-bottom:3px; }
.crumb b { color:#8ea0b8; font-weight:600; }
.top-title h1 { margin:0; font-size:20px; font-weight:700; font-family:'Sora',sans-serif; line-height:1.2; }
.top-search { position:relative; }
.top-search svg { position:absolute; left:12px; top:50%; transform:translateY(-50%); width:16px; height:16px; color:#5b6b82; pointer-events:none; }
.top-search input { width:250px; padding-left:38px; }
.top-actions { display:flex; align-items:center; gap:9px; }
.icon-btn { position:relative; width:38px; height:38px; border-radius:9px; border:1px solid #2a3a52; background:transparent; color:#a0aec0; display:flex; align-items:center; justify-content:center; cursor:pointer; padding:0; }
.icon-btn:hover { color:#fff; border-color:#3b4d6b; }
.icon-btn svg { width:18px; height:18px; }
.badge { position:absolute; top:-5px; right:-5px; min-width:17px; height:17px; border-radius:9px; background:#ef4444; color:#fff; font-size:10px; font-weight:700; display:flex; align-items:center; justify-content:center; padding:0 4px; box-sizing:border-box; box-shadow:0 0 0 2px #0b1120; }
.user-chip { display:flex; align-items:center; gap:9px; border:1px solid #2a3a52; background:transparent; border-radius:10px; padding:5px 10px 5px 6px; cursor:pointer; color:#e2e8f0; }
.user-chip:hover { border-color:#3b4d6b; }
.user-avatar { width:27px; height:27px; border-radius:7px; background:linear-gradient(135deg,#34d399,#60a5fa); color:#04111b; font-weight:800; font-size:12px; display:flex; align-items:center; justify-content:center; text-transform:uppercase; }
.user-chip .u-name { font-size:13px; font-weight:600; }
.user-chip .u-role { font-size:11px; color:#60a5fa; background:rgba(96,165,250,.12); border:1px solid rgba(96,165,250,.25); border-radius:999px; padding:1px 8px; }
.user-chip svg { width:14px; height:14px; color:#5b6b82; }
.dropdown { position:relative; }
.menu { position:absolute; right:0; top:calc(100% + 8px); min-width:240px; background:#111a2e; border:1px solid #1e2c40; border-radius:12px; box-shadow:0 14px 34px rgba(0,0,0,.5); padding:6px; display:none; z-index:60; }
.menu.open { display:block; }
.menu-head { padding:10px 12px; border-bottom:1px solid #1e2c40; margin-bottom:6px; }
.menu-head b { display:block; font-size:13px; color:#e2e8f0; }
.menu-head span { font-size:12px; color:#5b6b82; word-break:break-all; }
.menu a { display:flex; align-items:center; gap:10px; padding:9px 12px; border-radius:8px; color:#8ea0b8; text-decoration:none; font-size:13px; }
.menu a:hover { color:#fff; background:rgba(52,211,153,.1); }
.menu a svg { width:16px; height:16px; flex:none; }
.menu a.danger { color:#f87171; }
.menu a.danger:hover { background:rgba(127,29,29,.4); color:#fca5a5; }
.menu-empty { padding:10px 12px; color:#5b6b82; font-size:13px; }
.content { flex:1; width:100%; max-width:1200px; margin:0 auto; padding:24px 24px 64px; box-sizing:border-box; }
.scrim { position:fixed; inset:0; background:rgba(2,6,17,.62); z-index:45; display:none; }
.scrim.show { display:block; }
.page-sub { color:#8ea0b8; font-size:14px; margin:4px 0 6px; }
.kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(225px,1fr)); gap:14px; margin:20px 0 10px; }
.kpi { background:#16203a; border:1px solid #1e2c40; border-radius:14px; padding:16px 18px; display:flex; flex-direction:column; gap:11px; }
.kpi .k-top { display:flex; align-items:center; justify-content:space-between; }
.kpi .k-ico { width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center; background:rgba(52,211,153,.12); color:#34d399; }
.kpi .k-ico svg { width:18px; height:18px; }
.kpi .k-lbl { font-size:11px; color:#8ea0b8; letter-spacing:.5px; text-transform:uppercase; font-weight:600; }
.kpi .k-num { font-size:26px; font-weight:800; color:#fff; font-family:'Sora',sans-serif; line-height:1; }
.kpi .k-sub { font-size:12px; color:#5b6b82; }
.charts { display:grid; grid-template-columns:minmax(0,1.4fr) minmax(0,1fr); gap:16px; margin:16px 0; }
.chart-card { background:#16203a; border:1px solid #1e2c40; border-radius:14px; padding:16px 18px; min-width:0; overflow-x:auto; }
.chart-head { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:14px; flex-wrap:wrap; }
.chart-head h2 { margin:0; font-size:15px; }
.chart-period { font-size:12px; color:#5b6b82; background:#0b1120; border:1px solid #1e2c40; padding:3px 9px; border-radius:6px; white-space:nowrap; }
.barchart { display:flex; align-items:flex-end; gap:7px; height:190px; padding-top:16px; }
.bar-col { flex:1; min-width:0; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%; gap:4px; }
.bar-val { font-size:10px; color:#8ea0b8; line-height:1; }
.bar { width:100%; max-width:26px; border-radius:6px 6px 2px 2px; background:linear-gradient(180deg,#34d399,#22c55e); min-height:3px; }
.bar-col:hover .bar { background:linear-gradient(180deg,#4ade80,#34d399); }
.bar-lbl { font-size:10px; color:#5b6b82; white-space:nowrap; }
.stat-chips { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px; }
.chip { font-size:12px; color:#8ea0b8; background:#0b1120; border:1px solid #1e2c40; border-radius:6px; padding:5px 10px; }
.chip b { color:#e2e8f0; font-weight:600; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:13px; margin:16px 0; }
.card { background:#16203a; border:1px solid #1e2c40; border-radius:12px; padding:14px 16px; display:flex; flex-direction:column; gap:5px; }
.card .num { font-size:22px; font-weight:800; color:#34d399; font-family:'Sora',sans-serif; line-height:1.1; }
.card .lbl { font-size:12px; color:#8ea0b8; }
section { background:#16203a; border:1px solid #1e2c40; border-radius:14px; padding:16px 18px; margin:14px 0; min-width:0; overflow-x:auto; }
section h2 { margin:0 0 10px; font-size:15px; }
.chart-card .stat-chips, .chart-card table { min-width:0; }
table { width:100%; border-collapse:collapse; font-size:13px; }
th, td { text-align:left; padding:9px 8px; border-bottom:1px solid #1e2c40; vertical-align:middle; }
th { color:#8ea0b8; font-weight:600; font-size:11px; letter-spacing:.5px; text-transform:uppercase; }
tbody tr:hover { background:rgba(52,211,153,.04); }
.status { padding:2px 8px; border-radius:5px; font-size:11px; font-weight:700; }
.status.pendente { background:#78350f; color:#fbbf24; }
.status.pago { background:#064e3b; color:#4ade80; }
.status.entregue { background:#1e3a5f; color:#60a5fa; }
.status.cancelado { background:#7f1d1d; color:#f87171; }
.acts form, .acts form button { display:inline; }
.acts button { background:#334155; border:0; color:#e2e8f0; border-radius:6px; padding:5px 10px; cursor:pointer; font-size:12px; }
.acts button:hover { filter:brightness(1.15); }
.acts button.pago { background:#064e3b; color:#4ade80; }
.acts button.entregue { background:#1e3a5f; color:#60a5fa; }
.btn { display:inline-block; background:linear-gradient(135deg,#34d399,#60a5fa); color:#04111b; text-decoration:none; padding:10px 18px; border-radius:10px; font-weight:700; font-size:14px; border:0; cursor:pointer; }
.btn:hover { filter:brightness(1.12); }
.btn.ghost { background:transparent; border:1px solid #1e2c40; color:#e2e8f0; }
input, textarea, select { background:#0b1120; border:1px solid #2a3a52; color:#e2e8f0; border-radius:9px; padding:10px 12px; font-size:14px; width:100%; box-sizing:border-box; }
input:focus, textarea:focus, select:focus { outline:none; border-color:#34d399; box-shadow:0 0 0 3px rgba(52,211,153,.12); }
label { display:block; font-size:13px; color:#8ea0b8; margin:12px 0 4px; }
img.preview { max-width:120px; border-radius:8px; border:1px solid #1e2c40; margin-bottom:8px; }
.kicker { color:#34d399; font-size:12px; letter-spacing:2px; text-transform:uppercase; margin-bottom:4px; }
.box { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.notice { background:#0f2a22; border:1px solid #14532d; color:#4ade80; border-radius:9px; padding:10px 14px; font-size:13px; margin-bottom:14px; }
.error { background:#2a1020; border:1px solid #7f1d1d; color:#f87171; border-radius:9px; padding:10px 14px; font-size:13px; margin-bottom:14px; }
@media (max-width:1023px) {
  .sidebar { transform:translateX(-100%); transition:transform .22s ease; }
  .sidebar.open { transform:translateX(0); box-shadow:0 0 40px rgba(0,0,0,.55); }
  .wrap { margin-left:0; }
  .hamburger { display:flex; }
  .box { grid-template-columns:1fr; }
}
@media (max-width:760px) {
  .topbar { padding:10px 14px; gap:10px; flex-wrap:wrap; }
  .top-search { order:3; width:100%; }
  .top-search input { width:100%; }
  .content { padding:16px 14px 50px; }
  .charts { grid-template-columns:1fr; }
  .kpis { grid-template-columns:1fr 1fr; }
  .crumb { display:none; }
  .u-name { display:none; }
}
@media (max-width:480px) {
  .kpis { grid-template-columns:1fr; }
}
</style>
</head>
<body>
"""


def _page(user, title, body, active=""):
    role = (user or {}).get("role") or ""
    perms = set((user or {}).get("perms") or [])

    def peut(*reqs):
        return rbac.tem_perm(role, perms, *reqs)

    groups = []
    if peut("ver_dashboard"):
        groups.append(("Principal", [("/admin", "Dashboard", "dash", "grid")]))
    vendas = []
    if peut("ver_pedidos"):
        vendas.append(("/admin/pedidos", "Pedidos", "pedidos", "cart"))
    if peut("ver_itens"):
        vendas.append(("/admin/itens", "Itens", "itens", "package"))
    if peut("ver_pagamentos"):
        vendas.append(("/admin/pagamentos", "Pagamentos", "pagamentos", "wallet"))
    if vendas:
        groups.append(("Vendas", vendas))
    clientes = []
    if peut("ver_clientes"):
        clientes.append(("/admin/clientes", "Clientes", "clientes", "users"))
    if peut("ver_tickets"):
        clientes.append(("/admin/tickets", "Tickets", "tickets", "support"))
    if clientes:
        groups.append(("Clientes", clientes))
    sistema = []
    if peut("ver_grupos"):
        sistema.append(("/admin/grupos", "Grupos", "grupos", "brands"))
    if peut("ver_usuarios"):
        sistema.append(("/admin/usuarios", "Usuários", "usuarios", "shield"))
    if peut("ver_audit"):
        sistema.append(("/admin/audit", "Auditoria", "audit", "clipboard"))
    if peut("ver_config"):
        sistema.append(("/admin/config", "Configurações", "config", "gear"))
    if sistema:
        groups.append(("Sistema", sistema))
    side_links = ""
    for group_label, items in groups:
        side_links += f"<div class='side-group'>{group_label}</div>"
        for href, link_label, key, icon in items:
            active_cls = " active" if key == active else ""
            side_links += (
                f"<a class='side-item{active_cls}' href='{href}'>"
                + _icon(icon)
                + f"<span>{link_label}</span></a>"
            )
    side_foot = (
        f"<a class='side-item' href='{PORTFOLIO_URL}'>"
        + _icon("external")
        + "<span>Ver site</span></a>"
        "<a class='side-item' href='/acesso'>" + _icon("swap") + "<span>Trocar área</span></a>"
        "<a class='side-item' href='/logout'>" + _icon("logout") + "<span>Sair</span></a>"
    )

    pendentes_badge = 0
    abertos_badge = 0
    try:
        pendentes_badge = _count("pedidos", "&status=eq.pendente")
    except Exception:
        pass
    try:
        abertos_badge = _count("tickets", "&status=eq.aberto")
    except Exception:
        pass
    notif_items = ""
    if pendentes_badge and peut("ver_pagamentos"):
        notif_items += f"<a href='/admin/pagamentos'>{pendentes_badge} pedido(s) pendente(s)</a>"
    if abertos_badge and peut("ver_tickets"):
        notif_items += f"<a href='/admin/tickets'>{abertos_badge} ticket(s) aberto(s)</a>"
    if not notif_items:
        notif_items = "<div class='menu-empty'>Tudo em dia.</div>"
    total_badge = pendentes_badge + abertos_badge

    name = (user or {}).get("name") or (user or {}).get("email") or "Admin"
    email = (user or {}).get("email") or ""
    initial = html.escape((name or "A")[0].upper())

    layout = (
        "<div class='shell'>"
        "<aside class='sidebar' id='sidebar'>"
        "<div class='side-brand'><span class='side-logo'>BZ</span>"
        "<span class='brand-name'>BAP<span>ZX</span></span></div>"
        "<nav class='side-nav' id='sidenav'>" + side_links + "</nav>"
        "<div class='side-foot'>" + side_foot + "</div>"
        "</aside>"
        "<div class='wrap'>"
        "<header class='topbar'>"
        "<button class='hamburger' id='hamburger' aria-label='Menu'>" + _icon("menu") + "</button>"
        "<div class='top-title'>"
        f"<div class='crumb'>Administração / <b>{html.escape(title)}</b></div>"
        f"<h1>{html.escape(title)}</h1>"
        "</div>"
        "<div class='top-search'>" + _icon("search")
        + "<input id='globalsearch' type='search' placeholder='Buscar na página...'></div>"
        "<div class='top-actions'>"
        "<div class='dropdown'>"
        "<button class='icon-btn' data-dd='bellmenu' aria-label='Notificações'>"
        + _icon("bell")
        + (f"<span class='badge'>{total_badge}</span>" if total_badge else "")
        + "</button>"
        f"<div class='menu' id='bellmenu'>{notif_items}</div></div>"
        "<div class='dropdown'>"
        f"<button class='user-chip' data-dd='usermenu'>"
        f"<span class='user-avatar'>{initial}</span>"
        f"<span class='u-name'>{html.escape(name)}</span>"
        f"<span class='u-role'>{html.escape(rbac.cargo_label(role))}</span>"
        + _icon("chevron")
        + "</button>"
        "<div class='menu' id='usermenu'>"
        f"<div class='menu-head'><b>{html.escape(name)}</b><span>{html.escape(email)}</span>"
        f"<span style='color:#60a5fa;font-size:12px'>{html.escape(rbac.cargo_label(role))}</span></div>"
        f"<a href='{PORTFOLIO_URL}'>" + _icon("external") + "Ver site</a>"
        "<a href='/acesso'>" + _icon("swap") + "Trocar área</a>"
        "<a href='/logout' class='danger'>" + _icon("logout") + "Sair</a>"
        "</div></div></div></header>"
        f"<main class='content'>{body}</main>"
        "</div></div>"
        "<div class='scrim' id='scrim'></div>"
        "<script>"
        "var hb=document.getElementById('hamburger'),sd=document.getElementById('sidebar'),sc=document.getElementById('scrim');"
        "function closeDrawer(){if(sd){sd.classList.remove('open');}if(sc){sc.classList.remove('show');}}"
        "if(hb){hb.addEventListener('click',function(){if(sd){sd.classList.toggle('open');}if(sc){sc.classList.toggle('show');}});}"
        "if(sc){sc.addEventListener('click',closeDrawer);}"
        "var links=document.querySelectorAll('#sidenav a,.side-foot a');"
        "for(var i=0;i<links.length;i++){links[i].addEventListener('click',closeDrawer);}"
        "document.addEventListener('click',function(e){"
        "var t=e.target.closest('[data-dd]'),open=document.querySelectorAll('.menu.open');"
        "if(t){var m=document.getElementById(t.getAttribute('data-dd'));"
        "var was=m&&m.classList.contains('open');"
        "for(var i=0;i<open.length;i++){open[i].classList.remove('open');}"
        "if(m&&!was){m.classList.add('open');}return;}"
        "for(var j=0;j<open.length;j++){open[j].classList.remove('open');}"
        "});"
        "var sea=document.getElementById('globalsearch');"
        "if(sea){sea.addEventListener('input',function(){"
        "var q=sea.value.trim().toLowerCase(),tables=document.querySelectorAll('.content table');"
        "for(var i=0;i<tables.length;i++){var rows=tables[i].querySelectorAll('tr');"
        "for(var j=0;j<rows.length;j++){var tr=rows[j];"
        "if(tr.querySelector('th')){continue;}"
        "tr.style.display=(!q||tr.textContent.toLowerCase().indexOf(q)>=0)?'':'none';}}});}"
        "</script></body></html>"
    )
    return (
        LAYOUT_HEAD.replace("{title}", html.escape(title))
        + layout,
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )


def _admin_page(user, title, body, active=""):
    return _page(user, title, body, active)


def _orders_rows(orders, with_actions=True, csrf=""):
    rows = ""
    for order in sorted(orders, key=lambda o: o.get("data") or "", reverse=True):
        status = order.get("status") or "pendente"
        actions = ""
        if with_actions:
            form = (
                "<form method='post' action='/admin/marcar' style='display:inline'>"
                f"<input type='hidden' name='_csrf' value='{csrf}'>"
                "<input type='hidden' name='order_id' value='{oid}'>"
                "<input type='hidden' name='status' value='{st}'>"
                "<button class='{st}'>{lbl}</button></form>"
            )
            if status == "pendente":
                actions = form.format(oid=order.get("id"), st="pago", lbl="pago")
            if status in ("pendente", "pago"):
                actions += form.format(oid=order.get("id"), st="entregue", lbl="entregue")
        rows += (
            "<tr>"
            f"<td>{html.escape(str(order.get('data') or '-'))}</td>"
            f"<td>{html.escape(str(order.get('usuario') or '-'))}</td>"
            f"<td>{html.escape(str(order.get('char') or '-'))}</td>"
            f"<td>{html.escape(str(order.get('tc') or '-'))} RC</td>"
            f"<td>{html.escape(str(order.get('preco') or '-'))}</td>"
            f"<td>{html.escape(str(order.get('mundo') or '-'))}</td>"
            f"<td>{html.escape(str(order.get('email') or '-'))}</td>"
            f"<td><span class='status {html.escape(status)}'>{html.escape(status)}</span></td>"
            f"<td class='acts'>{actions}</td>"
            "</tr>"
        )
    if not rows:
        rows = "<tr><td colspan='9' class='empty' style='color:#64748b;padding:18px;text-align:center'>Nenhum pedido encontrado.</td></tr>"
    return rows
# --------------------------------------------------------------------------
# ROTAS DO PAINEL
# --------------------------------------------------------------------------

def _metrics(orders):
    faturado = 0.0
    por_dia = {}
    clientes = set()
    pagos = 0
    for order in orders:
        if (order.get("status") or "pendente") == "pago":
            faturado += _parse_brl(order.get("preco"))
            pagos += 1
        dia = (order.get("data") or "")[:10]
        if dia:
            por_dia[dia] = por_dia.get(dia, 0) + 1
        chat = order.get("chat_id")
        if chat is not None:
            clientes.add(chat)
    return faturado, por_dia, clientes, pagos


@bp.route("/admin", methods=["GET"])
def admin_dashboard():
    user = _require_perm("ver_dashboard")
    if not user:
        return redirect("/login")
    if _rate_limited("admin_get", _RATE_LIMIT_ADMIN_PER_MIN):
        return "Muitas requisicoes. Aguarde um instante.", 429

    orders = _fetch("pedidos", order="data.asc")
    faturado, por_dia, clientes, pagos = _metrics(orders)

    desde = _iso_days_ago(7)
    visitas7d = _count_since("visitas", desde)
    desde1 = _iso_days_ago(1)
    visitas1d = _count_since("visitas", desde1)
    visitas_total = _count("visitas")

    desde14 = _iso_days_ago(14)
    recente = _fetch(
        "visitas",
        select="pagina",
        query=f"criado_em=gte.{desde14}",
        range_="0-4999",
    )
    contagem = {}
    for vis in recente:
        pagina = vis.get("pagina") or "/"
        contagem[pagina] = contagem.get(pagina, 0) + 1
    top = sorted(contagem.items(), key=lambda kv: kv[1], reverse=True)[:10]
    top_rows = "".join(
        f"<tr><td>{html.escape(str(pagina))}</td><td>{count}</td></tr>"
        for pagina, count in top
    ) or "<tr><td colspan='2' style='color:#64748b;text-align:center'>Sem visitas ainda</td></tr>"

    audit = _fetch("audit_log", order="criado_em.desc", range_="0-9")
    audit_rows = "".join(
        f"<tr><td>{html.escape(str(a.get('criado_em') or '-'))}</td>"
        f"<td>{html.escape(str(a.get('email') or '-'))}</td>"
        f"<td>{html.escape(str(a.get('acao') or '-'))}</td>"
        f"<td>{html.escape(str(a.get('detalhes') or '-'))}</td></tr>"
        for a in audit
    ) or "<tr><td colspan='4' style='color:#64748b;text-align:center'>Sem auditoria ainda</td></tr>"

    # grafico de pedidos por dia (14 dias)
    dias = []
    base = datetime.now().date()
    for offset in range(13, -1, -1):
        dia = base - timedelta(days=offset)
        dias.append((dia.isoformat(), por_dia.get(dia.isoformat(), 0)))
    max_dia = max((c for _, c in dias), default=0) or 1

    sub = "<p class='page-sub'>Visão geral do sistema e indicadores recentes.</p>"

    pode_ver_finan = rbac.tem_perm(user["role"], user["perms"], "ver_pagamentos")
    kpis = "<div class='kpis'>"
    if pode_ver_finan:
        kpis += (
            "<div class='kpi'><div class='k-top'><span class='k-lbl'>Faturamento</span>"
            "<span class='k-ico'>" + _icon("dollar") + "</span></div>"
            f"<div class='k-num'>{_fmt_brl(faturado)}</div>"
            "<div class='k-sub'>Total confirmado</div></div>"
            "<div class='kpi'><div class='k-top'><span class='k-lbl'>Pagamentos</span>"
            "<span class='k-ico'>" + _icon("checks") + "</span></div>"
            f"<div class='k-num'>{pagos}</div>"
            "<div class='k-sub'>Pedidos pagos</div></div>"
        )
    kpis = (
        kpis
        + "<div class='kpi'><div class='k-top'><span class='k-lbl'>Pedidos</span>"
        "<span class='k-ico'>" + _icon("cart") + "</span></div>"
        f"<div class='k-num'>{len(orders)}</div>"
        "<div class='k-sub'>Total registrado</div></div>"
        "<div class='kpi'><div class='k-top'><span class='k-lbl'>Clientes</span>"
        "<span class='k-ico'>" + _icon("users") + "</span></div>"
        f"<div class='k-num'>{len(clientes)}</div>"
        "<div class='k-sub'>Contas únicas</div></div>"
        "</div>"
    )

    d0 = dias[0][0] if dias else ""
    d1 = dias[-1][0] if dias else ""
    periodo = f"{d0[8:10]}/{d0[5:7]} a {d1[8:10]}/{d1[5:7]}" if d0 and d1 else "14 dias"
    colunas = ""
    for iso, c in dias:
        pct = int(c / max_dia * 100) if c else 3
        colunas += (
            f"<div class='bar-col' title='{iso} — {c} pedido(s)'>"
            f"<span class='bar-val'>{c}</span>"
            f"<span class='bar' style='height:{pct}%'></span>"
            f"<span class='bar-lbl'>{iso[8:10]}</span></div>"
        )
    chart = (
        "<div class='chart-card'>"
        "<div class='chart-head'><h2>Pedidos nos últimos 14 dias</h2>"
        f"<span class='chart-period'>{periodo}</span></div>"
        f"<div class='barchart'>{colunas}</div></div>"
    )

    chips = (
        "<div class='stat-chips'>"
        f"<span class='chip'>7 dias <b>{visitas7d}</b></span>"
        f"<span class='chip'>Hoje <b>{visitas1d}</b></span>"
        f"<span class='chip'>Total <b>{visitas_total}</b></span></div>"
    )
    pages = (
        "<div class='chart-card'>"
        "<div class='chart-head'><h2>Páginas mais visitadas</h2></div>"
        + chips
        + "<table><tr><th>Página</th><th>Visitas</th></tr>" + top_rows + "</table></div>"
    )

    body = sub + kpis + f"<div class='charts'>{chart}{pages}</div>"
    if rbac.tem_perm(user["role"], user["perms"], "ver_audit"):
        body += (
            "<section><h2>Últimas ações do admin</h2><table>"
            "<tr><th>Quando</th><th>Quem</th><th>Ação</th><th>Detalhes</th></tr>"
            + audit_rows
            + "</table></section>"
        )
    pode_marcar = rbac.tem_qualquer_perm(user["role"], user["perms"], "marcar_pagamento", "marcar_entrega")
    body += (
        "<section><h2>Últimos pedidos</h2><table>"
        "<tr><th>Quando</th><th>Cliente</th><th>Char</th><th>Qtd</th>"
        "<th>Valor</th><th>Mundo</th><th>E-mail</th><th>Status</th><th>Ações</th></tr>"
        + _orders_rows(orders[:10], with_actions=pode_marcar, csrf=_csrf_token())
        + "</table></section>"
    )
    return _admin_page(user, "Dashboard", body, "dash")


@bp.route("/admin/pedidos", methods=["GET"])
def admin_pedidos():
    user = _require_perm("ver_pedidos")
    if not user:
        return redirect("/login")
    orders = _fetch("pedidos", order="data.asc")
    pode_marcar = rbac.tem_qualquer_perm(user["role"], user["perms"], "marcar_pagamento", "marcar_entrega")
    body = f"<div class='cards'><div class='card'><div class='num'>{len(orders)}</div><div class='lbl'>Pedidos</div></div></div>"
    body += (
        "<section><h2>Todos os pedidos</h2><table>"
        "<tr><th>Quando</th><th>Cliente</th><th>Char</th><th>Qtd</th>"
        "<th>Valor</th><th>Mundo</th><th>E-mail</th><th>Status</th><th>Ações</th></tr>"
        + _orders_rows(orders, with_actions=pode_marcar, csrf=_csrf_token())
        + "</table></section>"
    )
    return _admin_page(user, "Pedidos", body, "pedidos")


def _clientes_rows(profiles, orders):
    pedidos_por_email = {}
    for order in orders:
        email = (order.get("email") or "").strip().lower()
        if not email:
            continue
        item = pedidos_por_email.setdefault(email, {"pedidos": 0, "gasto": 0.0})
        item["pedidos"] += 1
        if (order.get("status") or "") in ("pago", "entregue"):
            item["gasto"] += _parse_brl(order.get("preco"))
    por_email = {p.get("email", "").strip().lower(): p for p in profiles}
    emails = sorted(set(list(por_email) + list(pedidos_por_email)))
    rows = ""
    for email in emails:
        profile = por_email.get(email) or {}
        stats = pedidos_por_email.get(email, {})
        bloqueado = "<span class='status cancelado'>bloqueado</span>" if profile.get("bloqueado") else ""
        role = html.escape(str(profile.get("role") or "cliente"))
        nome = html.escape(str(profile.get("name") or email))
        rows += (
            "<tr>"
            f"<td>{html.escape(email)}</td>"
            f"<td>{nome}</td>"
            f"<td>{role}</td>"
            f"<td>{stats.get('pedidos', 0)}</td>"
            f"<td>{_fmt_brl(stats.get('gasto', 0))}</td>"
            f"<td>{bloqueado}</td>"
            f"<td class='acts'><a class='btn ghost' style='padding:5px 10px;font-size:12px' "
            f"href='/admin/clientes/{html.escape(email)}'>Ver</a></td>"
            "</tr>"
        )
    if not rows:
        rows = "<tr><td colspan='7' class='empty' style='color:#64748b;padding:18px;text-align:center'>Nenhum cliente encontrado.</td></tr>"
    return rows


@bp.route("/admin/clientes", methods=["GET"])
def admin_clientes():
    user = _require_perm("ver_clientes")
    if not user:
        return redirect("/login")
    profiles = _fetch("profiles", order="email.asc")
    orders = _fetch("pedidos", order="data.asc")
    body = f"<div class='cards'><div class='card'><div class='num'>{len(profiles)}</div><div class='lbl'>Perfis</div></div></div>"
    body += (
        "<section><h2>Clientes</h2><table>"
        "<tr><th>E-mail</th><th>Nome</th><th>Papel</th><th>Pedidos</th><th>Gasto total</th><th>Status</th><th></th></tr>"
        + _clientes_rows(profiles, orders)
        + "</table></section>"
    )
    return _admin_page(user, "Clientes", body, "clientes")


@bp.route("/admin/clientes/<email>", methods=["GET"])
def admin_cliente_detalhe(email):
    user = _require_perm("ver_clientes")
    if not user:
        return redirect("/login")
    email_decoded = (email or "").lower()
    try:
        from urllib.parse import unquote
        email_decoded = unquote(email_decoded)
    except Exception:
        pass
    profiles = _fetch("profiles", query=f"email=eq.{email_decoded}")
    profile = profiles[0] if profiles else {}
    orders = _fetch("pedidos", order="data.desc", range_="0-499")
    mine = [o for o in orders if (o.get("email") or "").strip().lower() == email_decoded]
    rows = _orders_rows(mine, with_actions=True, csrf=_csrf_token())
    status_badge = "<span class='status cancelado'>bloqueado</span>" if profile.get("bloqueado") else "<span class='status pago'>ativo</span>"
    form = (
        "<section><h2>Dados do perfil</h2>"
        f"<form method='post' action='/admin/clientes/{html.escape(email_decoded)}/editar'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        f"<label>Nome</label><input name='name' value='{html.escape(str(profile.get('name') or ''))}'>"
        f"<label>Personagem</label><input name='personagem' value='{html.escape(str(profile.get('personagem') or ''))}'>"
        f"<label>Mundo</label><input name='mundo' value='{html.escape(str(profile.get('mundo') or ''))}'>"
        "<label>Papel</label>"
        f"<select name='role'><option value='cliente' {'selected' if not profile.get('role') or profile.get('role') == 'cliente' else ''}>cliente</option>"
        f"<option value='admin' {'selected' if profile.get('role') == 'admin' else ''}>admin</option></select>"
        f"<p style='margin-top:14px'><button class='btn' type='submit'>Salvar</button> "
        f"<a class='btn ghost' href='/admin/clientes'>Voltar</a></p>"
        "</form></section>"
    )
    acoes = ""
    if profile.get("bloqueado"):
        acoes = (
            "<form method='post' action='/admin/clientes/{e}/bloquear' style='display:inline'>"
            f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
            "<button class='btn' type='submit'>Desbloquear</button></form>"
        ).format(e=html.escape(email_decoded))
    else:
        acoes = (
            "<form method='post' action='/admin/clientes/{e}/bloquear' style='display:inline'>"
            f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
            "<button style='background:#7f1d1d;border:0;color:#fca5a5;border-radius:6px;padding:6px 12px;cursor:pointer'>Bloquear</button></form>"
        ).format(e=html.escape(email_decoded))
    body = (
        f"<div class='cards'><div class='card'><div class='num'>{email_decoded}</div><div class='lbl'>E-mail</div></div>"
        f"<div class='card'><div class='num'>{status_badge}</div><div class='lbl'>Status</div></div></div>"
        + form
        + "<section><h2>Ações</h2>" + acoes + "</section>"
        + "<section><h2>Pedidos do cliente</h2><table>"
        + "<tr><th>Quando</th><th>Cliente</th><th>Char</th><th>Qtd</th>"
        "<th>Valor</th><th>Mundo</th><th>E-mail</th><th>Status</th><th>Ações</th></tr>"
        + rows
        + "</table></section>"
    )
    return _admin_page(user, "Cliente", body, "clientes")


@bp.route("/admin/clientes/<email>/editar", methods=["POST"])
def admin_cliente_editar(email):
    user = _require_perm("gerenciar_clientes")
    if not user:
        return "Acesso restrito.", 403
    if not _csrf_ok():
        return "Requisição inválida (CSRF).", 403
    from urllib.parse import unquote
    email_decoded = unquote(email).lower()
    payload = {
        "name": (request.form.get("name") or "").strip()[:200],
        "personagem": (request.form.get("personagem") or "").strip()[:100],
        "mundo": (request.form.get("mundo") or "").strip()[:100],
        "role": (request.form.get("role") or "cliente")[:20],
    }
    try:
        requests.post(
            f"{SUPA_URL}/rest/v1/profiles?on_conflict=email",
            headers={**_headers(), "Prefer": "resolution=merge-duplicates"},
            json={"email": email_decoded, **payload},
            timeout=15,
        )
        _audit(user, "cliente_editar", email_decoded)
    except Exception as exc:
        return f"Falha: {exc}", 500
    return redirect(f"/admin/clientes/{email_decoded}")


@bp.route("/admin/pagamentos", methods=["GET"])
def admin_pagamentos():
    user = _require_perm("ver_pagamentos")
    if not user:
        return redirect("/login")
    orders = _fetch("pedidos", order="data.desc", range_="0-999")
    pendentes = [o for o in orders if (o.get("status") or "") == "pendente"]
    pagos = [o for o in orders if (o.get("status") or "") == "pago"]
    entregues = [o for o in orders if (o.get("status") or "") == "entregue"]
    cancelados = [o for o in orders if (o.get("status") or "") in ("cancelado", "cancelada")]
    soma = lambda lista: sum(_parse_brl(o.get("preco")) for o in lista)

    def rows(lista, with_ts=False):
        out = ""
        for o in lista:
            email = (o.get("email") or "-")
            ts = html.escape(str(o.get("pix_confirmado_em") or o.get("data_pagamento") or ""))[:19] if with_ts else ""
            out += (
                "<tr>"
                f"<td>{html.escape(str(o.get('id') or '-'))}</td>"
                f"<td>{html.escape(str(o.get('data') or ''))[:16]}</td>"
                f"<td>{html.escape(str(o.get('usuario') or '-'))}</td>"
                f"<td>{html.escape(str(o.get('tc') or '-'))} RC</td>"
                f"<td>{html.escape(str(o.get('preco') or '-'))}</td>"
                f"<td>{html.escape(email)}</td>"
                f"<td><span class='status {html.escape(o.get('status') or 'pendente')}'>{html.escape(o.get('status') or 'pendente')}</span></td>"
                f"{f'<td>{ts}</td>' if with_ts else ''}"
                "</tr>"
            )
        return out or "<tr><td colspan='8' class='empty' style='color:#64748b;padding:18px;text-align:center'>Sem pagamentos.</td></tr>"

    cards = (
        "<div class='cards'>"
        "<div class='card'><div class='num'>{p}</div><div class='lbl'>Pendentes</div></div>"
        "<div class='card'><div class='num'>{pg}</div><div class='lbl'>Aprovados</div></div>"
        "<div class='card'><div class='num'>{e}</div><div class='lbl'>Entregues</div></div>"
        "<div class='card'><div class='num'>{c}</div><div class='lbl'>Cancelados</div></div>"
        "<div class='card'><div class='num'>{v}</div><div class='lbl'>Faturado</div></div>"
        "</div>"
    ).format(
        p=len(pendentes),
        pg=len(pagos),
        e=len(entregues),
        c=len(cancelados),
        v=_fmt_brl(soma(pagos) + soma(entregues)),
    )
    tabs = (
        "<section><h2>Pendentes (aguardando confirmação)</h2><table>"
        "<tr><th>Id</th><th>Data</th><th>Cliente</th><th>Qtd</th><th>Valor</th><th>E-mail</th><th>Status</th></tr>"
        + rows(pendentes)
        + "</table></section>"
        "<section><h2>Aprovados</h2><table>"
        "<tr><th>Id</th><th>Data</th><th>Cliente</th><th>Qtd</th><th>Valor</th><th>E-mail</th><th>Status</th><th>Confirmado em</th></tr>"
        + rows(pagos, with_ts=True)
        + "</table></section>"
        "<section><h2>Entregues</h2><table>"
        "<tr><th>Id</th><th>Data</th><th>Cliente</th><th>Qtd</th><th>Valor</th><th>E-mail</th><th>Status</th></tr>"
        + rows(entregues)
        + "</table></section>"
        "<section><h2>Cancelados</h2><table>"
        "<tr><th>Id</th><th>Data</th><th>Cliente</th><th>Qtd</th><th>Valor</th><th>E-mail</th><th>Status</th></tr>"
        + rows(cancelados)
        + "</table></section>"
    )
    return _admin_page(user, "Pagamentos", cards + tabs, "pagamentos")


@bp.route("/admin/clientes/<email>/bloquear", methods=["POST"])
def admin_cliente_bloquear(email):
    user = _require_perm("gerenciar_clientes")
    if not user:
        return "Acesso restrito.", 403
    if not _csrf_ok():
        return "Requisição inválida (CSRF).", 403
    from urllib.parse import unquote
    email_decoded = unquote(email).lower()
    profiles = _fetch("profiles", select="bloqueado", query=f"email=eq.{email_decoded}")
    novo = not (profiles[0].get("bloqueado") if profiles else False)
    try:
        requests.post(
            f"{SUPA_URL}/rest/v1/profiles?on_conflict=email",
            headers={**_headers(), "Prefer": "resolution=merge-duplicates"},
            json={"email": email_decoded, "bloqueado": novo},
            timeout=15,
        )
        _audit(user, "cliente_bloquear" if novo else "cliente_desbloquear", email_decoded)
    except Exception as exc:
        return f"Falha: {exc}", 500
    return redirect(f"/admin/clientes/{email_decoded}")


@bp.route("/admin/marcar", methods=["POST"])
def admin_marcar():
    user = _require_any_perm("marcar_pagamento", "marcar_entrega")
    if not user:
        return "Acesso restrito.", 403
    if not _csrf_ok():
        return "Requisição inválida (CSRF).", 403
    if _rate_limited("admin_post", _RATE_LIMIT_ADMIN_PER_MIN):
        return "Muitas requisicoes. Aguarde um instante.", 429
    order_id_text = (request.form.get("order_id") or "").strip()
    status = (request.form.get("status") or "").strip()
    if not order_id_text.isdigit() or status not in ("pago", "entregue"):
        return "Parâmetros inválidos.", 400
    if status == "pago" and not rbac.tem_perm(user["cargo"], user["perms"], "marcar_pagamento"):
        return "Acesso restrito.", 403
    if status == "entregue" and not rbac.tem_perm(user["cargo"], user["perms"], "marcar_entrega"):
        return "Acesso restrito.", 403
    now = datetime.utcnow().isoformat()
    ts_field = "pix_confirmado_em" if status == "pago" else "entregue_em"
    try:
        requests.patch(
            f"{SUPA_URL}/rest/v1/pedidos?id=eq.{int(order_id_text)}",
            headers=_headers(),
            json={"status": status, ts_field: now},
timeout=15,
        )
        _audit(user, f"marcar_pedido_{status}", f"pedido {order_id_text}")
    except Exception as error:
        return f"Falha: {error}", 500
    return redirect("/admin/pedidos")


def _ticket_status_badge(status):
    return f"<span class='status {html.escape(status or 'aberto')}'>{html.escape(status or 'aberto')}</span>"


def _tickets_rows(tickets, with_ak=False, csrf=""):
    rows = ""
    for t in tickets:
        rows += (
            "<tr>"
            f"<td>{html.escape(str(t.get('id') or '-'))}</td>"
            f"<td>{html.escape(str(t.get('criado_em') or ''))[:16]}</td>"
            f"<td>{html.escape(str(t.get('email') or '-'))}</td>"
            f"<td>{html.escape(str(t.get('assunto') or '-'))}</td>"
            f"<td>{_ticket_status_badge(t.get('status'))}</td>"
            f"<td>{html.escape(str(t.get('prioridade') or 'normal'))}</td>"
            f"<td class='acts'><a class='btn ghost' style='padding:5px 10px;font-size:12px' "
            f"href='/admin/tickets/{t.get('id')}'>Abrir</a></td>"
            "</tr>"
        )
    return rows or "<tr><td colspan='7' class='empty' style='color:#64748b;padding:18px;text-align:center'>Nenhum ticket.</td></tr>"


@bp.route("/admin/tickets", methods=["GET"])
def admin_tickets():
    user = _require_perm("ver_tickets")
    if not user:
        return redirect("/login")
    tickets = []
    try:
        tickets = _fetch("tickets", order="criado_em.desc", range_="0-499")
    except Exception as error:
        print(f"[painel] tickets indisponível: {error}")
    abertos = [t for t in tickets if (t.get("status") or "aberto") == "aberto"]
    respondidos = [t for t in tickets if (t.get("status") or "") == "respondido"]
    encerrados = [t for t in tickets if (t.get("status") or "") == "encerrado"]
    cards = (
        "<div class='cards'>"
        "<div class='card'><div class='num'>{a}</div><div class='lbl'>Abertos</div></div>"
        "<div class='card'><div class='num'>{r}</div><div class='lbl'>Respondidos</div></div>"
        "<div class='card'><div class='num'>{e}</div><div class='lbl'>Encerrados</div></div>"
        "</div>"
    ).format(a=len(abertos), r=len(respondidos), e=len(encerrados))
    body = cards + (
        "<section><h2>Todos os tickets</h2><table>"
        "<tr><th>Id</th><th>Abertura</th><th>Cliente</th><th>Assunto</th><th>Status</th><th>Prioridade</th><th></th></tr>"
        + _tickets_rows(tickets)
        + "</table></section>"
    )
    return _admin_page(user, "Tickets", body, "tickets")


@bp.route("/admin/tickets/<int:ticket_id>", methods=["GET", "POST"])
def admin_ticket_detalhe(ticket_id):
    user = _require_perm("ver_tickets")
    if not user:
        return redirect("/login")
    tickets = _fetch("tickets", query=f"id=eq.{ticket_id}")
    if not tickets:
        return "Ticket não encontrado.", 404
    ticket = tickets[0]

    if request.method == "POST":
        if not _csrf_ok():
            return "Requisição inválida (CSRF).", 403
        acao = (request.form.get("acao") or "").strip()
        if acao == "responder":
            if not rbac.tem_perm(user["cargo"], user["perms"], "responder_tickets"):
                return "Acesso restrito.", 403
            resposta = (request.form.get("resposta") or "").strip()[:3000]
            if resposta:
                json_payload = {
                    "status": "respondido",
                    "resposta": resposta,
                    "respondido_em": datetime.utcnow().isoformat(),
                    "respondido_por": user["email"],
                }
                try:
                    requests.patch(
                        f"{SUPA_URL}/rest/v1/tickets?id=eq.{ticket_id}",
                        headers=_headers(),
                        json=json_payload,
                        timeout=15,
                    )
                    _audit(user, "ticket_responder", f"ticket {ticket_id}")
                except Exception as exc:
                    return f"Falha: {exc}", 500
        elif acao == "encerrar":
            if not rbac.tem_perm(user["cargo"], user["perms"], "encerrar_tickets"):
                return "Acesso restrito.", 403
            try:
                requests.patch(
                    f"{SUPA_URL}/rest/v1/tickets?id=eq.{ticket_id}",
                    headers=_headers(),
                    json={"status": "encerrado"},
                    timeout=15,
                )
            except Exception as exc:
                return f"Falha: {exc}", 500
        elif acao == "prioridade":
            prioridade = (request.form.get("prioridade") or "normal")[:20]
            try:
                requests.patch(
                    f"{SUPA_URL}/rest/v1/tickets?id=eq.{ticket_id}",
                    headers=_headers(),
                    json={"prioridade": prioridade},
                    timeout=15,
                )
            except Exception as exc:
                return f"Falha: {exc}", 500
        return redirect(f"/admin/tickets/{ticket_id}")

    top = (f"<a class='btn ghost' style='padding:6px 12px;font-size:12px' href='/admin/tickets'>Voltar</a>")
    body = (
        "<section><h2>Ticket #{id} · {status}</h2>"
        "<p style='color:#8ea0b8;font-size:13px'>"
        "De: <b>{email}</b> · Abertura: {criado} · "
        "Assunto: <b>{assunto}</b></p>"
        "<p style='color:#e2e8f0'>{mensagem}</p>"
        "{resposta_html}"
        "{responder_html}"
        "{acoes_html}"
        "</section>"
    ).format(
        id=ticket.get("id"),
        status=_ticket_status_badge(ticket.get("status")),
        email=html.escape(str(ticket.get("email") or "-")),
        criado=html.escape(str(ticket.get("criado_em") or ""))[:19],
        assunto=html.escape(str(ticket.get("assunto") or "-")),
        mensagem=html.escape(str(ticket.get("mensagem") or "-")),
        resposta_html=(
            "<p style='background:#0f2a22;border:1px solid #14532d;color:#4ade80;border-radius:9px;padding:10px 14px'>"
            f"<b>Resposta:</b> {html.escape(str(ticket.get('resposta') or ''))}</p>"
            if ticket.get("resposta")
            else ""
        ),
        responder_html=(
            "<section><h2>Responder</h2>"
            "<form method='post'>"
            f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
            "<input type='hidden' name='acao' value='responder'>"
            "<textarea name='resposta' rows='4' placeholder='Escreva a resposta do suporte...'></textarea>"
            "<p style='margin-top:14px'><button class='btn' type='submit'>Enviar resposta</button></p>"
            "</form></section>"
            if rbac.tem_perm(user["cargo"], user["perms"], "responder_tickets")
            else ""
        ),
        acoes_html=(
            "<section><h2>Ações</h2>"
            "<form method='post' action='' style='display:inline'>"
            f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
            "<input type='hidden' name='acao' value='prioridade'>"
            "<select name='prioridade'>"
            f"<option value='normal' {'selected' if (ticket.get('prioridade') or '') in ('', 'normal') else ''}>normal</option>"
            f"<option value='alta' {'selected' if ticket.get('prioridade') == 'alta' else ''}>alta</option>"
            "<option value='urgente' >urgente</option>"
            "</select>"
            "<button class='btn ghost' type='submit'>Definir prioridade</button></form>"
            "<form method='post' action='' style='display:inline'>"
            f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
            "<input type='hidden' name='acao' value='encerrar'>"
            "<button style='background:#7f1d1d;border:0;color:#fca5a5;border-radius:6px;padding:6px 12px;cursor:pointer' type='submit'>Encerrar ticket</button></form>"
            "</section>"
            if rbac.tem_perm(user["cargo"], user["perms"], "encerrar_tickets")
            else ""
        ),
    )
    return _admin_page(user, "Ticket", top + body, "tickets")


@bp.route("/admin/tickets/<int:ticket_id>/excluir", methods=["POST"])
def admin_ticket_excluir(ticket_id):
    user = _require_perm("excluir_tickets")
    if not user:
        return "Acesso restrito.", 403
    if not _csrf_ok():
        return "Requisição inválida (CSRF).", 403
    try:
        requests.delete(
            f"{SUPA_URL}/rest/v1/tickets?id=eq.{ticket_id}",
            headers=_headers(),
            timeout=15,
        )
        _audit(user, "ticket_excluir", str(ticket_id))
    except Exception as exc:
        return f"Falha: {exc}", 500
    return redirect("/admin/tickets")


def _item_card(item):
    image = html.escape(item.get("imagem") or "")
    img = f"<img src='{image}' alt='' class='preview' onerror=\"this.style.display='none'\">" if image else ""
    ativo = item.get("ativo")
    preco = html.escape(item.get("preco") or "R$ --")
    return (
        f"<div class='card'>"
        f"{img}"
        f"<div class='kicker'>{html.escape(item.get('categoria') or 'geral')} · "
        f"{'publicado' if ativo else 'rascunho'}</div>"
        f"<h3 style='margin:6px 0 2px'>{html.escape(item.get('nome') or '-')}</h3>"
        f"<div class='num' style='font-size:18px'>{preco}</div>"
f"<p style='color:#8ea0b8;font-size:13px;margin:8px 0'>{html.escape(item.get('descricao') or '-')}</p>"
        f"<div class='acts' style='margin-top:10px;display:flex;gap:6px;flex-wrap:wrap'>"
        f"<a class='btn ghost' style='padding:6px 12px;font-size:12px' href='/admin/itens/{item.get('id')}'>Editar</a>"
        f"<form method='post' action='/admin/itens/{item.get('id')}/toggle' style='display:inline'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        f"<button style='background:#334155;border:0;color:#e2e8f0;border-radius:6px;padding:6px 12px;cursor:pointer;font-size:12px'>"
        f"{'Ocultar' if ativo else 'Publicar'}</button></form>"
        f"<form method='post' action='/admin/itens/{item.get('id')}/excluir' style='display:inline'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        f"<button style='background:#7f1d1d;border:0;color:#fca5a5;border-radius:6px;padding:6px 12px;cursor:pointer;font-size:12px'>Excluir</button></form>"
        f"</div></div>"
    )


@bp.route("/admin/itens", methods=["GET"])
def admin_itens():
    user = _require_perm("ver_itens")
    if not user:
        return redirect("/login")
    itens = _fetch("itens", order="ativo.desc,ordem.asc")
    cards = "".join(_item_card(i) for i in itens) or (
        "<p style='color:#64748b'>Nenhum item cadastrado ainda.</p>"
    )
    form = (
        "<section><h2>Novo item</h2>"
        "<form method='post' action='/admin/itens/novo' enctype='multipart/form-data'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        "<label>Nome</label><input name='nome' required>"
        "<label>Preço</label><input name='preco' placeholder='R$ 20,00'>"
        "<label>Categoria</label><input name='categoria' placeholder='geral'>"
        "<label>Descrição</label><textarea name='descricao' rows='3'></textarea>"
        "<label>Imagem</label><input type='file' name='imagem' accept='image/png,image/jpeg,image/webp,image/gif'>"
        "<label>Publicado</label>"
        "<select name='ativo'><option value='1'>Sim</option><option value='0'>Não (rascunho)</option></select>"
        "<p style='margin-top:14px'><button class='btn' type='submit'>Criar item</button></p>"
        "</form></section>"
    )
    order_form = (
        "<section><h2>Ordem de exibição</h2>"
        "<p style='color:#8ea0b8;font-size:13px'>A ordem é controlada pela coluna 'ordem' "
        "(menor aparece primeiro). Los itens com 'ordem' igual seguem por nome.</p>"
        "</section>"
    )
    body = (
        "<div class='kicker'>Loja do site</div>"
        "<h2 style='margin:6px 0 14px'>Itens à venda</h2>"
        + order_form
        + f"<div class='cards'>{cards}</div>"
        + form
    )
    return _admin_page(user, "Itens", body, "itens")


@bp.route("/admin/itens/novo", methods=["POST"])
def admin_item_novo():
    user = _require_perm("gerenciar_itens")
    if not user:
        return "Acesso restrito.", 403
    if not _csrf_ok():
        return "Requisição inválida (CSRF).", 403
    nome = (request.form.get("nome") or "").strip()[:200]
    if not nome:
        return "Nome obrigatório.", 400
    preco = (request.form.get("preco") or "").strip()[:60]
    categoria = (request.form.get("categoria") or "geral").strip()[:60]
    descricao = (request.form.get("descricao") or "").strip()[:2000]
    ativo = request.form.get("ativo") == "1"

    imagem, error = _storage_upload(request.files.get("imagem")) if request.files.get("imagem") else ("", None)
    payload = {
        "nome": nome,
        "preco": preco,
        "categoria": categoria,
        "descricao": descricao,
        "ativo": ativo,
        "imagem": imagem,
    }
    try:
        response = requests.post(
            f"{SUPA_URL}/rest/v1/itens",
            headers={**_headers(), "Prefer": "return=representation"},
            json=payload,
            timeout=15,
        )
        if response.status_code not in (200, 201):
            return f"Falha ao criar ({response.status_code}): {response.text[:200]}", 400
        _audit(user, "item_criar", f"{nome} " + (f"| erro imagem: {error}" if error else ""))
    except Exception as exc:
        return f"Falha: {exc}", 500
    return redirect("/admin/itens")


@bp.route("/admin/itens/<item_id>", methods=["GET", "POST"])
def admin_item_editar(item_id):
    user = _require_perm("gerenciar_itens")
    if not user:
        return redirect("/login")
    itens = _fetch("itens", select="*", query=f"id=eq.{item_id}")
    if not itens:
        return "Item não encontrado.", 404
    item = itens[0]

    if request.method == "POST":
        if not _csrf_ok():
            return "Requisição inválida (CSRF).", 403
        payload = {
            "nome": (request.form.get("nome") or "").strip()[:200],
            "preco": (request.form.get("preco") or "").strip()[:60],
            "categoria": (request.form.get("categoria") or "geral").strip()[:60],
            "descricao": (request.form.get("descricao") or "").strip()[:2000],
            "ativo": request.form.get("ativo") == "1",
        }
        if request.files.get("imagem"):
            imagem, error = _storage_upload(request.files.get("imagem"))
            if imagem:
                payload["imagem"] = imagem
        try:
            response = requests.patch(
                f"{SUPA_URL}/rest/v1/itens?id=eq.{item_id}",
                headers=_headers(),
                json=payload,
                timeout=15,
            )
            if response.status_code not in (200, 204):
                return f"Falha ao atualizar ({response.status_code}): {response.text[:200]}", 400
            _audit(user, "item_editar", payload.get("nome", ""))
        except Exception as exc:
            return f"Falha: {exc}", 500
        return redirect("/admin/itens")

    image_html = (
        f"<img src='{html.escape(item.get('imagem') or '')}' alt='' class='preview' "
        f"onerror=\"this.style.display='none'\">"
        if item.get("imagem")
        else ""
    )
    ativo_option = 'checked' if item.get("ativo") else ''
    form = (
        f"<section><h2>Editar item</h2>"
        f"{image_html}"
        f"<form method='post' enctype='multipart/form-data'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        f"<label>Nome</label><input name='nome' required value='{html.escape(item.get('nome') or '')}'>"
        f"<label>Preço</label><input name='preco' value='{html.escape(item.get('preco') or '')}'>"
        f"<label>Categoria</label><input name='categoria' value='{html.escape(item.get('categoria') or '')}'>"
        f"<label>Descrição</label><textarea name='descricao' rows='3'>{html.escape(item.get('descricao') or '')}</textarea>"
        f"<label>Nova imagem (opcional)</label><input type='file' name='imagem' accept='image/png,image/jpeg,image/webp,image/gif'>"
        f"<label>Publicado</label>"
        f"<select name='ativo'><option value='1' {'selected' if item.get('ativo') else ''}>Sim</option>"
        f"<option value='0' {'' if item.get('ativo') else 'selected'}>Não (rascunho)</option></select>"
        f"<p style='margin-top:14px'><button class='btn' type='submit'>Salvar</button> "
        f"<a class='btn ghost' href='/admin/itens'>Voltar</a></p>"
        f"</form></section>"
    )
    return _admin_page(user, "Editar item", form, "itens")


@bp.route("/admin/itens/<item_id>/toggle", methods=["POST"])
def admin_item_toggle(item_id):
    user = _require_perm("gerenciar_itens")
    if not user:
        return "Acesso restrito.", 403
    if not _csrf_ok():
        return "Requisição inválida (CSRF).", 403
    itens = _fetch("itens", select="ativo", query=f"id=eq.{item_id}")
    if itens:
        novo = not itens[0].get("ativo")
    else:
        novo = False
    try:
        requests.patch(
            f"{SUPA_URL}/rest/v1/itens?id=eq.{item_id}",
            headers=_headers(),
            json={"ativo": novo},
            timeout=15,
        )
        _audit(user, "item_toggle", f"{item_id} -> {'publicar' if novo else 'ocultar'}")
    except Exception as exc:
        return f"Falha: {exc}", 500
    return redirect("/admin/itens")


@bp.route("/admin/itens/<item_id>/excluir", methods=["POST"])
def admin_item_excluir(item_id):
    user = _require_perm("gerenciar_itens")
    if not user:
        return "Acesso restrito.", 403
    if not _csrf_ok():
        return "Requisição inválida (CSRF).", 403
    try:
        requests.delete(
            f"{SUPA_URL}/rest/v1/itens?id=eq.{item_id}",
            headers=_headers(),
timeout=15,
        )
        _audit(user, "item_excluir", item_id)
    except Exception as exc:
        return f"Falha: {exc}", 500
    return redirect("/admin/itens")


@bp.route("/admin/config", methods=["GET"])
def admin_config():
    user = _require_perm("ver_config")
    if not user:
        return redirect("/login")
    cfg = _config_all()
    precos_texto = cfg.get("precos") or _precos_texto()
    form = (
        "<section><h2>Preços por pacote (RC → R$)</h2>"
        "<p style='color:#8ea0b8;font-size:13px'>Uma linha por pacote no formato "
        "<b>quantia=preço</b>, separados por quebra de linha. Ex.: <code>100=R$ 9,00</code>. "
        "Esse valor é usado na resposta do bot e no cálculo do Pix.</p>"
        "<form method='post' action='/admin/config/salvar'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        "<input type='hidden' name='chave' value='precos'>"
        f"<textarea name='valor' rows='6'>{html.escape(precos_texto)}</textarea>"
        "<p style='margin-top:14px'><button class='btn' type='submit'>Salvar preços</button></p>"
        "</form></section>"
    )
    notif_atual = cfg.get("notificar_pedido")
    notif_block = (
        "<section><h2>Notificações</h2>"
        "<p style='color:#8ea0b8;font-size:13px'>Receber aviso no Telegram quando um "
        "novo pedido chegar no bot.</p>"
        "<form method='post' action='/admin/config/salvar'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        "<input type='hidden' name='chave' value='notificar_pedido'>"
        "<label>Notificar dono</label>"
        f"<select name='valor'>"
        f"<option value='1' {'selected' if notif_atual in (None, '', '1') else ''}>Sim</option>"
        f"<option value='0' {'selected' if notif_atual == '0' else ''}>Não</option>"
        "</select>"
        "<p style='margin-top:14px'><button class='btn' type='submit'>Salvar</button></p>"
        "</form></section>"
    )
    return _admin_page(user, "Configurações", form + notif_block, "config")


@bp.route("/admin/config/salvar", methods=["POST"])
def admin_config_salvar():
    user = _require_perm("editar_config")
    if not user:
        return "Acesso restrito.", 403
    if not _csrf_ok():
        return "Requisição inválida (CSRF).", 403
    chave = (request.form.get("chave") or "").strip()[:50]
    valor = (request.form.get("valor") or "").strip()
    if not chave:
        return "Chave obrigatória.", 400
    if chave == "precos":
        try:
            novo = {}
            for linha in valor.splitlines():
                linha = linha.strip()
                if not linha:
                    continue
                k, sep, v = linha.rpartition("=")
                if not sep:
                    return f"Linha sem '=': {html.escape(linha)}", 400
                k = k.strip()
                if not k.isdigit():
                    return f"Pacote inválido: {html.escape(k)}", 400
                novo[k] = v.strip() or f"R$ {k}"
            valor = json.dumps(novo, ensure_ascii=False)
        except Exception as exc:
            return f"Falha ao interpretar: {exc}", 400
    try:
        _config_set(chave, valor)
        _audit(user, "config_salvar", chave)
    except Exception as exc:
        return f"Falha: {exc}", 500
    return redirect("/admin/config")


# --------------------------------------------------------------------------
# ROTAS DE USUÁRIOS (RBAC)
# --------------------------------------------------------------------------
def _usuarios_rows(usuarios):
    rows = ""
    for u in usuarios:
        nome = html.escape(str(u.get("nome") or "-"))
        cargo = html.escape(str(u.get("cargo") or "CLIENTE"))
        email = html.escape(str(u.get("email") or ""))
        ativo_lbl = "ativo" if u.get("ativo") else "inativo"
        created = html.escape(str(u.get("criado_em") or ""))[:16]
        rows += (
            "<tr>"
            f"<td>{email}</td><td>{nome}</td><td>{cargo}</td>"
            f"<td><span class='status {ativo_lbl}'>{ativo_lbl}</span></td>"
            f"<td>{created}</td>"
            f"<td class='acts'><a class='btn ghost' style='padding:5px 10px;font-size:12px' "
            f"href='/admin/usuarios/{email}'>Ver</a></td>"
            "</tr>"
        )
    return rows or (
        "<tr><td colspan='6' class='empty' style='color:#64748b;padding:18px;text-align:center'>Nenhum usuário.</td></tr>"
    )


@bp.route("/admin/usuarios", methods=["GET"])
def admin_usuarios():
    user = _require_perm("ver_usuarios")
    if not user:
        return redirect("/login")
    usuarios = _fetch_soft("users", order="criado_em.desc", range_="0-999")
    body = f"<div class='cards'><div class='card'><div class='num'>{len(usuarios)}</div><div class='lbl'>Usuários</div></div></div>"
    body += (
        "<section><h2>Usuários da equipe</h2><table>"
        "<tr><th>E-mail</th><th>Nome</th><th>Cargo</th><th>Status</th><th>Criado</th><th>Ações</th></tr>"
        + _usuarios_rows(usuarios)
        + "</table></section>"
    )
    return _admin_page(user, "Usuários", body, "usuarios")


@bp.route("/admin/usuarios/novo", methods=["GET", "POST"])
def admin_usuario_novo():
    user = _require_perm("gerenciar_usuarios")
    if not user:
        return redirect("/login")
    if request.method == "POST":
        if not _csrf_ok():
            return "Requisição inválida (CSRF).", 403
        email = (request.form.get("email") or "").strip().lower()
        nome = (request.form.get("nome") or "").strip()[:100]
        cargo = (request.form.get("cargo") or "CLIENTE").strip().upper()
        if not email or "@" not in email:
            return "E-mail inválido.", 400
        if cargo == "MASTER":
            return "Não é possível criar usuários MASTER.", 400
        if not rbac.cargo_valido(cargo):
            return "Cargo inválido.", 400
        now = datetime.utcnow().isoformat()
        payload = {"email": email, "nome": nome, "cargo": cargo, "ativo": True, "criado_em": now}
        try:
            requests.post(
                f"{SUPA_URL}/rest/v1/users",
                headers=_headers(),
                json=payload,
                timeout=15,
            )
            _audit(user, "usuario_criar", email)
        except Exception as exc:
            return f"Falha: {exc}", 500
        return redirect("/admin/usuarios")
    cargos = [(c, lbl) for c, lbl in rbac.CARGOS_LABEL.items() if c != "MASTER"]
    cargo_opts = "".join(
        f"<option value='{c}'>{html.escape(lbl)}</option>" for c, lbl in cargos
    )
    form = (
        "<section><h2>Novo usuário</h2>"
        "<form method='post'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        "<label>E-mail</label><input name='email' type='email' required placeholder='usuario@email.com'>"
        "<label>Nome</label><input name='nome' type='text' placeholder='Nome completo'>"
        "<label>Cargo</label><select name='cargo'>" + cargo_opts + "</select>"
        "<p style='margin-top:14px'><button class='btn' type='submit'>Criar usuário</button></p>"
        "</form></section>"
    )
    return _admin_page(user, "Novo usuário", form, "usuarios")


@bp.route("/admin/usuarios/<path:email>", methods=["GET", "POST"])
def admin_usuario_detalhe(email):
    user = _require_perm("gerenciar_usuarios")
    if not user:
        return redirect("/login")
    email = email.strip().lower()
    usuarios = _fetch_soft("users", query=f"email=eq.{email}")
    if not usuarios:
        return "Usuário não encontrado.", 404
    u = usuarios[0]
    if request.method == "POST":
        if not _csrf_ok():
            return "Requisição inválida (CSRF).", 403
        nome = (request.form.get("nome") or "").strip()[:100]
        cargo = (request.form.get("cargo") or "CLIENTE").strip().upper()
        ativo = request.form.get("ativo") == "on"
        if cargo == "MASTER":
            return "Cargo MASTER não permitido.", 400
        if not rbac.cargo_valido(cargo):
            return "Cargo inválido.", 400
        now = datetime.utcnow().isoformat()
        patch = {"nome": nome, "cargo": cargo, "ativo": ativo, "atualizado_em": now}
        try:
            requests.patch(
                f"{SUPA_URL}/rest/v1/users?email=eq.{email}",
                headers=_headers(),
                json=patch,
                timeout=15,
            )
            _audit(user, "usuario_editar", email)
        except Exception as exc:
            return f"Falha: {exc}", 500
        return redirect(f"/admin/usuarios/{email}")
    cargo_opts = ""
    for c, lbl in rbac.CARGOS_LABEL.items():
        if c == "MASTER":
            continue
        sel = "selected" if u.get("cargo") == c else ""
        cargo_opts += f"<option value='{c}' {sel}>{html.escape(lbl)}</option>"
    checked = "checked" if u.get("ativo") else ""
    nome_val = html.escape(str(u.get("nome") or ""))
    form = (
        "<section><h2>Editar usuário</h2>"
        f"<p style='color:#8ea0b8;font-size:13px'>E-mail: <b>{html.escape(email)}</b></p>"
        "<form method='post'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        "<label>Nome</label><input name='nome' type='text' value=\"" + nome_val + "\">"
        "<label>Cargo</label><select name='cargo'>" + cargo_opts + "</select>"
        f"<label style='display:flex;gap:8px;align-items:center;margin-top:8px'><input type='checkbox' name='ativo' {checked}> Ativo</label>"
        "<p style='margin-top:14px'><button class='btn' type='submit'>Salvar</button></p>"
        "</form></section>"
    )
    return _admin_page(user, "Editar usuário", form, "usuarios")


# --------------------------------------------------------------------------
# ROTAS DE AUDITORIA
# --------------------------------------------------------------------------
@bp.route("/admin/audit", methods=["GET"])
def admin_audit():
    user = _require_perm("ver_audit")
    if not user:
        return redirect("/login")
    logs = _fetch("audit_log", order="criado_em.desc", range_="0-499")
    rows = ""
    for a in logs:
        rows += (
            "<tr>"
            f"<td>{html.escape(str(a.get('criado_em') or ''))[:19]}</td>"
            f"<td>{html.escape(str(a.get('email') or '-'))}</td>"
            f"<td>{html.escape(str(a.get('acao') or '-'))}</td>"
            f"<td>{html.escape(str(a.get('detalhes') or '-'))}</td>"
            f"<td>{html.escape(str(a.get('ip') or '-'))}</td>"
            "</tr>"
        )
    rows = rows or (
        "<tr><td colspan='5' class='empty' style='color:#64748b;padding:18px;text-align:center'>Nenhum log encontrado.</td></tr>"
    )
    body = (
        "<section><h2>Log de auditoria</h2><table>"
        "<tr><th>Quando</th><th>Quem</th><th>Ação</th><th>Detalhes</th><th>IP</th></tr>"
        + rows
        + "</table></section>"
    )
    return _admin_page(user, "Auditoria", body, "audit")


# --------------------------------------------------------------------------
# ROTAS DE GRUPOS (WhatsApp)
# --------------------------------------------------------------------------
def _grupos_rows(grupos):
    rows = ""
    for g in grupos:
        gid = g.get("id")
        nome = html.escape(str(g.get("nome") or ""))
        link = g.get("link") or ""
        ativo_lbl = "ativo" if g.get("ativo") else "inativo"
        ordem = g.get("ordem") or 0
        link_lbl = f"<a href='{html.escape(link)}' rel='noopener'>{html.escape(link[:40])}</a>" if link else "<span style='color:#64748b'>—</span>"
        rows += (
            "<tr>"
            f"<td>{html.escape(str(gid))}</td>"
            f"<td>{nome}</td>"
            f"<td>{link_lbl}</td>"
            f"<td>{ordem}</td>"
            f"<td><span class='status {ativo_lbl}'>{ativo_lbl}</span></td>"
            f"<td class='acts'><a class='btn ghost' style='padding:5px 10px;font-size:12px' "
            f"href='/admin/grupos/{gid}'>Editar</a></td>"
            "</tr>"
        )
    return rows or (
        "<tr><td colspan='6' class='empty' style='color:#64748b;padding:18px;text-align:center'>Nenhum grupo.</td></tr>"
    )


@bp.route("/admin/grupos", methods=["GET"])
def admin_grupos():
    user = _require_perm("ver_grupos")
    if not user:
        return redirect("/login")
    grupos = _fetch_soft("grupos", order="ordem.asc")
    body = f"<div class='cards'><div class='card'><div class='num'>{len(grupos)}</div><div class='lbl'>Grupos</div></div></div>"
    body += (
        "<section><h2>Grupos do WhatsApp</h2><table>"
        "<tr><th>ID</th><th>Nome</th><th>Link</th><th>Ordem</th><th>Status</th><th>Ações</th></tr>"
        + _grupos_rows(grupos)
        + "</table></section>"
    )
    return _admin_page(user, "Grupos", body, "grupos")


@bp.route("/admin/grupos/<int:gid>", methods=["GET", "POST"])
def admin_grupo_detalhe(gid):
    user = _require_perm("gerenciar_grupos")
    if not user:
        return redirect("/login")
    grupos = _fetch_soft("grupos", query=f"id=eq.{gid}")
    if not grupos:
        return "Grupo não encontrado.", 404
    g = grupos[0]
    if request.method == "POST":
        if not _csrf_ok():
            return "Requisição inválida (CSRF).", 403
        nome = (request.form.get("nome") or "").strip()[:100]
        link = (request.form.get("link") or "").strip()
        ativo = request.form.get("ativo") == "on"
        ordem = int((request.form.get("ordem") or "0").strip() or "0")
        now = datetime.utcnow().isoformat()
        patch = {"nome": nome, "link": link, "ativo": ativo, "ordem": ordem, "atualizado_em": now}
        try:
            requests.patch(
                f"{SUPA_URL}/rest/v1/grupos?id=eq.{gid}",
                headers=_headers(),
                json=patch,
                timeout=15,
            )
            _audit(user, "grupo_editar", f"{gid} ({nome})")
        except Exception as exc:
            return f"Falha: {exc}", 500
        return redirect("/admin/grupos")
    checked = "checked" if g.get("ativo") else ""
    nome_val = html.escape(str(g.get("nome") or ""))
    link_val = html.escape(str(g.get("link") or ""))
    ordem_val = g.get("ordem") or 0
    form = (
        "<section><h2>Editar grupo</h2>"
        "<form method='post'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        "<label>Nome</label><input name='nome' type='text' value=\"" + nome_val + "\" required>"
        "<label>Link (WhatsApp /wa.me/...)</label><input name='link' type='url' value=\"" + link_val + "\" placeholder='https://chat.whatsapp.com/...'>"
        "<label>Ordem</label><input name='ordem' type='number' value='" + str(ordem_val) + "'>"
        f"<label style='display:flex;gap:8px;align-items:center;margin-top:8px'><input type='checkbox' name='ativo' {checked}> Ativo</label>"
        "<p style='margin-top:14px'><button class='btn' type='submit'>Salvar</button></p>"
        "</form></section>"
    )
    return _admin_page(user, "Editar grupo", form, "grupos")


@bp.route("/api/grupos", methods=["GET"])
def api_grupos():
    if _rate_limited("api_grupos", _RATE_LIMIT_TRACK_PER_MIN):
        return jsonify({"ok": False, "error": "rate limit"}), 429
    origin = request.headers.get("Origin") or ""
    grupos = _fetch_soft("grupos", query="ativo=eq.true", order="ordem.asc")
    payload = [
        {
            "id": g.get("id"),
            "nome": g.get("nome") or "",
            "link": g.get("link") or "",
            "ativo": bool(g.get("ativo")),
            "ordem": g.get("ordem") or 0,
        }
        for g in grupos
        if (g.get("link") or "").strip()
    ]
    resp = jsonify({"ok": True, "grupos": payload})
    if origin:
        resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Vary"] = "Origin"
    return resp


@bp.route("/api/itens", methods=["GET"])
def api_itens():
    if _rate_limited("api_itens", _RATE_LIMIT_TRACK_PER_MIN):
        return jsonify({"ok": False, "error": "rate limit"}), 429
    origin = request.headers.get("Origin") or ""
    itens = _fetch("itens", select="*", query="ativo=eq.true", order="ordem.asc")
    payload = [
        {
            "id": it.get("id"),
            "nome": it.get("nome"),
            "preco": it.get("preco"),
            "descricao": it.get("descricao"),
            "imagem": it.get("imagem"),
            "categoria": it.get("categoria"),
        }
        for it in itens
    ]
    response = jsonify({"ok": True, "itens": payload})
    if origin and _cors_ok():
        response.headers["Access-Control-Allow-Origin"] = origin
    return response


@bp.route("/api/servicos", methods=["GET"])
def api_servicos():
    if _rate_limited("api_servicos", _RATE_LIMIT_TRACK_PER_MIN):
        return jsonify({"ok": False, "error": "rate limit"}), 429
    origin = request.headers.get("Origin") or ""
    servicos = _fetch_soft("servicos", select="*", query="ativo=eq.true", order="ordem.asc")
    payload = [
        {
            "id": s.get("id"),
            "nome": s.get("nome"),
            "preco": s.get("preco"),
            "descricao": s.get("descricao"),
            "imagem": s.get("imagem"),
            "categoria": s.get("categoria"),
        }
        for s in servicos
    ]
    response = jsonify({"ok": True, "servicos": payload})
    if origin and _cors_ok():
        response.headers["Access-Control-Allow-Origin"] = origin
    return response


@bp.route("/api/track", methods=["POST", "OPTIONS"])
def api_track():
    if request.method == "OPTIONS":
        response = jsonify({})
        if _cors_ok():
            response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin") or "*"
            response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response, 204
    if _rate_limited("api_track", _RATE_LIMIT_TRACK_PER_MIN):
        return jsonify({"ok": False, "error": "rate limit"}), 429
    data = request.get_json(silent=True) or {}
    pagina = (data.get("pagina") or "/")[:250]
    referer = (data.get("referer") or "")[:500]
    altura = str(data.get("altura") or "")[:20]
    requests.post(
        f"{SUPA_URL}/rest/v1/visitas",
        headers=_headers(),
        json={"pagina": pagina, "referer": referer, "pagina_resolucao": altura},
        timeout=10,
    )
    response = jsonify({"ok": True})
    if _cors_ok():
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin") or "*"
    return response
