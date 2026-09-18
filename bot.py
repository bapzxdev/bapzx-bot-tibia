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
from datetime import datetime, timedelta

import requests
from flask import Flask, request, redirect, session
from werkzeug.exceptions import HTTPException

from storage import OrderStore
from painel import bp as painel_bp
from painel import _csrf_token as _csrf_token, _csrf_ok as _csrf_ok
import rbac as rbac
import legais as legais

VERSION = "2.7.3"

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


def price_table_text():
    return (
        "🪙 TABELA DE PREÇOS — BAPZX COINS\n\n"
        "100 RC  — R$ 9,00\n"
        "250 RC  — R$ 22,50\n"
        "500 RC  — R$ 45,00\n"
        "1.000 RC — R$ 90,00\n"
        "2.500 RC — R$ 225,00\n\n"
        "💳 Pagamento: Pix\n\n"
        "⚡ Entrega:\n"
        "Será enviada em até 10 minutos após a confirmação do pagamento.\n\n"
        "🛒 Para comprar, use /compra\n"
        "💬 Atendimento: /vendedor"
    )


def price_table_compact():
    lines = []
    for value, price in PRICES.items():
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


def load_persona():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "persona.txt")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return 'Você é um assistente de atendimento em português do Brasil.'


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
        'proporção de que 1.000 RC custam R$ 90: multiplique a quantidade por 90, divida '
        'por 1.000 e mostre o cálculo passo a passo, terminando com o valor em Reais.\n'
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
    tabela = _precos_config()
    if tc in tabela:
        return tabela[tc]
    value = tc * 90 / 1000
    return f"R${value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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
main {{ padding: 24px; max-width: 900px; margin: 0 auto; }}
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
<title>BAPZX · {title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@500;700;800&display=swap" rel="stylesheet">
<style>
body {{ font-family: Arial, sans-serif; margin: 0; background: #0f172a; color: #e2e8f0; }}
header {{ background: #1e293b; padding: 18px 24px; display: flex; align-items: center; justify-content: space-between; }}
header h1 {{ margin: 0; font-size: 18px; }}
header a {{ color: #94a3b8; font-size: 13px; text-decoration: none; }}
.brand {{ font-family: 'Sora', sans-serif; font-weight: 800; font-size: 18px; letter-spacing: 2px; color: #fff; }}
.brand span {{ background: linear-gradient(135deg,#34d399 0%,#4ade80 35%,#60a5fa 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }}
main {{ padding: 24px; max-width: 960px; margin: 0 auto; }}
label {{ display: block; margin-top: 10px; color: #94a3b8; font-size: 13px; }}
input, select, textarea {{ width: 100%; margin-top: 4px; padding: 9px 11px; border: 1px solid #334155; border-radius: 8px; background: #0f172a; color: #e2e8f0; font-size: 14px; box-sizing: border-box; }}
.btn {{ background: #4ade80; color: #052e16; border: 0; border-radius: 8px; padding: 10px 18px; font-weight: bold; cursor: pointer; font-size: 14px; }}
.legal-note {{ font-size: 12px; color: #64748b; margin-top: 12px; }}
footer {{ border-top: 1px solid #1e293b; margin-top: 34px; padding: 20px 24px; background: #0b1424; font-size: 12.5px; color: #64748b; text-align: center; }}
footer a {{ color: #8ea0b8; text-decoration: none; margin: 0 8px; }}
.size-note {{ font-size: 12px; color: #64748b; }}
.cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 18px 0; }}
.card {{ background: #1e293b; border-radius: 10px; padding: 14px 18px; flex: 1; min-width: 150px; }}
.card .num {{ font-size: 24px; font-weight: bold; color: #4ade80; }}
.card .lbl {{ font-size: 12px; color: #94a3b8; }}
section {{ background: #1e293b; border-radius: 10px; padding: 16px 20px; margin: 18px 0; }}
section h2 {{ margin-top: 0; font-size: 15px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ text-align: left; padding: 7px 8px; border-bottom: 1px solid #334155; vertical-align: middle; }}
th {{ color: #94a3b8; font-weight: normal; }}
.empty {{ text-align: center; color: #64748b; padding: 18px; }}
.status {{ padding: 2px 8px; border-radius: 5px; font-size: 11px; font-weight: bold; }}
.status.pendente {{ background: #78350f; color: #fbbf24; }}
.status.pago {{ background: #064e3b; color: #4ade80; }}
.status.entregue {{ background: #1e3a5f; color: #60a5fa; }}
.status.cancelado {{ background: #7f1d1d; color: #f87171; }}
.acts form {{ display: inline; }}
.acts button {{ background: #334155; border: 0; color: #e2e8f0; border-radius: 6px; padding: 5px 10px; cursor: pointer; font-size: 12px; }}
.acts button.pago {{ background: #064e3b; color: #4ade80; }}
.acts button.entregue {{ background: #1e3a5f; color: #60a5fa; }}
.note {{ font-size: 12.5px; color: #94a3b8; }}
.big {{ display: inline-block; background: #4ade80; color: #052e16; text-decoration: none; padding: 12px 22px; border-radius: 10px; font-weight: bold; }}
</style>
</head>
<body>
<header><h1><span class="brand">BAP<span>ZX</span></span> · {brand}</h1>{top}</header>
<main>{body}</main>
<footer>
  <span>© 2026 BAPZX · Vendas de RC no Tibia</span><br>
  <a href="/privacidade">Política de Privacidade</a>
  <a href="/termos">Termos de Uso</a>
  <a href="/reembolso">Política de Reembolso</a>
  <a href="{whatsapp}" rel="noopener">WhatsApp</a>
</footer>
</body>
</html>"""


def _page(title, brand, top, body):
    return (
        AUTH_LAYOUT.format(
            title=html.escape(title),
            brand=html.escape(brand),
            top=top,
            body=body,
            whatsapp=SERVICE_WHATSAPP_LINK,
        ),
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )


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
        "<a href='" + PORTFOLIO_URL + "' style='padding:6px 12px;background:rgba(96,165,250,.12);"
        "border-radius:6px;text-decoration:none;color:#60a5fa;font-size:13px'>Voltar ao site</a> "
        "<a href='https://wa.me/5519991813598' style='margin-left:8px' rel='noopener'>WhatsApp</a>"
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
    top = (
        "<a href='" + PORTFOLIO_URL + "' style='padding:6px 12px;background:rgba(96,165,250,.12);"
        "border-radius:6px;text-decoration:none;color:#60a5fa;font-size:13px'>Voltar ao site</a>"
    )
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
    top = (
        "<a href='" + PORTFOLIO_URL + "' style='padding:6px 12px;background:rgba(96,165,250,.12);"
        "border-radius:6px;text-decoration:none;color:#60a5fa;font-size:13px'>Voltar ao site</a>"
    )
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
        "<a href='" + PORTFOLIO_URL + "' style='padding:6px 12px;background:rgba(96,165,250,.12);"
        "border-radius:6px;text-decoration:none;color:#60a5fa;font-size:13px'>Voltar ao site</a> "
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


@app.route("/cliente")
def cliente():
    user = current_user()
    if not user:
        return redirect("/login")
    mine = [
        o
        for o in STORE.list()
        if (o.get("email") or "").strip().lower() == user["email"]
    ]
    rows = _orders_rows(mine)
    top = (
        "<a href='/cliente/perfil' style='padding:6px 12px;background:rgba(52,211,153,.12);border-radius:6px;text-decoration:none;color:#34d399;font-size:13px'>Meu perfil</a> "
        "<a href='/cliente/suporte' style='padding:6px 12px;background:rgba(96,165,250,.12);border-radius:6px;text-decoration:none;color:#60a5fa;font-size:13px'>Suporte</a> "
        f"<span style='color:#94a3b8;font-size:12px;margin-left:12px'>{html.escape(user['name'])}</span> "
        "<a href='/acesso' style='margin-left:8px'>Trocar área</a> "
        "<a href='/logout' style='margin-left:8px'>Sair</a>"
    )
    body = (
        "<div class='cards'>"
        "<div class='card'><div class='num'>{n}</div><div class='lbl'>Meus pedidos</div></div>"
        "</div>"
    ).format(n=len(mine))
    note = (
        "Os pedidos aparecem aqui quando o pagamento foi solicitado com o "
        "<b>mesmo e-mail</b> da sua conta Google. Se faltar algum pedido, finalize "
        "a compra no Telegram usando esse e-mail no Pix."
    )
    body += f"<section><h2>Meus pedidos</h2>{rows}</section><p class='note'>{note}</p>"
    return _page("Minha conta", "Minha conta", top, body)


@app.route("/cliente/perfil", methods=["GET", "POST"])
def cliente_perfil():
    user = current_user()
    if not user:
        return redirect("/login")
    email = user["email"].lower()
    profiles = []
    if STORE.remote:
        try:
            response = requests.get(
                f"{STORE.url}/rest/v1/profiles?email=eq.{email}&select=*",
                headers=STORE._headers(),
                timeout=15,
            )
            if response.status_code == 200:
                profiles = response.json()
        except Exception:
            profiles = []
    profile = profiles[0] if profiles else {}

    if request.method == "POST":
        if not _csrf_ok():
            return "Requisição inválida (CSRF).", 403
        payload = {
            "email": email,
            "name": user["name"],
            "sub": user.get("sub") or "",
            "role": user.get("role") or "cliente",
            "personagem": (request.form.get("personagem") or "").strip()[:100],
            "mundo": (request.form.get("mundo") or "").strip()[:100],
        }
        if STORE.remote:
            try:
                requests.post(
                    f"{STORE.url}/rest/v1/profiles?on_conflict=email",
                    headers={**STORE._headers(), "Prefer": "resolution=merge-duplicates"},
                    json=payload,
                    timeout=15,
                )
            except Exception:
                pass
        return redirect("/cliente/perfil")

    top = (
        f"<span style='color:#94a3b8;font-size:12px'>{html.escape(user['name'])}</span> "
        f"<a href='/logout'>Sair</a>"
    )
    body = (
        "<section><h2>Meu perfil</h2>"
        "<p style='color:#8ea0b8;font-size:13px'>"
        "Informe seu personagem e mundo para agilizar seus próximos pedidos.</p>"
        "<form method='post'>"
        f"<label>E-mail</label><input value='{html.escape(email)}' disabled>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        f"<label>Personagem</label><input name='personagem' value='{html.escape(str(profile.get('personagem') or ''))}' "
        "placeholder='Nome do personagem'>"
        f"<label>Mundo</label><input name='mundo' value='{html.escape(str(profile.get('mundo') or ''))}' "
        "placeholder='Ex.: antica'>"
        "<p style='margin-top:14px'><button class='btn' type='submit'>Salvar perfil</button></p>"
        "</form>"
        "<p class='legal-note'>Ao salvar seu perfil, seus dados (personagem e mundo) são usados "
        "apenas para agilizar seus pedidos. Consulte nossa "
        "<a href='/privacidade' style='color:#60a5fa'>Política de Privacidade</a> (LGPD) para saber mais.</p>"
        "</section>"
    )
    return _page("Meu perfil", "Meu perfil", top, body)


@app.route("/cliente/suporte", methods=["GET", "POST"])
def cliente_suporte():
    user = current_user()
    if not user:
        return redirect("/login")
    top = (
        f"<span style='color:#94a3b8;font-size:12px'>{html.escape(user['name'])}</span> "
        f"<a href='/logout'>Sair</a>"
    )
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

    tickets = []
    if STORE.remote:
        try:
            response = requests.get(
                f"{STORE.url}/rest/v1/tickets?email=eq.{email}&order=criado_em.desc&select=*",
                headers=STORE._headers(),
                timeout=15,
            )
            if response.status_code == 200:
                tickets = response.json()
        except Exception:
            tickets = []
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(t.get('id') or '-'))}</td>"
        f"<td>{html.escape(str(t.get('criado_em') or ''))[:16]}</td>"
        f"<td>{html.escape(str(t.get('assunto') or '-'))}</td>"
        f"<td><span class='status {html.escape(t.get('status') or 'aberto')}'>{html.escape(t.get('status') or 'aberto')}</span></td>"
        f"<td><a class='btn ghost' style='padding:4px 10px;font-size:12px' href='/cliente/suporte/{t.get('id')}'>Ver</a></td>"
        "</tr>"
        for t in tickets
    ) or "<tr><td colspan='5' style='color:#64748b;text-align:center'>Nenhum chamado aberto.</td></tr>"
    body = (
        "<section><h2>Abrir chamado</h2>"
        "<form method='post'>"
        f"<input type='hidden' name='_csrf' value='{html.escape(_csrf_token())}'>"
        "<label>Assunto</label><input name='assunto' required placeholder='Resumo curto'>"
        "<label>Mensagem</label><textarea name='mensagem' rows='4' required></textarea>"
        "<p style='margin-top:14px'><button class='btn' type='submit'>Enviar chamado</button></p>"
        "</form>"
        "<p class='legal-note'>As mensagens enviadas aqui são tratadas em sigilo para atender seu "
        "chamado. Consulte nossa <a href='/privacidade' style='color:#60a5fa'>Política de "
        "Privacidade</a> (LGPD).</p>"
        "</section>"
        "<section><h2>Meus chamados</h2><table>"
        "<tr><th>Id</th><th>Data</th><th>Assunto</th><th>Status</th><th></th></tr>"
        + rows
        + "</table></section>"
    )
    return _page("Suporte", "Suporte", top, body)


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
    top = (
        f"<span style='color:#94a3b8;font-size:12px'>{html.escape(user['name'])}</span> "
        f"<a href='/logout'>Sair</a>"
    )
    resposta = ""
    if ticket.get("resposta"):
        resposta = (
            "<p style='background:#0f2a22;border:1px solid #14532d;color:#4ade80;"
            "border-radius:9px;padding:10px 14px'><b>Resposta:</b> "
            f"{html.escape(str(ticket.get('resposta') or ''))}</p>"
        )
    body = (
        "<section><h2>Chamado #{id} · {status}</h2>"
        "<p style='color:#8ea0b8;font-size:13px'>Abertura: {criado}</p>"
        "<p><b>{assunto}</b></p>"
        "<p style='color:#e2e8f0'>{mensagem}</p>"
        "{resposta}"
        "</section>"
        "<p><a class='btn ghost' href='/cliente/suporte'>Voltar aos chamados</a></p>"
    ).format(
        id=ticket.get("id"),
        status=html.escape(ticket.get("status") or "aberto"),
        criado=html.escape(str(ticket.get("criado_em") or ""))[:19],
        assunto=html.escape(str(ticket.get("assunto") or "-")),
        mensagem=html.escape(str(ticket.get("mensagem") or "-")),
        resposta=resposta,
    )
    return _page("Chamado", "Suporte", top, body)


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
        set_webhook(sys.argv[2] if len(sys.argv) > 2 else f"http://localhost:{port}/webhook")
    else:
        import threading

        threading.Thread(target=_relatorio_automatico, daemon=True).start()
        app.run(host="0.0.0.0", port=port)