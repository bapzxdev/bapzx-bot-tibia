# Testes do módulo MARKTRADE (marketplace) — v2.10.1.
# Painel /admin/marketplace + integração no bot (client, webhook, confirm).
# Padrão: test client do painel com mocks, igual ao test_coins.py.
# Rodar: .venv\Scripts\python.exe test_marketplace.py

import unittest
import time
from unittest import mock

import bot
import painel
import rbac
import storage

CFG = {
    "id": 1,
    "preco_publicacao": 2.99,
    "preco_destaque": 5.00,
    "preco_vip": 12.99,
    "limite_publicacoes": 3,
    "duracao_publicacao_dias": 30,
    "duracao_destaque_dias": 30,
    "duracao_vip_dias": 30,
    "status": "ativo",
    "atualizado_em": "2026-09-23T12:00:00+00:00",
    "atualizado_por": "admin@bapzx.com",
}

LISTING = {
    "id": 1,
    "user_id": "cliente@x.com",
    "item_name": "War Hammer",
    "description": "topo",
    "character_name": "Bapz",
    "world": "Auroria",
    "contact": "@bapzx",
    "category": "",
    "tipo_anuncio": "venda",
    "status": "pendente",
    "is_destaque": False,
    "preco": 250000.0,
    "aceita_ofertas": True,
    "sprite": "",
    "tipo_pvp": "Open PvP",
    "verificado": False,
    "created_at": "2026-09-23T10:00:00+00:00",
}

PAG = {
    "id": 10,
    "external_reference": "PUB-1",
    "tipo": "publicacao",
    "listing_id": 1,
    "user_id": "cliente@x.com",
    "valor": 2.99,
    "status": "pendente",
    "mp_id": "",
    "created_at": "2026-09-23T10:00:00+00:00",
}


def _fake_fetch(table, **kw):
    query = kw.get("query") or ""
    if table == "marketplace_config":
        return [dict(CFG)]
    if table == "marketplace_listings":
        if "id=eq." in query and "cliente" in query:
            return []
        return [dict(LISTING)]
    if table == "marketplace_pagamentos":
        return [dict(PAG)]
    if table == "profiles":
        return [{"email": "cliente@x.com", "vip_until": None}]
    return []


def _login(client, cargo="ADMINISTRADOR", email="admin@bapzx.com", perms=None):
    with client.session_transaction() as s:
        s["email"] = email
        s["cargo"] = cargo
        s["perms"] = perms if perms is not None else (["ALL"] if cargo == "ADMINISTRADOR" else [])
        s["_csrf"] = "tokenteste"


class _FakeResp:
    status_code = 200
    text = ""
    headers = {}

    def json(self):
        return []

    def raise_for_status(self):
        if self.status_code and self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class TestMkPainel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bot.app.config["TESTING"] = True
        bot.app.secret_key = "teste-marketplace"

    def setUp(self):
        patchers = [
            mock.patch.object(painel, "_sessao_ativa", lambda sid: True),
            mock.patch.object(painel, "_notificacoes", lambda _user: ([], [], 0)),
            mock.patch.object(painel, "ADMIN_IP_ALLOWLIST", ""),
        ]
        for p in patchers:
            p.start()
            self.addCleanup(p.stop)

    # ---------- helpers ----------

    def test_mk_tipo_lbl(self):
        self.assertEqual(painel._mk_tipo_lbl("venda"), "venda")
        self.assertEqual(painel._mk_tipo_lbl("compra", low=False), "Compra")
        self.assertEqual(painel._mk_tipo_lbl("troca", low=False), "Troca")
        self.assertEqual(painel._mk_tipo_lbl("x", low=False), "Venda")

    def test_mk_status_badge_listing(self):
        self.assertIn("pago", painel._mk_status_badge("ativa"))
        self.assertIn("pendente", painel._mk_status_badge("pendente"))
        self.assertIn("cancelado", painel._mk_status_badge("bloqueada"))
        self.assertIn("Aguardando pagamento", painel._mk_status_badge("pendente"))
        self.assertIn("Encerrada", painel._mk_status_badge("encerrada"))

    def test_mk_status_badge_payment(self):
        self.assertIn("pago", painel._mk_status_badge("confirmado", "payment"))
        self.assertIn("Confirmado", painel._mk_status_badge("confirmado", "payment"))
        self.assertIn("Aguardando", painel._mk_status_badge("pendente", "payment"))

    def test_mk_gp_admin(self):
        self.assertEqual(painel._mk_gp_admin(250000), "250.000")
        self.assertEqual(painel._mk_gp_admin(250000.5), "250.000,50")
        self.assertEqual(painel._mk_gp_admin(None), "Aceita ofertas")
        self.assertEqual(painel._mk_gp_admin(""), "Aceita ofertas")

    def test_mk_linha_limite_preco(self):
        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch):
            self.assertEqual(painel._mk_linha()["id"], 1)
            self.assertEqual(painel._mk_limite(), 3)
            self.assertEqual(painel._mk_preco("preco_publicacao", 2.99), 2.99)

    # ---------- GET /admin/marketplace ----------

    def test_get_sem_login_redireciona(self):
        c = bot.app.test_client()
        resp = c.get("/admin/marketplace")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_get_sem_perm_redireciona(self):
        c = bot.app.test_client()
        _login(c, "CLIENTE", "cliente@x.com")
        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch):
            resp = c.get("/admin/marketplace")
        self.assertEqual(resp.status_code, 302)

    def test_get_admin_renderiza(self):
        c = bot.app.test_client()
        _login(c)
        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch):
            resp = c.get("/admin/marketplace")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("MARKTRADE", html)
        self.assertIn("Anúncios ativos", html)
        self.assertIn("Publicação", html)
        self.assertIn("Editar configurações", html)
        self.assertIn("Anúncios", html)
        self.assertIn("War Hammer", html)
        self.assertIn("Pagamentos (PIX)", html)
        self.assertIn("Testar status VIP", html)
        self.assertIn("250.000", html)

    def test_get_sem_tabela_avisa_migration(self):
        c = bot.app.test_client()
        _login(c)

        def sem_tabela(table, **kw):
            return []

        with mock.patch.object(painel, "_fetch_soft", side_effect=sem_tabela):
            resp = c.get("/admin/marketplace")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("supabase_migracao_v124.sql", html)
        self.assertIn("C:\\DEV\\Supabase", html)
        self.assertIn("Anúncios ativos", html)

    def test_get_moderador_sem_gerenciar_oculta_form(self):
        c = bot.app.test_client()
        _login(c, "MODERADOR", "moderador@x.com", perms=["ver_marketplace"])
        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch):
            resp = c.get("/admin/marketplace")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Anúncios", html)
        self.assertNotIn("Editar configurações", html)
        self.assertNotIn("Testar status VIP", html)

    # ---------- POST /admin/marketplace/salvar ----------

    def test_post_salvar_envia_config_e_audit(self):
        c = bot.app.test_client()
        _login(c)
        calls = []

        def fakepost(url, **kw):
            calls.append((url, kw))
            return _FakeResp()

        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch), \
             mock.patch.object(painel.requests, "post", side_effect=fakepost):
            resp = c.post(
                "/admin/marketplace/salvar",
                data={
                    "_csrf": "tokenteste",
                    "preco_publicacao": "3,49",
                    "preco_destaque": "6",
                    "preco_vip": "14,99",
                    "limite_publicacoes": "5",
                    "duracao_publicacao_dias": "45",
                    "duracao_vip_dias": "30",
                    "status": "pausado",
                    "observacao": "black friday",
                },
            )
        self.assertEqual(resp.status_code, 302)
        conf = [x for x in calls if "/rest/v1/marketplace_config" in x[0]]
        aud = [x for x in calls if "/rest/v1/audit_log" in x[0]]
        self.assertTrue(conf, "config upsert nao enviado")
        payload = conf[0][1]["json"]
        self.assertEqual(payload["id"], 1)
        self.assertEqual(payload["preco_publicacao"], 3.49)
        self.assertEqual(payload["limite_publicacoes"], 5)
        self.assertEqual(payload["status"], "pausado")
        self.assertEqual(payload["duracao_publicacao_dias"], 45)
        self.assertTrue(aud, "auditoria nao registrada")
        self.assertEqual(aud[0][1]["json"]["acao"], "marketplace_config")

    def test_post_salvar_csrf_invalido_403(self):
        c = bot.app.test_client()
        _login(c)
        resp = c.post(
            "/admin/marketplace/salvar",
            data={
                "_csrf": "errado",
                "preco_publicacao": "3",
                "preco_destaque": "5",
                "preco_vip": "12",
                "limite_publicacoes": "3",
                "status": "ativo",
            },
        )
        self.assertEqual(resp.status_code, 403)

    def test_post_salvar_sem_perm_403(self):
        c = bot.app.test_client()
        _login(c, "MODERADOR", "moderador@x.com", perms=["ver_marketplace"])
        resp = c.post(
            "/admin/marketplace/salvar",
            data={
                "_csrf": "tokenteste",
                "preco_publicacao": "3",
                "preco_destaque": "5",
                "preco_vip": "12",
                "limite_publicacoes": "3",
                "status": "ativo",
            },
        )
        self.assertEqual(resp.status_code, 403)

    # ---------- POST /admin/marketplace/<lid>/acao ----------

    def test_post_acao_ativar(self):
        c = bot.app.test_client()
        _login(c)
        calls = []

        def fakepatch(url, **kw):
            calls.append((url, kw))
            return _FakeResp()

        def fakepost(url, **kw):
            calls.append((url, kw))
            return _FakeResp()

        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch), \
             mock.patch.object(painel.requests, "patch", side_effect=fakepatch), \
             mock.patch.object(painel.requests, "post", side_effect=fakepost):
            resp = c.post("/admin/marketplace/1/acao", data={"_csrf": "tokenteste", "acao": "ativar"})
        self.assertEqual(resp.status_code, 302)
        pl = [x for x in calls if "/rest/v1/marketplace_listings" in x[0] and "PATCH" == x[0].split("?")[0][-1] or "/rest/v1/marketplace_listings" in x[0]]
        self.assertTrue(pl, "patch nao enviado")
        payload = pl[-1][1]["json"]
        self.assertEqual(payload["status"], "ativa")
        aud = [x for x in calls if "/rest/v1/audit_log" in x[0]]
        self.assertTrue(aud)
        self.assertEqual(aud[0][1]["json"]["acao"], "marketplace_acao")

    def test_post_acao_verificar_inverte(self):
        c = bot.app.test_client()
        _login(c)
        calls = []

        def fakepatch(url, **kw):
            calls.append((url, kw))
            return _FakeResp()

        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch), \
             mock.patch.object(painel.requests, "patch", side_effect=fakepatch), \
             mock.patch.object(painel.requests, "post", side_effect=lambda url, **kw: _FakeResp()):
            resp = c.post("/admin/marketplace/1/acao", data={"_csrf": "tokenteste", "acao": "verificar"})
        self.assertEqual(resp.status_code, 302)
        pl = [x for x in calls if "/rest/v1/marketplace_listings" in x[0]]
        self.assertTrue(pl)
        self.assertTrue(pl[-1][1]["json"]["verificado"])

    def test_post_acao_invalida_400(self):
        c = bot.app.test_client()
        _login(c)
        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch):
            resp = c.post("/admin/marketplace/1/acao", data={"_csrf": "tokenteste", "acao": "explodir"})
        self.assertEqual(resp.status_code, 400)

    # ---------- POST /admin/marketplace/vip/testar ----------

    def test_post_vip_ativar(self):
        c = bot.app.test_client()
        _login(c)
        calls = []

        def fakepatch(url, **kw):
            calls.append((url, kw))
            return _FakeResp()

        with mock.patch.object(painel.requests, "patch", side_effect=fakepatch), \
             mock.patch.object(painel.requests, "post", side_effect=lambda url, **kw: _FakeResp()):
            resp = c.post(
                "/admin/marketplace/vip/testar",
                data={"_csrf": "tokenteste", "email": "cliente@x.com", "dias": "60", "acao": "ativar"},
            )
        self.assertEqual(resp.status_code, 302)
        pp = [x for x in calls if "/rest/v1/profiles" in x[0]]
        self.assertTrue(pp)
        self.assertIsNotNone(pp[-1][1]["json"]["vip_until"])

    def test_post_vip_remover(self):
        c = bot.app.test_client()
        _login(c)
        calls = []

        def fakepatch(url, **kw):
            calls.append((url, kw))
            return _FakeResp()

        with mock.patch.object(painel.requests, "patch", side_effect=fakepatch), \
             mock.patch.object(painel.requests, "post", side_effect=lambda url, **kw: _FakeResp()):
            resp = c.post(
                "/admin/marketplace/vip/testar",
                data={"_csrf": "tokenteste", "email": "cliente@x.com", "acao": "remover"},
            )
        self.assertEqual(resp.status_code, 302)
        pp = [x for x in calls if "/rest/v1/profiles" in x[0]]
        self.assertTrue(pp)
        self.assertIsNone(pp[-1][1]["json"]["vip_until"])


class TestMkBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bot.app.config["TESTING"] = True
        bot.app.config["PROPAGATE_EXCEPTIONS"] = True
        bot.app.secret_key = "teste-marketplace"

    def setUp(self):
        bot._MK_CACHE["ts"] = 0.0
        bot._MK_CACHE["dados"] = None
        bot._MK_VIP_CACHE.clear()
        bot._SPRITE_CACHE.clear()

    # ---------- helpers ----------

    def test_mk_mundos(self):
        self.assertEqual(len(bot._MK_MUNDOS), 16)
        for m in ("Auroria", "Belaria", "Infernum I", "Infernum II", "Infernum III", "Vesperia"):
            self.assertIn(m, bot._MK_MUNDOS)

    def test_mk_itemsprite_sucesso(self):
        resp1 = _FakeResp()
        resp1.json = lambda: {
            "query": {
                "pages": {
                    "1": {
                        "images": [
                            {"title": "Arquivo:War_Hammer_ingred.gif"},
                            {"title": "Arquivo:War Hammer.gif"},
                        ]
                    }
                }
            }
        }
        resp2 = _FakeResp()
        resp2.json = lambda: {
            "query": {
                "pages": {
                    "1": {
                        "imageinfo": [
                            {"thumburl": "https://www.tibiawiki.com.br/images/thumb/2/25/War_Hammer.gif"}
                        ]
                    }
                }
            }
        }
        calls = []

        def fakeget(url, **kw):
            calls.append(url)
            return resp1 if "prop=images" in url else resp2

        with mock.patch.object(bot.requests, "get", side_effect=fakeget):
            url = bot._mk_itemsprite("War Hammer")
        self.assertEqual(url, "https://www.tibiawiki.com.br/images/thumb/2/25/War_Hammer.gif")
        self.assertEqual(len(calls), 2)

    def test_mk_itemsprite_cache(self):
        resp1 = _FakeResp()
        resp1.json = lambda: {"query": {"pages": {"1": {"images": [{"title": "Arquivo:Pocao.gif"}]}}}}
        resp2 = _FakeResp()
        resp2.json = lambda: {
            "query": {"pages": {"1": {"imageinfo": [{"thumburl": "https://www.tibiawiki.com.br/t/Pocao.gif"}]}}}
        }

        def fakeget(url, **kw):
            return resp1 if "prop=images" in url else resp2

        with mock.patch.object(bot.requests, "get", side_effect=fakeget):
            url = bot._mk_itemsprite("Poção")
        with mock.patch.object(bot.requests, "get", side_effect=AssertionError("nao deve chamar rede")):
            self.assertEqual(bot._mk_itemsprite("Poção"), url)

    def test_mk_itemsprite_falha_e_vazio(self):
        with mock.patch.object(bot.requests, "get", side_effect=Exception("boom")):
            self.assertEqual(bot._mk_itemsprite("Algum Item"), "")
        self.assertEqual(bot._mk_itemsprite(""), "")
        self.assertEqual(bot._mk_itemsprite("  "), "")

    # ---------- helpers ----------

    def test_mk_gp(self):
        self.assertEqual(bot._mk_gp(None), "Aceita ofertas")
        self.assertEqual(bot._mk_gp(""), "Aceita ofertas")
        self.assertEqual(bot._mk_gp(250000), "250.000")
        self.assertEqual(bot._mk_gp(120000), "120.000")
        self.assertEqual(bot._mk_gp(250000.5), "250.000,50")
        self.assertEqual(bot._mk_gp("250000"), "250.000")

    def test_mk_limite_preco_ativo_defaults(self):
        with mock.patch.object(bot, "_marketplace_config", return_value=None):
            self.assertEqual(bot._mk_limite(), 3)
            self.assertEqual(bot._mk_preco("preco_publicacao", 2.99), 2.99)
            self.assertEqual(bot._mk_duracao("duracao_publicacao_dias", 30), 30)
            self.assertTrue(bot._mk_ativo())

    def test_mk_ativos_com_config(self):
        cfg = {"limite_publicacoes": 5, "preco_publicacao": 3.5, "status": "pausado"}
        with mock.patch.object(bot, "_marketplace_config", return_value=cfg):
            self.assertEqual(bot._mk_limite(), 5)
            self.assertEqual(bot._mk_preco("preco_publicacao", 2.99), 3.5)
            self.assertFalse(bot._mk_ativo())

    def test_mk_listing_status_lbl(self):
        self.assertEqual(bot._mk_listing_status_lbl("ativa"), "Ativa")
        self.assertEqual(bot._mk_listing_status_lbl("pendente"), "Aguardando pagamento")
        self.assertEqual(bot._mk_listing_status_lbl("bloqueada"), "Bloqueada")

    def test_mk_parse_dt(self):
        import datetime as dt_mod
        parsed = bot._mk_parse_dt("2026-09-23T12:00:00Z")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed, dt_mod.datetime(2026, 9, 23, 12, 0, 0))
        self.assertIsNone(bot._mk_parse_dt(""))
        self.assertIsNone(bot._mk_parse_dt("data invalida"))

    def test_mk_fmt_dt(self):
        self.assertIn("2026", bot._mk_fmt_dt("2026-09-23T12:00:00Z"))
        self.assertEqual(bot._mk_fmt_dt(""), "-")

    # ---------- _marketplace_confirm ----------

    def test_confirm_publicacao_ativa_listing(self):
        calls = []

        def fakepatch(url, **kw):
            calls.append((url, kw))
            return _FakeResp()

        pag = dict(PAG)
        with mock.patch.object(bot, "_mk_find_pagamento", return_value=pag), \
             mock.patch.object(bot, "_mk_listing", return_value=dict(LISTING)), \
             mock.patch.object(bot, "_mk_duracao", return_value=30), \
             mock.patch.object(bot.requests, "patch", side_effect=fakepatch), \
             mock.patch.object(bot, "_marketplace_config", return_value=None):
            ok = bot._marketplace_confirm("PUB-1", "mp999")
        self.assertTrue(ok)
        pag_patch = [x for x in calls if "/rest/v1/marketplace_pagamentos" in x[0]]
        listing_patch = [x for x in calls if "/rest/v1/marketplace_listings" in x[0]]
        self.assertTrue(pag_patch)
        self.assertEqual(pag_patch[0][1]["json"]["status"], "confirmado")
        self.assertTrue(listing_patch)
        self.assertEqual(listing_patch[0][1]["json"]["status"], "ativa")
        self.assertIn("expires_at", listing_patch[0][1]["json"])

    def test_confirm_destaque_em_listing_ativa(self):
        calls = []

        def fakepatch(url, **kw):
            calls.append((url, kw))
            return _FakeResp()

        pag = dict(PAG)
        pag["tipo"] = "destaque"
        pag["external_reference"] = "DES-1"
        ativa = dict(LISTING)
        ativa["status"] = "ativa"
        with mock.patch.object(bot, "_mk_find_pagamento", return_value=pag), \
             mock.patch.object(bot, "_mk_listing", return_value=ativa), \
             mock.patch.object(bot, "_mk_duracao", return_value=30), \
             mock.patch.object(bot.requests, "patch", side_effect=fakepatch), \
             mock.patch.object(bot, "_marketplace_config", return_value=None):
            ok = bot._marketplace_confirm("DES-1", "mp888")
        self.assertTrue(ok)
        listing_patch = [x for x in calls if "/rest/v1/marketplace_listings" in x[0]]
        self.assertTrue(listing_patch)
        lp = listing_patch[-1][1]["json"]
        self.assertNotIn("status", lp, "anúncio já ativo não deve mudar status")
        self.assertTrue(lp["is_destaque"])
        self.assertIn("destaque_until", lp)

    def test_confirm_vip_atualiza_profile(self):
        calls = []

        def fakepatch(url, **kw):
            calls.append((url, kw))
            return _FakeResp()

        pag = {
            "id": 20,
            "external_reference": "VIP-cliente@x.com",
            "tipo": "vip",
            "listing_id": None,
            "user_id": "cliente@x.com",
            "valor": 12.99,
            "status": "pendente",
        }
        with mock.patch.object(bot, "_mk_find_pagamento", return_value=pag), \
             mock.patch.object(bot, "_mk_duracao", return_value=30), \
             mock.patch.object(bot.requests, "patch", side_effect=fakepatch), \
             mock.patch.object(bot, "_marketplace_config", return_value=None):
            ok = bot._marketplace_confirm("VIP-cliente@x.com", "mp777")
        self.assertTrue(ok)
        prof = [x for x in calls if "/rest/v1/profiles" in x[0]]
        self.assertTrue(prof)
        self.assertIn("vip_until", prof[0][1]["json"])
        self.assertNotIn("cliente@x.com", bot._MK_VIP_CACHE)

    def test_confirm_nao_encontrado(self):
        with mock.patch.object(bot, "_mk_find_pagamento", return_value=None):
            self.assertFalse(bot._marketplace_confirm("PUB-999", "mp1"))

    # ---------- webhook ----------

    def test_webhook_prefixo_marketplace_confirma(self):
        _login_object = {}
        import bot as _bot

        old_token = _bot.MP_ACCESS_TOKEN
        confirmed = []

        def fake_payment_get(url, **kw):
            if "api.mercadopago.com" in url:
                class P:
                    status_code = 200

                    def json(self):
                        return {"id": "555", "external_reference": "VIP-cliente@x.com", "status": "approved"}
                return P()
            return _FakeResp()

        def fake_confirm(ref, mp_id):
            confirmed.append((ref, mp_id))

        try:
            _bot.MP_ACCESS_TOKEN = "tokenteste"
            with mock.patch.object(_bot, "_mp_rate_limited", lambda: False), \
                 mock.patch.object(_bot.requests, "get", side_effect=fake_payment_get), \
                 mock.patch.object(_bot, "_marketplace_confirm", side_effect=fake_confirm):
                c = bot.app.test_client()
                resp = c.post("/webhook/mp", json={"data": {"id": "555"}})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(confirmed, [("VIP-cliente@x.com", "555")])
        finally:
            _bot.MP_ACCESS_TOKEN = old_token

    # ---------- GET /cliente/troca ----------

    def test_cliente_troca_renderiza(self):
        use = {
            "get": None,
        }

        def fake_getuser():
            return {"email": "cliente@x.com", "name": "Cliente Teste"}

        with mock.patch.object(bot, "current_user", fake_getuser), \
             mock.patch.object(bot, "_cliente_header", lambda user, x: "top-mock"), \
             mock.patch.object(bot, "_mk_vip_ativo", lambda email: False), \
             mock.patch.object(bot, "_mk_ativo", lambda: True), \
             mock.patch.object(bot, "_mk_profile", lambda email: {}), \
             mock.patch.object(bot, "_marketplace_config", lambda: None), \
             mock.patch.object(bot, "_mk_minhas_listings", lambda email: []), \
             mock.patch.object(bot, "_mk_meus_pagamentos", lambda email: []):
            c = bot.app.test_client()
            resp = c.get("/cliente/troca")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Publicar anúncio", html)
        self.assertIn("VIP BAPZX", html)
        self.assertIn("Você ainda não publicou nada", html)
        self.assertIn("MARKTRADE", html)
        self.assertIn("<select name='world'", html)
        self.assertIn(">Auroria<", html)
        self.assertIn(">Infernum I<", html)
        self.assertIn("Wiki Tibia", html)
        self.assertNotIn("tipo_pvp", html)

    # ---------- POST /cliente/troca/publicar ----------

    def test_publicar_mundo_invalido_rejeita(self):
        c = bot.app.test_client()
        with mock.patch.object(bot, "current_user", lambda: {"email": "cliente@x.com"}), \
             mock.patch.object(bot, "_csrf_ok", lambda: True), \
             mock.patch.object(bot, "_mk_ativo", lambda: True), \
             mock.patch.object(bot, "_mk_minhas_listings", side_effect=AssertionError("nao deve consultar")):
            resp = c.post(
                "/cliente/troca/publicar",
                data={
                    "_csrf": "tokenteste",
                    "item_name": "War Hammer",
                    "character_name": "Bapz",
                    "world": "honbra",
                },
            )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/cliente/troca", resp.headers.get("Location", ""))

    def test_publicar_mundo_ok_nao_valida_mundo(self):
        c = bot.app.test_client()
        bot._SPRITE_CACHE.clear()
        posts = []

        def fakeget(url, **kw):
            raise Exception("nao deve alcançar a rede")

        def fakepost(url, **kw):
            posts.append(kw.get("json") or {})
            return _FakeResp()

        with mock.patch.object(bot, "current_user", lambda: {"email": "cliente@x.com"}), \
             mock.patch.object(bot, "_csrf_ok", lambda: True), \
             mock.patch.object(bot, "_mk_ativo", lambda: True), \
             mock.patch.object(bot, "_mk_minhas_listings", lambda email: []), \
             mock.patch.object(bot, "_mk_limite", lambda: 5), \
             mock.patch.object(bot, "_mk_duracao", lambda chave, default: 30), \
             mock.patch.object(bot, "_mk_vip_ativo", lambda email: False), \
             mock.patch.object(bot.requests, "get", side_effect=fakeget), \
             mock.patch.object(bot.requests, "post", side_effect=fakepost):
            resp = c.post("/cliente/troca/publicar", data={
                "_csrf": "tokenteste",
                "item_name": "War Hammer",
                "character_name": "Bapz",
                "world": "Auroria",
            })
        self.assertEqual(resp.status_code, 500)
        self.assertTrue(posts, "deve chegar ao Supabase")
        pl = posts[0]
        self.assertEqual(pl["world"], "Auroria")
        self.assertEqual(pl["item_name"], "War Hammer")
        self.assertNotIn("tipo_pvp", pl)

    def test_publicar_sprite_vazio_busca_auto(self):
        c = bot.app.test_client()
        bot._SPRITE_CACHE.clear()
        calls = []
        posts = []
        resp1 = _FakeResp()
        resp1.json = lambda: {"query": {"pages": {"1": {"images": [{"title": "Arquivo:War Hammer.gif"}]}}}}
        resp2 = _FakeResp()
        resp2.json = lambda: {
            "query": {"pages": {"1": {"imageinfo": [{"thumburl": "https://www.tibiawiki.com.br/t/War_Hammer.gif"}]}}}
        }

        def fakeget(url, **kw):
            calls.append(url)
            return resp1 if "prop=images" in url else resp2

        def fakepost(url, **kw):
            posts.append(kw.get("json") or {})
            return _FakeResp()

        with mock.patch.object(bot, "current_user", lambda: {"email": "cliente@x.com"}), \
             mock.patch.object(bot, "_csrf_ok", lambda: True), \
             mock.patch.object(bot, "_mk_ativo", lambda: True), \
             mock.patch.object(bot, "_mk_minhas_listings", lambda email: []), \
             mock.patch.object(bot, "_mk_limite", lambda: 5), \
             mock.patch.object(bot, "_mk_vip_ativo", lambda email: False), \
             mock.patch.object(bot, "_mk_duracao", lambda chave, default: 30), \
             mock.patch.object(bot.requests, "get", side_effect=fakeget), \
             mock.patch.object(bot.requests, "post", side_effect=fakepost):
            resp = c.post("/cliente/troca/publicar", data={
                "_csrf": "tokenteste",
                "item_name": "War Hammer",
                "character_name": "Bapz",
                "world": "Auroria",
            })
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(len(calls), 2)
        self.assertTrue(posts)
        self.assertEqual(posts[0]["sprite"], "https://www.tibiawiki.com.br/t/War_Hammer.gif")


if __name__ == "__main__":
    unittest.main(verbosity=2)