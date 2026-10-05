import base64
import html
import json
import os
import json
import re
import secrets
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests
from flask import Flask, request, redirect, session
from werkzeug.exceptions import HTTPException

from vendas.pedidos import OrderStore
from painel import bp as painel_bp
from painel import _registra_invalidador_coins, _registra_invalidador_marketplace, _csrf_token as _csrf_token, _csrf_ok as _csrf_ok
from painel import _mk_max_tier as _mk_max_tier, _mk_class_of as _mk_class_of
from painel import _wiki_get as _mk_wiki_get
from acesso import rbac as rbac
from legal import legais as legais
from marktrade.dados.mk_itens import _MK_ITENS_DB

VERSION = "2.10.40"

BRAND = "BAPZX"
STORE = "RUBINI COINS"
SERVICE_NAME = "Service BAPZX"
SERVICE_PRICE = "R$20 por hora"
SERVICE_WHATSAPP_DISPLAY = "(19) 99181-3598"
SERVICE_WHATSAPP_LINK = "https://wa.me/5519991813598"
DELIVERY_NOTE = 'Entrega: enviada em até 10 minutos após a confirmação do pagamento.'

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def load_env_key(var, paths=None):
    value = os.environ.get(var)
    if value:
        return value
    candidates = paths or [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gemini-cli", ".env"),
    ]
    for env_path in candidates:
        if os.path.isfile(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(var + "=") and not line.startswith("#"):
                        return line.split("=", 1)[1].strip()
    return None


TOKEN = load_env_key("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("Token nao encontrado. Crie o .env com TELEGRAM_BOT_TOKEN=seu_token")
    sys.exit(1)

BASE = f"https://api.telegram.org/bot{TOKEN}"
PIX_KEY = load_env_key("PIX_KEY")
MP_ACCESS_TOKEN = load_env_key("MP_ACCESS_TOKEN")
SHEET_WEBAPP_URL = load_env_key("SHEET_WEBAPP_URL")
SHEET_TOKEN = load_env_key("SHEET_TOKEN")
RENDER_URL = load_env_key("RENDER_URL") or "https://bapzx-bot-tibia.onrender.com"
PORTFOLIO_URL = "https://bapzxdev.github.io/bapzx-portfolio/"
TELEGRAM_WEBHOOK_SECRET = load_env_key("TELEGRAM_WEBHOOK_SECRET") or ""
ALLOWED_HOSTS = {h.strip() for h in (load_env_key("ALLOWED_HOSTS") or "").split(",") if h.strip()}
try:
    _render_host = urlparse(RENDER_URL).hostname or ""
    if _render_host:
        ALLOWED_HOSTS.add(_render_host)
except Exception:
    pass
ALLOWED_HOSTS.update({"localhost", "127.0.0.1", "bapzx-bot-tibia.onrender.com"})
GOOGLE_CLIENT_ID = load_env_key("GOOGLE_CLIENT_ID") or ""
GOOGLE_CLIENT_SECRET = load_env_key("GOOGLE_CLIENT_SECRET") or ""
ADMIN_EMAILS = set(
    e.strip().lower()
    for e in (load_env_key("ADMIN_EMAILS") or "").split(",")
    if e.strip()
)
MASTER_EMAILS = set(
    e.strip().lower()
    for e in (load_env_key("MASTER_EMAILS") or load_env_key("ADMIN_EMAILS") or "").split(",")
    if e.strip()
) or ADMIN_EMAILS
AWAITING_EMAIL = {}
AWAITING_CHAR = {}
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")
CHAT_HISTORY = {}
EMAIL_EXPIRY_SECONDS = 30 * 60
CHAR_EXPIRY_SECONDS = 15 * 60
CHAR_YES_WORDS = {"sim", "confirmo", "confirmar", "pode", "pode confirmar", "ok", "isso", "afirmativo", "yes", "ss"}
AWAITING_FEEDBACK = {}
FEEDBACK_EXPIRY_SECONDS = 7 * 24 * 60 * 60
CONFIRM_KEYBOARD = {
    "inline_keyboard": [
        [
            {"text": "SIM", "callback_data": "char_sim"},
            {"text": "NÃO", "callback_data": "char_nao"},
        ]
    ]
}
MENU_KEYBOARD = {
    "inline_keyboard": [
        [
            {"text": "Comprar RC", "callback_data": "menu_comprar"},
            {"text": "/site", "callback_data": "menu_site"},
            {"text": "/info", "callback_data": "menu_info"},
            {"text": "/vendedor", "callback_data": "menu_vendedor"},
        ]
    ]
}
CHAR_STOP_WORDS = {
    "mundo", "world", "pagamento", "pix", "via", "em", "na", "no", "com",
    "para", "pra", "e", "vou", "quero", "trade", "email", "e-mail", "depois",
    "aguardando", "entrega", "sera", "vai",
}
SHEET_STATUS_MAP = {"pendente": "pagamento_pendente"}
MODELS = [
    "models/gemini-3.6-flash",
    "models/gemini-3-flash-preview",
    "models/gemini-3.5-flash",
]
PRICES = {
    100: "R$9,00",
    250: "R$22,50",
    500: "R$45,00",
    1000: "R$90,00",
    2500: "R$225,00",
}

HELP_TEXT = (
    "Boa tarde! Seja bem-vindo à BAPZX.\n\n"
    "Comandos:\n"
    "  /compra - ver pacotes de RC e comprar\n"
    "  /site - acessar o site da loja\n"
    "  /info - informações sobre a loja RUBINI COINS\n\n"
    "Também oferecemos service no servidor do RubinOT a partir de R$20 hora.\n"
    "Use /servico para saber mais ou /vendedor para falar com um atendente humano."
)

ABOUT_TEXT = (
    "A BAPZX é a loja que revende Rubini Coins (RC) da RUBINI COINS: venda rápida e segura.\n"
    "Pagamento via Pix e entrega enviada em até 10 minutos após a confirmação.\n"
    "Entrega em até 10 minutos após a confirmação do pagamento.\n"
    "Use /compra para comprar RC, /site para o site da loja, "
    "/servico para os services BAPZX, /vendedor para falar com um atendente humano "
    "e /ajuda para rever as opções."
)

COMPRA_TEXT = (
    "🛒 COMPRAR RUBINI COINS (RC)\n\n"
    "Para realizar sua compra, informe os 3 dados abaixo:\n\n"
    "1️⃣ Nome do char\n"
    "2️⃣ Quantidade de Rubini Coins (RC)\n"
    "3️⃣ Forma de pagamento: Pix\n\n"
    "📝 Exemplo:\n"
    "Quero comprar 500 RC, char Teste, pagamento Pix.\n\n"
    "💰 Consulte os preços usando /preco\n\n"
    "⚡ Entrega em até 10 minutos após a confirmação do pagamento."
)

SITE_TEXT = (
    "💰 Consulte a tabela de preços usando [/preco](tg://bot_command?command=preco).\n\n"
    "⚡ Entrega em até 10 minutos após a confirmação do pagamento.\n\n"
    "🌐 Site oficial da BAPZX:\n"
    f"[{PORTFOLIO_URL}]({PORTFOLIO_URL})\n\n"
    "No site, você encontra informações sobre as Rubini Coins (RC) e os Services da BAPZX.\n\n"
    "🛒 Para comprar Rubini Coins, use [/compra](tg://bot_command?command=compra).\n\n"
    "💬 Para falar com um atendente, use [/vendedor](tg://bot_command?command=vendedor)."
)

SERVICO_TEXT = (
    f"\U0001f4bc Service BAPZX\n\n"
    f"Valor: {SERVICE_PRICE}\n"
    "O que inclui: service dedicado a UP level no RubinOT (1 hora).\n\n"
    "Para solicitar, entre em contato pelo WhatsApp:\n"
    f"{SERVICE_WHATSAPP_DISPLAY}\n"
    f"{SERVICE_WHATSAPP_LINK}\n\n"
    "\U0001f4b3 RC? Fale comigo aqui ou use /preco."
)


_COINS_CACHE = {"ts": 0.0, "dados": None}
_COINS_TTL = 30


def _coins_invalidate():
    """Zera o cache de configuração COINS (o painel chama isso ao salvar,
    então a próxima leitura do bot busca o valor novo na hora)."""
    _COINS_CACHE["ts"] = 0.0
    _COINS_CACHE["dados"] = None


_registra_invalidador_coins(_coins_invalidate)


def _coins_config():
    """Configuração atual do módulo COINS (linha única id=1).
    Cache de 2 min. Nunca derruba: sem a tabela ou em falha devolve None e o
    bot segue com o comportamento antigo (PRICES fixos, sem travas)."""
    if time.time() - _COINS_CACHE["ts"] < _COINS_TTL:
        return _COINS_CACHE["dados"]
    dados = None
    if STORE.remote:
        try:
            response = requests.get(
                f"{STORE.url}/rest/v1/coins_config?select=*&id=eq.1",
                headers=STORE._headers(),
                timeout=10,
            )
            if response.status_code == 200 and response.json():
                dados = response.json()[0]
        except Exception:
            dados = None
    _COINS_CACHE["ts"] = time.time()
    _COINS_CACHE["dados"] = dados
    return dados


def _coins_preco_mil():
    """Preço configurado por 1.000 COINS (float) ou None se não houver."""
    cfg = _coins_config() or {}
    try:
        value = float(cfg.get("preco_mil") or 0)
    except (TypeError, ValueError):
        value = 0.0
    return value if value > 0 else None


def _coins_limites():
    """min/max de compra vigentes (0 = limite desativado)."""
    cfg = _coins_config() or {}
    try:
        mn = float(cfg.get("min_compra") or 0)
    except (TypeError, ValueError):
        mn = 0.0
    try:
        mx = float(cfg.get("max_compra") or 0)
    except (TypeError, ValueError):
        mx = 0.0
    return mn, mx


def _coins_check(tc):
    """Bloqueia a compra se as vendas estiverem pausadas ou a quantidade
    estiver fora dos limites. Devolve a mensagem de bloqueio ou None (ok).
    Sem config (tabela ainda não criada) libera sempre — comportamento antigo."""
    cfg = _coins_config()
    if not cfg:
        return None
    status = (cfg.get("status") or "ativo").strip().lower()
    if status not in ("ativo", "aberto", ""):
        return ("As vendas de COINS estão pausadas neste momento.\n"
                "Fale com um atendente: /vendedor")
    mn, mx = _coins_limites()
    if mn > 0 and tc is not None and tc < mn:
        return f"A compra mínima é de {int(mn):,} COINS.".replace(",", ".")
    if mx > 0 and tc is not None and tc > mx:
        return f"A compra máxima é de {int(mx):,} COINS.".replace(",", ".")
    return None


# ============ MARKETPLACE (MARKTRADE) — configuração ============
_MK_CACHE = {"ts": 0.0, "dados": None}
_MK_TTL = 30
_MK_VIP_CACHE = {}


def _marketplace_invalidate():
    """Zera o cache de configuração do marketplace (o painel chama isso ao
    salvar, então a próxima leitura do bot busca o valor novo na hora)."""
    _MK_CACHE["ts"] = 0.0
    _MK_CACHE["dados"] = None


_registra_invalidador_marketplace(_marketplace_invalidate)


def _marketplace_config():
    """Configuração atual do MARKTRADE (linha única id=1). Cache de 30s.
    Nunca derruba: sem a tabela ou em falha devolve None e o bot segue com os
    valores padrão do modelo comercial."""
    if time.time() - _MK_CACHE["ts"] < _MK_TTL:
        return _MK_CACHE["dados"]
    dados = None
    if STORE.remote:
        try:
            response = requests.get(
                f"{STORE.url}/rest/v1/marketplace_config?select=*&id=eq.1",
                headers=STORE._headers(),
                timeout=10,
            )
            if response.status_code == 200 and response.json():
                dados = response.json()[0]
        except Exception:
            dados = None
    _MK_CACHE["ts"] = time.time()
    _MK_CACHE["dados"] = dados
    return dados


def _mk_num(value, default=0.0):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default


def _mk_preco(chave, default):
    """Preço configurado (R$) do marketplace, ou o default sugerido."""
    cfg = _marketplace_config() or {}
    v = _mk_num(cfg.get(chave), 0)
    return v if v > 0 else default


def _mk_limite():
    cfg = _marketplace_config() or {}
    try:
        v = int(float(cfg.get("limite_publicacoes") or 0))
    except (TypeError, ValueError):
        v = 0
    return v if v > 0 else 3


def _mk_duracao(chave, default):
    cfg = _marketplace_config() or {}
    try:
        v = int(float(cfg.get(chave) or 0))
    except (TypeError, ValueError):
        v = 0
    return v if v > 0 else default


def _mk_ativo():
    """True = publicações liberadas (ou config ausente)."""
    cfg = _marketplace_config()
    if not cfg:
        return True
    return (cfg.get("status") or "ativo").strip().lower() in ("ativo", "aberto", "")


_MK_MUNDOS = (
    "Auroria", "Belaria", "Bellum", "Drakaria", "Eldrian", "Elysian",
    "Infernum I", "Infernum II", "Infernum III", "Lunarian", "Malveria",
    "Mystian", "Obsidian", "Solarian", "Tenebrium", "Vesperia",
)

_SPRITE_CACHE = {}

_MK_CONECTIVOS = {
    "a", "as", "ai", "ao", "aos", "com", "da", "das", "de", "desde", "do", "dos",
    "e", "em", "entre", "na", "nas", "no", "nos", "o", "os", "para", "pela",
    "pelas", "pelo", "pelos", "por", "um", "uma", "umas", "uns",
    "the", "of", "and", "or", "to", "in", "on", "at", "for", "from", "with",
    "into", "onto", "van", "von",
}
_MK_ITENS_JSON = json.dumps(_MK_ITENS_DB, ensure_ascii=False)

_MK_AC_CSS = """
<style>
.mk-pub-ac{position:relative}
.mk-pub-ac-drop{position:absolute;top:calc(100% + 4px);left:0;right:0;z-index:80;background:var(--panel-2);border:1px solid var(--border-2);border-radius:10px;overflow:hidden;box-shadow:0 12px 28px rgba(0,0,0,.5);max-height:260px;overflow-y:auto}
.mk-pub-ac-item{display:flex;align-items:center;gap:8px;padding:9px 12px;cursor:pointer;background:transparent;color:var(--text);font-size:14px;border-bottom:1px solid var(--border);text-align:left;width:100%;min-width:0}
.mk-pub-ac-item:last-child{border-bottom:0}
.mk-pub-ac-item:hover,.mk-pub-ac-item.on{background:rgba(96,165,250,.14)}
.mk-pub-ac-item b{color:var(--green);font-weight:700;white-space:nowrap}
.mk-pub-ac-name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mk-pub-ac-sub{margin-left:auto;color:var(--muted);font-size:12px;flex-shrink:0;white-space:nowrap;padding-left:8px}
.mk-pub-ac-drop::-webkit-scrollbar{width:8px}
.mk-pub-ac-drop::-webkit-scrollbar-thumb{background:var(--border-2);border-radius:8px}
.mk-sprite-prev{display:inline-block;vertical-align:middle;margin-left:8px;line-height:0}
.mk-sprite-prev img{width:44px;height:44px;object-fit:contain;image-rendering:pixelated;border:1px solid var(--border-2);border-radius:10px;background:var(--panel-2)}
</style>
"""

_MK_AC_SCRIPT = ("""
<script>
(function () {
  var ITENS = __MK_ITENS_JSON__;
  var campo = document.getElementById("item_name");
  if (!campo) return;
  var wrap = document.createElement("div");
  wrap.className = "mk-pub-ac";
  campo.parentNode.insertBefore(wrap, campo);
  wrap.appendChild(campo);
  var dd = document.createElement("div");
  dd.className = "mk-pub-ac-drop";
  dd.hidden = true;
  wrap.appendChild(dd);
  var sel = -1;
  function norm(s) {
    return String(s || "").toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
  }
  function sedd() {
    var raw = String(campo.value || "");
    var q = norm(raw).replace(/\\s+/g, " ").trim();
    if (q.length < 2) { dd.hidden = true; sel = -1; return; }
    var qlow = raw.toLowerCase();
    var found = [];
    for (var i = 0; i < ITENS.length; i++) {
      var nn = norm(ITENS[i][0]);
      var at = nn.indexOf(q);
      if (at < 0) continue;
      found.push({it: ITENS[i], i: i, rank: (nn === q) ? 0 : (at === 0 ? 1 : 2)});
    }
    found.sort(function (x, y) { return (x.rank - y.rank) || (String(x.it[0]).length - String(y.it[0]).length); });
    var res = found.slice(0, 8);
    if (!res.length) { dd.hidden = true; sel = -1; return; }
    sel = -1;
    dd.innerHTML = res.map(function (r) {
      var it = r.it;
      var n = String(it[0]);
      var k = n.toLowerCase().indexOf(qlow);
      var str = "";
      if (k < 0) { str = esc(n); } else {
        str = esc(n.slice(0, k)) + "<b>" + esc(n.slice(k, k + qlow.length)) + "</b>" + esc(n.slice(k + qlow.length));
      }
      var extra = (it[1] && it[1] !== "0") ? ('<span class="mk-pub-ac-sub">Nv ' + esc(it[1]) + (it[2] ? " · " + esc(it[2]) : "") + "</span>") : "";
      return '<button type="button" class="mk-pub-ac-item" data-i="' + r.i + '"><span class="mk-pub-ac-name">' + str + "</span>" + extra + "</button>";
    }).join("");
    dd.hidden = false;
    vzFirst();
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function vzFirst() {
    var itens = dd.querySelectorAll(".mk-pub-ac-item");
    if (itens.length && sel === -1) sel = 0;
    for (var i = 0; i < itens.length; i++) itens[i].classList.toggle("on", i === sel);
  }
  function mover(dir) {
    var itens = dd.querySelectorAll(".mk-pub-ac-item");
    if (!itens.length) return;
    if (sel < 0) sel = dir > 0 ? 0 : itens.length - 1; else sel = (sel + dir + itens.length) % itens.length;
    for (var i = 0; i < itens.length; i++) itens[i].classList.toggle("on", i === sel);
  }
  function aplicar(it) {
    if (!it) return;
    campo.value = it[0];
    dd.hidden = true;
    tierSync();
  }
  var tierSel = document.getElementById("mk_tier");
  var tierHint = document.getElementById("mk_tier_hint");
  var CLASS_MAX = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 10};
  function tierSync() {
    if (!tierSel) return;
    var q = norm(campo.value).replace(/\\s+/g, " ").trim();
    var max = 10, cls = "", achou = false;
    if (q.length >= 2) {
      for (var i = 0; i < ITENS.length; i++) {
        if (norm(ITENS[i][0]) === q) {
          cls = String(ITENS[i][8] != null ? ITENS[i][8] : "");
          max = (cls in CLASS_MAX) ? CLASS_MAX[cls] : 0;
          achou = true;
          break;
        }
      }
    }
    for (var j = 0; j < tierSel.options.length; j++) {
      var v = Number(tierSel.options[j].value);
      tierSel.options[j].disabled = v > max;
    }
    if (Number(tierSel.value) > max) tierSel.value = String(max);
    if (tierHint) {
      tierHint.innerHTML = achou
        ? esc(campo.value.trim()) + " \u2014 classe <b>" + esc(cls === "" ? "?" : cls) + "</b> \u2192 tier m\u00e1ximo <b>" + max + "</b>."
        : "Itens normais usam <b>tier 0</b>. O m\u00e1ximo vai pela classifica\u00e7\u00e3o do item (classe <b>1 \u2192 1</b>, <b>2 \u2192 2</b>, <b>3 \u2192 3</b>, <b>4 \u2192 10</b>).";
    }
  }
  campo.addEventListener("input", sedd);
  campo.addEventListener("input", tierSync);
  tierSync();
  campo.addEventListener("keydown", function (e) {
    if (!dd.hidden && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
      e.preventDefault();
      mover(e.key === "ArrowDown" ? 1 : -1);
      return;
    }
    if (e.key === "Enter" && !dd.hidden && sel >= 0) {
      e.preventDefault();
      var items = dd.querySelectorAll(".mk-pub-ac-item");
      if (items[sel]) aplicar(ITENS[Number(items[sel].getAttribute("data-i"))]);
    }
    if (e.key === "Escape" && !dd.hidden) { dd.hidden = true; sel = -1; }
  });
  dd.addEventListener("click", function (e) {
    var item = e.target.closest(".mk-pub-ac-item");
    if (!item) return;
    aplicar(ITENS[Number(item.getAttribute("data-i"))]);
  });
  document.addEventListener("click", function (e) {
    if (!dd.hidden && !e.target.closest(".mk-pub-ac")) { dd.hidden = true; sel = -1; }
  });
})();
</script>
""").replace("__MK_ITENS_JSON__", _MK_ITENS_JSON)

_MK_FORM_CSS = """
<style>
form.mk-form{max-width:920px}
.mk-seg{display:flex;gap:8px;margin:6px 0 10px}
.mk-seg-opt{flex:1;padding:10px;border:1px solid var(--border-2);background:var(--panel-2);color:var(--text);border-radius:10px;cursor:pointer;font-size:13px;font-weight:600;text-align:center;transition:.15s}
.mk-seg-opt:hover{border-color:var(--purple)}
.mk-seg-opt.on{background:rgba(167,139,250,.16);border-color:var(--purple);color:var(--purple)}
.mk-destaque{position:relative;display:flex;align-items:center;gap:12px;margin-top:14px;cursor:pointer;width:100%}
.mk-destaque input{position:absolute;opacity:0;width:0;height:0}
.mk-destaque-box{display:flex;align-items:center;gap:14px;border:1px solid rgba(212,175,55,.30);background:linear-gradient(180deg,#18233a 0%,#101a2c 100%);border-radius:16px;padding:16px 18px;width:100%;box-shadow:0 12px 30px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.04);transition:.18s}
.mk-destaque:hover .mk-destaque-box{border-color:rgba(212,175,55,.55);box-shadow:0 14px 34px rgba(0,0,0,.34),0 0 18px rgba(212,175,55,.12)}
.mk-destaque input:checked ~ .mk-destaque-box{border-color:rgba(212,175,55,.75);box-shadow:0 14px 34px rgba(0,0,0,.34),0 0 22px rgba(212,175,55,.22)}
.mk-destaque-dot{width:22px;height:22px;border-radius:50%;background:#0b0f1a;border:2px solid #3a4a6b;position:relative;flex-shrink:0;transition:.18s}
.mk-destaque-dot::after{content:"✓";position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#fff;font-size:13px;font-weight:800;opacity:0;transform:scale(.5);transition:.15s}
.mk-destaque input:checked ~ .mk-destaque-box .mk-destaque-dot{background:linear-gradient(135deg,#34d399,#22d3ee);border-color:rgba(255,255,255,.40);box-shadow:0 0 12px rgba(52,211,153,.50)}
.mk-destaque input:checked ~ .mk-destaque-box .mk-destaque-dot::after{opacity:1;transform:scale(1)}
.mk-destaque-star{display:inline-flex;flex-shrink:0;filter:drop-shadow(0 0 6px rgba(251,191,36,.60))}
.mk-destaque-star svg{display:block}
.mk-destaque-txt{display:flex;flex-direction:column;gap:2px;min-width:0}
.mk-destaque-title{color:#fff;font-family:'Sora',sans-serif;font-weight:700;font-size:15px;letter-spacing:.2px}
.mk-destaque-price{color:#4ade80;font-weight:800;font-size:14.5px}
.mk-destaque-note{color:#8ea0b8;font-size:12.5px;font-weight:400}
.mk-publish-btn{width:100%;text-align:center;font-family:'Sora',sans-serif;font-size:15px;font-weight:700;letter-spacing:.3px;padding:12px 16px;border-radius:11px;background:linear-gradient(135deg,#059669 0%,#10b981 45%,#06b6d4 100%);color:#fff;border:0;cursor:pointer;box-shadow:0 11px 24px rgba(5,150,105,.32);transition:filter .15s,transform .05s}
.mk-publish-btn:hover{filter:brightness(1.12);box-shadow:0 13px 28px rgba(5,150,105,.42)}
.mk-publish-btn:active{transform:scale(.98)}
.mk-form label{display:block;color:#eaf2ff;font-weight:600;font-size:13.5px}
.mk-form .note{color:#a9bccd}
.panel .note b,.mk-form .note b{color:#fbbf24}
.mk-form input,.mk-form select{color:#fff}
.mk-form input::placeholder{color:#647a93}
.mk-form select option{background:#101a2c;color:#e6edf7}
.mk-form input:focus,.mk-form select:focus{border-color:#34d399;box-shadow:0 0 0 3px rgba(52,211,153,.18);outline:none}
.mk-seg-opt{color:#d7e2f2}
.mk-seg-opt.on{color:#c4b5fd;border-color:var(--purple)}
.mk-form .mk-destaque-note{color:#9fb2ca}
.mk-form p{margin:8px 0}
.mk-form label{margin:2px 0 5px}
.mk-form input,.mk-form select{padding:9px 12px}
.mk-form{min-width:0}
.mk-row{display:grid;gap:10px 12px;margin:0 0 10px}
.mk-row>div{min-width:0}
.mk-row.c2{grid-template-columns:repeat(2,minmax(0,1fr))}
.mk-row.c3{grid-template-columns:repeat(3,minmax(0,1fr))}
.mk-seg{margin:4px 0 8px}
.mk-destaque-box{padding:12px 14px}
@media(max-width:900px){.mk-row.c3{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:640px){.mk-row.c2,.mk-row.c3{grid-template-columns:minmax(0,1fr)}}
</style>
"""

_MK_PAGE_CSS = """
<style>
.welcome{border:1px solid rgba(212,175,55,.30);background:linear-gradient(180deg,#18233a 0%,#101a2c 100%);box-shadow:0 12px 30px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.04)}
.welcome h2{text-shadow:0 0 18px rgba(52,211,153,.45)}
.welcome .btn{display:inline-flex;align-items:center;gap:8px;justify-content:center;background:linear-gradient(135deg,#059669 0%,#10b981 45%,#06b6d4 100%);color:#fff;border:0;font-family:'Sora',sans-serif;font-weight:700;font-size:13.5px;letter-spacing:.2px;padding:11px 18px;border-radius:11px;box-shadow:0 10px 22px rgba(5,150,105,.32);transition:filter .15s,transform .05s}
.welcome .btn:hover{filter:brightness(1.12);transform:translateY(-1px)}
.kpi{background:linear-gradient(180deg,#18233a 0%,#101a2c 100%);border:1px solid rgba(212,175,55,.24);border-radius:16px;box-shadow:0 12px 28px rgba(0,0,0,.26),inset 0 1px 0 rgba(255,255,255,.04);transition:border-color .15s,transform .1s,box-shadow .15s}
.kpi:hover{border-color:rgba(212,175,55,.55);box-shadow:0 14px 34px rgba(0,0,0,.34),0 0 16px rgba(212,175,55,.12)}
.kpi .num{text-shadow:0 0 14px rgba(74,222,128,.35)}
.kpi.amber .num{text-shadow:0 0 14px rgba(251,191,36,.35)}
.kpi.blue .num{text-shadow:0 0 14px rgba(96,165,250,.35)}
.kpi.purple .num{text-shadow:0 0 14px rgba(167,139,250,.40)}
.panel{background:linear-gradient(180deg,#18233a 0%,#101a2c 100%);border:1px solid rgba(212,175,55,.24);border-radius:18px;box-shadow:0 14px 30px rgba(0,0,0,.30),inset 0 1px 0 rgba(255,255,255,.04)}
.panel-hd a.btn,.panel-hd a.btn.ghost.small{display:inline-flex;align-items:center;gap:7px;justify-content:center;background:linear-gradient(135deg,#059669 0%,#10b981 45%,#06b6d4 100%);color:#fff;border:0;font-family:'Sora',sans-serif;font-weight:700;font-size:13px;letter-spacing:.2px;padding:9px 15px;border-radius:10px;box-shadow:0 8px 18px rgba(5,150,105,.30);transition:filter .15s}
.panel-hd a.btn:hover,.panel-hd a.btn.ghost.small:hover{filter:brightness(1.12)}
.table-wrap{border-color:rgba(212,175,55,.18);border-radius:14px}
th{background:rgba(16,26,44,.60)}
</style>
"""

_MK_FORM_JS = """
<script>
(function () {
  var contato = document.getElementById("mk_contato");
  var modo = document.getElementById("mk_modo_preco");
  var blocoPreco = document.getElementById("mk_bloco_preco");
  var preco = document.getElementById("mk_preco");
  var opts = document.querySelectorAll(".mk-seg-opt");
  function appl(v) {
    if (!modo || !blocoPreco || !preco) return;
    var fixo = v === "preco_fixo";
    modo.value = v;
    blocoPreco.style.display = fixo ? "" : "none";
    preco.required = fixo;
    preco.disabled = !fixo;
    for (var i = 0; i < opts.length; i++) {
      opts[i].classList.toggle("on", opts[i].getAttribute("data-target") === v);
    }
  }
  for (var i = 0; i < opts.length; i++) {
    (function (o) {
      o.addEventListener("click", function () { appl(o.getAttribute("data-target")); });
    })(opts[i]);
  }
  appl(modo ? modo.value : "preco_fixo");
  function somenteDigitos() {
    if (!preco) return;
    preco.value = String(preco.value || "").replace(/\\D/g, "");
  }
  if (preco) preco.addEventListener("input", somenteDigitos);
  function fone() {
    if (!contato) return;
    var d = String(contato.value || "").replace(/\\D/g, "").slice(0, 11);
    if (d.length > 6) contato.value = "(" + d.slice(0, 2) + ") " + d.slice(2, 7) + "-" + d.slice(7);
    else if (d.length > 2) contato.value = "(" + d.slice(0, 2) + ") " + d.slice(2);
    else contato.value = d;
  }
  if (contato) contato.addEventListener("input", fone);
})();
</script>
"""


_MK_SPRITE_JS = """
<script>
(function () {
  var campo = document.getElementById("item_name");
  var hid = document.getElementById("mk_sprite_url");
  var prev = document.getElementById("mk_sprite_prev");
  if (!campo || !hid) return;
  var cache = {};
  function api(params) {
    return fetch("https://www.tibiawiki.com.br/api.php?" + params + "&origin=*").then(function (r) {
      if (!r.ok) throw new Error("http " + r.status);
      return r.json();
    });
  }
  function resolver(nome) {
    nome = String(nome || "").trim();
    if (!nome) return Promise.resolve("");
    var k = nome.toLowerCase();
    if (cache[k] !== undefined) return Promise.resolve(cache[k]);
    var alvo = k.replace(/\\s+/g, "_");
    function guarda(url) { cache[k] = url || ""; return cache[k]; }
    return api("action=query&format=json&redirects=1&prop=images&imlimit=500&titles=" + encodeURIComponent(nome)).then(function (d) {
      var achou = "";
      var pages = ((d || {}).query || {}).pages || {};
      Object.keys(pages).forEach(function (pid) {
        var imgs = pages[pid].images || [];
        for (var i = 0; i < imgs.length; i++) {
          var t = String(imgs[i].title || "");
          if (t.slice(0, 8).toLowerCase() !== "arquivo:") continue;
          var stem = t.slice(8);
          var dot = stem.lastIndexOf(".");
          var base = (dot > 0 ? stem.slice(0, dot) : stem).toLowerCase().replace(/\\s+/g, "_");
          if (base === alvo) { achou = t; break; }
          if (!achou && base.indexOf(alvo) === 0) achou = t;
        }
      });
      if (!achou) return "";
      return api("action=query&format=json&prop=imageinfo&iiprop=url&iiurlwidth=96&titles=" + encodeURIComponent(achou)).then(function (d2) {
        var p2 = ((d2 || {}).query || {}).pages || {};
        var url = "";
        Object.keys(p2).forEach(function (pid) {
          var ii = p2[pid].imageinfo || [];
          if (ii.length && ii[0].thumburl) url = ii[0].thumburl;
        });
        return url;
      });
    }).catch(function () { return ""; }).then(guarda);
  }
  function mostrar(url) {
    if (!prev) return;
    if (url) {
      prev.innerHTML = '<img src="' + url.replace(/"/g, "&quot;") + '" alt="" width="44" height="44" loading="lazy">';
      prev.hidden = false;
    } else {
      prev.innerHTML = "";
      prev.hidden = true;
    }
  }
  window.__mkResolverSprite = resolver;
  var t = null;
  campo.addEventListener("input", function () {
    hid.value = "";
    mostrar("");
    if (t) clearTimeout(t);
    t = setTimeout(function () {
      var v = campo.value.trim();
      if (v.length < 3) return;
      resolver(v).then(function (url) {
        if (campo.value.trim() === v) { hid.value = url; mostrar(url); }
      });
    }, 450);
  });
  var form = campo.closest("form");
  if (form) form.addEventListener("submit", function (e) {
    var v = campo.value.trim();
    if (!v || hid.value) return;
    e.preventDefault();
    var feito = false;
    function envia() { if (!feito) { feito = true; form.submit(); } }
    setTimeout(envia, 6000);
    resolver(v).then(function (url) { hid.value = url; envia(); });
  });
})();
</script>
"""


def _mk_whatsapp(value):
    """Valida e normaliza WhatsApp brasileiro com DDD.

    Aceita 10 ou 11 dígitos (com ou sem máscara, ex. "19987654321" ou
    "(19) 98765-4321"). Devolve "(99) 9XXXX-XXXX" / "(99) XXXX-XXXX",
    ou "" se inválido. Nunca derruba."""
    if not value:
        return ""
    dig = re.sub(r"\D", "", str(value))
    if len(dig) == 11:
        return f"({dig[:2]}) {dig[2:7]}-{dig[7:]}"
    if len(dig) == 10:
        return f"({dig[:2]}) {dig[2:6]}-{dig[6:]}"
    return ""


def _mk_title_case(text):
    """Padroniza o nome do item: cada palavra começa com maiúscula e o resto
    fica minúsculo, conectivos comuns ficam minúsculos.

    Ex.: "WAR HAMMER" -> "War Hammer", "war hammer" -> "War Hammer",
    "sword of the phoenix" -> "Sword of the Phoenix". Nunca derruba."""
    palavras = (text or "").strip().split()
    saida = []
    for i, p in enumerate(palavras):
        if not p:
            continue
        base = p[:1].upper() + p[1:].lower()
        if i > 0 and base.lower() in _MK_CONECTIVOS:
            base = base.lower()
        saida.append(base)
    return " ".join(saida)


def _mk_itemsprite(item_name):
    """Busca a imagem oficial do item no Wiki Tibia (tibiawiki.com.br).

    Fluxo: prop=images para achar "Arquivo:<Item>.gif/png" e depois imageinfo
    com iiurlwidth=96 para gerar o thumb. Se a primeira tentativa não achar
    nada, tenta de novo com o nome padronizado (title case). Nunca derruba:
    devolve "" (o anúncio fica sem sprite e o cliente pode mandar a URL)."""
    nome = (item_name or "").strip()
    if not nome:
        return ""
    chave = nome.lower()
    if chave in _SPRITE_CACHE:
        return _SPRITE_CACHE[chave]
    resultado = ""
    try:
        alvo = nome.lower().replace(" ", "_")
        achou = None

        def _get(params):
            dados, diag = _mk_wiki_get(params, timeout=(5, 12))
            if diag != "ok":
                raise Exception(f"wiki:{diag}")
            return dados

        dados = _get({
            "action": "query",
            "format": "json",
            "redirects": "1",
            "prop": "images",
            "imlimit": "500",
            "titles": nome,
        })
        for page in ((dados.get("query") or {}).get("pages") or {}).values():
            for img in (page.get("images") or []):
                titulo = (img.get("title") or "").strip()
                if not titulo.lower().startswith("arquivo:"):
                    continue
                stem, _, _ext = titulo[8:].rpartition(".")
                stem_norm = stem.lower().replace(" ", "_")
                if stem_norm == alvo:
                    achou = titulo
                    break
                if not achou and stem_norm.startswith(alvo):
                    achou = titulo
            if achou:
                break
        if achou:
            dados2 = _get({
                "action": "query",
                "format": "json",
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": "96",
                "titles": achou,
            })
            for page in ((dados2.get("query") or {}).get("pages") or {}).values():
                ii = page.get("imageinfo") or []
                if ii and ii[0].get("thumburl"):
                    resultado = ii[0]["thumburl"]
                    break
    except Exception:
        resultado = ""
    if not resultado and nome != _mk_title_case(nome):
        resultado = _mk_itemsprite(_mk_title_case(nome))
    if len(_SPRITE_CACHE) > 800:
        _SPRITE_CACHE.clear()
    _SPRITE_CACHE[chave] = resultado
    return resultado


def _mk_sprite_host(url):
    """Hospeda o GIF do item numa CDN quando configurado (cascata).

    A env MK_SPRITE_HOST aceita uma lista separada por vírgula na ordem de
    prioridade — ex.: 'cloudinary,supabase' (tenta Cloudinary primeiro; se
    falhar, tenta Supabase). Provedores suportados:
      'supabase'   -> baixa do Wiki e sobe num bucket público do Supabase;
      'cloudinary' -> baixa do Wiki e sobe no Cloudinary (image/upload);
    Se nenhum deles funcionar (ou a env não listar ninguém), devolve a URL
    original do Wiki (hotlink direto). Nunca derruba."""
    if not url or not url.startswith("http"):
        return url or ""
    provedores = [
        p.strip().lower()
        for p in (os.environ.get("MK_SPRITE_HOST") or "").split(",")
        if p.strip().lower() in ("supabase", "cloudinary")
    ]
    if not provedores:
        return url
    for provedor in provedores:
        try:
            blob = requests.get(
                url,
                timeout=20,
                headers={"User-Agent": f"BAPZX-MARKTRADE/{VERSION}/host"},
            ).content
            if provedor == "supabase":
                novo = _mk_sprite_host_supabase(blob, url)
            else:
                novo = _mk_sprite_host_cloudinary(blob, url)
            if novo:
                return novo
        except Exception:
            continue
    return url


def _mk_sprite_host_supabase(blob, original_url):
    """Sobe os bytes do GIF num bucket público do Supabase e devolve a URL."""
    from painel import SUPA_URL, SUPA_KEY
    if not SUPA_URL or not SUPA_KEY:
        return ""
    try:
        from urllib.parse import urlparse
        ext = (os.path.splitext(urlparse(original_url).path)[1] or ".gif").lower()
        if ext not in (".gif", ".png", ".jpg", ".jpeg", ".webp"):
            ext = ".gif"
        mime = {
            ".gif": "image/gif", ".png": "image/png", ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg", ".webp": "image/webp",
        }.get(ext, "image/gif")
        nome = f"mk-sprite-{secrets.token_hex(8)}{ext}"
        resposta = requests.post(
            f"{SUPA_URL}/storage/v1/object/mk-sprites/{nome}",
            headers={
                "apikey": SUPA_KEY,
                "Authorization": f"Bearer {SUPA_KEY}",
                "Content-Type": mime,
            },
            data=blob,
            timeout=40,
        )
        if resposta.status_code in (200, 201):
            return f"{SUPA_URL}/storage/v1/object/public/mk-sprites/{nome}"
    except Exception:
        pass
    return ""


def _mk_sprite_host_cloudinary(blob, original_url):
    """Sobe os bytes do GIF no Cloudinary (image/upload, não image/fetch).

    Requer envs CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY e
    CLOUDINARY_API_SECRET. Sem elas, devolve "". Nunca derruba."""
    cloud = (os.environ.get("CLOUDINARY_CLOUD_NAME") or "").strip()
    api_key = (os.environ.get("CLOUDINARY_API_KEY") or "").strip()
    api_secret = (os.environ.get("CLOUDINARY_API_SECRET") or "").strip()
    if not cloud or not api_key or not api_secret:
        return ""
    try:
        import hashlib
        from urllib.parse import urlparse
        ts = int(time.time())
        folder = "mk-sprites"
        public_id = f"mk-{ts}"
        params = {
            "folder": folder,
            "public_id": public_id,
            "timestamp": str(ts),
        }
        msg = "&".join(f"{k}={v}" for k, v in sorted(params.items())) + api_secret
        params["api_key"] = api_key
        params["signature"] = hashlib.sha1(msg.encode("utf-8")).hexdigest()
        resposta = requests.post(
            f"https://api.cloudinary.com/v1_1/{cloud}/image/upload",
            data=params,
            files={"file": (os.path.basename(urlparse(original_url).path) or "sprite.gif", blob)},
            timeout=40,
        )
        dados = resposta.json() or {}
        if resposta.status_code in (200, 201) and dados.get("secure_url"):
            return dados["secure_url"]
    except Exception:
        pass
    return ""


def _mk_parse_dt(value):
    try:
        s = str(value or "").strip()
        if not s:
            return None
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return None


def _mk_fmt_dt(value):
    """dd/mm/aaaa hh:mm no fuso de São Paulo (UTC-3, sem DST desde 2019);
    cru se der erro."""
    dt = _mk_parse_dt(value)
    if not dt:
        return "-"
    try:
        try:
            from zoneinfo import ZoneInfo
            br = dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("America/Sao_Paulo"))
        except Exception:
            br = dt.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=-3)))
        return br.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return dt.strftime("%Y-%m-%d %H:%M")


def _mk_profile(email):
    if not (STORE.remote and email):
        return {}
    try:
        response = requests.get(
            f"{STORE.url}/rest/v1/profiles?email=eq.{email}&select=*",
            headers=STORE._headers(),
            timeout=15,
        )
        if response.status_code == 200:
            rows = response.json() or []
            if rows:
                return rows[0]
    except Exception:
        pass
    return {}


def _mk_vip_ativo(email):
    """True se o cliente tem VIP BAPZX vigente (cache 30s por e-mail)."""
    if not email:
        return False
    now = time.time()
    cached = _MK_VIP_CACHE.get(email)
    if cached and now - cached[0] < 30:
        return cached[1]
    ativo = False
    dt = _mk_parse_dt((_mk_profile(email) or {}).get("vip_until"))
    if dt:
        ativo = dt > datetime.utcnow()
    _MK_VIP_CACHE[email] = (now, ativo)
    return ativo


def _mk_minhas_listings(email):
    if not (STORE.remote and email):
        return []
    try:
        response = requests.get(
            f"{STORE.url}/rest/v1/marketplace_listings?user_id=eq.{email}"
            "&order=created_at.desc&select=*",
            headers=STORE._headers(),
            timeout=15,
        )
        if response.status_code == 200:
            return response.json() or []
    except Exception:
        pass
    return []


def _mk_meus_pagamentos(email):
    if not (STORE.remote and email):
        return []
    try:
        response = requests.get(
            f"{STORE.url}/rest/v1/marketplace_pagamentos?user_id=eq.{email}"
            "&order=created_at.desc&select=*",
            headers=STORE._headers(),
            timeout=15,
        )
        if response.status_code == 200:
            return response.json() or []
    except Exception:
        pass
    return []


def _mk_listing(lid):
    if not STORE.remote:
        return None
    try:
        response = requests.get(
            f"{STORE.url}/rest/v1/marketplace_listings?id=eq.{lid}&select=*",
            headers=STORE._headers(),
            timeout=15,
        )
        if response.status_code == 200:
            rows = response.json() or []
            if rows:
                return rows[0]
    except Exception:
        pass
    return None


def _mk_find_pagamento(reference):
    if not STORE.remote:
        return None
    try:
        response = requests.get(
            f"{STORE.url}/rest/v1/marketplace_pagamentos?external_reference=eq.{reference}&select=*",
            headers=STORE._headers(),
            timeout=15,
        )
        if response.status_code == 200:
            rows = response.json() or []
            if rows:
                return rows[0]
    except Exception:
        pass
    return None


def _mk_listing_status_lbl(status):
    return {
        "pendente": "Aguardando pagamento",
        "ativa": "Ativa",
        "expirada": "Expirada",
        "encerrada": "Encerrada",
        "bloqueada": "Bloqueada",
    }.get(status or "pendente", (status or "pendente").capitalize())


def _fmt_coin_brl(value):
    return f"R${value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def price_table_text():
    preco_mil = _coins_preco_mil()
    linhas = ["🪙 TABELA DE PREÇOS — BAPZX COINS", ""]
    for value, _ in PRICES.items():
        if preco_mil:
            price = "R$ " + _fmt_coin_brl(value * preco_mil / 1000)[2:]
        else:
            price = PRICES[value].replace("R$", "R$ ")
        qtd = f"{value:,}".replace(",", ".")
        linhas.append(f"{qtd} RC  — {price}")
    linhas += [
        "",
        "💳 Pagamento: Pix",
        "",
        "⚡ Entrega:",
        "Será enviada em até 10 minutos após a confirmação do pagamento.",
        "",
        "🛒 Para comprar, use /compra",
        "💬 Atendimento: /vendedor",
    ]
    return "\n".join(linhas)


def price_table_compact():
    preco_mil = _coins_preco_mil()
    lines = []
    for value, price in PRICES.items():
        if preco_mil:
            price = _fmt_coin_brl(value * preco_mil / 1000)
        qtd = f"{value:,}".replace(",", ".")
        lines.append(f"  {qtd} RC - {price}")
    return "\n".join(lines)


def confirmacao_pedido_text(entry):
    qtd = entry.get("tc") or "-"
    try:
        qtd = f"{int(qtd):,}".replace(",", ".")
    except (TypeError, ValueError):
        pass
    preco = entry.get("preco") or "-"
    if preco.startswith("R$") and not preco.startswith("R$ "):
        preco = "R$ " + preco[2:]
    return "\n".join([
        "🪙 CONFIRMAÇÃO DO PEDIDO",
        "",
        f"Valor: {qtd} RC",
        f"Preço: {preco}",
        "Forma de pagamento: Pix",
        f"Nome do personagem: {entry.get('char') or '-'}",
        "",
        "✅ Confira os dados acima para gerar o QR Code de pagamento.",
        "⚡ Após a confirmação do pagamento, será enviado em até 10 minutos.",
    ])


def _default_payer_email():
    admin = load_env_key("ADMIN_EMAILS")
    if admin:
        first = admin.split(",")[0].strip()
        if first:
            return first
    return "cliente@bapzx.com"


def _persona_precos():
    """Blocos de preços da persona com o preço/1.000 configurado.
    Mantém o formato atual da persona (abertura com 'R$ ' e produtos sem)."""
    preco_mil = _coins_preco_mil()
    abertura, produtos = [], []
    for value, preco_fixo in PRICES.items():
        if preco_mil:
            p_esp = "R$ " + _fmt_coin_brl(value * preco_mil / 1000)[2:]
            p_cur = _fmt_coin_brl(value * preco_mil / 1000)
        else:
            p_esp = preco_fixo.replace("R$", "R$ ")
            p_cur = preco_fixo
        qtd_p = f"{value:,}".replace(",", ".")
        abertura.append(f"{qtd_p} RC — {p_esp}")
        produtos.append(f"- {value} RC: [{p_cur}]")
    return "\n".join(abertura), "\n".join(produtos)


def load_persona():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendas", "persona.txt")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            persona = f.read().strip()
    else:
        persona = 'Você é um assistente de atendimento em português do Brasil.'
    abertura_novo, produtos_novo = _persona_precos()
    persona = persona.replace(
        "100 RC — R$ 9,00\n250 RC — R$ 22,50\n500 RC — R$ 45,00\n1.000 RC — R$ 90,00\n2.500 RC — R$ 225,00",
        abertura_novo,
    )
    persona = persona.replace(
        "- 100 RC: [R$9,00]\n- 250 RC: [R$22,50]\n- 500 RC: [R$45,00]\n- 1000 RC: [R$90,00]\n- 2500 RC: [R$225,00]",
        produtos_novo,
    )
    return persona


def clean_ai_text(text):
    return (text or "").replace("*", "").replace("```", "").replace("`", "").strip()


def ask_ai(text):
    from google import genai

    key = load_env_key("GOOGLE_API_KEY")
    if not key:
        return "IA nao configurada (sem GOOGLE_API_KEY)."
    client = genai.Client(api_key=key)
    persona = load_persona()
    tabela = price_table_compact()
    prompt = (
        f"{persona}\n\n"
        f"TABELA DE PREÇOS OFICIAL (use EXATAMENTE estes valores, nunca outros):\n"
        f"{tabela}\n\n"
        "REGRAS DE RESPOSTA:\n"
        '- Nunca use asteriscos (*), negrito ou marcação de texto. Responda em texto simples.\n'
        '- Quando o cliente quiser comprar, peça/confirme os 3 dados obrigatórios:\n'
        "  nome do char, quantidade de RC e forma de pagamento (Pix).\n"
        '- O e-mail do cliente quem pede é o próprio sistema (depois de fechar o pedido);\n'
        '  não peça e-mail na conversa da IA.\n'
        "- Para calcular o valor de uma quantidade de TC fora da tabela acima, use a "
        f"proporção de que 1.000 RC custam {_fmt_coin_brl((_coins_preco_mil() or 90) * 1000 / 1000)}: multiplique a quantidade por "
        f"{_coins_preco_mil() or 90}, divida por 1.000 e mostre o cálculo passo a passo, "
        'terminando com o valor em Reais.\n'
        '- Quantidades que estão na tabela (100, 250, 500, 1.000, 2.500 RC) usam o valor '
        'da tabela, sem recálculo.\n\n'
        f"Cliente: {text}"
    )
    last = None
    for attempt in range(2):
        for model in MODELS:
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                return clean_ai_text(response.text)
            except Exception as error:
                last = error
                code = getattr(getattr(error, "error", None), "code", None) or getattr(error, "code", None)
                if code in (503, 429):
                    import time
                    time.sleep(2 + attempt * 2)
                    continue
                return f"Erro: {error}"
    return f"IA ocupada, tente em instantes. ({last})"


def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{BASE}/sendMessage", json=payload, timeout=15)
    except Exception as error:
        print(f"[telegram] sendMessage falhou ({chat_id}): {error}")


def answer_callback_query(callback_id, text=None):
    payload = {"callback_query_id": callback_id}
    if text:
        payload["text"] = text
    try:
        requests.post(f"{BASE}/answerCallbackQuery", json=payload, timeout=15)
    except Exception as error:
        print(f"[telegram] answerCallbackQuery falhou ({callback_id}): {error}")


def edit_message_reply_markup(chat_id, message_id, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{BASE}/editMessageReplyMarkup", json=payload, timeout=15)
    except Exception as error:
        print(f"[telegram] editMessageReplyMarkup falhou ({chat_id}): {error}")


def _finalizar_confirmacao_char(chat_id, confirmado):
    pending = AWAITING_CHAR.pop(chat_id, None) or {}
    if not pending:
        return
    expired = bool(pending) and time.time() - pending.get("ts", 0) > CHAR_EXPIRY_SECONDS
    if expired:
        send_message(
            chat_id,
            'O tempo para confirmar o personagem expirou. Faça um novo pedido ou use /vendedor.',
        )
        return
    if not confirmado:
        send_message(
            chat_id,
            'Sem problemas! Pedido cancelado. Quando quiser, é só me mandar de novo '
            "os dados certos ou usar /start.",
        )
        return
    entry = pending.get("entry") or {}
    entry = save_order(entry)
    audit_log(
        "pedido_criado",
        f"pedido {entry.get('id')} | {entry.get('tc')} RC | {entry.get('preco')} | {entry.get('mundo') or '-'}",
    )
    notify_owner(entry)
    push_to_sheet(entry)
    if MP_ACCESS_TOKEN and entry.get("id"):
        ok_pix, result = create_pix_charge(entry, _default_payer_email())
        if ok_pix:
            send_qr(chat_id, result, entry)
            notify_owner_pix(result, entry)
        else:
            send_message(chat_id, 'Não consegui gerar o Pix agora. ' + result)
            audit_log(
                "erro_pagamento",
                f"pedido {entry.get('id')} | falha ao gerar pix: {result}",
            )
            notify_payment(entry)
        return
    notify_payment(entry)


def relatorio_mensal(ano=None, mes=None):
    now = datetime.now()
    ano = ano or now.year
    mes = mes or now.month
    prefix = f"{ano:04d}-{mes:02d}"
    pedidos = [o for o in STORE.list() if str(o.get("data") or "").startswith(prefix)]
    total = len(pedidos)
    pagos = [o for o in pedidos if o.get("status") == "pago"]
    entregues = [o for o in pedidos if o.get("status") == "entregue"]
    pendentes = [o for o in pedidos if o.get("status") == "pendente"]
    faturado = sum(parse_brl(o.get("preco") or "0") for o in pagos)
    valor = f"R$ {faturado:,.2f}"
    valor = valor.replace(",", "X").replace(".", ",").replace("X", ".")
    return (
        f"📊 RELATORIO MENSAL - {mes:02d}/{ano}\n"
        f"  Pedidos: {total}\n"
        f"  Pagos: {len(pagos)}\n"
        f"  Entregues: {len(entregues)}\n"
        f"  Pendentes: {len(pendentes)}\n"
        f"  Faturado (pagos): {valor}"
    )


_last_relatorio_sent = None


def _relatorio_automatico():
    global _last_relatorio_sent
    while True:
        time.sleep(3600)
        now = datetime.now()
        if now.day == 1 and now.hour >= 9 and _last_relatorio_sent != (now.year, now.month):
            owner = load_env_key("TELEGRAM_OWNER_CHAT_ID")
            if owner:
                send_message(owner, relatorio_mensal(now.year, now.month))
            _last_relatorio_sent = (now.year, now.month)


def pedidos_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "pedidos.json")


def parse_amount(text):
    m = re.search(
        r"(\d{1,4}(?:[.,]\d{3})?)\s*(?:tc\b|t\b|rc\b|rubini\s+coins?\b|tibias?\b|tibia\s+coins?\b|coins?\b|mil\b)",
        text,
        re.IGNORECASE,
    )
    if m:
        return int(m.group(1).replace(".", "").replace(",", ""))
    m2 = re.search(r"\b(\d{1,4}(?:[.,]\d{3})?)\b", text)
    if m2:
        return int(m2.group(1).replace(".", "").replace(",", ""))
    return None


INTENT_WORDS = {
    "quero", "quer", "querendo", "querendo", "gostaria", "vou", "preciso",
    "precisava", "queria", "comprar", "compra", "comprando", "compras",
    "pedindo", "pedir", "pedido", "fazer", "passo", "to", "estou", "me",
    "pro", "pra", "para", "do", "da", "de", "em", "no", "na", "dos", "das",
    "um", "uma", "meu", "minha", "o", "a", "e", "se", "seu", "sua", "vc",
    "voce", "quanto", "custa", "valor", "vale", "seria", "fica", "eh", "e",
    "saber", "ajuda", "duvida", "exemplo", "numero", "mais", "so", "somar",
}


def _char_fallback(text):
    lower = re.sub(r"\d[\d.,]*", " ", text.lower())
    tokens = re.findall(r"[a-z\u00e0-\u00ff]{2,}", lower)
    keep = [t for t in tokens
            if t not in CHAR_STOP_WORDS
            and t not in INTENT_WORDS
            and t not in ("rc", "tc", "coins", "rubini", "tibia", "pix")]
    return " ".join(keep[:3]) or None


_PRECOS_CACHE = {"ts": 0.0, "dados": {}}


def _precos_config():
    if time.time() - _PRECOS_CACHE["ts"] < 120:
        return _PRECOS_CACHE["dados"]
    dados = {}
    if STORE.remote:
        try:
            response = requests.get(
                f"{STORE.url}/rest/v1/config?chave=eq.precos&select=valor",
                headers=STORE._headers(),
                timeout=10,
            )
            if response.status_code == 200 and response.json():
                raw = response.json()[0].get("valor") or ""
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and parsed:
                    dados = {int(k): str(v) for k, v in parsed.items() if str(k).isdigit()}
        except Exception:
            dados = {}
    if not dados:
        dados = PRICES
    _PRECOS_CACHE["ts"] = time.time()
    _PRECOS_CACHE["dados"] = dados
    return dados


def calc_price(tc):
    if not tc:
        return None
    preco_mil = _coins_preco_mil()
    if preco_mil:
        return _fmt_coin_brl(tc * preco_mil / 1000)
    tabela = _precos_config()
    if tc in tabela:
        return tabela[tc]
    value = tc * 90 / 1000
    return _fmt_coin_brl(value)


_CONFIG_CACHE = {"ts": 0.0, "dados": {}}


def _config_map():
    """Configurações gerais (item 11) da tabela `config`, com cache de 2 min.
    Nunca derruba: em falha devolve {} (comportamento padrão dos avisos)."""
    if time.time() - _CONFIG_CACHE["ts"] < 120:
        return _CONFIG_CACHE["dados"]
    dados = {}
    if STORE.remote:
        try:
            response = requests.get(
                f"{STORE.url}/rest/v1/config?select=chave,valor",
                headers=STORE._headers(),
                timeout=10,
            )
            if response.status_code == 200:
                dados = {r.get("chave"): r.get("valor", "") for r in (response.json() or [])}
        except Exception:
            dados = {}
    _CONFIG_CACHE["ts"] = time.time()
    _CONFIG_CACHE["dados"] = dados
    return dados


def clean_char(raw):
    partes = []
    for word in raw.split():
        if word in CHAR_STOP_WORDS:
            break
        partes.append(word)
        if len(partes) == 4:
            break
    return " ".join(partes) or None


def extract_order_details(text, pagamento=None):
    lower = text.lower()
    tc = parse_amount(lower)
    mundo = re.search(r"(?:mundo|world)\s*[:=]?\s*([a-z0-9]+)", lower)
    char = re.search(
        r"(?:char|personagem|nick|nome do char)\s*[:=]?\s*([a-z0-9]+(?:\s+[a-z0-9]+){0,3})",
        lower,
    )
    return {
        "tc": tc,
        "preco": calc_price(tc) if tc else None,
        "pagamento": pagamento or ("Pix" if "pix" in lower else None),
        "mundo": mundo.group(1) if mundo else None,
        "char": clean_char(char.group(1)) if char else _char_fallback(text),
    }


def build_order(chat_id, username, text):
    entry = {
        "data": datetime.now().isoformat(timespec="seconds"),
        "chat_id": chat_id,
        "usuario": username,
        "mensagem": text,
        "status": "pendente",
    }
    entry.update(extract_order_details(text))
    return entry


def save_order(entry):
    return STORE.save(entry)


def payment_text(entry):
    linhas = ["PAGAMENTO DOS SEUS RC", ""]
    linhas.append("Resumo do seu pedido:")
    if entry.get("tc"):
        linhas.append(f"  RC: {entry['tc']}")
    if entry.get("preco"):
        linhas.append(f"  Valor: {entry['preco']}")
    if entry.get("mundo"):
        linhas.append(f"  Mundo: {entry['mundo']}")
    if entry.get("char"):
        linhas.append(f"  Char: {entry['char']}")
    linhas.append("")
    pix_chave = _config_map().get("pix_chave") or PIX_KEY
    if pix_chave:
        linhas.append(f"Para pagar via Pix, envie {entry.get('preco') or 'o valor'} para a chave Pix:")
        linhas.append(f"  {pix_chave}")
    else:
        linhas.append('Para pagar via Pix, peça a chave Pix ao atendente com /vendedor.')
    linhas.append("")
    linhas.append("Depois de pagar, me avise aqui: paguei")
    linhas.append('Quando o pagamento for confirmado, você recebe a confirmação aqui.')
    linhas.append(DELIVERY_NOTE)
    return "\n".join(linhas)


def notify_payment(entry):
    send_message(entry["chat_id"], payment_text(entry))


def push_to_sheet(order):
    if not SHEET_WEBAPP_URL or not SHEET_TOKEN:
        return
    status = (order.get("status") or "pendente")
    payload = {
        "token": SHEET_TOKEN,
        "order": {
            "data": (order.get("data") or "")[:10],
            "cliente": order.get("usuario") or "",
            "contato": str(order.get("chat_id") or ""),
            "origem": "Bot/Telegram",
            "mundo": order.get("mundo") or "",
            "char": order.get("char") or "",
            "quantidade_tc": order.get("tc") or "",
            "preco": order.get("preco") or "",
            "tipo_pagamento": "MP Pix" if MP_ACCESS_TOKEN else "Pix manual",
            "data_pagamento": (order.get("pix_confirmado_em") or "")[:10],
            "data_entrega": (order.get("entregue_em") or "")[:10],
            "status": SHEET_STATUS_MAP.get(status, status),
            "id_pedido": order.get("id") or "",
            "observacoes": "",
        },
    }
    try:
        response = requests.post(SHEET_WEBAPP_URL, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"[planilha] status {response.status_code}: {response.text[:200]}")
    except Exception as error:
        print(f"[planilha] erro ao enviar pedido {order.get('id')}: {error}")


def create_pix_charge(order, email):
    amount = parse_brl(order.get("preco"))
    if amount <= 0:
        return False, "pedido sem valor definido."
    tc = order.get("tc")
    description = f"Compra RC {tc} - pedido {order['id']}" if tc else f"Compra de RC - pedido {order['id']}"
    payload = {
        "transaction_amount": amount,
        "description": description,
        "payment_method_id": "pix",
        "payer": {
            "email": email,
            "first_name": order.get("usuario") or "Cliente",
        },
        "external_reference": str(order["id"]),
        "notification_url": f"{RENDER_URL}/webhook/mp",
    }
    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4()),
    }
    try:
        response = requests.post(
            "https://api.mercadopago.com/v1/payments", json=payload, headers=headers, timeout=20
        )
    except Exception as error:
        return False, str(error)
    if response.status_code not in (200, 201):
        return False, f"Mercado Pago {response.status_code}: {response.text[:200]}"
    data = response.json()
    if data.get("status") != "pending":
        return False, f"status inesperado: {data.get('status')}"
    return True, data


def send_qr(chat_id, data, order=None):
    order = order or {}
    transaction_data = ((data.get("point_of_interaction") or {}).get("transaction_data")) or {}
    img_b64 = transaction_data.get("qr_code_base64")
    if img_b64:
        try:
            png = base64.b64decode(img_b64)
            requests.post(
                f"{BASE}/sendPhoto",
                data={"chat_id": chat_id, "caption": "QR Code Pix - BAPZX RC"},
                files={"photo": ("qr.png", png, "image/png")},
                timeout=15,
            )
        except Exception as error:
            print(f"[mp] erro ao enviar QR: {error}")
    qr_code = transaction_data.get("qr_code")
    linhas = [
        "PIX GERADO - Pedido confirmado",
        "",
        "Resumo do seu pedido:",
        f"  RC: {order.get('tc') or '-'}",
        f"  Valor: {order.get('preco') or '-'}",
        f"  Mundo: {order.get('mundo') or '-'}",
        f"  Char: {order.get('char') or '-'}",
        "",
        'Escaneie o QR Code acima ou use o código abaixo (copia e cola):',
        "",
        qr_code or '(código indisponível)',
        "",
        "Validade: 30 minutos.",
        DELIVERY_NOTE,
        'O pagamento é confirmado automaticamente. Assim que bater, te aviso aqui!',
    ]
    send_message(chat_id, "\n".join(linhas))


def create_marketplace_pix(reference, valor, descricao, email, primeiro_nome="Cliente"):
    """Gera um Pix Mercado Pago para o marketplace (MARKTRADE).

    external_reference usa prefixos que NÃO colidem com os pedidos do bot:
      PUB-<listing> -> publicação comum
      DES-<listing> -> publicação com destaque (ou destaque avulso)
      VIP-<email>   -> plano VIP mensal
    """
    amount = _mk_num(valor, 0)
    if amount <= 0:
        return False, "valor inválido."
    if not (MP_ACCESS_TOKEN and RENDER_URL):
        return False, "gateway de pagamento não configurado."
    payload = {
        "transaction_amount": amount,
        "description": ("BAPZX MARKTRADE · " + str(descricao))[:180],
        "payment_method_id": "pix",
        "payer": {"email": email, "first_name": primeiro_nome},
        "external_reference": reference,
        "notification_url": f"{RENDER_URL}/webhook/mp",
    }
    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4()),
    }
    try:
        response = requests.post(
            "https://api.mercadopago.com/v1/payments", json=payload, headers=headers, timeout=20
        )
    except Exception as error:
        return False, str(error)
    if response.status_code not in (200, 201):
        return False, f"Mercado Pago {response.status_code}: {response.text[:200]}"
    data = response.json()
    if data.get("status") != "pending":
        return False, f"status inesperado: {data.get('status')}"
    return True, data


def _mk_mp_transaction(pag):
    """Dados atuais do PIX (qr_code + imagem) junto ao Mercado Pago."""
    mp_id = pag.get("mp_id") or ""
    if not (mp_id and MP_ACCESS_TOKEN):
        return None
    try:
        response = requests.get(
            f"https://api.mercadopago.com/v1/payments/{mp_id}",
            headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
            timeout=15,
        )
        if response.status_code == 200:
            return (response.json().get("point_of_interaction") or {}).get("transaction_data") or None
    except Exception:
        pass
    return None


def _marketplace_confirm(reference, mp_payment_id):
    """Efeitos de um pagamento MARKTRADE confirmado (chamado pelo webhook e pela
    página de pagamento quando o cliente consulta o PIX direto no MP).

    Nunca confia em dados do frontend: lê o marketplace_pagamentos por ref e só
    ativa anúncio/VIP depois da confirmação real (webhook ou query no MP)."""
    pag = _mk_find_pagamento(reference)
    if not pag:
        print(f"[mk] pagamento {reference} não encontrado")
        return False
    if (pag.get("status") or "pendente") == "confirmado":
        return True
    agora = datetime.utcnow()
    try:
        requests.patch(
            f"{STORE.url}/rest/v1/marketplace_pagamentos?id=eq.{pag['id']}",
            headers=STORE._headers(),
            json={
                "status": "confirmado",
                "mp_id": str(mp_payment_id or pag.get("mp_id") or ""),
                "confirmed_at": agora.isoformat(timespec="seconds"),
            },
            timeout=15,
        )
    except Exception as exc:
        print(f"[mk] falha ao confirmar pagamento {reference}: {exc}")
        return False
    tipo = pag.get("tipo") or "publicacao"
    listing_id = pag.get("listing_id")
    if tipo == "vip":
        email = (pag.get("user_id") or "").lower()
        dias = _mk_duracao("duracao_vip_dias", 30)
        try:
            requests.patch(
                f"{STORE.url}/rest/v1/profiles?email=eq.{email}",
                headers=STORE._headers(),
                json={"vip_until": (agora + timedelta(days=dias)).isoformat(timespec="seconds")},
                timeout=15,
            )
            _MK_VIP_CACHE.pop(email, None)
        except Exception as exc:
            print(f"[mk] falha ao aplicar VIP p/ {email}: {exc}")
            return False
        return True
    if not listing_id:
        return True
    listing = _mk_listing(listing_id)
    patch = {}
    if not listing or (listing.get("status") or "") != "ativa":
        patch["status"] = "ativa"
        patch["expires_at"] = (agora + timedelta(days=_mk_duracao("duracao_publicacao_dias", 30))).isoformat(timespec="seconds")
    if tipo == "destaque":
        patch["is_destaque"] = True
        patch["destaque_until"] = (agora + timedelta(days=_mk_duracao("duracao_destaque_dias", 30))).isoformat(timespec="seconds")
    try:
        requests.patch(
            f"{STORE.url}/rest/v1/marketplace_listings?id=eq.{listing_id}",
            headers=STORE._headers(),
            json={**patch, "updated_at": agora.isoformat(timespec="seconds")},
            timeout=15,
        )
    except Exception as exc:
        print(f"[mk] falha ao ativar anúncio {listing_id}: {exc}")
        return False
    return True


def apply_status(order_id, status, ts_field=None):
    order = STORE.find(order_id)
    if not order:
        return "nao encontrado", None
    now_iso = datetime.now().isoformat(timespec="seconds")
    STORE.set_status(order_id, status, ts_field, now_iso)
    updated = STORE.find(order_id) or order
    push_to_sheet(updated)
    audit_log(
        f"pedido_{status}",
        f"pedido {order_id} | {updated.get('tc')} RC | {updated.get('preco')}",
    )
    return "ok", order


def looks_like_order(text):
    lower = text.lower()
    markers = ["quero", "vou querer", "queria comprar", "pode fechar",
               "comprar", "fechado", "vou levar", "vou pegar", "to comprando"]
    if any(marker in lower for marker in markers):
        return True
    has_num = re.search(r"\d{1,4}(?:[.,]\d{3})?", lower) is not None
    hints = ("pix", "pagamento", "rc", " tc ", " coi", "coins")
    return has_num and any(h in lower for h in hints)


def rate_limited(chat_id):
    now = time.time()
    stamps = [t for t in CHAT_HISTORY.get(chat_id, []) if now - t < 12]
    stamps.append(now)
    CHAT_HISTORY[chat_id] = stamps
    return len(stamps) > 5


def _host_ok(host):
    return (host or "").split(":")[0].lower() in ALLOWED_HOSTS


MP_WEBHOOK_HITS = {}


def _mp_rate_limited():
    ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.remote_addr
        or "?"
    )
    now = time.time()
    hits = [t for t in MP_WEBHOOK_HITS.get(ip, []) if now - t < 60]
    hits.append(now)
    MP_WEBHOOK_HITS[ip] = hits
    if len(hits) > 60:
        print(f"[mp] throttle no webhook de pagamento: {ip}")
        return True
    return False


def dashboard_allowed():
    expected = load_env_key("DASHBOARD_KEY")
    if not expected:
        return False
    given = request.args.get("key") or request.headers.get("X-Dashboard-Key")
    return given == expected


app = Flask(__name__)
app.config.update(
    SECRET_KEY=load_env_key("SECRET_KEY") or "dev-secret-key-change-me",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    if request.is_secure or request.headers.get("x-forwarded-proto", "").lower() == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


@app.errorhandler(404)
def _error404(error):
    print("404:", request.path)
    return "nao encontrado", 404


@app.errorhandler(HTTPException)
def _error_http(error):
    return error.name, error.code


@app.errorhandler(Exception)
def _error500(error):
    import traceback as tb

    ext = tb.format_exc()
    print("ERRO 500:", request.path, ext)
    if _config_map().get("notificar_erro") != "0":
        try:
            dono = load_env_key("TELEGRAM_OWNER_CHAT_ID")
            if dono:
                linhas = ext.splitlines()
                resumo = linhas[-2] if linhas else ""
                send_message(dono, f"⚠️ ERRO 500 em {request.path}\n{resumo[:400]}")
        except Exception:
            pass
    return "erro", 500

GOOGLE_OAUTH_READY = False
_oauth = None
try:
    from authlib.integrations.flask_client import OAuth

    _oauth = OAuth(app)
    _oauth.register(
        "google",
        client_id=GOOGLE_CLIENT_ID or "missing",
        client_secret=GOOGLE_CLIENT_SECRET or "missing",
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    GOOGLE_OAUTH_READY = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
except Exception as error:
    print(f"[auth] authlib indisponivel: {error}")
    _oauth = None

STORE = OrderStore(
    pedidos_path(),
    url=load_env_key("SUPABASE_URL"),
    key=load_env_key("SUPABASE_KEY"),
)

app.register_blueprint(painel_bp)

print(f"[start] v{VERSION} | STORE.remote={bool(STORE.remote)}")
print(f"[start] TELEGRAM_OWNER_CHAT_ID={load_env_key('TELEGRAM_OWNER_CHAT_ID')!r}")


def audit_log(acao, detalhes=""):
    try:
        requests.post(
            f"{STORE.url}/rest/v1/audit_log",
            headers=STORE._headers(),
            json={"email": "sistema@bapzx", "acao": acao, "detalhes": detalhes[:500], "ip": "sistema"},
            timeout=10,
        )
    except Exception as error:
        print(f"[audit] falhou: {error}")


def _client_ip_bot():
    try:
        return (request.headers.get("X-Forwarded-For") or request.remote_addr or "").split(",")[0].strip()
    except Exception:
        return ""


def _registrar_sessao(email):
    """Grava a sessão de login na tabela sessoes (área Segurança)."""
    sid = session.get("sid")
    if not sid or not email:
        return sid
    try:
        requests.post(
            f"{STORE.url}/rest/v1/sessoes",
            headers={**STORE._headers(), "Prefer": "return=minimal"},
            json={
                "sid": sid,
                "email": email,
                "ip": _client_ip_bot()[:45],
                "user_agent": (request.headers.get("User-Agent") or "")[:250],
                "criado_em": datetime.utcnow().isoformat() + "Z",
                "ativo": True,
            },
            timeout=10,
        )
    except Exception as error:
        print(f"[auth] falha ao registrar sessão: {error}")
    return sid


def _encerrar_sessao(sid):
    """Marca a sessão como encerrada (logout)."""
    if not sid:
        return
    try:
        requests.patch(
            f"{STORE.url}/rest/v1/sessoes?sid=eq.{sid}",
            headers={**STORE._headers(), "Prefer": "return=minimal"},
            json={"ativo": False, "encerrado_em": datetime.utcnow().isoformat() + "Z"},
            timeout=10,
        )
    except Exception as error:
        print(f"[auth] falha ao encerrar sessão: {error}")


@app.route("/", methods=["GET"])
def home():
    return redirect(PORTFOLIO_URL, code=302)


@app.route("/health", methods=["GET"])
def health():
    return f"bot ok v{VERSION}", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    if TELEGRAM_WEBHOOK_SECRET:
        provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token") or ""
        if not secrets.compare_digest(provided, TELEGRAM_WEBHOOK_SECRET):
            return "ok", 403
    update = request.get_json(silent=True) or {}
    callback = update.get("callback_query")
    if callback:
        cb_data = callback.get("data") or ""
        cb_message = callback.get("message") or {}
        cb_chat = cb_message.get("chat") or {}
        cb_chat_id = cb_chat.get("id")
        cb_chat_type = cb_chat.get("type")
        cb_msg_id = cb_message.get("message_id")
        callback_id = callback.get("id")
        cb_username = cb_message.get("from", {}).get("first_name") or cb_message.get("from", {}).get("username") or str(cb_chat_id)
        if callback_id:
            answer_callback_query(callback_id)
        if cb_chat_type != "private" or not cb_chat_id:
            return "ok", 200
        print(f"[{cb_chat_id}] callback: {cb_data}")
        if cb_data in ("char_sim", "char_nao"):
            _finalizar_confirmacao_char(cb_chat_id, cb_data == "char_sim")
            if cb_msg_id:
                edit_message_reply_markup(cb_chat_id, cb_msg_id)
            return "ok", 200
        if cb_data == "menu_preco":
            send_message(cb_chat_id, price_table_text())
        elif cb_data == "menu_servico":
            send_message(cb_chat_id, SERVICO_TEXT)
        elif cb_data == "menu_site":
            send_message(cb_chat_id, SITE_TEXT, parse_mode="Markdown")
        elif cb_data == "menu_info":
            send_message(cb_chat_id, ABOUT_TEXT)
        elif cb_data == "menu_vendedor":
            reply_vendor(cb_chat_id, cb_username)
        elif cb_data == "menu_comprar":
            send_message(cb_chat_id, COMPRA_TEXT)
            send_message(cb_chat_id, SITE_TEXT, parse_mode="Markdown")
        return "ok", 200

    message = update.get("message") or {}
    text = message.get("text")
    chat_id = message.get("chat", {}).get("id")
    chat_type = message.get("chat", {}).get("type")
    username = message.get("from", {}).get("first_name") or message.get("from", {}).get("username") or str(chat_id)
    if not text or not chat_id:
        return "ok", 200

    print(f"[{chat_id}] {text}")

    if text.strip() == "/id":
        send_message(chat_id, f"Seu chat_id é: {chat_id}")
        return "ok", 200

    command = text.strip().lower().split(" ", 1)[0]
    if command in ("/start", "/inicio", "/ajuda", "/help"):
        send_message(chat_id, HELP_TEXT, reply_markup=MENU_KEYBOARD)
        return "ok", 200

    if command == "/preco":
        send_message(chat_id, price_table_text())
        return "ok", 200

    if command == "/quemsomos":
        send_message(chat_id, ABOUT_TEXT)
        return "ok", 200

    if command == "/info":
        send_message(chat_id, ABOUT_TEXT)
        return "ok", 200

    if command == "/site":
        send_message(chat_id, SITE_TEXT, parse_mode="Markdown")
        return "ok", 200

    if command == "/compra":
        send_message(chat_id, COMPRA_TEXT)
        send_message(chat_id, SITE_TEXT, parse_mode="Markdown")
        return "ok", 200

    if command == "/vendedor":
        reply_vendor(chat_id, username)
        return "ok", 200

    if command in ("/servico", "/servicos", "/service"):
        send_message(chat_id, SERVICO_TEXT)
        return "ok", 200

    if command in ("/pago", "/entregue"):
        owner_chat = load_env_key("TELEGRAM_OWNER_CHAT_ID")
        if str(chat_id) != str(owner_chat):
            print(f"[owner] {command} recusado: chat={chat_id} | TELEGRAM_OWNER_CHAT_ID={owner_chat!r}")
            send_message(chat_id, 'Comando indisponível. Se precisar, use /vendedor.')
            return "ok", 200
        parts = text.strip().split()
        if len(parts) < 2:
            send_message(chat_id, 'Use o comando com o número do pedido. Ex.: /pago 12 ou /entregue 12')
            return "ok", 200
        try:
            order_id = int(parts[1])
        except ValueError:
            send_message(chat_id, 'O número do pedido deve ser numérico. Ex.: /pago 12')
            return "ok", 200
        if command == "/pago":
            result, order = apply_status(order_id, "pago", "pix_confirmado_em")
            if result == "nao encontrado":
                send_message(chat_id, f"Não achei o pedido {order_id}.")
                return "ok", 200
            send_message(chat_id, f"Pedido {order_id} marcado como PAGO. Cliente avisado para combinar a entrega.")
            if order:
                send_message(
                    order["chat_id"],
                    "Seu pagamento foi CONFIRMADO. O atendente vai te chamar aqui para combinar a entrega.\n"
                    'Preparado o char certo e on-line no horário combinado.',
                )
            return "ok", 200
        if command == "/entregue":
            result, order = apply_status(order_id, "entregue", "entregue_em")
            if result == "nao encontrado":
                send_message(chat_id, f"Não achei o pedido {order_id}.")
                return "ok", 200
            send_message(chat_id, f"Pedido {order_id} marcado como ENTREGUE. Cliente encerrado.")
            if order:
                send_message(
                    order["chat_id"],
                    'RC entregues! Obrigado pela confiança e até a próxima. =)',
                )
                AWAITING_FEEDBACK[order["chat_id"]] = {"order_id": order["id"], "ts": time.time()}
                send_message(
                    order["chat_id"],
                    "Tudo certo com a entrega? Se puder, responde aqui com uma nota de 1 a 5 "
                    'e/ou um comentário rápido (ex.: "5, super rápido").',
                )
            return "ok", 200

    if command == "/relatorio":
        owner_chat = load_env_key("TELEGRAM_OWNER_CHAT_ID")
        if str(chat_id) != str(owner_chat):
            print(f"[owner] /relatorio recusado: chat={chat_id} | TELEGRAM_OWNER_CHAT_ID={owner_chat!r}")
            send_message(chat_id, 'Comando indisponível. Se precisar, use /vendedor.')
            return "ok", 200
        send_message(chat_id, relatorio_mensal())
        return "ok", 200

    if chat_type == "private" and chat_id in AWAITING_EMAIL:
        info = AWAITING_EMAIL.get(chat_id)
        expired = bool(info) and time.time() - info["ts"] > EMAIL_EXPIRY_SECONDS
        candidate = text.strip()
        if expired:
            AWAITING_EMAIL.pop(chat_id, None)
            send_message(
                chat_id,
                'O tempo para gerar o Pix expirou. Faça um novo pedido ou use /vendedor.',
            )
            return "ok", 200
        if not EMAIL_RE.match(candidate):
            send_message(
                chat_id,
                "Preciso do seu e-mail (ex.: nome@exemplo.com) para gerar o QR Code do Pix.",
            )
            return "ok", 200
        AWAITING_EMAIL.pop(chat_id, None)
        order = STORE.find(info["order_id"]) if info else None
        if not order:
            send_message(chat_id, 'Não encontrei seu pedido. Fale com um atendente usando /vendedor.')
            return "ok", 200
        ok, result = create_pix_charge(order, candidate)
        try:
            STORE.save_email(order["id"], candidate)
        except Exception as error:
            print(f"[auth] falha ao gravar e-mail do pedido: {error}")
        if not ok:
            send_message(chat_id, 'Não consegui gerar o Pix agora. ' + result)
            send_message(chat_id, payment_text(order))
        else:
            send_qr(chat_id, result, order)
            notify_owner_pix(result, order)
        return "ok", 200

    if chat_type == "private" and chat_id in AWAITING_CHAR:
        confirmacao = text.strip().lower().rstrip(".!")
        if confirmacao in CHAR_YES_WORDS:
            _finalizar_confirmacao_char(chat_id, True)
        else:
            _finalizar_confirmacao_char(chat_id, False)
        return "ok", 200

    if chat_type == "private" and chat_id in AWAITING_FEEDBACK:
        fb_info = AWAITING_FEEDBACK.get(chat_id) or {}
        if time.time() - fb_info.get("ts", 0) > FEEDBACK_EXPIRY_SECONDS:
            AWAITING_FEEDBACK.pop(chat_id, None)
            send_message(
                chat_id,
                'O tempo para enviar o feedback expirou, mas obrigado pela confiança!',
            )
            return "ok", 200
        fb_text = text.strip()
        fb_lower = fb_text.lower()
        is_command = fb_lower.startswith("/")
        if not is_command and not looks_like_order(fb_text):
            AWAITING_FEEDBACK.pop(chat_id, None)
            order_id = fb_info.get("order_id")
            score = None
            m = re.search(r"\b([1-5])\b", fb_lower)
            if m:
                score = int(m.group(1))
            try:
                STORE.update(order_id, {"feedback": fb_text, "feedback_score": score})
                audit_log(
                    "feedback_recebido",
                    f"pedido {order_id} | nota {score} | {fb_text[:120]}",
                )
            except Exception as error:
                print(f"[feedback] falha ao gravar feedback do pedido {order_id}: {error}")
            owner_chat = load_env_key("TELEGRAM_OWNER_CHAT_ID")
            if owner_chat:
                score_part = f" (nota {score}/5)" if score else ""
                send_message(
                    owner_chat,
                    f"⭐ FEEDBACK do pedido {order_id}:\n\"{fb_text}\"{score_part}",
                )
            send_message(chat_id, 'Obrigado pelo feedback! Sua opinião ajuda a melhorar.')
            return "ok", 200

    if chat_type == "private" and looks_like_order(text):
        entry = build_order(chat_id, username, text)
        bloqueio = _coins_check(entry.get("tc"))
        if bloqueio:
            send_message(chat_id, bloqueio)
            return "ok", 200
        if not entry.get("tc") and not entry.get("char"):
            send_message(
                chat_id,
                "Consegui ver que você quer comprar, mas faltou a quantidade de RC e o char. "
                'Manda assim: "500 rc, char Teste, pagamento pix".',
            )
            return "ok", 200
        if not entry.get("tc"):
            send_message(chat_id, "Me diz a quantidade de Rubini Coins (ex.: 500 rc).")
            return "ok", 200
        if not entry.get("char"):
            send_message(chat_id, "Me diz o nome do personagem (ex.: inmortals).")
            return "ok", 200
        AWAITING_CHAR[chat_id] = {
            "entry": dict(entry),
            "ts": time.time(),
        }
        send_message(
            chat_id,
            confirmacao_pedido_text(entry),
            reply_markup=CONFIRM_KEYBOARD,
        )
        return "ok", 200

        entry = save_order(entry)
        notify_owner(entry)
        push_to_sheet(entry)
        if MP_ACCESS_TOKEN and entry.get("id"):
            ok_pix, result = create_pix_charge(entry, _default_payer_email())
            if ok_pix:
                send_qr(chat_id, result, entry)
                notify_owner_pix(result, entry)
            else:
                send_message(chat_id, 'Não consegui gerar o Pix agora. ' + result)
                notify_payment(entry)
            return "ok", 200
        notify_payment(entry)

    if rate_limited(chat_id):
        send_message(
            chat_id,
            'Calma aí! Estou processando suas mensagens em sequência. Escreva aqui em instantes.',
        )
        return "ok", 200

    reply = ask_ai(text)
    send_message(chat_id, reply)
    return "ok", 200


@app.route("/webhook/mp", methods=["POST"])
def webhook_mp():
    if _mp_rate_limited():
        return "too many", 429
    payload = request.get_json(silent=True) or {}
    data = payload.get("data") or {}
    payment_id = data.get("id")
    if not payment_id or not MP_ACCESS_TOKEN:
        return "ok", 200
    try:
        response = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
            timeout=15,
        )
    except Exception as error:
        print(f"[mp] erro ao consultar pagamento: {error}")
        return "ok", 200
    if response.status_code != 200:
        return "ok", 200
    payment = response.json()
    reference = payment.get("external_reference") or ""
    if payment.get("status") != "approved":
        if reference.isdigit():
            audit_log(
                "erro_pagamento",
                f"pedido {reference} | mp status {payment.get('status') or '-'}",
            )
        return "ok", 200
    if reference.startswith(("PUB-", "DES-", "VIP-")):
        _marketplace_confirm(reference, payment_id)
        return "ok", 200
    if not reference.isdigit():
        return "ok", 200
    order_id = int(reference)
    order = STORE.find(order_id)
    if not order:
        print(f"[mp] pedido {order_id} nao encontrado")
        return "ok", 200
    if (order.get("status") or "pendente") == "pago":
        return "ok", 200
    apply_status(order_id, "pago", "pix_confirmado_em")
    owner_chat = load_env_key("TELEGRAM_OWNER_CHAT_ID")
    send_message(
        order["chat_id"],
        "Seu pagamento foi CONFIRMADO. O atendente vai te chamar aqui para combinar a entrega.\n"
        'Deixa o char certo on-line no horário combinado.',
    )
    if owner_chat:
        linhas = ["💸 PAGAMENTO CONFIRMADO - PIX", f"Pedido: {order_id}"]
        if order.get("tc"):
            linhas.append(f"RC: {order['tc']}")
        if order.get("preco"):
            linhas.append(f"Valor: {order['preco']}")
        if order.get("char"):
            linhas.append(f"Char: {order['char']}")
        if order.get("mundo"):
            linhas.append(f"Mundo: {order['mundo']}")
        linhas.append("Pagamento confirmado automaticamente via Mercado Pago.")
        linhas.append(f"Chame o cliente para a entrega e use /entregue {order_id}")
        send_message(owner_chat, "\n".join(linhas))
    return "ok", 200


def parse_brl(value):
    if not value:
        return 0.0
    text = str(value).replace("R$", "").replace(" ", "")
    return float(text.replace(".", "").replace(",", "."))


def dashboard_metrics(orders):
    faturado = 0.0
    por_dia = {}
    clientes = set()
    pagos = 0
    for order in orders:
        if (order.get("status") or "pendente") == "pago":
            faturado += parse_brl(order.get("preco"))
            pagos += 1
        dia = (order.get("data") or "")[:10]
        if dia:
            por_dia[dia] = por_dia.get(dia, 0) + 1
        chat = order.get("chat_id")
        if chat is not None:
            clientes.add(chat)
    return faturado, por_dia, clientes, pagos


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if not dashboard_allowed():
        return "Acesso restrito.", 401
    orders = STORE.list()
    faturado, por_dia, clientes, pagos = dashboard_metrics(orders)

    dias = []
    from datetime import timedelta
    base = datetime.now().date()
    for offset in range(13, -1, -1):
        dia = base - timedelta(days=offset)
        dias.append((dia.isoformat(), por_dia.get(dia.isoformat(), 0)))
    max_dia = max((count for _, count in dias), default=0) or 1

    bars = []
    for dia, count in dias:
        width = int((count / max_dia) * 100)
        bars.append(
            f"<div class='day'><span class='label'>{dia}</span>"
            f"<div class='bar'><div class='fill' style='width:{width}%'></div></div>"
            f"<span class='value'>{count}</span></div>"
        )

    total_brl = f"R$ {faturado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    rows = ""
    for order in sorted(orders, key=lambda o: (o.get("data") or ""), reverse=True)[:10]:
        status = order.get("status") or "pendente"
        rows += (
            "<tr>"
            f"<td>{html.escape(str(order.get('data') or '-'))}</td>"
            f"<td>{html.escape(str(order.get('char') or '-'))}</td>"
            f"<td>{html.escape(str(order.get('tc') or '-'))} RC</td>"
            f"<td>{html.escape(str(order.get('preco') or '-'))}</td>"
            f"<td>{html.escape(str(order.get('mundo') or '-'))}</td>"
            f"<td>{html.escape(str(order.get('pagamento') or '-'))}</td>"
            f"<td>{html.escape(str(order.get('usuario') or '-'))}</td>"
            f"<td><span class='status {html.escape(status)}'>{html.escape(status)}</span></td>"
            "</tr>"
        )
    if not rows:
        rows = "<tr><td colspan='8' class='empty'>Nenhum pedido ainda</td></tr>"
    title = html.escape("BAPZX - Dashboard de vendas")

    page = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 0; background: #0f172a; color: #e2e8f0; }}
header {{ background: #1e293b; padding: 18px 24px; }}
header h1 {{ margin: 0; font-size: 20px; }}
main {{ padding: 24px 32px; max-width: none; margin: 0; }}
.cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
.card {{ background: #1e293b; border-radius: 10px; padding: 16px 20px; flex: 1; min-width: 160px; }}
.card .num {{ font-size: 26px; font-weight: bold; color: #4ade80; }}
.card .lbl {{ font-size: 13px; color: #94a3b8; }}
section {{ background: #1e293b; border-radius: 10px; padding: 16px 20px; margin-bottom: 24px; }}
section h2 {{ margin-top: 0; font-size: 16px; }}
.day {{ display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }}
.label {{ width: 110px; font-size: 12px; color: #94a3b8; }}
.bar {{ flex: 1; background: #334155; height: 14px; border-radius: 7px; overflow: hidden; }}
.fill {{ height: 100%; background: #4ade80; }}
.value {{ width: 28px; font-size: 12px; text-align: right; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ text-align: left; padding: 7px 8px; border-bottom: 1px solid #334155; }}
th {{ color: #94a3b8; font-weight: normal; }}
.empty {{ text-align: center; color: #64748b; padding: 18px; }}
.status {{ padding: 2px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; }}
.status.pendente {{ background: #78350f; color: #fbbf24; }}
.status.pago {{ background: #064e3b; color: #4ade80; }}
.status.entregue {{ background: #1e3a5f; color: #60a5fa; }}
.status.cancelado {{ background: #7f1d1d; color: #f87171; }}
</style>
</head>
<body>
<header><h1>BAPZX - Dashboard de vendas</h1></header>
<main>
<div class="cards">
<div class="card"><div class="num">{total_brl}</div><div class="lbl">Faturado (pagos)</div></div>
<div class="card"><div class="num">{pagos}</div><div class="lbl">Pagos</div></div>
<div class="card"><div class="num">{len(orders)}</div><div class="lbl">Pedidos</div></div>
<div class="card"><div class="num">{len(clientes)}</div><div class="lbl">Clientes</div></div>
</div>
<section><h2>Pedidos nos últimos 14 dias</h2>{''.join(bars)}</section>
<section><h2>Últimos pedidos</h2>
<table><tr><th>Quando</th><th>Char</th><th>Qtd</th><th>Valor</th><th>Mundo</th><th>Pagamento</th><th>Cliente</th><th>Status</th></tr>{rows}</table>
</section>
</main>
</body>
</html>"""
    return page, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/pedidos", methods=["GET"])
def pedidos():
    if not dashboard_allowed():
        return "Acesso restrito.", 401
    return f"{STORE.count()} pedido(s) registrado(s) | dashboard: /dashboard?key=SUA_CHAVE", 200


AUTH_LAYOUT = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BAPZX · @@TITLE@@</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #0b0f1a;
  --panel: #111a2c;
  --panel-2: #18233a;
  --border: #22304a;
  --border-2: #2c3d5e;
  --text: #e6edf7;
  --muted: #8ea0b8;
  --green: #4ade80;
  --purple: #a78bfa;
  --blue: #60a5fa;
  --amber: #fbbf24;
  --red: #f87171;
  --grad: linear-gradient(135deg,#34d399 0%,#4ade80 35%,#60a5fa 100%);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  font-family: 'Inter', Arial, sans-serif; margin: 0;
  background: radial-gradient(1100px 520px at 85% -10%, rgba(124,58,237,.14), transparent 60%),
              radial-gradient(900px 460px at -10% 0%, rgba(52,211,153,.10), transparent 55%),
              var(--bg);
  color: var(--text); min-height: 100vh; line-height: 1.5;
}
a { color: var(--blue); text-decoration: none; }
a:hover { text-decoration: underline; }
a:focus-visible, button:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible {
  outline: 2px solid var(--purple); outline-offset: 2px; border-radius: 8px;
}
header {
  position: sticky; top: 0; z-index: 40;
  background: rgba(11,15,26,.86); backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding: 12px 24px;
  display: flex; align-items: center; justify-content: space-between; gap: 14px;
}
header h1 { margin: 0; font-size: 18px; display: flex; align-items: center; gap: 10px; white-space: nowrap; }
header a { color: var(--muted); font-size: 13px; text-decoration: none; }
header a:hover { color: #fff; }
.brand { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 19px; letter-spacing: 2px; color: #fff; }
.brand span { background: var(--grad); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.brand-tag { font-family: 'Sora', sans-serif; font-size: 12px; font-weight: 600; color: var(--muted); letter-spacing: .4px; }
main { padding: 26px 32px 46px; max-width: none; margin: 0; }
label { display: block; margin-top: 8px; color: var(--muted); font-size: 13px; font-weight: 600; }
.frow { display:grid; gap:10px 12px; margin:0 0 10px; }
.frow>div { min-width:0; }
.frow.c2 { grid-template-columns:repeat(2,minmax(0,1fr)); }
.frow.c3 { grid-template-columns:repeat(3,minmax(0,1fr)); }
@media(max-width:900px){.frow.c3{grid-template-columns:repeat(2,minmax(0,1fr));}}
@media(max-width:640px){.frow.c2,.frow.c3{grid-template-columns:minmax(0,1fr);}}
input, select, textarea {
  width: 100%; margin-top: 5px; padding: 9px 12px;
  border: 1px solid var(--border-2); border-radius: 10px;
  background: var(--bg); color: var(--text); font-size: 14px; box-sizing: border-box;
  transition: border-color .15s;
}
input:focus, select:focus, textarea:focus { border-color: var(--purple); outline: 2px solid transparent; }
input:disabled { opacity: .55; }
.btn {
  display: inline-flex; align-items: center; gap: 8px;
  background: var(--grad); color: #04281a; border: 0; border-radius: 10px;
  padding: 10px 18px; font-weight: 700; cursor: pointer; font-size: 14px; text-decoration: none;
  transition: filter .15s, transform .05s;
}
.btn:hover { filter: brightness(1.08); text-decoration: none; }
.btn:active { transform: scale(.98); }
.btn.ghost { background: transparent; color: var(--blue); border: 1px solid var(--border-2); }
.btn.ghost:hover { background: rgba(96,165,250,.10); }
.btn.blue { background: linear-gradient(135deg,#3b82f6,#60a5fa); color: #fff; }
.btn.small { padding: 7px 12px; font-size: 12.5px; border-radius: 8px; }
.legal-note { font-size: 12px; color: var(--muted); margin-top: 12px; }
.size-note { font-size: 12px; color: var(--muted); }
.note { font-size: 13px; color: var(--muted); }
footer {
  border-top: 1px solid var(--border); margin-top: 40px; padding: 22px 24px;
  background: #070b12; font-size: 12.5px; color: var(--muted); text-align: center;
}
footer a { color: #9db0cc; text-decoration: none; margin: 0 10px; }
footer a:hover { color: #fff; }
.foot-main { margin-bottom: 8px; }
/* ---------- Header do cliente ---------- */
.nav { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.nav-link {
  padding: 7px 12px; border-radius: 999px; font-size: 13px; font-weight: 600; color: var(--muted);
  transition: background .15s, color .15s;
}
.nav-link:hover { background: rgba(96,165,250,.12); color: #fff; text-decoration: none; }
.nav-link.active { background: rgba(167,139,250,.18); color: var(--purple); }
.user { position: relative; display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 6px 10px; border-radius: 999px; border: 1px solid var(--border); background: rgba(17,26,44,.6); }
.avatar {
  width: 30px; height: 30px; border-radius: 50%; background: var(--grad);
  color: #04281a; font-weight: 800; font-size: 12px; display: flex; align-items: center; justify-content: center;
}
.user .uname { font-size: 13px; color: #fff; max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-menu {
  position: absolute; right: 0; top: calc(100% + 10px); min-width: 190px;
  background: var(--panel-2); border: 1px solid var(--border-2); border-radius: 12px;
  padding: 6px; box-shadow: 0 18px 40px rgba(0,0,0,.5); z-index: 50;
  opacity: 0; visibility: hidden; transform: translateY(-6px); transition: .18s;
}
.user:hover .user-menu, .user:focus-within .user-menu { opacity: 1; visibility: visible; transform: translateY(0); }
.user-menu a {
  display: block; padding: 9px 12px; border-radius: 8px; color: var(--text); font-size: 13.5px;
}
.user-menu a:hover { background: rgba(96,165,250,.12); color: #fff; text-decoration: none; }
.user-menu a.danger:hover { background: rgba(248,113,113,.14); color: var(--red); }
.user-menu .u-name { padding: 8px 12px; font-weight: 700; color: #fff; }
.user-menu .u-mail { padding: 0 12px 8px; font-size: 12px; color: var(--muted); }
.user-menu hr { border: 0; border-top: 1px solid var(--border-2); margin: 5px 8px; }
/* ---------- Welcome ---------- */
.welcome {
  display: flex; align-items: center; justify-content: space-between; gap: 18px; flex-wrap: wrap;
  background: linear-gradient(120deg, rgba(124,58,237,.16), rgba(96,165,250,.10)), var(--panel);
  border: 1px solid rgba(167,139,250,.35); border-radius: 16px; padding: 22px 24px; margin-bottom: 20px;
}
.welcome h2 { margin: 0 0 6px; font-size: 22px; font-family: 'Sora', sans-serif; }
.welcome p { margin: 0; color: var(--muted); font-size: 14px; }
/* ---------- KPIs ---------- */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin: 20px 0; }
.kpi {
  background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 16px 18px;
  display: flex; align-items: center; gap: 14px; transition: border-color .15s, transform .1s;
}
.kpi:hover { border-color: var(--border-2); transform: translateY(-2px); }
.kpi .ic {
  width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0;
}
.kpi .num { font-size: 24px; font-weight: 800; font-family: 'Sora', sans-serif; line-height: 1.1; }
.kpi .lbl { font-size: 12.5px; color: var(--muted); }
.kpi.green .ic { background: rgba(74,222,128,.14); }
.kpi.green .num { color: var(--green); }
.kpi.amber .ic { background: rgba(251,191,36,.14); }
.kpi.amber .num { color: var(--amber); }
.kpi.blue .ic { background: rgba(96,165,250,.14); }
.kpi.blue .num { color: var(--blue); }
.kpi.purple .ic { background: rgba(167,139,250,.16); }
.kpi.purple .num { color: var(--purple); }
/* ---------- Painéis ---------- */
.panel {
  background: var(--panel); border: 1px solid var(--border); border-radius: 16px;
  padding: 20px 22px; margin: 18px 0;
}
.panel h2 { margin: 0 0 14px; font-size: 16px; font-family: 'Sora', sans-serif; display: flex; align-items: center; gap: 10px; }
.panel-hd { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; margin-bottom: 12px; }
.panel-hd h2 { margin: 0; }
section { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 18px 22px; margin: 18px 0; }
section h2 { margin-top: 0; font-size: 15px; font-family: 'Sora', sans-serif; }
/* ---------- Tabelas ---------- */
.table-wrap { overflow-x: auto; border-radius: 12px; border: 1px solid var(--border); }
table { width: 100%; border-collapse: collapse; font-size: 13.5px; min-width: 640px; }
th, td { text-align: left; padding: 11px 12px; border-bottom: 1px solid var(--border); vertical-align: middle; }
th { color: var(--muted); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: .4px; background: rgba(24,35,58,.5); }
tbody tr:hover { background: rgba(96,165,250,.06); }
.empty { text-align: center; color: var(--muted); padding: 20px; }
/* ---------- Badges de status ---------- */
.badge {
  display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px;
  font-size: 11.5px; font-weight: 700; border: 1px solid transparent;
}
.badge::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.badge.pendente { background: rgba(251,191,36,.12); color: var(--amber); border-color: rgba(251,191,36,.3); }
.badge.pago { background: rgba(74,222,128,.12); color: var(--green); border-color: rgba(74,222,128,.3); }
.badge.entregue { background: rgba(96,165,250,.12); color: var(--blue); border-color: rgba(96,165,250,.3); }
.badge.cancelado { background: rgba(248,113,113,.12); color: var(--red); border-color: rgba(248,113,113,.3); }
.badge.aberto { background: rgba(251,191,36,.12); color: var(--amber); border-color: rgba(251,191,36,.3); }
.badge.respondido { background: rgba(96,165,250,.12); color: var(--blue); border-color: rgba(96,165,250,.3); }
.badge.encerrado { background: rgba(142,160,184,.14); color: var(--muted); border-color: rgba(142,160,184,.3); }
/* compat (painel usa .status) */
.status { padding: 2px 9px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.status.pendente { background: #78350f; color: #fbbf24; }
.status.pago { background: #064e3b; color: #4ade80; }
.status.entregue { background: #1e3a5f; color: #60a5fa; }
.status.cancelado { background: #7f1d1d; color: #f87171; }
.acts form { display: inline; }
.acts button { background: #334155; border: 0; color: #e2e8f0; border-radius: 6px; padding: 5px 10px; cursor: pointer; font-size: 12px; }
.acts button.pago { background: #064e3b; color: #4ade80; }
.acts button.entregue { background: #1e3a5f; color: #60a5fa; }
.big { display: inline-block; background: var(--grad); color: #04281a; text-decoration: none; padding: 12px 22px; border-radius: 10px; font-weight: 700; }
/* ---------- Empty state ---------- */
.empty-state {
  text-align: center; padding: 40px 20px; border: 1px dashed var(--border-2); border-radius: 16px; background: rgba(17,26,44,.4);
}
.empty-state .em-ic { font-size: 42px; margin-bottom: 10px; }
.empty-state h3 { margin: 0 0 6px; font-size: 17px; font-family: 'Sora', sans-serif; }
.empty-state p { margin: 0 auto 16px; color: var(--muted); font-size: 13.5px; max-width: 420px; }
/* ---------- Cartões de ajuda / perfil ---------- */
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 14px; }
.help-card, .field-card {
  background: var(--panel-2); border: 1px solid var(--border); border-radius: 14px; padding: 16px 18px; text-decoration: none; transition: border-color .15s, transform .1s;
}
.help-card:hover { border-color: var(--purple); transform: translateY(-2px); text-decoration: none; }
.help-card .h-ic { font-size: 22px; margin-bottom: 8px; }
.help-card .h-t { font-weight: 700; color: var(--text); font-size: 14.5px; }
.help-card .h-s { color: var(--muted); font-size: 12.5px; margin-top: 3px; }
.field-card .f-lbl { font-size: 11.5px; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; }
.field-card .f-val { font-size: 15px; font-weight: 600; margin-top: 2px; }
/* ---------- Aviso / erro ---------- */
.alert {
  display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;
  background: rgba(248,113,113,.10); border: 1px solid rgba(248,113,113,.35); border-radius: 12px;
  padding: 12px 16px; font-size: 13.5px; color: var(--red); margin-bottom: 16px;
}
.alert a { color: var(--red); font-weight: 700; }
.alert.info { background: rgba(96,165,250,.10); border-color: rgba(96,165,250,.35); color: var(--blue); }
.alert.info a { color: var(--blue); }
.fade-in { animation: fadeUp .35s ease both; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } .fade-in { animation: none; } }
/* ---------- Responsivo ---------- */
@media (max-width: 900px) {
  header { flex-wrap: wrap; }
  .user .uname { display: none; }
}
@media (max-width: 640px) {
  main { padding: 18px 14px 36px; }
  header { padding: 10px 14px; }
  .welcome { padding: 16px 18px; }
  .welcome h2 { font-size: 18px; }
  .kpis { gap: 10px; }
  .kpi .num { font-size: 20px; }
  .panel, section { padding: 15px 16px; }
  .nav { gap: 2px; }
  .nav-link { padding: 6px 9px; font-size: 12px; }
  .user { padding: 5px 8px; }
  .foot-main a { display: inline-block; margin: 4px 6px; }
}
@media (max-width: 480px) {
  .kpis { grid-template-columns: 1fr 1fr; }
  .brand-tag { display: none; }
  .nav-link { padding: 5px 7px; font-size: 11px; }
}
</style>
</head>
<body>
<header>
  <h1><span class="brand">BAP<span>ZX</span></span> <span class="brand-tag">· @@BRAND@@</span></h1>
  @@TOP@@
</header>
<main class="fade-in">@@BODY@@</main>
<footer>
  <div class="foot-main">
    © 2026 BAPZX · Vendas de RC no Tibia
  </div>
  <div>
    <a href="/privacidade">Política de Privacidade</a>
    <a href="/termos">Termos de Uso</a>
    <a href="/reembolso">Política de Reembolso</a>
    <a href="@@WHATSAPP@@" rel="noopener">WhatsApp</a>
  </div>
</footer>
</body>
</html>"""


def _render_layout(title, brand, top, body):
    return (
        AUTH_LAYOUT.replace("@@TITLE@@", html.escape(title))
        .replace("@@BRAND@@", html.escape(brand))
        .replace("@@TOP@@", top)
        .replace("@@BODY@@", body)
        .replace("@@WHATSAPP@@", SERVICE_WHATSAPP_LINK),
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )


def _page(title, brand, top, body):
    return _render_layout(title, brand, top, body)


def current_user():
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
        "sub": session.get("sub"),
    }


def _fetch_user_row(email):
    """Retorna a linha da tabela users (RBAC) para um e-mail, ou None."""
    if not (STORE.remote and email):
        return None
    try:
        response = requests.get(
            f"{STORE.url}/rest/v1/users?email=eq.{email}&select=*",
            headers=STORE._headers(),
            timeout=15,
        )
        if response.status_code == 200:
            rows = response.json() or []
            if rows:
                return rows[0]
    except Exception as error:
        print(f"[rbac] falha ao consultar users: {error}")
    return None


def resolve_cargo_perms(email):
    """Decide cargo+permissões para um e-mail logado.

    1) MASTER_EMAILS (env) => MASTER com tudo;
    2) users.ativo com cargo => cargo + permissões individuais (se houver);
    3) senão => CLIENTE.
    """
    if rbac.eh_master(email, MASTER_EMAILS):
        return "MASTER", sorted(rbac.perms_efetivas("MASTER"))
    row = _fetch_user_row(email)
    if row and row.get("ativo"):
        cargo = (row.get("cargo") or "CLIENTE").upper()
        if rbac.cargo_valido(cargo) and cargo != "MASTER":
            explicitas = row.get("permissoes") or []
            return cargo, sorted(rbac.perms_efetivas(cargo, explicitas))
    return "CLIENTE", []


def save_profile(email, name, sub, role):
    if not (STORE.remote and email):
        return False
    payload = {"email": email, "name": name, "sub": sub or "", "role": role}
    headers = {
        **STORE._headers(),
        "Prefer": "resolution=merge-duplicates",
    }
    response = requests.post(
        f"{STORE.url}/rest/v1/profiles?on_conflict=email",
        headers=headers,
        json=payload,
        timeout=15,
    )
    return response.status_code in (200, 201)


def _orders_rows(orders, with_actions=False):
    rows = ""
    for order in sorted(orders, key=lambda o: o.get("data") or "", reverse=True):
        status = order.get("status") or "pendente"
        email = (order.get("email") or "-")
        actions = ""
        if with_actions:
            form = (
                "<form method='post' action='/admin/marcar'>"
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
            f"<td>{html.escape(email)}</td>"
            f"<td><span class='status {html.escape(status)}'>{html.escape(status)}</span></td>"
            f"<td class='acts'>{actions}</td>"
            "</tr>"
        )
    if not rows:
        rows = "<tr><td colspan='9' class='empty'>Nenhum pedido encontrado.</td></tr>"
    return rows


@app.route("/privacidade")
def privacidade():
    top = (
        "<a href='https://wa.me/5519991813598' rel='noopener'>WhatsApp</a>"
    )
    body, _ = legais._render_legal_page(
        "Política de Privacidade",
        legais.privacidade_html(),
        "Como tratamos seus dados pessoais em conformidade com a LGPD (Lei 13.709/2018).",
        "15/09/2026",
        top,
    )
    body += "<p class='size-note'>BAPZX · WhatsApp " + legais.WHATSAPP_DISPLAY + "</p>"
    return _page("Política de Privacidade", "Legal", top, body)


@app.route("/termos")
def termos():
    top = ""
    body, _ = legais._render_legal_page(
        "Termos de Uso",
        legais.termos_html(),
        "Regras gerais para uso dos serviços BAPZX.",
        "15/09/2026",
        top,
    )
    return _page("Termos de Uso", "Legal", top, body)


@app.route("/reembolso")
def reembolso():
    top = ""
    body, _ = legais._render_legal_page(
        "Política de Reembolso",
        legais.reembolso_html(),
        "Condições para solicitar reembolso de pedidos.",
        "15/09/2026",
        top,
    )
    return _page("Política de Reembolso", "Legal", top, body)


@app.route("/privacidade/pdf")
def privacidade_pdf():
    try:
        bytes_pdf = legais.privacidade_pdf_bytes()
    except Exception as error:
        print(f"[legal] falha ao gerar PDF: {error}")
        return "Falha ao gerar o PDF. Tente novamente em instantes.", 500
    return (
        bytes_pdf,
        200,
        {
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="politica-de-privacidade-bapzx.pdf"',
            "Content-Length": str(len(bytes_pdf)),
        },
    )


@app.route("/login")
def login():
    if not _host_ok(request.host):
        return "Origem inválida.", 403
    if not GOOGLE_OAUTH_READY:
        return _page(
            "Login",
            "Área do cliente",
            "",
            "<h2>Login indisponível</h2>"
            "<p>As credenciais do Google ainda não foram configuradas no servidor "
            "(GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET). Avise o administrador.</p>",
        )
    redirect_uri = f"https://{request.host}/oauth/callback"
    return _oauth.google.authorize_redirect(redirect_uri)


@app.route("/oauth/callback")
def oauth_callback():
    if not GOOGLE_OAUTH_READY:
        return "Login indisponível.", 503
    try:
        token = _oauth.google.authorize_access_token()
    except Exception as error:
        print(f"[auth] falha no callback OAuth: {error}")
        return "Falha ao autenticar com o Google. Tente novamente.", 400
    info = token.get("userinfo") or {}
    email = (info.get("email") or "").strip().lower()
    if not email or not info.get("email_verified"):
        return "Conta Google sem e-mail verificado. Não é possível continuar.", 403
    name = info.get("name") or email.split("@")[0]
    sub = info.get("sub") or ""
    try:
        cargo, perms = resolve_cargo_perms(email)
    except Exception as error:
        print(f"[rbac] falha ao resolver cargo: {error}")
        cargo, perms = "CLIENTE", []
    role = "admin" if cargo != "CLIENTE" else "cliente"
    try:
        save_profile(email, name, sub, role)
    except Exception as error:
        print(f"[auth] falha ao salvar perfil: {error}")
    session["email"] = email
    session["name"] = name
    session["role"] = role
    session["cargo"] = cargo
    session["perms"] = perms
    session["sub"] = sub
    session["sid"] = secrets.token_urlsafe(24)
    session.permanent = True
    _registrar_sessao(email)
    if cargo != "CLIENTE":
        audit_log("login", f"{email} | {name}")
    return redirect("/acesso")


@app.route("/logout")
def logout():
    _encerrar_sessao(session.get("sid"))
    if session.get("email"):
        audit_log("logout", session.get("email", ""))
    session.clear()
    return redirect(PORTFOLIO_URL)


@app.route("/acesso")
def acesso():
    user = current_user()
    if not user:
        return redirect("/login")
    top = (
        "<span style='color:#94a3b8;font-size:12px'>"
        f"Bem-vindo, {html.escape(user['name'])}</span> "
        "<a href='/logout' style='margin-left:8px'>Sair</a>"
    )
    admin_btn = ""
    if user.get("cargo") != "CLIENTE" and user.get("perms"):
        admin_btn = (
            "<a href='/admin' style='display:block;background:linear-gradient(135deg,#312e81,#4c1d95);"
            "border:2px solid #7c3aed;border-radius:14px;padding:28px 32px;text-decoration:none;color:#e2e8f0;flex:1;min-width:200px'>"
            "<div style='font-size:28px;margin-bottom:8px'>&#9881;</div>"
            "<div style='font-size:22px;font-weight:bold;margin-bottom:4px'>Administração</div>"
            "<div style='font-size:13px;color:#c4b5fd'>Área restrita da equipe BAPZX</div>"
            "</a>"
        )
    body = (
        "<section style='background:transparent;padding:0'>"
        "<h2 style='font-size:16px;margin-bottom:20px'>Para onde deseja ir?</h2>"
        "<div style='display:flex;gap:16px;flex-wrap:wrap'>"
        "<a href='/cliente' style='display:block;background:linear-gradient(135deg,#064e3b,#065f46);"
        "border:2px solid #10b981;border-radius:14px;padding:28px 32px;text-decoration:none;color:#e2e8f0;flex:1;min-width:200px'>"
        "<div style='font-size:28px;margin-bottom:8px'>&#128100;</div>"
        "<div style='font-size:22px;font-weight:bold;margin-bottom:4px'>Cliente</div>"
        "<div style='font-size:13px;color:#6ee7b7'>Meus pedidos, perfil e suporte</div>"
        "</a>"
        f"{admin_btn}"
        "</div></section>"
    )
    return _page("Escolha a área", "Escolha a área", top, body)


def _title_initials(name):
    parts = [p for p in re.split(r"[\s._-]+", name or "") if p]
    base = (parts[0] if parts else "C")[:1] + (parts[-1] if len(parts) > 1 else "")[:1]
    return html.escape(base.upper() or "C")


def _cliente_vip_chip(user):
    if not _mk_vip_ativo(user.get("email") or ""):
        return ""
    return ("<span title='VIP BAPZX ativo' style='background:#0f2a22;border:1px solid #14532d;"
            "color:#4ade80;border-radius:999px;padding:1px 7px;font-size:10px;font-weight:800;"
            "letter-spacing:.3px;flex-shrink:0'>VIP</span>")


def _cliente_user_menu(user):
    nome = user["name"] if user.get("name") else user["email"]
    inicial = _title_initials(nome)
    return (
        "<div class='user' tabindex='0' aria-label='Menu da conta'>"
        f"<span class='avatar' aria-hidden='true'>{inicial}</span>"
        f"<span class='uname'>{html.escape(str(nome))}</span>"
        f"{_cliente_vip_chip(user)}"
        "<div class='user-menu'>"
        f"<div class='u-name'>{html.escape(str(nome))}</div>"
        f"<div class='u-mail'>{html.escape(user['email'])}</div>"
        "<hr>"
        "<a href='/cliente/perfil'>Meu perfil</a>"
        "<a href='/cliente/troca'>MARKTRADE</a>"
        "<a href='/cliente/suporte'>Suporte</a>"
        "<a href='/acesso'>Trocar área</a>"
        "<a class='danger' href='/logout'>Sair</a>"
        "</div></div>"
    )


def _cliente_header(user, active="visao"):
    # Legado: todas as páginas do cliente usam o dashboard (_cliente_dash_page).
    # Mantido para compatibilidade (testes o referenciam).
    nav = (
        "<nav class='nav' aria-label='Navegação do cliente'>"
        "<a class='nav-link %s' href='/cliente'>Visão Geral</a>"
        "<a class='nav-link %s' href='/cliente#pedidos'>Meus Pedidos</a>"
        "<a class='nav-link %s' href='/cliente/troca'>MARKTRADE</a>"
        "<a class='nav-link %s' href='/cliente/suporte'>Suporte</a>"
        "<a class='nav-link %s' href='/cliente/perfil'>Meu Perfil</a>"
        "</nav>"
    ) % (
        "active" if active == "visao" else "",
        "active" if active == "pedidos" else "",
        "active" if active == "troca" else "",
        "active" if active == "suporte" else "",
        "active" if active == "perfil" else "",
    )
    return nav + _cliente_user_menu(user)


TELEGRAM_BOT_LINK = "https://t.me/bapzx_bot"

_CLIENTE_NAV_ITENS = (
    ("visao", "&#127968; Dashboard", "/cliente", "PRINCIPAL"),
    ("pedidos", "&#128230; Meus Pedidos", "/cliente/pedidos", None),
    ("pagamentos", "&#128176; Pagamentos", "/cliente/pagamentos", "FINANCEIRO"),
    ("plano", "&#128142; Meu Plano", "/cliente/plano", None),
    ("troca", "&#127991; MARKTRADE", "/cliente/troca", "NEGOCIAÇÃO"),
    ("servicos", "&#128736; Meus Serviços", "/cliente/servicos", None),
    ("automacoes", "&#9881; Automações", "/cliente/automacoes", "AUTOMAÇÃO"),
    ("bot", "&#129302; Meu Bot", "/cliente/bot", None),
    ("suporte", "&#127915; Suporte", "/cliente/suporte", "AJUDA"),
    ("notificacoes", "&#128276; Notificações", "/cliente/notificacoes", None),
    ("perfil", "&#128100; Meu Perfil", "/cliente/perfil", "CONTA"),
)


def _cliente_pedidos(email):
    """Pedidos do cliente (mais recentes primeiro). Nunca derruba."""
    try:
        mine = [
            o
            for o in STORE.list()
            if (o.get("email") or "").strip().lower() == email
        ]
    except Exception:
        return []
    return sorted(mine, key=lambda o: o.get("data") or "", reverse=True)


def _so_digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))


def _cliente_servicos_catalogo():
    """Catálogo de serviços contratáveis (tabela `servicos`). Nunca derruba."""
    if not STORE.remote:
        return []
    try:
        response = requests.get(
            f"{STORE.url}/rest/v1/servicos?ativo=eq.true&order=ordem.asc&select=*",
            headers=STORE._headers(),
            timeout=15,
        )
        if response.status_code == 200:
            return response.json() or []
    except Exception:
        pass
    return []


def _cliente_servicos_meus(whatsapp):
    """Serviços já contratados: casa pelo WhatsApp (só dígitos) nos últimos
    50 registros de `servicos_manuais`. Nunca derruba."""
    dig = _so_digitos(whatsapp)
    if not (STORE.remote and dig):
        return []
    try:
        response = requests.get(
            f"{STORE.url}/rest/v1/servicos_manuais?order=criado_em.desc&limit=50&select=*",
            headers={**STORE._headers(), "Range": "0-49"},
            timeout=15,
        )
        if response.status_code != 200:
            return []
        return [
            s for s in (response.json() or [])
            if _so_digitos(s.get("whatsapp")) == dig
        ]
    except Exception:
        return []

_CLIENTE_DASH_CSS = """
<style>
.c-shell{display:flex;min-height:100vh}
.c-sidebar{position:fixed;top:0;left:0;bottom:0;width:250px;background:#0e1626;border-right:1px solid #1e2c40;
display:flex;flex-direction:column;z-index:60}
.c-side-brand{display:flex;align-items:center;gap:11px;padding:18px;border-bottom:1px solid #1e2c40}
.c-side-logo{width:36px;height:36px;border-radius:10px;background:var(--grad);display:flex;align-items:center;
justify-content:center;color:#04111b;font-weight:800;font-family:'Sora',sans-serif;font-size:11px;letter-spacing:1px;flex:none}
.c-brand-name{font-family:'Sora',sans-serif;font-weight:800;letter-spacing:2px;font-size:15px;color:#fff}
.c-brand-name span{background:var(--grad);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.c-side-nav{flex:1;overflow-y:auto;padding:14px 10px 8px}
.c-side-group{font-size:10px;letter-spacing:1.6px;text-transform:uppercase;color:#5b6b82;margin:16px 10px 6px;font-weight:600}
.c-side-group:first-child{margin-top:2px}
.c-side-item{display:flex;align-items:center;gap:11px;padding:10px 12px;border-radius:9px;color:#8ea0b8;
text-decoration:none;font-size:14px;margin:2px 0}
.c-side-item:hover{color:#fff;background:rgba(52,211,153,.08);text-decoration:none}
.c-side-item.active{color:#fff;background:linear-gradient(135deg,rgba(52,211,153,.16),rgba(96,165,250,.14));
box-shadow:inset 0 0 0 1px rgba(52,211,153,.28)}
.c-side-item .ic{width:20px;text-align:center;flex:none}
.c-side-foot{padding:12px 10px;border-top:1px solid #1e2c40}
.c-wrap{flex:1;margin-left:250px;min-width:0;display:flex;flex-direction:column}
.c-topbar{position:sticky;top:0;z-index:50;background:rgba(11,17,32,.88);backdrop-filter:blur(8px);
border-bottom:1px solid #1e2c40;display:flex;align-items:center;gap:14px;padding:12px 22px}
.c-hamburger{display:none;background:transparent;border:1px solid #2a3a52;color:#e2e8f0;width:38px;height:38px;
border-radius:9px;cursor:pointer;align-items:center;justify-content:center;font-size:17px;flex:none}
.c-top-title{flex:1;min-width:0}
.c-crumb{font-size:12px;color:#5b6b82;margin-bottom:3px}
.c-top-title h1{margin:0;font-size:20px;font-weight:700;font-family:'Sora',sans-serif;line-height:1.2}
.c-top-actions{display:flex;align-items:center;gap:10px}
.c-wrap main{padding:26px 32px 46px;max-width:none;margin:0;width:100%}
.c-wrap footer{margin-top:auto}
.c-scrim{position:fixed;inset:0;background:rgba(2,6,17,.62);z-index:55;display:none}
.c-scrim.show{display:block}
@media (max-width:1024px){
.c-sidebar{transform:translateX(-100%);transition:transform .2s}
.c-sidebar.open{transform:none}
.c-wrap{margin-left:0}
.c-hamburger{display:inline-flex}
}
@media (max-width:640px){.c-wrap main{padding:18px 14px 36px}.c-topbar{padding:10px 14px}}
</style>
"""

_CLIENTE_DASH_DRAWER_JS = """
<script>
(function () {
  var hb = document.getElementById("c-hamburger"), sd = document.getElementById("c-sidebar"),
      sc = document.getElementById("c-scrim");
  function fecha() { if (sd) sd.classList.remove("open"); if (sc) sc.classList.remove("show"); }
  if (hb) hb.addEventListener("click", function () {
    if (sd) sd.classList.toggle("open"); if (sc) sc.classList.toggle("show");
  });
  if (sc) sc.addEventListener("click", fecha);
})();
</script>
"""


def _cliente_dash_layout():
    """Layout dashboard do cliente (sidebar + topbar), reaproveitando todo o
    CSS do AUTH_LAYOUT. Montado por replace com fallback seguro: se algum
    marcador mudar, a página cai no layout antigo em vez de quebrar."""
    base = AUTH_LAYOUT
    corpo_antigo = (
        "<header>\n"
        '  <h1><span class="brand">BAP<span>ZX</span></span> <span class="brand-tag">· @@BRAND@@</span></h1>\n'
        "  @@TOP@@\n"
        "</header>\n"
        '<main class="fade-in">@@BODY@@</main>'
    )
    corpo_novo = (
        "<div class='c-shell'>\n"
        "<aside class='c-sidebar' id='c-sidebar'>\n"
        "  <div class='c-side-brand'><span class='c-side-logo'>BZ</span>"
        "<span class='c-brand-name'>BAP<span>ZX</span></span></div>\n"
        "  <nav class='c-side-nav' aria-label='Navegação do cliente'>@@NAV@@</nav>\n"
        "  <div class='c-side-foot'>@@FOOT@@</div>\n"
        "</aside>\n"
        "<div class='c-wrap'>\n"
        "<div class='c-topbar'>\n"
        "  <button class='c-hamburger' id='c-hamburger' aria-label='Abrir menu'>&#9776;</button>\n"
        "  <div class='c-top-title'><div class='c-crumb'>Área do Cliente</div><h1>@@PAGE@@</h1></div>\n"
        "  <div class='c-top-actions'>@@USER@@</div>\n"
        "</div>\n"
        '<main class="fade-in">@@BODY@@</main>'
    )
    if corpo_antigo in base:
        base = base.replace(corpo_antigo, corpo_novo)
    cauda_antiga = "</footer>\n</body>\n</html>"
    cauda_nova = (
        "</footer>\n</div>\n</div>\n"
        "<div class='c-scrim' id='c-scrim'></div>\n"
        + _CLIENTE_DASH_DRAWER_JS
        + "\n</body>\n</html>"
    )
    if cauda_antiga in base:
        base = base.replace(cauda_antiga, cauda_nova)
    if _CLIENTE_DASH_CSS not in base:
        base = base.replace("</style>", _CLIENTE_DASH_CSS + "\n</style>", 1)
    return base


_CLIENTE_DASH_LAYOUT = _cliente_dash_layout()


def _voltar_card(titulo, subtitulo, botao, href):
    """Card de voltar padrão (estilo VIP: título + descrição + botão ghost à
    direita). Usa .welcome — proporcional em todas as páginas."""
    return (
        "<div class='welcome'><div><h2>" + html.escape(titulo) + "</h2>"
        f"<p>{html.escape(subtitulo)}</p></div>"
        f"<a class='btn ghost' href='{html.escape(href)}'>{html.escape(botao)}</a></div>"
    )


def _cliente_dash_page(title, page, active, user, body):
    nav = []
    for chave, rotulo, href, grupo in _CLIENTE_NAV_ITENS:
        if grupo:
            nav.append(f"<div class='c-side-group'>{html.escape(grupo)}</div>")
        nav.append(
            f"<a class='c-side-item{' active' if chave == active else ''}' href='{href}'>"
            f"<span class='ic' aria-hidden='true'>{rotulo.split(' ', 1)[0]}</span>"
            f"<span>{html.escape(rotulo.split(' ', 1)[1])}</span></a>"
        )
    foot = (
        "<a class='c-side-item' href='/acesso'><span class='ic' aria-hidden='true'>&#8646;</span>"
        "<span>Trocar área</span></a>"
        "<a class='c-side-item' href='/logout'><span class='ic' aria-hidden='true'>&#10162;</span>"
        "<span>Sair</span></a>"
    )
    return (
        _CLIENTE_DASH_LAYOUT.replace("@@TITLE@@", html.escape(title))
        .replace("@@BRAND@@", "Área do Cliente")
        .replace("@@NAV@@", "".join(nav))
        .replace("@@FOOT@@", foot)
        .replace("@@PAGE@@", html.escape(page))
        .replace("@@USER@@", _cliente_user_menu(user))
        .replace("@@BODY@@", body)
        .replace("@@WHATSAPP@@", SERVICE_WHATSAPP_LINK)
        .replace("@@TOP@@", ""),
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )


def _status_badge(status):
    status = (status or "pendente").lower()
    label = {
        "pendente": "Pendente",
        "pago": "Pago",
        "entregue": "Concluído",
        "cancelado": "Cancelado",
        "aberto": "Pendente",
        "respondido": "Respondido",
        "encerrado": "Encerrado",
    }.get(status, status.capitalize())
    cls = status if status in ("pendente", "pago", "entregue", "cancelado", "aberto", "respondido", "encerrado") else "aberto"
    return f"<span class='badge {html.escape(cls)}'>{html.escape(label)}</span>"


def _fmt_brl(value):
    try:
        numero = parse_brl(value)
    except Exception:
        return html.escape(str(value or "-"))
    if numero == 0:
        return html.escape(str(value or "-"))
    inteiro, _, dec = f"{numero:,.2f}".partition(".")
    inteiro = inteiro.replace(",", ".")
    return f"R$ {inteiro},{dec}"


def _cliente_profile(email):
    if not (STORE.remote and email):
        return {}
    try:
        response = requests.get(
            f"{STORE.url}/rest/v1/profiles?email=eq.{email}&select=*",
            headers=STORE._headers(),
            timeout=15,
        )
        if response.status_code == 200:
            profiles = response.json() or []
            if profiles:
                return profiles[0]
    except Exception:
        pass
    return {}


def _cliente_tickets(email):
    if not (STORE.remote and email):
        return []
    try:
        response = requests.get(
            f"{STORE.url}/rest/v1/tickets?email=eq.{email}&order=criado_em.desc&select=*",
            headers=STORE._headers(),
            timeout=15,
        )
        if response.status_code == 200:
            return response.json() or []
    except Exception:
        pass
    return []


_PERFIL_VOCACOES = ("Knight", "Paladin", "Sorcerer", "Druid", "Monk")
_PERFIL_TEMAS = (("escuro", "Escuro"), ("claro", "Claro"))
_PERFIL_IDIOMAS = (("pt-BR", "Português (BR)"), ("en", "English"), ("es", "Español"))

_PERFIL_CSS = """
<style>
.perfil-head{display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.pf-avatar{width:84px;height:84px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;
background:var(--grad);color:#04281a;font-weight:800;font-size:30px;overflow:hidden;border:2px solid var(--border-2)}
.pf-avatar img{width:100%;height:100%;object-fit:cover}
.pf-id{flex:1;min-width:200px}
.pf-id h2{margin:0 0 4px;font-size:20px}
.pf-mail{color:var(--muted);font-size:13px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.pf-chip{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:700;border-radius:999px;
padding:2px 10px;border:1px solid rgba(74,222,128,.35);background:rgba(74,222,128,.12);color:var(--green)}
.avatar-edit{cursor:pointer;display:inline-flex;align-items:center;gap:8px;color:var(--blue);
border:1px solid var(--border-2);border-radius:10px;padding:9px 16px;font-size:13.5px;font-weight:600}
.avatar-edit:hover{background:rgba(96,165,250,.10)}
.avatar-edit input{display:none}
.pf-sec-desc{margin:0 0 12px;color:var(--muted);font-size:13px}
.pf-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px 14px}
@media (max-width:640px){.pf-grid{grid-template-columns:1fr}}
label.req::after{content:' *';color:var(--red);font-weight:800}
.pf-opt{font-size:12px;color:var(--muted);font-weight:400;margin-left:6px}
.switch-row{display:flex;align-items:center;gap:10px;padding:9px 0;font-size:14px}
.switch-row input{width:18px;height:18px;accent-color:#4ade80;flex:none}
.switch-row small{display:block;color:var(--muted);font-size:12px}
.pf-actions{display:flex;align-items:center;gap:12px;margin-top:18px;flex-wrap:wrap}
.pf-actions .btn:disabled{opacity:.75;cursor:wait}
.pf-dirty{font-size:12.5px;color:var(--amber);font-weight:600}
.pf-toast{position:fixed;right:18px;bottom:18px;z-index:200;max-width:min(360px,calc(100vw - 36px));
padding:12px 16px;border-radius:12px;font-size:13.5px;font-weight:600;border:1px solid;
box-shadow:0 14px 34px rgba(0,0,0,.5);animation:pf-in .25s ease-out}
.pf-toast.ok{background:#052e22;color:#6ee7b7;border-color:rgba(74,222,128,.4)}
.pf-toast.erro{background:#3b0d0d;color:#fca5a5;border-color:rgba(248,113,113,.4)}
.pf-toast.hide{opacity:0;transition:opacity .4s}
@keyframes pf-in{from{transform:translateY(10px);opacity:0}to{transform:none;opacity:1}}
</style>
"""

_PERFIL_JS = """
<script>
(function () {
  var form = document.getElementById("perfil-form");
  var toast = document.getElementById("perfil-toast");
  if (toast) setTimeout(function () {
    toast.classList.add("hide");
    setTimeout(function () { toast.remove(); }, 450);
  }, 5000);
  if (!form) return;
  var btn = document.getElementById("perfil-save");
  var dirty = document.getElementById("perfil-dirty");
  var snap = {};
  function val(el) {
    if (!el.name) return null;
    if (el.type === "checkbox") return el.checked ? "1" : "0";
    if (el.type === "file") return el.value ? "f:" + el.value : "";
    return el.value;
  }
  function foto() {
    snap = {};
    form.querySelectorAll("[data-pf]").forEach(function (el) { snap[el.name] = val(el); });
  }
  function mudou() {
    var els = form.querySelectorAll("[data-pf]");
    for (var i = 0; i < els.length; i++) {
      if (snap[els[i].name] !== val(els[i])) return true;
    }
    return false;
  }
  function marca() {
    var m = mudou();
    if (dirty) dirty.hidden = !m;
    if (btn) btn.classList.toggle("has-changes", m);
  }
  foto();
  form.addEventListener("input", marca);
  form.addEventListener("change", marca);
  var av = document.getElementById("pf-avatar-input");
  var prev = document.getElementById("pf-avatar-prev");
  if (av) av.addEventListener("change", function () {
    var f = av.files && av.files[0];
    if (!f || !prev) return;
    var r = new FileReader();
    r.onload = function (e) {
      prev.innerHTML = "<img src='" + String(e.target.result).replace(/"/g, "&quot;") + "' alt='Prévia do avatar'>";
    };
    r.readAsDataURL(f);
  });
  form.addEventListener("submit", function () {
    if (!btn) return;
    btn.disabled = true;
    var t = btn.querySelector(".t");
    if (t) t.textContent = "Salvando\\u2026";
  });
})();
</script>
"""


def _perfil_flash(tipo, texto):
    session["_perfil_msg"] = [tipo, texto]


def _perfil_consume_toast():
    msg = session.pop("_perfil_msg", None)
    if not msg:
        return ""
    tipo, texto = msg[0], msg[1]
    cls = "ok" if tipo == "ok" else "erro"
    return (
        f"<div class='pf-toast {cls}' id='perfil-toast' role='status'>"
        f"{html.escape(str(texto))}</div>"
    )


def _perfil_options(pares, atual, vazio=None):
    out = []
    if vazio is not None:
        out.append(
            f"<option value=''{(' selected' if not atual else '')}>"
            f"{html.escape(vazio)}</option>"
        )
    for valor, rotulo in pares:
        out.append(
            f"<option value='{html.escape(valor)}'"
            f"{(' selected' if atual == valor else '')}>"
            f"{html.escape(rotulo)}</option>"
        )
    return "".join(out)


def _perfil_mundo_options(atual):
    atual = (atual or "").strip()
    opts = [
        f"<option value=''{(' selected' if not atual else '')}>"
        "Selecione o mundo...</option>"
    ]
    if atual and atual not in _MK_MUNDOS:
        opts.append(
            f"<option value='{html.escape(atual)}' selected>"
            f"{html.escape(atual)} (antigo)</option>"
        )
    for mundo in _MK_MUNDOS:
        opts.append(
            f"<option value='{html.escape(mundo)}'"
            f"{(' selected' if atual == mundo else '')}>"
            f"{html.escape(mundo)}</option>"
        )
    return "".join(opts)


def _cliente_avatar_upload(file_storage):
    """Sobe o avatar no bucket público 'avatares'. Devolve (url, erro)."""
    from painel import SUPA_URL, SUPA_KEY

    if not SUPA_URL or not SUPA_KEY:
        return None, "Armazenamento indisponível."
    try:
        blob = file_storage.read()
    except Exception:
        return None, "Não foi possível ler o arquivo."
    if not blob:
        return None, "Arquivo vazio."
    if len(blob) > 2 * 1024 * 1024:
        return None, "Imagem maior que 2 MB."
    nome = (getattr(file_storage, "filename", "") or "").lower()
    ext = os.path.splitext(nome)[1] or ".png"
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        return None, "Formato inválido (use png, jpg, webp ou gif)."
    mime = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".gif": "image/gif",
    }[ext]
    chave = f"avatar-{secrets.token_hex(8)}{ext}"
    try:
        resposta = requests.post(
            f"{SUPA_URL}/storage/v1/object/avatares/{chave}",
            headers={
                "apikey": SUPA_KEY,
                "Authorization": f"Bearer {SUPA_KEY}",
                "Content-Type": getattr(file_storage, "mimetype", None) or mime,
            },
            data=blob,
            timeout=30,
        )
    except Exception:
        return None, "Falha de conexão no upload."
    if resposta.status_code not in (200, 201):
        return None, f"Upload falhou ({resposta.status_code})."
    return f"{SUPA_URL}/storage/v1/object/public/avatares/{chave}", None


@app.route("/cliente")
def cliente():
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()
    try:
        mine = [
            o
            for o in STORE.list()
            if (o.get("email") or "").strip().lower() == email
        ]
    except Exception:
        mine = []
    profile = _cliente_profile(email)
    tickets = _cliente_tickets(email)

    total = len(mine)
    em_andamento = sum(1 for o in mine if (o.get("status") or "pendente") in ("pendente", "pago"))
    concluidos = sum(1 for o in mine if (o.get("status") or "pendente") == "entregue")
    abertos = sum(1 for t in tickets if (t.get("status") or "") == "aberto")
    resolvidos = sum(1 for t in tickets if (t.get("status") or "") in ("encerrado", "respondido"))
    vip = _mk_vip_ativo(email)
    preco_vip = _mk_preco("preco_vip", 12.99)

    nome_parts = re.split(r"[\s]+", user["name"].strip()) if user.get("name") else [email.split("@")[0]]
    primeiro = html.escape((nome_parts[0] if nome_parts else "Cliente").title())

    def _uso_barra(rotulo, feitos, total_q):
        pct = round(100 * feitos / total_q) if total_q else 0
        return (
            f"<div class='uso'><div class='uso-top'><span>{html.escape(rotulo)}</span>"
            f"<span>{feitos}/{total_q}</span></div>"
            f"<div class='uso-bar'><span style='width:{pct}%'></span></div></div>"
        )

    conta_chip = "&#128994; Conta ativa" if not profile.get("bloqueado") else "&#128308; Conta suspensa"
    saudacao = (
        "<div class='welcome'>"
        f"<div><h2>Olá, {primeiro}! &#128075;</h2>"
        "<p>Bem-vindo de volta à sua área do cliente BAPZX.</p></div>"
        f"<span class='conta-chip'>{conta_chip}</span>"
        "</div>"
    )

    plano_lbl = f"{_mk_brl(preco_vip)}/mês" if vip else "Grátis"
    resumo = (
        "<div class='kpis'>"
        f"<div class='kpi purple'><div class='ic' aria-hidden='true'>&#128142;</div>"
        f"<div><div class='num'>{'VIP' if vip else 'Básico'}</div><div class='lbl'>Plano · {plano_lbl}</div></div></div>"
        f"<div class='kpi green'><div class='ic' aria-hidden='true'>&#128230;</div>"
        f"<div><div class='num'>{total}</div><div class='lbl'>Pedidos · {em_andamento} em andamento</div></div></div>"
        f"<div class='kpi blue'><div class='ic' aria-hidden='true'>&#127915;</div>"
        f"<div><div class='num'>{abertos}</div><div class='lbl'>Tickets abertos</div></div></div>"
        f"<div class='kpi amber'><div class='ic' aria-hidden='true'>&#129302;</div>"
        f"<div><div class='num'>{1 if vip else 0}</div><div class='lbl'>Bots ativos</div></div></div>"
        "</div>"
    )

    atv = []
    for o in mine[:3]:
        st = (o.get("status") or "pendente")
        icone = "&#128994;" if st == "entregue" else ("&#128309;" if st == "pago" else "&#128993;")
        atv.append(
            f"<div class='atv'><span aria-hidden='true'>{icone}</span>"
            f"<span><b>Pedido #{html.escape(str(o.get('id') or '-'))}</b> — "
            f"RC {html.escape(str(o.get('tc') or '-'))}</span>{_status_badge(st)}</div>"
        )
    for t in tickets[:2]:
        atv.append(
            f"<div class='atv'><span aria-hidden='true'>&#128309;</span>"
            f"<span><b>Ticket #{html.escape(str(t.get('id') or '-'))}</b> — "
            f"{html.escape(str(t.get('assunto') or '-'))[:40]}</span>{_status_badge(t.get('status'))}</div>"
        )
    atividade = (
        "<div class='panel'><div class='panel-hd'><h2>&#128230; Atividade recente</h2>"
        "<a class='btn ghost small' href='/cliente/pedidos'>Ver tudo</a></div>"
        + ("".join(atv) if atv else "<p class='note'>Nenhuma atividade ainda.</p>")
        + "</div>"
    )

    acesso = (
        "<div class='panel'><div class='panel-hd'><h2>&#9889; Acesso rápido</h2></div>"
        "<div class='grid2'>"
        f"<a class='help-card' rel='noopener' href='{PORTFOLIO_URL}'>"
        "<div class='h-ic' aria-hidden='true'>&#128722;</div>"
        "<div><div class='h-t'>Comprar RC</div>"
        "<div class='h-s'>Ver ofertas e fechar pedido</div></div></a>"
        f"<a class='help-card' rel='noopener' href='{SERVICE_WHATSAPP_LINK}'>"
        "<div class='h-ic' aria-hidden='true'>&#128736;</div>"
        "<div><div class='h-t'>Solicitar serviço</div>"
        "<div class='h-s'>UP level e serviços no WhatsApp</div></div></a>"
        "<a class='help-card' href='/cliente/suporte#novo'>"
        "<div class='h-ic' aria-hidden='true'>&#128172;</div>"
        "<div><div class='h-t'>Abrir ticket</div>"
        "<div class='h-s'>Falar com a equipe BAPZX</div></div></a>"
        "<a class='help-card' href='/cliente/bot'>"
        "<div class='h-ic' aria-hidden='true'>&#129302;</div>"
        "<div><div class='h-t'>Gerenciar bot</div>"
        "<div class='h-s'>Acesso e recursos do seu bot</div></div></a>"
        "</div></div>"
    )

    barras = ""
    if vip:
        try:
            from datetime import datetime as _dt

            dt = _mk_parse_dt((_mk_profile(email) or {}).get("vip_until"))
            restam = max(0, (dt - _dt.utcnow()).days) if dt else 0
            barras += _uso_barra("Validade do VIP", restam, 30)
        except Exception:
            pass
    barras += _uso_barra("Pedidos concluídos", concluidos, total)
    barras += _uso_barra("Tickets resolvidos", resolvidos, len(tickets))
    plano = (
        "<div class='panel'><div class='panel-hd'><h2>&#128142; Seu plano</h2>"
        "<a class='btn ghost small' href='/cliente/plano'>Gerenciar plano</a></div>"
        "<div class='grid2'>"
        f"<div class='field-card'><div class='f-lbl'>Plano atual</div>"
        f"<div class='f-val'>{'VIP Pro' if vip else 'Básico'} · {plano_lbl}</div></div>"
        f"<div class='field-card'><div class='f-lbl'>Uso</div>{barras}</div>"
        "</div></div>"
    )

    feed = _cliente_feed_itens(email, profile, tickets, mine)
    if feed:
        avisos = "".join(
            f"<div class='atv'><span aria-hidden='true'>{icone}</span>"
            f"<span>{texto}</span><span>{acao}</span></div>"
            for icone, texto, acao in feed[:4]
        )
    else:
        avisos = "<p class='note'>Tudo em dia. &#9989;</p>"
    avisos_panel = (
        "<div class='panel'><div class='panel-hd'><h2>&#128276; Avisos</h2>"
        "<a class='btn ghost small' href='/cliente/notificacoes'>Ver todas</a></div>"
        + avisos + "</div>"
    )

    sistema_ok = bool(STORE.remote)
    status = (
        "<div class='panel'><div class='panel-hd'><h2>&#127760; Status dos serviços</h2></div>"
        f"<div class='atv'><span aria-hidden='true'>{'&#128994;' if sistema_ok else '&#128993;'}</span>"
        f"<span>Sistema</span><span>{'Operacional' if sistema_ok else 'Em manutenção'}</span></div>"
        f"<div class='atv'><span aria-hidden='true'>&#128994;</span><span>Bot</span>"
        f"<span><a rel='noopener' href='{TELEGRAM_BOT_LINK}'>Online</a></span></div>"
        f"<div class='atv'><span aria-hidden='true'>{'&#128994;' if MP_ACCESS_TOKEN else '&#128993;'}</span>"
        f"<span>Pagamentos</span><span>{'Operacional' if MP_ACCESS_TOKEN else 'A configurar'}</span></div>"
        "<div class='atv'><span aria-hidden='true'>&#128994;</span><span>Entregas</span><span>Operacional</span></div>"
        "</div>"
    )

    dash_css = (
        "<style>"
        ".conta-chip{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:700;"
        "border-radius:999px;padding:5px 14px;border:1px solid rgba(74,222,128,.35);"
        "background:rgba(74,222,128,.12);color:var(--green);white-space:nowrap}"
        ".atv{display:flex;align-items:center;gap:10px;padding:9px 2px;border-bottom:1px solid var(--border);font-size:13.5px}"
        ".atv:last-child{border-bottom:0}"
        ".atv span:nth-child(2){flex:1;min-width:0}"
        ".uso{margin:8px 0}"
        ".uso-top{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-bottom:4px}"
        ".uso-bar{height:8px;border-radius:99px;background:rgba(142,160,184,.15);overflow:hidden}"
        ".uso-bar span{display:block;height:100%;border-radius:99px;background:var(--grad)}"
        "</style>"
    )
    body = saudacao + resumo + atividade + acesso + plano + avisos_panel + status + dash_css
    return _cliente_dash_page("Minha conta", "Visão Geral", "visao", user, body)


@app.route("/cliente/pedidos", methods=["GET"])
def cliente_pedidos():
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()
    mine = _cliente_pedidos(email)
    if mine:
        tabela = "".join(
            "<tr>"
            f"<td><b>#{html.escape(str(o.get('id') or '-'))}</b></td>"
            f"<td>{html.escape(str(o.get('tc') or '-'))} RC · {html.escape(str(o.get('mundo') or '-'))}</td>"
            f"<td>{html.escape(str(o.get('data') or ''))[:16]}</td>"
            f"<td>{_fmt_brl(o.get('preco'))}</td>"
            f"<td>{_status_badge(o.get('status'))}</td>"
            "<td><a class='btn ghost small' href='/cliente/suporte'>Ajuda</a></td>"
            "</tr>"
            for o in mine
        )
        corpo = (
            "<div class='table-wrap'><table>"
            "<tr><th>Pedido</th><th>Produto</th><th>Data</th><th>Valor</th><th>Status</th><th>Ação</th></tr>"
            + tabela
            + "</table></div>"
        )
    else:
        corpo = (
            "<div class='empty-state'>"
            "<div class='em-ic' aria-hidden='true'>&#128232;</div>"
            "<h3>Você ainda não possui pedidos</h3>"
            "<p>Quando você fechar uma compra no Telegram com o mesmo e-mail da sua conta, "
            "seus pedidos aparecem aqui.</p>"
            "<a class='btn blue' rel='noopener' href='" + PORTFOLIO_URL + "'>Explorar serviços</a>"
            "</div>"
        )
    body = (
        "<div class='panel'><div class='panel-hd'><h2>&#128230; Meus pedidos</h2></div>"
        + corpo + "</div>"
        "<p class='note'>Os pedidos aparecem aqui quando o pagamento foi solicitado com o "
        "<b>mesmo e-mail</b> da sua conta Google. Se faltar algum pedido, finalize "
        "a compra no Telegram usando esse e-mail no Pix.</p>"
    )
    body = _voltar_card("Meus Pedidos", "Todos os seus pedidos em um só lugar.",
                        "Voltar ao Dashboard", "/cliente") + body
    return _cliente_dash_page("Meus Pedidos", "Meus Pedidos", "pedidos", user, body)


@app.route("/cliente/perfil", methods=["GET", "POST"])
def cliente_perfil():
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()
    profile = _cliente_profile(email)

    if request.method == "POST":
        if not _csrf_ok():
            return "Requisição inválida (CSRF).", 403
        personagem = (request.form.get("personagem") or "").strip()[:100]
        if not personagem:
            _perfil_flash("erro", "Informe seu personagem para salvar o perfil.")
            return redirect("/cliente/perfil")
        mundo = (request.form.get("mundo") or "").strip()[:100]
        if mundo and mundo not in _MK_MUNDOS:
            mundo = ""
        vocacao = (request.form.get("vocacao") or "").strip()[:20]
        if vocacao and vocacao not in _PERFIL_VOCACOES:
            vocacao = ""
        tema = (request.form.get("tema") or "escuro").strip()
        if tema not in ("escuro", "claro"):
            tema = "escuro"
        idioma = (request.form.get("idioma") or "pt-BR").strip()
        if idioma not in ("pt-BR", "en", "es"):
            idioma = "pt-BR"
        wpp_raw = (request.form.get("whatsapp") or "").strip()[:20]
        whatsapp = _mk_whatsapp(wpp_raw)
        if wpp_raw and not whatsapp:
            _perfil_flash("erro", "WhatsApp inválido — use DDD + número, ex.: (19) 98765-4321.")
            return redirect("/cliente/perfil")
        avatar_url = str(profile.get("avatar_url") or "")
        arq = request.files.get("avatar")
        if arq and (arq.filename or "").strip():
            avatar_url, erro = _cliente_avatar_upload(arq)
            if erro:
                _perfil_flash("erro", f"Avatar: {erro}")
                return redirect("/cliente/perfil")
        payload = {
            "email": email,
            "name": user["name"],
            "sub": user.get("sub") or "",
            "role": user.get("role") or "cliente",
            "personagem": personagem,
            "mundo": mundo,
            "apelido": (request.form.get("apelido") or "").strip()[:60],
            "vocacao": vocacao,
            "discord": (request.form.get("discord") or "").strip()[:60],
            "whatsapp": whatsapp,
            "avatar_url": avatar_url,
            "notif_pedidos": request.form.get("notif_pedidos") == "1",
            "notif_promos": request.form.get("notif_promos") == "1",
            "tema": tema,
            "idioma": idioma,
        }
        legado = {
            k: payload[k]
            for k in ("email", "name", "sub", "role", "personagem", "mundo")
        }
        salvo = False
        if STORE.remote:
            for tentativa in (payload, legado):
                try:
                    resposta = requests.post(
                        f"{STORE.url}/rest/v1/profiles?on_conflict=email",
                        headers={**STORE._headers(), "Prefer": "resolution=merge-duplicates"},
                        json=tentativa,
                        timeout=15,
                    )
                    if resposta.status_code in (200, 201, 204):
                        salvo = True
                        break
                except Exception:
                    break
        _perfil_flash(
            "ok" if salvo else "erro",
            "Perfil salvo com sucesso!" if salvo else "Não foi possível salvar agora — tente de novo.",
        )
        return redirect("/cliente/perfil")

    apelido = str(profile.get("apelido") or "")
    titulo_id = apelido or user["name"]
    avatar_atual = str(profile.get("avatar_url") or "")
    if avatar_atual:
        avatar_html = (
            f"<span class='pf-avatar' id='pf-avatar-prev'>"
            f"<img src='{html.escape(avatar_atual)}' alt='Avatar'></span>"
        )
    else:
        avatar_html = (
            f"<span class='pf-avatar' id='pf-avatar-prev' aria-hidden='true'>"
            f"{_title_initials(titulo_id)}</span>"
        )
    vocacao_atual = str(profile.get("vocacao") or "")
    if profile.get("notif_pedidos", True):
        chk_ped = " checked"
    else:
        chk_ped = ""
    if profile.get("notif_promos", True):
        chk_pro = " checked"
    else:
        chk_pro = ""
    body = (
        _perfil_consume_toast()
        + "<div class='panel'><div class='perfil-head'>"
        f"{avatar_html}"
        "<div class='pf-id'>"
        f"<h2>{html.escape(titulo_id)}</h2>"
        f"<div class='pf-mail'>{html.escape(email)} "
        "<span class='pf-chip'>&#10003; Verificado via Google</span></div>"
        "</div>"
        "</div></div>"
        "<form method='post' enctype='multipart/form-data' id='perfil-form'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        "<div class='panel'>"
        "<div class='panel-hd'><h2>&#128100; Informações pessoais</h2></div>"
        "<p class='pf-sec-desc'>Como você aparece para a equipe BAPZX.</p>"
        "<div class='pf-grid'>"
        "<div><label class='req'>Apelido</label>"
        f"<input name='apelido' data-pf maxlength='60' placeholder='Ex.: Bapz' "
        f"value='{html.escape(apelido)}'></div>"
        "<div><label>E-mail</label>"
        f"<input value='{html.escape(email)}' disabled>"
        "<div class='size-note'>Login via Google — por segurança, o e-mail não pode ser alterado.</div></div>"
        "</div>"
        "<div><label>Foto de perfil<span class='pf-opt'>png, jpg, webp ou gif até 2 MB</span></label><br>"
        "<label class='avatar-edit'>&#128247; Trocar foto"
        "<input type='file' name='avatar' id='pf-avatar-input' data-pf accept='image/png,image/jpeg,image/webp,image/gif'>"
        "</label></div>"
        "<div><label>WhatsApp<span class='pf-opt'>opcional</span></label>"
        f"<input name='whatsapp' data-pf maxlength='16' inputmode='numeric' placeholder='(19) 98765-4321' "
        f"value='{html.escape(str(profile.get('whatsapp') or ''))}'></div>"
        "</div>"
        "<div class='panel'>"
        "<div class='panel-hd'><h2>&#127918; Dados de jogo</h2></div>"
        "<p class='pf-sec-desc'>Usados para agilizar seus próximos pedidos.</p>"
        "<div class='pf-grid'>"
        "<div><label class='req'>Personagem</label>"
        f"<input name='personagem' data-pf required maxlength='100' placeholder='Nome do personagem' "
        f"value='{html.escape(str(profile.get('personagem') or ''))}'></div>"
        "<div><label>Mundo</label>"
        f"<select name='mundo' data-pf>{_perfil_mundo_options(str(profile.get('mundo') or ''))}</select></div>"
        "<div><label>Vocação preferida<span class='pf-opt'>opcional</span></label>"
        f"<select name='vocacao' data-pf>{_perfil_options([(v, v) for v in _PERFIL_VOCACOES], vocacao_atual, 'Selecione...')}</select></div>"
        "<div><label>Discord<span class='pf-opt'>opcional</span></label>"
        f"<input name='discord' data-pf maxlength='60' placeholder='Ex.: bapz_01' "
        f"value='{html.escape(str(profile.get('discord') or ''))}'></div>"
        "</div>"
        "</div>"
        "<div class='panel'>"
        "<div class='panel-hd'><h2>&#9881; Preferências</h2></div>"
        "<p class='pf-sec-desc'>Como a BAPZX fala com você.</p>"
        "<label class='switch-row'><input type='checkbox' name='notif_pedidos' data-pf value='1'"
        f"{chk_ped}><span>Avisos de pedido<small>Status do pedido, Pix e entrega.</small></span></label>"
        "<label class='switch-row'><input type='checkbox' name='notif_promos' data-pf value='1'"
        f"{chk_pro}><span>Ofertas e novidades<small>Promoções e itens novos. Sem spam.</small></span></label>"
        "<div class='pf-grid'>"
        "<div><label>Tema</label>"
        f"<select name='tema' data-pf>{_perfil_options(_PERFIL_TEMAS, str(profile.get('tema') or 'escuro'))}</select></div>"
        "<div><label>Idioma</label>"
        f"<select name='idioma' data-pf>{_perfil_options(_PERFIL_IDIOMAS, str(profile.get('idioma') or 'pt-BR'))}</select></div>"
        "</div>"
        "<div class='pf-actions'>"
        "<button class='btn' type='submit' id='perfil-save'><span class='t'>Salvar perfil</span></button>"
        "<span class='pf-dirty' id='perfil-dirty' hidden>&#9679; alterações não salvas</span>"
        "</div>"
        "</div>"
        "</form>"
        "<p class='legal-note'>Ao salvar, seus dados são usados apenas para agilizar seus pedidos. Consulte nossa "
        "<a href='/privacidade'>Política de Privacidade</a> (LGPD) para saber mais.</p>"
        + _PERFIL_CSS
        + _PERFIL_JS
    )
    body = _voltar_card("Meu Perfil", "Seus dados e preferências.",
                        "Voltar ao Dashboard", "/cliente") + body
    return _cliente_dash_page("Meu perfil", "Meu Perfil", "perfil", user, body)


@app.route("/cliente/suporte", methods=["GET", "POST"])
def cliente_suporte():
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()

    if request.method == "POST":
        if not _csrf_ok():
            return "Requisição inválida (CSRF).", 403
        assunto = (request.form.get("assunto") or "").strip()[:200]
        mensagem = (request.form.get("mensagem") or "").strip()[:3000]
        if not assunto or not mensagem:
            return "Assunto e mensagem obrigatórios.", 400
        if STORE.remote:
            try:
                requests.post(
                    f"{STORE.url}/rest/v1/tickets",
                    headers={**STORE._headers(), "Prefer": "return=representation"},
                    json={"email": email, "assunto": assunto, "mensagem": mensagem},
                    timeout=15,
                )
                dono = load_env_key("TELEGRAM_OWNER_CHAT_ID")
                if dono:
                    send_message(
                        dono,
                        f"🎫 NOVO TICKET de {email}\n\nAssunto: {assunto}\n\n{mensagem[:400]}",
                    )
            except Exception:
                pass
        return redirect("/cliente/suporte")

    tickets = _cliente_tickets(email)
    if tickets:
        rows = "".join(
            "<tr>"
            f"<td><b>#{html.escape(str(t.get('id') or '-'))}</b></td>"
            f"<td>{html.escape(str(t.get('criado_em') or ''))[:16]}</td>"
            f"<td>{html.escape(str(t.get('assunto') or '-'))}</td>"
            f"<td>{_status_badge(t.get('status'))}</td>"
            f"<td><a class='btn ghost small' href='/cliente/suporte/{t.get('id')}'>Ver</a></td>"
            "</tr>"
            for t in tickets
        )
        chamados = (
            "<div class='table-wrap'><table>"
            "<tr><th>Chamado</th><th>Data</th><th>Assunto</th><th>Status</th><th></th></tr>"
            + rows
            + "</table></div>"
        )
    else:
        chamados = (
            "<div class='empty-state'>"
            "<div class='em-ic' aria-hidden='true'>&#128279;</div>"
            "<h3>Nenhum chamado aberto</h3>"
            "<p>Quando você abrir um atendimento, ele aparece aqui para acompanhamento.</p>"
            "</div>"
        )
    body = (
        "<div class='panel' id='novo'>"
        "<div class='panel-hd'><h2>&#128172; Abrir chamado</h2></div>"
        "<form method='post'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        "<label>Assunto</label><input name='assunto' required placeholder='Resumo curto'>"
        "<label>Mensagem</label><textarea name='mensagem' rows='4' required></textarea>"
        "<p style='margin-top:16px'><button class='btn' type='submit'>Enviar chamado</button></p>"
        "</form>"
        "<p class='legal-note'>As mensagens enviadas aqui são tratadas em sigilo para atender seu "
        "chamado. Consulte nossa <a href='/privacidade'>Política de "
        "Privacidade</a> (LGPD).</p>"
        "</div>"
        "<div class='panel' id='chamados'>"
        "<div class='panel-hd'><h2>&#128279; Meus chamados</h2></div>"
        + chamados
        + "</div>"
    )
    body = _voltar_card("Suporte", "Atendimento e chamados.",
                        "Voltar ao Dashboard", "/cliente") + body
    return _cliente_dash_page("Suporte", "Suporte", "suporte", user, body)


@app.route("/cliente/suporte/<int:ticket_id>", methods=["GET"])
def cliente_suporte_detalhe(ticket_id):
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()
    tickets = []
    if STORE.remote:
        try:
            response = requests.get(
                f"{STORE.url}/rest/v1/tickets?id=eq.{ticket_id}&email=eq.{email}&select=*",
                headers=STORE._headers(),
                timeout=15,
            )
            if response.status_code == 200:
                tickets = response.json()
        except Exception:
            tickets = []
    if not tickets:
        return "Chamado não encontrado.", 404
    ticket = tickets[0]
    resposta = ""
    if ticket.get("resposta"):
        resposta = (
            "<div style='background:#0f2a22;border:1px solid #14532d;color:#4ade80;"
            "border-radius:12px;padding:12px 16px'><b>Resposta:</b> "
            f"{html.escape(str(ticket.get('resposta') or ''))}</div>"
        )
    body = (
        "<div class='panel'>"
        "<div class='panel-hd'><h2>Chamado #%s&nbsp; %s</h2></div>"
        "<p class='note'>Abertura: %s</p>"
        "<p><b>%s</b></p>"
        "<p style='color:#e2e8f0'>%s</p>"
        "%s"
        "</div>"
        "<p><a class='btn ghost' href='/cliente/suporte#chamados'>Voltar aos chamados</a></p>"
    ) % (
        html.escape(str(ticket.get("id") or "-")),
        _status_badge(ticket.get("status")),
        html.escape(str(ticket.get("criado_em") or ""))[:19],
        html.escape(str(ticket.get("assunto") or "-")),
        html.escape(str(ticket.get("mensagem") or "-")),
        resposta,
    )
    body = _voltar_card(f"Chamado #{ticket.get('id')}", "Detalhes do atendimento.",
                        "Voltar ao Suporte", "/cliente/suporte") + body
    return _cliente_dash_page("Chamado", "Suporte", "suporte", user, body)


@app.route("/cliente/pagamentos", methods=["GET"])
def cliente_pagamentos():
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()
    mine = _cliente_pedidos(email)
    pagos = [o for o in mine if (o.get("status") or "") == "pago"]
    entregues = [o for o in mine if (o.get("status") or "") == "entregue"]
    pendentes = [o for o in mine if (o.get("status") or "") == "pendente"]
    try:
        total = sum(parse_brl(o.get("preco")) for o in pagos + entregues)
    except Exception:
        total = 0
    if mine:
        tabela = "".join(
            "<tr>"
            f"<td><b>#{html.escape(str(o.get('id') or '-'))}</b></td>"
            f"<td>{html.escape(str(o.get('data') or ''))[:16]}</td>"
            f"<td>{html.escape(str(o.get('tc') or '-'))} RC</td>"
            f"<td>{_fmt_brl(o.get('preco'))}</td>"
            f"<td>Pix</td>"
            f"<td>{_status_badge(o.get('status'))}</td>"
            "</tr>"
            for o in mine[:20]
        )
        corpo = (
            "<div class='table-wrap'><table>"
            "<tr><th>Pedido</th><th>Data</th><th>Produto</th><th>Valor</th><th>Método</th><th>Status</th></tr>"
            + tabela
            + "</table></div>"
        )
    else:
        corpo = (
            "<div class='empty-state'>"
            "<div class='em-ic' aria-hidden='true'>&#128176;</div>"
            "<h3>Nenhuma fatura ainda</h3>"
            "<p>Quando você comprar, seus pagamentos Pix aparecem aqui.</p>"
            f"<a class='btn blue' rel='noopener' href='{PORTFOLIO_URL}'>Ver ofertas</a>"
            "</div>"
        )
    body = (
        "<div class='kpis'>"
        f"<div class='kpi green'><div class='ic' aria-hidden='true'>&#128176;</div>"
        f"<div><div class='num'>{_fmt_brl(total)}</div><div class='lbl'>Total pago</div></div></div>"
        f"<div class='kpi amber'><div class='ic' aria-hidden='true'>&#9203;</div>"
        f"<div><div class='num'>{len(pendentes)}</div><div class='lbl'>Aguardando pagamento</div></div></div>"
        f"<div class='kpi blue'><div class='ic' aria-hidden='true'>&#9989;</div>"
        f"<div><div class='num'>{len(entregues)}</div><div class='lbl'>Entregues</div></div></div>"
        "</div>"
        "<div class='panel'><div class='panel-hd'><h2>&#128176; Faturas</h2></div>"
        + corpo +
        "</div>"
        "<p class='note'>Pagamento via <b>Pix com confirmação automática</b> — "
        "o status muda sozinho após a compensação.</p>"
    )
    body = _voltar_card("Pagamentos", "Suas faturas e cobranças Pix.",
                        "Voltar ao Dashboard", "/cliente") + body
    return _cliente_dash_page("Pagamentos", "Pagamentos", "pagamentos", user, body)


@app.route("/cliente/automacoes", methods=["GET", "POST"])
def cliente_automacoes():
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()
    if request.method == "POST":
        if not _csrf_ok():
            return "Requisição inválida (CSRF).", 403
        ok = False
        if STORE.remote:
            try:
                resposta = requests.patch(
                    f"{STORE.url}/rest/v1/profiles?email=eq.{email}",
                    headers=STORE._headers(),
                    json={
                        "notif_pedidos": request.form.get("notif_pedidos") == "1",
                        "notif_promos": request.form.get("notif_promos") == "1",
                    },
                    timeout=15,
                )
                ok = resposta.status_code in (200, 204)
            except Exception:
                ok = False
        return redirect("/cliente/automacoes?salvo=1" if ok else "/cliente/automacoes?salvo=0")
    profile = _cliente_profile(email)
    aviso = ""
    if request.args.get("salvo") == "1":
        aviso = "<div class='alert info'>Automações atualizadas.</div>"
    elif request.args.get("salvo") == "0":
        aviso = "<div class='alert'>Não foi possível salvar agora — tente de novo.</div>"
    chk_ped = " checked" if profile.get("notif_pedidos", True) else ""
    chk_pro = " checked" if profile.get("notif_promos", True) else ""
    body = (
        aviso
        + "<div class='panel'><div class='panel-hd'><h2>&#9881; Minhas automações</h2></div>"
        "<div class='grid2'>"
        "<div class='help-card'><div class='h-ic' aria-hidden='true'>&#9889;</div>"
        "<div class='h-t'>Confirmação automática de Pix</div>"
        "<div class='h-s'>O pagamento é confirmado sozinho via webhook. Sem comprovante manual.</div>"
        "<div style='margin-top:8px'>" + _status_badge("pago") + "</div></div>"
        "<div class='help-card'><div class='h-ic' aria-hidden='true'>&#128142;</div>"
        "<div class='h-t'>Renovação do VIP</div>"
        "<div class='h-s'>Seu VIP dura 30 dias e pode ser renovado quando quiser.</div>"
        "<div style='margin-top:8px'><a class='btn ghost small' href='/cliente/troca/vip'>Gerenciar VIP</a></div></div>"
        "</div></div>"
        "<div class='panel'><div class='panel-hd'><h2>&#128276; Avisos automáticos</h2></div>"
        "<form method='post'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        "<label class='switch-row'><input type='checkbox' name='notif_pedidos' value='1'"
        f"{chk_ped}><span>Avisos de pedido<small>Status, Pix e entrega.</small></span></label>"
        "<label class='switch-row'><input type='checkbox' name='notif_promos' value='1'"
        f"{chk_pro}><span>Ofertas e novidades<small>Promoções e itens novos. Sem spam.</small></span></label>"
        "<div class='pf-actions' style='margin-top:14px'>"
        "<button class='btn' type='submit'>Salvar automações</button></div>"
        "</form></div>"
        + _PERFIL_CSS
    )
    body = _voltar_card("Automações", "Confirmações e avisos automáticos.",
                        "Voltar ao Dashboard", "/cliente") + body
    return _cliente_dash_page("Automações", "Automações", "automacoes", user, body)


@app.route("/cliente/bot", methods=["GET"])
def cliente_bot():
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()
    if _mk_vip_ativo(email):
        corpo = (
            "<div class='panel'><div class='panel-hd'><h2>&#129302; Meu Bot</h2></div>"
            "<p>" + _status_badge("pago") + " <b>Bot liberado para você.</b></p>"
            "<div class='grid2'>"
            "<div class='help-card'><div class='h-ic' aria-hidden='true'>&#129302;</div>"
            "<div class='h-t'>Atendimento 24/7</div>"
            "<div class='h-s'>Comprar RC, tirar dúvidas e acompanhar pedidos no Telegram.</div></div>"
            "<div class='help-card'><div class='h-ic' aria-hidden='true'>&#127991;</div>"
            "<div class='h-t'>MARKTRADE</div>"
            "<div class='h-s'>Publique e negocie anúncios com destaque.</div></div>"
            "</div>"
            f"<p style='margin-top:14px'><a class='btn' rel='noopener' href='{TELEGRAM_BOT_LINK}'>Abrir bot no Telegram</a> "
            f"<a class='btn ghost' rel='noopener' href='{SERVICE_WHATSAPP_LINK}'>Falar no WhatsApp</a></p>"
            "</div>"
        )
    else:
        preco_vip = _mk_preco("preco_vip", 12.99)
        corpo = (
            "<div class='panel'><div class='panel-hd'><h2>&#129302; Meu Bot</h2></div>"
            "<div class='empty-state'>"
            "<div class='em-ic' aria-hidden='true'>&#128274;</div>"
            "<h3>Recurso do plano VIP</h3>"
            f"<p>O bot liberado com prioridade custa <b>{_mk_brl(preco_vip)}</b> e vale por 30 dias.</p>"
            "<a class='btn blue' href='/cliente/troca/vip'>Assinar VIP</a>"
            "</div></div>"
        )
    corpo = _voltar_card("Meu Bot", "Atendimento automático no Telegram.",
                         "Voltar ao Dashboard", "/cliente") + corpo
    return _cliente_dash_page("Meu Bot", "Meu Bot", "bot", user, corpo)


@app.route("/cliente/servicos", methods=["GET"])
def cliente_servicos():
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()
    profile = _cliente_profile(email)
    meus = _cliente_servicos_meus(profile.get("whatsapp") or "")
    if meus:
        linhas = "".join(
            "<tr>"
            f"<td>{html.escape(str(s.get('criado_em') or s.get('data') or ''))[:10]}</td>"
            f"<td>{html.escape(str(s.get('servico') or '-'))}</td>"
            f"<td>{_fmt_brl(s.get('valor'))}</td>"
            f"<td>{_status_badge(s.get('status'))}</td>"
            "</tr>"
            for s in meus[:20]
        )
        meus_html = (
            "<div class='table-wrap'><table>"
            "<tr><th>Data</th><th>Serviço</th><th>Valor</th><th>Status</th></tr>"
            + linhas + "</table></div>"
        )
    else:
        meus_html = (
            "<div class='empty-state'>"
            "<div class='em-ic' aria-hidden='true'>&#128736;</div>"
            "<h3>Nenhum serviço contratado</h3>"
            "<p>Os serviços que você contratar com seu WhatsApp aparecem aqui.</p>"
            "</div>"
        )
    catalogo = _cliente_servicos_catalogo()
    if catalogo:
        cards = "".join(
            "<div class='help-card'><div class='h-t'>"
            f"{html.escape(str(s.get('nome') or '-'))}</div>"
            f"<div class='h-s'>{html.escape(str(s.get('descricao') or ''))[:120]}</div>"
            f"<div style='margin-top:8px;font-weight:800'>{html.escape(str(s.get('preco') or ''))}</div></div>"
            for s in catalogo[:6]
        )
        cat_html = (
            "<div class='panel'><div class='panel-hd'><h2>&#128722; Contratar serviço</h2></div>"
            f"<div class='grid2'>{cards}</div>"
            f"<p style='margin-top:12px'><a class='btn' rel='noopener' href='{SERVICE_WHATSAPP_LINK}'>Contratar no WhatsApp</a></p>"
            "</div>"
        )
    else:
        cat_html = ""
    body = (
        "<div class='panel'><div class='panel-hd'><h2>&#128736; Meus serviços</h2></div>"
        + meus_html + "</div>" + cat_html
    )
    body = _voltar_card("Meus Serviços", "Serviços contratados e catálogo.",
                        "Voltar ao Dashboard", "/cliente") + body
    return _cliente_dash_page("Meus Serviços", "Meus Serviços", "servicos", user, body)


@app.route("/cliente/plano", methods=["GET"])
def cliente_plano():
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()
    vip = _mk_vip_ativo(email)
    preco_vip = _mk_preco("preco_vip", 12.99)
    if vip:
        validade = _mk_fmt_dt((_mk_profile(email) or {}).get("vip_until"))
        atual = (
            "<div class='kpi green'><div class='ic' aria-hidden='true'>&#128142;</div>"
            f"<div><div class='num'>VIP Pro</div><div class='lbl'>Ativo até {html.escape(validade)}</div></div></div>"
        )
        cta = "<a class='btn ghost' href='/cliente/troca/vip'>Renovar VIP</a>"
    else:
        atual = (
            "<div class='kpi amber'><div class='ic' aria-hidden='true'>&#128142;</div>"
            "<div><div class='num'>Básico</div><div class='lbl'>Plano gratuito</div></div></div>"
        )
        cta = "<a class='btn blue' href='/cliente/troca/vip'>Assinar VIP</a>"
    pags = _mk_meus_pagamentos(email)[:5]
    if pags:
        hist = "".join(
            "<tr>"
            f"<td>{html.escape(str(p.get('criado_em') or ''))[:10]}</td>"
            f"<td>{html.escape(str(p.get('tipo') or '-')).upper()}</td>"
            f"<td>{_mk_brl(p.get('valor'))}</td>"
            f"<td>{_status_badge(p.get('status'))}</td>"
            "</tr>"
            for p in pags
        )
        hist_html = (
            "<div class='panel'><div class='panel-hd'><h2>&#128179; Últimas cobranças</h2></div>"
            "<div class='table-wrap'><table>"
            "<tr><th>Data</th><th>Tipo</th><th>Valor</th><th>Status</th></tr>"
            + hist + "</table></div></div>"
        )
    else:
        hist_html = ""
    body = (
        f"<div class='kpis'>{atual}</div>"
        "<div class='panel'><div class='panel-hd'><h2>&#128142; Planos</h2></div>"
        "<div class='table-wrap'><table>"
        "<tr><th></th><th>Básico</th><th>VIP Pro</th></tr>"
        "<tr><td>Preço</td><td>Grátis</td><td><b>" + _mk_brl(preco_vip) + " / 30 dias</b></td></tr>"
        "<tr><td>Comprar RC e acompanhar pedidos</td><td>&#9989;</td><td>&#9989;</td></tr>"
        "<tr><td>Publicar no MARKTRADE</td><td>&#9989;</td><td>&#9989;</td></tr>"
        "<tr><td>Bot liberado com prioridade</td><td>&#10060;</td><td>&#9989;</td></tr>"
        "<tr><td>Selo VIP nos anúncios</td><td>&#10060;</td><td>&#9989;</td></tr>"
        "</table></div>"
        f"<p style='margin-top:14px'>{cta}</p>"
        "</div>" + hist_html
    )
    body = _voltar_card("Meu Plano", "Assinatura, benefícios e cobranças.",
                        "Voltar ao Dashboard", "/cliente") + body
    return _cliente_dash_page("Meu Plano", "Meu Plano", "plano", user, body)


def _cliente_feed_itens(email, profile, tickets, mine):
    """Itens do feed do cliente (avisos/notificações) como (icone, texto, acao).
    Nunca derruba."""
    feed = []
    try:
        if not (profile.get("personagem") or "").strip():
            feed.append(
                ("&#128100;", "Complete seu perfil com personagem e mundo.",
                 "<a class='btn ghost small' href='/cliente/perfil'>Completar</a>")
            )
        for o in [x for x in mine if (x.get("status") or "") == "pendente"][:3]:
            feed.append(
                ("&#9203;", f"Pedido #{o.get('id')} aguarda pagamento "
                 f"({_fmt_brl(o.get('preco'))}).",
                 _status_badge("pendente"))
            )
        for o in mine[:3]:
            if (o.get("status") or "") == "pago":
                feed.append(
                    ("&#9989;", f"Pagamento do pedido #{o.get('id')} confirmado.",
                     _status_badge("pago"))
                )
            elif (o.get("status") or "") == "entregue":
                feed.append(
                    ("&#127881;", f"Pedido #{o.get('id')} concluído. Obrigado!",
                     _status_badge("entregue"))
                )
        for t in tickets[:5]:
            if (t.get("status") or "") == "respondido":
                feed.append(
                    ("&#128172;", f"Nova resposta no chamado #{t.get('id')}.",
                     f"<a class='btn ghost small' href='/cliente/suporte/{t.get('id')}'>Ver</a>")
                )
            elif (t.get("status") or "") == "aberto":
                feed.append(
                    ("&#9203;", f"Chamado #{t.get('id')} em atendimento.",
                     _status_badge("aberto"))
                )
        try:
            from datetime import datetime as _dt

            dt = _mk_parse_dt((_mk_profile(email) or {}).get("vip_until"))
            if dt and _mk_vip_ativo(email) and (dt - _dt.utcnow()).days <= 7:
                feed.append(
                    ("&#128142;", "Seu VIP vence em breve.",
                     "<a class='btn ghost small' href='/cliente/troca/vip'>Renovar</a>")
                )
        except Exception:
            pass
    except Exception:
        pass
    return feed


@app.route("/cliente/notificacoes", methods=["GET"])
def cliente_notificacoes():
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()
    profile = _cliente_profile(email)
    tickets = _cliente_tickets(email)
    mine = _cliente_pedidos(email)
    feed = _cliente_feed_itens(email, profile, tickets, mine)
    if feed:
        itens = "".join(
            f"<div class='help-card'><div class='h-ic' aria-hidden='true'>{icone}</div>"
            f"<div class='h-t'>{texto}</div>"
            f"<div style='margin-top:8px'>{acao}</div></div>"
            for icone, texto, acao in feed[:8]
        )
        corpo = f"<div class='grid2'>{itens}</div>"
    else:
        corpo = (
            "<div class='empty-state'>"
            "<div class='em-ic' aria-hidden='true'>&#128276;</div>"
            "<h3>Tudo em dia</h3>"
            "<p>Nenhuma novidade por aqui.</p>"
            "</div>"
        )
    body = (
        "<div class='panel'><div class='panel-hd'><h2>&#128276; Notificações</h2></div>"
        + corpo + "</div>"
    )
    body = _voltar_card("Notificações", "Tudo que precisa da sua atenção.",
                        "Voltar ao Dashboard", "/cliente") + body
    return _cliente_dash_page("Notificações", "Notificações", "notificacoes", user, body)


# ============ MARKETPLACE (MARKTRADE) — área do cliente ============
def _mk_brl(value):
    v = _mk_num(value, 0)
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _mk_gp(value):
    """Formata preço em gp sem moeda inventada: inteiro com milhares, ou decimal."""
    if value is None or str(value).strip() == "":
        return "Aceita ofertas"
    v = _mk_num(value, 0)
    if v == int(v):
        return f"{int(v):,}".replace(",", ".")
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    inteiro, decimal = s.split(",")
    return f"{inteiro},{decimal}"


def _mk_num_br(value):
    """Decimal em formato BR (vírgula) ou ponto; None se vazio/inválido."""
    if value is None or str(value).strip() == "":
        return None
    text = str(value).replace("R$", "").replace(" ", "").strip()
    if "," in text:
        try:
            return float(text.replace(".", "").replace(",", "."))
        except ValueError:
            return None
    try:
        return float(text)
    except ValueError:
        return None


def _mk_tipo_lbl(tipo):
    return {"venda": "Venda", "compra": "Compra", "troca": "Troca"}.get(tipo or "venda", "Venda")


def _mk_status_badge(status):
    lbl = _mk_listing_status_lbl(status)
    cls = {
        "pendente": "pendente",
        "ativa": "pago",
        "expirada": "aberto",
        "encerrada": "aberto",
        "bloqueada": "cancelado",
    }.get(status or "pendente", "aberto")
    return f"<span class='badge {html.escape(cls)}'>{html.escape(lbl)}</span>"


def _mk_flash(tipo, texto):
    session["_mk_msg"] = [tipo, texto]


def _mk_consume_flash():
    msg = session.pop("_mk_msg", None)
    if not msg:
        return ""
    tipo, texto = msg[0], msg[1]
    cor = {"erro": "#f87171", "ok": "#4ade80"}.get(tipo, "#e2e8f0")
    return (
        "<div class='notice' style='color:" + cor + ";border-color:" + cor + "88'>"
        f"{html.escape(str(texto))}</div>"
    )


def _mk_pix_card(pag):
    """QR (imagem) + copia-e-cola do PIX de uma intenção de pagamento."""
    tx = _mk_mp_transaction(pag) or {}
    qr_b64 = tx.get("qr_code_base64") or ""
    qr_text = tx.get("qr_code") or pag.get("qr_code") or ""
    parts = ["<div style='margin:14px 0'>"]
    if qr_b64:
        parts.append(
            "<div style='text-align:center;margin-bottom:12px'>"
            f"<img src='data:image/png;base64,{html.escape(qr_b64)}' alt='QR Code Pix' "
            "style='width:190px;height:190px;border-radius:12px;background:#fff;padding:8px'></div>"
        )
    if qr_text:
        parts.append(
            "<label>Código PIX (copia e cola)</label>"
            f"<textarea rows='3' readonly style='font-size:12px'>{html.escape(qr_text)}</textarea>"
        )
    else:
        parts.append("<p style='color:#94a3b8'>QR indisponível no momento. Tente novamente em instantes.</p>")
    parts.append(
        "<p class='note'>Seu anúncio (ou VIP) é ATIVADO AUTOMATICAMENTE assim que o pagamento "
        "for confirmado pelo Mercado Pago — não precisa avisar ninguém.</p></div>"
    )
    return "".join(parts)


@app.route("/cliente/troca", methods=["GET"])
def cliente_troca():
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()

    cfg = _marketplace_config() or {}
    preco_pub = _mk_preco("preco_publicacao", 2.99)
    preco_des = _mk_preco("preco_destaque", 5.00)
    preco_vip = _mk_preco("preco_vip", 12.99)
    limite = _mk_limite()
    ativo = _mk_ativo()

    vip = _mk_vip_ativo(email)

    mine = _mk_minhas_listings(email)
    pagamentos = _mk_meus_pagamentos(email)
    pend = [l for l in mine if (l.get("status") or "") == "pendente"]
    ativas = [l for l in mine if (l.get("status") or "") in ("ativa", "pendente")]
    ilimitado = email in MASTER_EMAILS
    vagas = float("inf") if ilimitado else max(0, limite - len(ativas))

    kpis = (
        "<div class='kpis'>"
        f"<div class='kpi green'><div class='ic' aria-hidden='true'>&#128230;</div>"
        f"<div><div class='num'>{len(mine)}</div><div class='lbl'>Meus anúncios</div></div></div>"
        f"<div class='kpi blue'><div class='ic' aria-hidden='true'>&#11088;</div>"
        f"<div><div class='num'>{len(ativas)}</div><div class='lbl'>Ativos / pendentes</div></div></div>"
        f"<div class='kpi amber'><div class='ic' aria-hidden='true'>&#127919;</div>"
        f"<div><div class='num'>{'∞' if ilimitado else vagas}</div><div class='lbl'>Vagas ({'ilimitadas' if ilimitado else f'máx. {limite}'})</div></div></div>"
        f"<div class='kpi purple'><div class='ic' aria-hidden='true'>&#128081;</div>"
        f"<div><div class='num'>{'ATIVO' if vip else '—'}</div><div class='lbl'>VIP BAPZX</div></div></div>"
        "</div>"
    )

    vip_card = (
        "<div class='panel'>"
        "<div class='panel-hd'><h2>&#128081; VIP BAPZX</h2>"
        "<a class='btn ghost small' href='/cliente/troca/vip'>"
        + ("Renovar" if vip else "Assinar")
        + "</a></div>"
        + (
            f"<p>Seu VIP está <b>ativo</b> até <b>{_mk_fmt_dt((_mk_profile(email) or {}).get('vip_until'))}</b>. "
            "Anúncios de VIPs ganham o selo de verificado &#10004; e destaque na página pública do MARKTRADE."
            if vip
            else f"<p>Com o VIP BAPZX seu anúncio ganha o <b>selo ✓ de verificado</b> e suporte premium. "
            f"Plano mensal por <b>{_mk_brl(preco_vip)}</b>.</p>"
        )
        + "</div>"
    )

    if not ativo:
        tables = (
            "<div class='notice' style='color:#f87171'>As publicações do MARKTRADE estão "
            "<b>pausadas</b> no momento. Volte em breve.</div>"
        )
    else:
        form = (
            "<div class='panel'>"
            "<div class='panel-hd'><h2>&#128722; Publicar anúncio</h2>"
            f"<span class='badge pago'>{_mk_brl(preco_pub)}</span>"
            "</div>"
            f"<p class='note' style='font-weight:700'>Publicação por <b>{_mk_brl(preco_pub)}</b> · Destaque VIP + <b>{_mk_brl(preco_des)}</b> · "
            f"o anúncio fica válido por <b>{_mk_duracao('duracao_publicacao_dias', 30)} dias</b>. "
            f"Você publica quando quiser (até <b>{limite} ativos</b> ao mesmo tempo).</p>"
            + _MK_AC_CSS
            + _MK_FORM_CSS
            + "<form method='post' action='/cliente/troca/publicar' class='mk-form'>"
            f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
            "<div class='mk-row c3'>"
            "<div><label>Item *</label><input name='item_name' id='item_name' required maxlength='120' "
            "placeholder='Ex.: War Hammer' autocomplete='off'>"
            "<input type='hidden' name='sprite' id='mk_sprite_url' value=''>"
            "<span id='mk_sprite_prev' class='mk-sprite-prev' hidden></span></div>"
            "<div><label>Personagem *</label><input name='character_name' required maxlength='60' "
            "placeholder='Ex.: Bapz'></div>"
            "<div><label>Mundo *</label><select name='world' required>"
            "<option value=''>Selecione o mundo...</option>"
            + "".join(f"<option value='{html.escape(m)}'>{html.escape(m)}</option>" for m in _MK_MUNDOS)
            + "</select></div>"
            "</div>"
            "<div class='mk-row c2'>"
            "<div><label>Tipo de anúncio</label><select name='tipo_anuncio'>"
            "<option value='venda'>Vendendo</option>"
            "<option value='compra'>Comprando</option>"
            "<option value='troca'>Quer trocar</option>"
            "</select></div>"
            "<div><label>Tier do item *</label><select name='tier' id='mk_tier'>"
            "<option value='0' selected>0 — Normal (sem upgrade)</option>"
            + "".join(f"<option value='{t}'>Tier {t}</option>" for t in range(1, 11))
            + "</select>"
            "</div>"
            "</div>"
            "<label>Como quer negociar?</label>"
            "<div class='mk-seg'>"
            "<button type='button' class='mk-seg-opt on' data-target='preco_fixo'>Preço fixo</button>"
            "<button type='button' class='mk-seg-opt' data-target='aceito_ofertas'>Aceito ofertas</button>"
            "</div>"
            "<input type='hidden' name='modo_preco' id='mk_modo_preco' value='preco_fixo'>"
            "<div class='mk-row c2'>"
            "<div id='mk_bloco_preco'><label>Preço em gp *</label>"
            "<input name='preco' id='mk_preco' type='text' inputmode='numeric' required placeholder='Ex.: 250000'></div>"
            "<div><label>WhatsApp com DDD *</label>"
            "<input name='contact' required id='mk_contato' maxlength='16' inputmode='numeric' "
            "autocomplete='tel' placeholder='(19) 98765-4321'>"
            "<p class='note' style='margin-top:2px'>Só aceitamos WhatsApp com DDD — ex.: <b>(19) 98765-4321</b>.</p></div>"
            "</div>"
"<p><label class='mk-destaque'>"
            "<input type='checkbox' name='destaque' value='1'>"
            "<span class='mk-destaque-box'>"
            "<span class='mk-destaque-dot' aria-hidden='true'></span>"
            "<span class='mk-destaque-star' aria-hidden='true'><svg viewBox='0 0 24 24' width='24' height='24'><path fill='#fbbf24' d='M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z'/></svg></span>"
            "<span class='mk-destaque-txt'>"
            "<span class='mk-destaque-title'>Destacar meu anúncio "
            f"<b class='mk-destaque-price'>(+ {_mk_brl(preco_des)})</b></span>"
            "<span class='mk-destaque-note'>Fica no topo da lista pública do MARKTRADE com a tag de destaque.</span>"
            "</span></span></label></p>"
            "<p style='margin-top:10px'><button class='btn mk-publish-btn' type='submit'>Publicar agora</button></p>"
            "</form>"
            + _MK_AC_SCRIPT
            + _MK_FORM_JS
            + _MK_SPRITE_JS
            + "</div>"
        )

        if mine:
            por_listing = {}
            for p in pagamentos:
                por_listing.setdefault(p.get("listing_id"), []).append(p)

            def _linha(l):
                lid = l.get("id")
                pend_pags = [p for p in (por_listing.get(lid) or []) if (p.get("status") or "") == "pendente"]
                acoes = []
                if (l.get("status") or "") == "pendente" and pend_pags:
                    acoes.append(
                        f"<form method='get' action='/cliente/troca/pagar/{lid}' style='display:inline'>"
                        "<button class='btn small'>Pagar Pix</button></form>"
                    )
                if (l.get("status") or "") in ("pendente", "ativa"):
                    acoes.append(
                        f"<form method='post' action='/cliente/troca/cancelar/{lid}' style='display:inline'>"
                        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
                        "<button class='btn ghost small'>Encerrar</button></form>"
                    )
                dest = (
                    "<span title='Destaque' style='color:#f59e0b'>&#11088; </span>"
                    if l.get("is_destaque")
                    else ""
                )
                ver = "&#10004; " if l.get("verificado") else ""
                preco_txt = (
                    f"<b>{html.escape(_mk_gp(l.get('preco')))}</b>"
                    if l.get("preco") is not None
                    else "Aceita ofertas"
                )
                try:
                    _t = l.get("tier", None)
                    tier_txt = (
                        "—" if _t is None or str(_t).strip() == ""
                        else (f"Tier {int(float(str(_t).strip()))}" if int(float(str(_t).strip())) > 0 else "Normal")
                    )
                except (TypeError, ValueError):
                    tier_txt = "—"
                return (
                    "<tr>"
                    f"<td><b>#{html.escape(str(lid or '-'))}</b></td>"
                    f"<td>{dest}{f'{ver}'}{html.escape(str(l.get('item_name') or '-'))}</td>"
                    f"<td>{html.escape(_mk_tipo_lbl(l.get('tipo_anuncio')))}</td>"
                    f"<td>{html.escape(tier_txt)}</td>"
                    f"<td>{preco_txt}</td>"
                    f"<td>{html.escape(str(l.get('world') or '-'))}</td>"
                    f"<td>{html.escape(_mk_fmt_dt(l.get('created_at')))}</td>"
                    f"<td>{_mk_status_badge(l.get('status'))}</td>"
                    f"<td class='acts'>{''.join(acoes)}</td>"
                    "</tr>"
                )

            tabela = "".join(_linha(l) for l in mine)
            wipe_btn = (
                f"<form method='post' action='/cliente/troca/excluir-tudo' style='display:inline;margin-left:auto' "
                f"onsubmit=\"return confirm('Excluir TODOS os anúncios? Não tem volta!')\">"
                f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
                "<button class='btn ghost small' style='color:#f87171;border-color:rgba(248,113,113,.5)'>"
                "EXCLUIR TUDO</button></form>"
                if email in MASTER_EMAILS else ""
            )
            meus = (
                "<div class='panel'><div class='panel-hd'><h2>&#128203; Meus anúncios</h2>"
                + wipe_btn + "</div>"
                "<div class='table-wrap'><table>"
                "<tr><th>#</th><th>Item</th><th>Tipo</th><th>Tier</th><th>Preço</th><th>Mundo</th><th>Publicado</th>"
                "<th>Status</th><th>Ação</th></tr>"
                + tabela
                + "</table></div></div>"
            )
        else:
            meus = (
                "<div class='panel'>"
                "<div class='empty-state'><div class='em-ic' aria-hidden='true'>&#128230;</div>"
                "<h3>Você ainda não publicou nada</h3>"
                "<p>Publique um anúncio de venda, compra ou troca de itens do Tibia. "
                "Ele aparece na página pública do MARKTRADE após o pagamento.</p></div>"
                "</div>"
            )
        tables = form + meus

    body = (
        _MK_PAGE_CSS
        + "<div class='welcome'>"
        "<div><h2>MARKTRADE &#128176;</h2>"
        "<p>Troca de itens do Tibia — publique venda, compra ou troca e negocie entre jogadores.</p></div>"
        f"<a class='btn' href='{PORTFOLIO_URL}troca.html'>Ver anúncios públicos</a>"
        "<a class='btn ghost' href='/cliente'>Voltar ao Dashboard</a></div>"
        + _mk_consume_flash()
        + (
            "<div class='notice' style='color:#fbbf24'>Você está no <b>modo teste do dono</b> — "
            "publicações e VIP são ativados sem gerar cobrança/Pix.</div>"
            if email in MASTER_EMAILS
            else ""
        )
        + kpis
        + vip_card
        + tables
    )
    return _cliente_dash_page("MARKTRADE", "MARKTRADE", "troca", user, body)


@app.route("/cliente/troca/publicar", methods=["POST"])
def cliente_troca_publicar():
    user = current_user()
    if not user:
        return redirect("/login")
    if not _csrf_ok():
        return "Requisição inválida (CSRF).", 403
    if not _mk_ativo():
        _mk_flash("erro", "As publicações do MARKTRADE estão pausadas no momento.")
        return redirect("/cliente/troca")
    email = user["email"].lower()

    item_name = _mk_title_case((request.form.get("item_name") or "").strip())[:120]
    character_name = (request.form.get("character_name") or "").strip()[:60]
    world = (request.form.get("world") or "").strip()
    contact = _mk_whatsapp(request.form.get("contact"))
    tipo = (request.form.get("tipo_anuncio") or "venda").strip().lower()
    sprite = (request.form.get("sprite") or "").strip()[:300]
    if sprite and not (sprite.startswith("http://") or sprite.startswith("https://")):
        sprite = ""
    if not sprite:
        sprite = _mk_itemsprite(item_name)
    if sprite:
        sprite = _mk_sprite_host(sprite)
    if tipo not in ("venda", "compra", "troca"):
        return "Tipo de anúncio inválido.", 400
    if not item_name or not character_name or not world:
        _mk_flash("erro", "Informe o item, o personagem e o mundo.")
        return redirect("/cliente/troca")
    if not contact:
        _mk_flash("erro", "Informe um WhatsApp válido com DDD — ex.: (19) 98765-4321.")
        return redirect("/cliente/troca")
    if world not in _MK_MUNDOS:
        _mk_flash("erro", "Selecione um mundo válido para o anúncio.")
        return redirect("/cliente/troca")

    modo_preco = (request.form.get("modo_preco") or "").strip().lower()
    preco = _mk_num_br(request.form.get("preco"))
    aceita_ofertas = request.form.get("aceita_ofertas") == "1" or modo_preco == "aceito_ofertas"
    if modo_preco == "preco_fixo" and preco is None and not aceita_ofertas:
        _mk_flash("erro", "Defina o preço em gp ou escolha 'Aceito ofertas'.")
        return redirect("/cliente/troca")
    if preco is not None and preco < 0:
        _mk_flash("erro", "Preço não pode ser negativo.")
        return redirect("/cliente/troca")
    if preco is None and not aceita_ofertas:
        aceita_ofertas = True
    destaque = request.form.get("destaque") == "1"

    try:
        tier = int(str(request.form.get("tier") or "0").strip())
    except (TypeError, ValueError):
        tier = 0
    if tier < 0:
        tier = 0
    max_tier = _mk_max_tier(item_name)
    if tier > max_tier:
        cls = _mk_class_of(item_name)
        detalhe = f"classe {cls} (máximo {max_tier})" if cls else f"máximo permitido {max_tier}"
        _mk_flash("erro", f"{item_name} é {detalhe} — ajuste o tier do anúncio.")
        return redirect("/cliente/troca")

    ativas = [l for l in _mk_minhas_listings(email) if (l.get("status") or "") in ("ativa", "pendente")]
    limite = _mk_limite()
    if email not in MASTER_EMAILS and len(ativas) >= limite:
        _mk_flash("erro", f"Você atingiu o limite de {limite} publicações ativas no MARKTRADE.")
        return redirect("/cliente/troca")

    agora = datetime.utcnow()
    payload = {
        "user_id": email,
        "item_name": item_name,
        "character_name": character_name,
        "world": world,
        "contact": contact,
        "tipo_anuncio": tipo,
        "status": "pendente",
        "is_destaque": False,
        "preco": preco,
        "aceita_ofertas": aceita_ofertas,
        "sprite": sprite,
        "tier": tier,
        "verificado": _mk_vip_ativo(email),
        "expires_at": (agora + timedelta(days=_mk_duracao("duracao_publicacao_dias", 30))).isoformat(timespec="seconds"),
    }
    try:
        response = requests.post(
            f"{STORE.url}/rest/v1/marketplace_listings",
            headers={**STORE._headers(), "Prefer": "return=representation"},
            json=payload,
            timeout=15,
        )
    except Exception as exc:
        return f"Falha ao publicar: {exc}", 500
    if response.status_code == 400 and "tier" in (response.text or "") and "tier" in payload:
        # Coluna tier ainda não criada no Supabase: republica sem o campo
        # para não travar a publicação (o tier passa a valer após a migration).
        payload.pop("tier", None)
        try:
            response = requests.post(
                f"{STORE.url}/rest/v1/marketplace_listings",
                headers={**STORE._headers(), "Prefer": "return=representation"},
                json=payload,
                timeout=15,
            )
        except Exception as exc:
            return f"Falha ao publicar: {exc}", 500
    if response.status_code not in (200, 201):
        return f"Falha ao publicar: {response.status_code} {response.text[:200]}", 500
    criado = (response.json() or [{}])[0]
    lid = criado.get("id")
    if not lid:
        return "Resposta inesperada do servidor.", 500

    # Modo teste do dono (MASTER): publica ATIVADO direto, sem gerar Pix/QR.
    if email in MASTER_EMAILS:
        agora_iso = agora.isoformat(timespec="seconds")
        patch = {
            "status": "ativa",
            "is_destaque": bool(destaque),
            "expires_at": (agora + timedelta(days=_mk_duracao("duracao_publicacao_dias", 30))).isoformat(timespec="seconds"),
            "updated_at": agora_iso,
        }
        if destaque:
            patch["destaque_until"] = (agora + timedelta(days=_mk_duracao("duracao_destaque_dias", 30))).isoformat(timespec="seconds")
        try:
            requests.patch(
                f"{STORE.url}/rest/v1/marketplace_listings?id=eq.{lid}",
                headers=STORE._headers(),
                json=patch,
                timeout=15,
            )
        except Exception as exc:
            print(f"[mk] falha ao ativar anúncio (modo teste) {lid}: {exc}")
        _mk_flash("ok", "Anúncio publicado! (modo teste do dono — publicado sem cobrança).")
        return redirect("/cliente/troca")

    preco_pub = _mk_preco("preco_publicacao", 2.99)
    preco_des = _mk_preco("preco_destaque", 5.00)
    if destaque:
        ref, tipo_pag, valor = f"DES-{lid}", "destaque", preco_pub + preco_des
    else:
        ref, tipo_pag, valor = f"PUB-{lid}", "publicacao", preco_pub

    try:
        response = requests.post(
            f"{STORE.url}/rest/v1/marketplace_pagamentos",
            headers={**STORE._headers(), "Prefer": "return=representation"},
            json={
                "external_reference": ref,
                "tipo": tipo_pag,
                "listing_id": lid,
                "user_id": email,
                "valor": valor,
                "status": "pendente",
            },
            timeout=15,
        )
        pag = (response.json() or [{}])[0]
        pid = pag.get("id")
    except Exception as exc:
        return f"Falha ao criar o pagamento: {exc}", 500

    ok = False
    try:
        ok, charge = create_marketplace_pix(ref, valor, f"{item_name} ({_mk_tipo_lbl(tipo)})", email, user.get("name") or "Cliente")
    except Exception as exc:
        ok, charge = False, f"erro interno: {exc}"
    if not ok:
        _mk_flash("erro", f"Não foi possível gerar o Pix agora: {charge}")
        return redirect(f"/cliente/troca/pagar/{lid}")
    tx = (charge.get("point_of_interaction") or {}).get("transaction_data") or {}
    try:
        requests.patch(
            f"{STORE.url}/rest/v1/marketplace_pagamentos?id=eq.{pid}",
            headers=STORE._headers(),
            json={
                "mp_id": str(charge.get("id") or ""),
                "qr_code": tx.get("qr_code") or "",
            },
            timeout=15,
        )
    except Exception:
        pass
    return redirect(f"/cliente/troca/pagar/{lid}")


@app.route("/cliente/troca/gerar/<int:lid>", methods=["POST"])
def cliente_troca_gerar(lid):
    user = current_user()
    if not user:
        return redirect("/login")
    if not _csrf_ok():
        return "Requisição inválida (CSRF).", 403
    email = user["email"].lower()
    listing = _mk_listing(lid)
    if not listing or (listing.get("user_id") or "").lower() != email:
        return "Anúncio não encontrado.", 404
    if (listing.get("status") or "") != "pendente":
        _mk_flash("ok", "Este anúncio já foi processado.")
        return redirect("/cliente/troca")
    pag = None
    for p in _mk_meus_pagamentos(email):
        if p.get("listing_id") == lid and (p.get("status") or "") == "pendente":
            pag = p
            break
    if not pag:
        _mk_flash("erro", "Pagamento não localizado; publique novamente.")
        return redirect("/cliente/troca")
    valor = _mk_num(pag.get("valor"), 0)
    ref = pag.get("external_reference") or f"PUB-{lid}"
    try:
        ok, charge = create_marketplace_pix(ref, valor, listing.get("item_name") or "Anúncio", email, user.get("name") or "Cliente")
    except Exception as exc:
        ok, charge = False, f"erro interno: {exc}"
    if not ok:
        _mk_flash("erro", f"Não foi possível gerar o Pix: {charge}")
        return redirect(f"/cliente/troca/pagar/{lid}")
    tx = (charge.get("point_of_interaction") or {}).get("transaction_data") or {}
    try:
        requests.patch(
            f"{STORE.url}/rest/v1/marketplace_pagamentos?id=eq.{pag['id']}",
            headers=STORE._headers(),
            json={"mp_id": str(charge.get("id") or ""), "qr_code": tx.get("qr_code") or ""},
            timeout=15,
        )
    except Exception:
        pass
    return redirect(f"/cliente/troca/pagar/{lid}")


@app.route("/cliente/troca/pagar/<int:lid>", methods=["GET", "POST"])
def cliente_troca_pagar(lid):
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()
    if request.method == "POST":
        if not _csrf_ok():
            return "Requisição inválida (CSRF).", 403
        return redirect(f"/cliente/troca/gerar/{lid}")
    listing = _mk_listing(lid)
    if not listing or (listing.get("user_id") or "").lower() != email:
        return "Anúncio não encontrado.", 404
    if (listing.get("status") or "") in ("ativa", "expirada"):
        _mk_flash("ok", "Seu anúncio já está no ar no MARKTRADE.")
        return redirect("/cliente/troca")
    if (listing.get("status") or "") in ("encerrada", "bloqueada"):
        _mk_flash("erro", "Este anúncio foi encerrado.")
        return redirect("/cliente/troca")

    pag = None
    for p in _mk_meus_pagamentos(email):
        if p.get("listing_id") == lid and (p.get("status") or "") == "pendente":
            pag = p
            break

    corpo_qr = ""
    retry = ""
    if not pag:
        retry = (
            "<p class='note'>Nenhum Pix em aberto para este anúncio. Gere um novo.</p>"
            "<form method='post' action='/cliente/troca/gerar/" + str(lid) + "'>"
            f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
            "<button class='btn' type='submit'>Gerar Pix agora</button></form>"
        )
    else:
        tx = _mk_mp_transaction(pag)
        status_mp = ""
        if pag.get("mp_id") and MP_ACCESS_TOKEN:
            try:
                resp = requests.get(
                    f"https://api.mercadopago.com/v1/payments/{pag['mp_id']}",
                    headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
                    timeout=15,
                )
                if resp.status_code == 200:
                    status_mp = (resp.json() or {}).get("status") or ""
            except Exception:
                status_mp = ""
        if status_mp == "approved":
            _marketplace_confirm(pag.get("external_reference") or f"PUB-{lid}", pag.get("mp_id"))
            _mk_flash("ok", "Pagamento confirmado! Seu anúncio já está no ar.")
            return redirect("/cliente/troca")
        corpo_qr = _mk_pix_card(pag or {})
        retry = (
            "<form method='post' action='/cliente/troca/gerar/" + str(lid) + "' style='margin-top:12px'>"
            f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
            "<button class='btn ghost small' type='submit'>O código expirou? Gerar outro Pix</button></form>"
        )

    body = (
        _voltar_card("Pagamento", "Conclua o Pix para ativar seu anúncio.",
                     "Voltar ao MARKTRADE", "/cliente/troca")
        + "<div class='panel'>"
        f"<div class='panel-hd'><h2>&#128179; Pagamento da publicação #{html.escape(str(lid or '-'))}</h2></div>"
        f"<p><b>{html.escape(str(listing.get('item_name') or '-'))}</b> · "
        f"{html.escape(_mk_tipo_lbl(listing.get('tipo_anuncio')))} · "
        f"<b>{_mk_brl((pag or {}).get('valor') or 0)}</b></p>"
        + _mk_consume_flash()
        + corpo_qr
        + retry
        + "<p class='legal-note'>Ao publicar, você concorda com nossos "
        "<a href='/termos'>Termos de Uso</a> e <a href='/privacidade'>Política de Privacidade</a> (LGPD)."
        "</div>"
    )
    return _cliente_dash_page("Pagamento", "MARKTRADE", "troca", user, body)


@app.route("/cliente/troca/cancelar/<int:lid>", methods=["POST"])
def cliente_troca_cancelar(lid):
    user = current_user()
    if not user:
        return redirect("/login")
    if not _csrf_ok():
        return "Requisição inválida (CSRF).", 403
    email = user["email"].lower()
    listing = _mk_listing(lid)
    if not listing or (listing.get("user_id") or "").lower() != email:
        return "Anúncio não encontrado.", 404
    if (listing.get("status") or "") not in ("pendente", "ativa"):
        _mk_flash("erro", "Este anúncio não pode mais ser encerrado.")
        return redirect("/cliente/troca")
    try:
        requests.patch(
            f"{STORE.url}/rest/v1/marketplace_listings?id=eq.{lid}",
            headers=STORE._headers(),
            json={"status": "encerrada", "updated_at": datetime.utcnow().isoformat(timespec="seconds")},
            timeout=15,
        )
        requests.patch(
            f"{STORE.url}/rest/v1/marketplace_pagamentos?listing_id=eq.{lid}&status=eq.pendente",
            headers=STORE._headers(),
            json={"status": "cancelado"},
            timeout=15,
        )
    except Exception as exc:
        return f"Falha ao encerrar: {exc}", 500
    _mk_flash("ok", "Anúncio encerrado.")
    return redirect("/cliente/troca")


@app.route("/cliente/troca/excluir-tudo", methods=["POST"])
def cliente_troca_excluir_tudo():
    """Apaga TODOS os anúncios (modo teste do dono). Só MASTER."""
    user = current_user()
    if not user:
        return redirect("/login")
    if not _csrf_ok():
        return "Requisição inválida (CSRF).", 403
    email = user["email"].lower()
    if email not in MASTER_EMAILS:
        return "Acesso restrito ao dono.", 403
    try:
        got = requests.get(
            f"{STORE.url}/rest/v1/marketplace_listings?select=id&limit=1000",
            headers=STORE._headers(),
            timeout=20,
        )
        ids = [r.get("id") for r in (got.json() or []) if r.get("id") is not None]
    except Exception as exc:
        return f"Falha ao listar: {exc}", 500
    apagados = 0
    for lid in ids:
        try:
            resp = requests.delete(
                f"{STORE.url}/rest/v1/marketplace_listings?id=eq.{lid}",
                headers=STORE._headers(),
                timeout=15,
            )
            if resp.status_code in (200, 204):
                apagados += 1
        except Exception:
            continue
    _mk_flash("ok", f"{apagados} anúncio(s) excluído(s).")
    return redirect("/cliente/troca")


@app.route("/cliente/troca/vip", methods=["GET", "POST"])
def cliente_troca_vip():
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()

    if request.method == "POST":
        if not _csrf_ok():
            return "Requisição inválida (CSRF).", 403
        preco_vip = _mk_preco("preco_vip", 12.99)
        ref, tipo_pag, valor = f"VIP-{email}", "vip", preco_vip
        # Modo teste do dono (MASTER): ativa o VIP direto, sem gerar Pix/QR.
        if email in MASTER_EMAILS:
            dia = (datetime.utcnow() + timedelta(days=_mk_duracao("duracao_vip_dias", 30))).isoformat(timespec="seconds")
            try:
                requests.patch(
                    f"{STORE.url}/rest/v1/profiles?email=eq.{email}",
                    headers=STORE._headers(),
                    json={"vip_until": dia},
                    timeout=15,
                )
                _MK_VIP_CACHE.pop(email, None)
            except Exception as exc:
                return f"Falha ao ativar VIP: {exc}", 500
            _mk_flash("ok", "VIP BAPZX ativado! (modo teste do dono — sem cobrança).")
            return redirect("/cliente/troca/vip")
        try:
            response = requests.post(
                f"{STORE.url}/rest/v1/marketplace_pagamentos",
                headers={**STORE._headers(), "Prefer": "return=representation"},
                json={
                    "external_reference": ref,
                    "tipo": tipo_pag,
                    "user_id": email,
                    "valor": valor,
                    "status": "pendente",
                },
                timeout=15,
            )
            pag = (response.json() or [{}])[0]
            pid = pag.get("id")
        except Exception as exc:
            return f"Falha ao criar o pagamento: {exc}", 500
        try:
            ok, charge = create_marketplace_pix(ref, valor, "Plano VIP BAPZX mensal", email, user.get("name") or "Cliente")
        except Exception as exc:
            ok, charge = False, f"erro interno: {exc}"
        if not ok:
            _mk_flash("erro", f"Não foi possível gerar o Pix agora: {charge}")
            return redirect("/cliente/troca/vip")
        tx = (charge.get("point_of_interaction") or {}).get("transaction_data") or {}
        try:
            requests.patch(
                f"{STORE.url}/rest/v1/marketplace_pagamentos?id=eq.{pid}",
                headers=STORE._headers(),
                json={"mp_id": str(charge.get("id") or ""), "qr_code": tx.get("qr_code") or ""},
                timeout=15,
            )
        except Exception:
            pass
        return redirect("/cliente/troca/vip")

    preco_vip = _mk_preco("preco_vip", 12.99)
    vip_dt = _mk_parse_dt((_mk_profile(email) or {}).get("vip_until"))
    vip = bool(vip_dt and vip_dt > datetime.utcnow())
    pend = None
    for p in _mk_meus_pagamentos(email):
        if (p.get("tipo") or "") == "vip" and (p.get("status") or "") == "pendente":
            pend = p
            break

    if pend and pend.get("mp_id"):
        status_mp = ""
        try:
            resp = requests.get(
                f"https://api.mercadopago.com/v1/payments/{pend['mp_id']}",
                headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
                timeout=15,
            )
            if resp.status_code == 200:
                status_mp = (resp.json() or {}).get("status") or ""
        except Exception:
            status_mp = ""
        if status_mp == "approved":
            _marketplace_confirm(pend.get("external_reference") or f"VIP-{email}", pend.get("mp_id"))
            _MK_VIP_CACHE.pop(email, None)
            _mk_flash("ok", "Pagamento confirmado! Você já é VIP BAPZX.")
            return redirect("/cliente/troca/vip")

    status_card = (
        "<div class='panel'>"
        "<div class='panel-hd'><h2>&#128081; Sua assinatura VIP</h2></div>"
        + (
            f"<p>Você é <b>VIP BAPZX</b> até <b>{_mk_fmt_dt((_mk_profile(email) or {}).get('vip_until'))}</b>. "
            "Renove quando quiser — adicionamos os dias a partir de hoje.</p>"
            if vip
            else f"<p>Você ainda não é VIP. Plano mensal por <b>{_mk_brl(preco_vip)}</b> via Pix.</p>"
        )
        + "<p>Vantagens: &#10004; selo de verificado nos anúncios do MARKTRADE · &#128081; badge VIP "
        "na sua área do cliente · &#129351; prioridade no atendimento.</p>"
        + "</div>"
    )

    corpo_qr = _mk_pix_card(pend) if pend else ""
    assinar = (
        "<div class='panel'>"
        "<div class='panel-hd'><h2>"
        + ("Novo pagamento" if pend else "Assinar VIP")
        + "</h2></div>"
        + _mk_consume_flash()
        + corpo_qr
        + ("<p class='note'>Você já tem um Pix em aberto — finalize ele ou aguarde alguns minutos "
           "para o anterior expirar.</p>" if pend else "")
        + ("<form method='post'><input type='hidden' name='_csrf' value='" + html.escape(_csrf_token()) + "'>"
           "<p style='margin-top:8px'><button class='btn' type='submit'>"
           f"Gerar Pix de {_mk_brl(preco_vip)}</button></p></form>"
           if not pend else "")
        + "</div>"
    )

    body = (
        "<div class='welcome'><div><h2>VIP BAPZX</h2>"
        "<p>Plano mensal com selo de verificado no MARKTRADE e prioridade no atendimento.</p></div>"
        "<a class='btn ghost' href='/cliente/troca'>Voltar ao MARKTRADE</a></div>"
        + (
            "<div class='notice' style='color:#fbbf24'>Você está no <b>modo teste do dono</b> — "
            "o VIP é ativado sem gerar cobrança/Pix.</div>"
            if email in MASTER_EMAILS
            else ""
        )
        + status_card
        + assinar
    )
    return _cliente_dash_page("VIP BAPZX", "MARKTRADE", "troca", user, body)


def notify_owner(entry):
    owner_chat = load_env_key("TELEGRAM_OWNER_CHAT_ID")
    if not owner_chat:
        return
    if _config_map().get("notificar_pedido") == "0":
        return
    lines = ["🛒 NOVO PEDIDO"]
    lines.append(f"Usuário: {entry['usuario']}")
    lines.append(f"ID: {entry['chat_id']}")
    if entry.get("tc"):
        lines.append(f"RC: {entry['tc']}")
    if entry.get("preco"):
        lines.append(f"Preço: {entry['preco']}")
    if entry.get("pagamento"):
        lines.append(f"Pagamento: {entry['pagamento']}")
    if entry.get("mundo"):
        lines.append(f"Mundo: {entry['mundo']}")
    if entry.get("char"):
        lines.append(f"Char: {entry['char']}")
    lines.append(f"Status: {entry.get('status') or 'pendente'} (confirme com /pago + id)")
    lines.append(f"Quando: {entry['data']}")
    lines.append(f"Mensagem: {entry['mensagem']}")
    send_message(owner_chat, "\n".join(lines))


def notify_owner_pix(charge, entry):
    audit_log(
        "pix_gerado",
        f"pedido {entry.get('id')} | {entry.get('tc')} RC | {entry.get('preco')} | MP {charge.get('id')}",
    )
    owner_chat = load_env_key("TELEGRAM_OWNER_CHAT_ID")
    if not owner_chat:
        return
    if _config_map().get("notificar_pix") == "0":
        return
    linhas = ["🧾 PIX GERADO PARA O PEDIDO"]
    linhas.append(f"Pedido: {entry.get('id')}")
    if entry.get("tc"):
        linhas.append(f"RC: {entry['tc']}")
    if entry.get("preco"):
        linhas.append(f"Valor: {entry['preco']}")
    if entry.get("usuario"):
        linhas.append(f"Cliente: {entry['usuario']}")
    linhas.append(f"Mercado Pago id: {charge.get('id')}")
    linhas.append('Aguardando pagamento (confirmação automática).')
    send_message(owner_chat, "\n".join(linhas))


def reply_vendor(chat_id, username):
    owner_chat = load_env_key("TELEGRAM_OWNER_CHAT_ID")
    send_message(
        chat_id,
        'Você foi encaminhado a um atendente humano. Ele vai te chamar aqui '
        "em instantes. Fique on-line e me diga se a demora passar de alguns minutos.",
    )
    if owner_chat:
        send_message(
            owner_chat,
            "ðŸ™‹ CLIENTE SOLICITOU ATENDENTE HUMANO\n"
            f"Usuário: {username}\n"
            f"ID: {chat_id}\n"
            "Responda este chat iniciando a conversa com o cliente.",
        )


def set_webhook(url):
    payload = {"url": url}
    if TELEGRAM_WEBHOOK_SECRET:
        payload["secret_token"] = TELEGRAM_WEBHOOK_SECRET
    response = requests.post(f"{BASE}/setWebhook", json=payload, timeout=15)
    print("setWebhook:", response.json())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    if len(sys.argv) > 1 and sys.argv[1] == "--set-webhook":
        set_webhook(sys.argv[2] if len(sys.argv) > 2 else f"{RENDER_URL}/webhook")
    else:
        import threading

        threading.Thread(target=_relatorio_automatico, daemon=True).start()
        app.run(host="0.0.0.0", port=port)
