import html
import json
import os
import secrets
import time
from datetime import datetime, timedelta

import requests
from flask import Blueprint, jsonify, redirect, request, session

bp = Blueprint("painel", __name__)

BRAND = "BAPZX"
VERSION = "1.16.0"
PORTFOLIO_URL = os.environ.get("PORTFOLIO_URL", "https://bapzxdev.github.io/bapzx-portfolio/")


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
    return {
        "email": email,
        "name": session.get("name") or email,
        "role": session.get("role") or "cliente",
    }


def _require_admin():
    user = _current_user()
    if not user or user["role"] != "admin":
        return None
    if ADMIN_IP_ALLOWLIST and _client_ip() not in ADMIN_IP_ALLOWLIST:
        return None
    return user


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


LAYOUT_HEAD = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@500;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
body {{ font-family:'Inter',Arial,sans-serif; margin:0; background:#0b1120; color:#e2e8f0; }}
nav {{ background:#111a2e; border-bottom:1px solid #1e2c40; padding:12px 22px; display:flex; gap:20px; align-items:center; flex-wrap:wrap; }}
nav .brand {{ font-family:'Sora',sans-serif; font-weight:800; letter-spacing:2px; color:#fff; }}
nav .brand span {{ background:linear-gradient(135deg,#34d399,#60a5fa); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }}
nav a {{ color:#8ea0b8; text-decoration:none; font-size:14px; padding:8px 12px; border-radius:9px; }}
nav a:hover, nav a.active {{ color:#fff; background:rgba(52,211,153,.12); }}
main {{ max-width:1100px; margin:0 auto; padding:24px 22px 60px; }}
.cards {{ display:flex; gap:14px; flex-wrap:wrap; margin:18px 0; }}
.card {{ background:#16203a; border:1px solid #1e2c40; border-radius:12px; padding:14px 18px; flex:1; min-width:150px; }}
.card .num {{ font-size:24px; font-weight:800; color:#34d399; }}
.card .lbl {{ font-size:12px; color:#8ea0b8; }}
section {{ background:#111a2e; border:1px solid #1e2c40; border-radius:12px; padding:18px 20px; margin:16px 0; }}
section h2 {{ margin-top:0; font-size:16px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th, td {{ text-align:left; padding:7px 8px; border-bottom:1px solid #1e2c40; vertical-align:middle; }}
th {{ color:#8ea0b8; font-weight:normal; }}
.status {{ padding:2px 8px; border-radius:5px; font-size:11px; font-weight:700; }}
.status.pendente {{ background:#78350f; color:#fbbf24; }}
.status.pago {{ background:#064e3b; color:#4ade80; }}
.status.entregue {{ background:#1e3a5f; color:#60a5fa; }}
.status.cancelado {{ background:#7f1d1d; color:#f87171; }}
.acts form, .acts form button {{ display:inline; }}
.acts button {{ background:#334155; border:0; color:#e2e8f0; border-radius:6px; padding:5px 10px; cursor:pointer; font-size:12px; }}
.acts button.pago {{ background:#064e3b; color:#4ade80; }}
.acts button.entregue {{ background:#1e3a5f; color:#60a5fa; }}
.btn {{ display:inline-block; background:linear-gradient(135deg,#34d399,#60a5fa); color:#04111b; text-decoration:none; padding:10px 18px; border-radius:10px; font-weight:700; font-size:14px; }}
.btn.ghost {{ background:transparent; border:1px solid #1e2c40; color:#e2e8f0; }}
input, textarea, select {{ background:#0b1120; border:1px solid #2a3a52; color:#e2e8f0; border-radius:9px; padding:10px 12px; font-size:14px; width:100%; box-sizing:border-box; }}
label {{ display:block; font-size:13px; color:#8ea0b8; margin:12px 0 4px; }}
img.preview {{ max-width:120px; border-radius:8px; border:1px solid #1e2c40; margin-bottom:8px; }}
.kicker {{ color:#34d399; font-size:12px; letter-spacing:2px; text-transform:uppercase; margin-bottom:4px; }}
.box {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
@media(max-width:760px){{ .box {{ grid-template-columns:1fr; }} }}
.notice {{ background:#0f2a22; border:1px solid #14532d; color:#4ade80; border-radius:9px; padding:10px 14px; font-size:13px; margin-bottom:14px; }}
.error {{ background:#2a1020; border:1px solid #7f1d1d; color:#f87171; border-radius:9px; padding:10px 14px; font-size:13px; margin-bottom:14px; }}
</style>
</head>
<body>
"""


def _page(user, title, body, active=""):
    nav_items = [
        ("/admin", "Dashboard", "dash"),
        ("/admin/pedidos", "Pedidos", "pedidos"),
        ("/admin/itens", "Itens", "itens"),
        ("/admin/clientes", "Clientes", "clientes"),
        ("/admin/pagamentos", "Pagamentos", "pagamentos"),
        ("/admin/tickets", "Tickets", "tickets"),
        ("/admin/config", "Configurações", "config"),
    ]
    nav = "".join(
        f"<a {'class=active ' if key == active else ''}href='{href}'>{label}</a>"
        for href, label, key in nav_items
    )
    top = (
        f"<a href='{PORTFOLIO_URL}' target='_blank' rel='noopener'>Ver site</a>"
        f"<a href='/logout'>Sair</a>"
    )
    return (
        LAYOUT_HEAD.replace("{title}", html.escape(title))
        + "<nav><div class='brand'>BAP<span>ZX</span> ADMIN</div>"
        + nav
        + f"<span style='flex:1'></span>{top}</nav><main>"
        + body
        + "</main></body></html>",
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
    user = _require_admin()
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

    cards = (
        "<div class='cards'>"
        "<div class='card'><div class='num'>{f}</div><div class='lbl'>Faturado (pagos)</div></div>"
        "<div class='card'><div class='num'>{p}</div><div class='lbl'>Pagos</div></div>"
        "<div class='card'><div class='num'>{n}</div><div class='lbl'>Pedidos</div></div>"
        "<div class='card'><div class='num'>{c}</div><div class='lbl'>Clientes</div></div>"
        "<div class='card'><div class='num'>{v}</div><div class='lbl'>Visitas 7 dias</div></div>"
        "<div class='card'><div class='num'>{v1}</div><div class='lbl'>Visitas hoje</div></div>"
        "<div class='card'><div class='num'>{vt}</div><div class='lbl'>Visitas total</div></div>"
        "</div>"
    ).format(
        f=_fmt_brl(faturado),
        p=pagos,
        n=len(orders),
        c=len(clientes),
        v=visitas7d,
        v1=visitas1d,
        vt=visitas_total,
    )

    # grafico de pedidos por dia (14 dias)
    dias = []
    base = datetime.now().date()
    for offset in range(13, -1, -1):
        dia = base - timedelta(days=offset)
        dias.append((dia.isoformat(), por_dia.get(dia.isoformat(), 0)))
    max_dia = max((c for _, c in dias), default=0) or 1
    bars = "".join(
        f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px'>"
        f"<span style='width:110px;font-size:12px;color:#8ea0b8'>{dia}</span>"
        f"<div style='flex:1;background:#334155;height:14px;border-radius:7px;overflow:hidden'>"
        f"<div style='height:100%;width:{int(c / max_dia * 100)}%;background:#34d399'></div></div>"
        f"<span style='width:28px;font-size:12px;text-align:right'>{c}</span></div>"
        for dia, c in dias
    )

    body = cards
    body += f"<section><h2>Pedidos nos ultimos 14 dias</h2>{bars}</section>"
    body += (
        "<section><h2>Paginas mais visitadas</h2><table>"
        "<tr><th>Pagina</th><th>Visitas</th></tr>" + top_rows + "</table></section>"
    )
    body += (
        "<section><h2>Ultimas acoes do admin</h2><table>"
        "<tr><th>Quando</th><th>Quem</th><th>Acao</th><th>Detalhes</th></tr>"
        + audit_rows
        + "</table></section>"
    )
    body += (
        "<section><h2>Ultimos pedidos</h2><table>"
        "<tr><th>Quando</th><th>Cliente</th><th>Char</th><th>Qtd</th>"
        "<th>Valor</th><th>Mundo</th><th>E-mail</th><th>Status</th><th>Acoes</th></tr>"
        + _orders_rows(orders[:10], with_actions=True, csrf=_csrf_token())
        + "</table></section>"
    )
    return _admin_page(user, "Dashboard", body, "dash")


@bp.route("/admin/pedidos", methods=["GET"])
def admin_pedidos():
    user = _require_admin()
    if not user:
        return redirect("/login")
    orders = _fetch("pedidos", order="data.asc")
    body = f"<div class='cards'><div class='card'><div class='num'>{len(orders)}</div><div class='lbl'>Pedidos</div></div></div>"
    body += (
        "<section><h2>Todos os pedidos</h2><table>"
        "<tr><th>Quando</th><th>Cliente</th><th>Char</th><th>Qtd</th>"
        "<th>Valor</th><th>Mundo</th><th>E-mail</th><th>Status</th><th>Ações</th></tr>"
        + _orders_rows(orders, with_actions=True, csrf=_csrf_token())
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
    user = _require_admin()
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
    user = _require_admin()
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
    user = _require_admin()
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
    user = _require_admin()
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
    user = _require_admin()
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
    user = _require_admin()
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
    user = _require_admin()
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
    user = _require_admin()
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
        "<section><h2>Ticket #{id} &middot; {status}</h2>"
        "<p style='color:#8ea0b8;font-size:13px'>"
        "De: <b>{email}</b> &middot; Abertura: {criado} &middot; "
        "Assunto: <b>{assunto}</b></p>"
        "<p style='color:#e2e8f0'>{mensagem}</p>"
        "{resposta_html}"
        "</section>"
        "<section><h2>Responder</h2>"
        "<form method='post'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        "<input type='hidden' name='acao' value='responder'>"
        "<textarea name='resposta' rows='4' placeholder='Escreva a resposta do suporte...'></textarea>"
        "<p style='margin-top:14px'><button class='btn' type='submit'>Enviar resposta</button></p>"
        "</form></section>"
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
    )
    return _admin_page(user, "Ticket", top + body, "tickets")


@bp.route("/admin/tickets/<int:ticket_id>/excluir", methods=["POST"])
def admin_ticket_excluir(ticket_id):
    user = _require_admin()
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
        f"<div class='kicker'>{html.escape(item.get('categoria') or 'geral')} &middot; "
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
    user = _require_admin()
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
    user = _require_admin()
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
    user = _require_admin()
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
    user = _require_admin()
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
    user = _require_admin()
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
    user = _require_admin()
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
    user = _require_admin()
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
