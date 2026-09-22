# Testes do módulo COINS (v2.8.0): painel /admin/coins + integração no bot.
# Padrão usado nas versões anteriores: test client do painel com mocks.
# Rodar: python test_coins.py

import unittest
from unittest import mock

import bot
import painel
import rbac
import storage

CONFIG = {
    "estoque": 150000.0,
    "preco_mil": 90.0,
    "min_compra": 100.0,
    "max_compra": 50000.0,
    "status": "ativo",
    "observacao": "",
    "atualizado_em": "2026-09-22T12:00:00+00:00",
    "atualizado_por": "admin@bapzx.com",
}

HIST = [
    {
        "criado_em": "2026-09-22T11:00:00+00:00",
        "admin": "admin@bapzx.com",
        "qtd_anterior": 100000.0,
        "qtd_nova": 150000.0,
        "preco_anterior": 90.0,
        "preco_novo": 90.0,
        "alteracao": "estoque 100.000 → 150.000 (por admin@bapzx.com)",
    }
]


def _fake_fetch(table, **kw):
    if table == "coins_config":
        return [dict(CONFIG)]
    if table == "coins_historico":
        return [dict(h) for h in HIST]
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


class TestCoinsPainel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bot.app.config["TESTING"] = True
        bot.app.secret_key = "teste-coins"

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

    def test_coins_num_aceita_formatos_br(self):
        self.assertEqual(painel._coins_num("90"), 90.0)
        self.assertEqual(painel._coins_num("89,50"), 89.5)
        self.assertEqual(painel._coins_num("2.500,50"), 2500.5)
        self.assertEqual(painel._coins_num("2500.5"), 2500.5)
        self.assertEqual(painel._coins_num(""), 0.0)
        self.assertEqual(painel._coins_num(None), 0.0)

    def test_coins_int_formata_milhar(self):
        self.assertEqual(painel._coins_int(1000), "1.000")
        self.assertEqual(painel._coins_int(150000), "150.000")
        self.assertEqual(painel._coins_int(50), "50")

    def test_coins_dec(self):
        self.assertEqual(painel._coins_dec(90), "90")
        self.assertEqual(painel._coins_dec(89.5), "89,50")

    # ---------- GET /admin/coins ----------

    def test_get_sem_login_redireciona(self):
        c = bot.app.test_client()
        resp = c.get("/admin/coins")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_get_cliente_sem_perm_redireciona(self):
        c = bot.app.test_client()
        _login(c, "CLIENTE", "cliente@x.com")
        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch):
            resp = c.get("/admin/coins")
        self.assertEqual(resp.status_code, 302)

    def test_get_admin_renderiza_cards_form_historico(self):
        c = bot.app.test_client()
        _login(c)
        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch):
            resp = c.get("/admin/coins")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("COINS disponíveis", html)
        self.assertIn("150.000", html)
        self.assertIn("Preço por 1.000", html)
        self.assertIn("ATIVO", html)
        self.assertIn("Editar configurações", html)
        self.assertIn("Calculadora de COINS", html)
        self.assertIn("Histórico de alterações", html)
        self.assertIn("100.000 → 150.000", html)
        self.assertIn("1.000 COINS = R$ 90,00", html)

    def test_get_sem_tabela_avisa_migration(self):
        c = bot.app.test_client()
        _login(c)

        def fetch_sem_tabela(table, **kw):
            if table == "coins_historico":
                return []
            return []

        with mock.patch.object(painel, "_fetch_soft", side_effect=fetch_sem_tabela):
            resp = c.get("/admin/coins")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("supabase_migracao_v123.sql", html)
        self.assertIn("COINS disponíveis", html)

    def test_get_sem_perm_gerenciar_oculta_form(self):
        c = bot.app.test_client()
        _login(c, "MODERADOR", "moderador@x.com", perms=["ver_coins"])
        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch):
            resp = c.get("/admin/coins")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("COINS disponíveis", html)
        self.assertNotIn("Editar configurações", html)
        self.assertNotIn("<button class='btn' type='submit'>Salvar alterações</button>", html)

    # ---------- POST /admin/coins/salvar ----------

    def test_post_salvar_envia_config_e_historico(self):
        c = bot.app.test_client()
        _login(c)
        calls = []

        def fakepost(url, **kw):
            calls.append((url, kw))
            return _FakeResp()

        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch), \
             mock.patch.object(painel.requests, "post", side_effect=fakepost):
            resp = c.post(
                "/admin/coins/salvar",
                data={
                    "_csrf": "tokenteste",
                    "estoque": "200.000",
                    "preco_mil": "85",
                    "min_compra": "200",
                    "max_compra": "40000",
                    "status": "pausado",
                    "observacao": "novo leilao",
                },
            )
        self.assertEqual(resp.status_code, 302)
        conf = [x for x in calls if "/rest/v1/coins_config" in x[0]]
        hist = [x for x in calls if "/rest/v1/coins_historico" in x[0]]
        aud = [x for x in calls if "/rest/v1/audit_log" in x[0]]
        self.assertTrue(conf, "config upsert nao enviado")
        payload = conf[0][1]["json"]
        self.assertEqual(payload["id"], 1)
        self.assertEqual(payload["estoque"], 200000.0)
        self.assertEqual(payload["preco_mil"], 85.0)
        self.assertEqual(payload["status"], "pausado")
        self.assertEqual(payload["observacao"], "novo leilao")
        self.assertTrue(hist, "historico nao registrado")
        hp = hist[0][1]["json"]
        self.assertEqual(hp["admin"], "admin@bapzx.com")
        self.assertEqual(hp["qtd_anterior"], 150000.0)
        self.assertEqual(hp["qtd_nova"], 200000.0)
        self.assertEqual(hp["preco_anterior"], 90.0)
        self.assertEqual(hp["preco_novo"], 85.0)
        self.assertIn("estoque", hp["alteracao"])
        self.assertIn("preço", hp["alteracao"])
        self.assertIn("status", hp["alteracao"])
        self.assertTrue(aud, "auditoria nao registrada")
        self.assertEqual(aud[0][1]["json"]["acao"], "coins_salvar")

    def test_post_sem_mudanca_nao_grava_historico(self):
        c = bot.app.test_client()
        _login(c)
        calls = []

        def fakepost(url, **kw):
            calls.append((url, kw))
            return _FakeResp()

        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch), \
             mock.patch.object(painel.requests, "post", side_effect=fakepost):
            resp = c.post(
                "/admin/coins/salvar",
                data={
                    "_csrf": "tokenteste",
                    "estoque": "150000",
                    "preco_mil": "90",
                    "min_compra": "100",
                    "max_compra": "50000",
                    "status": "ativo",
                    "observacao": "",
                },
            )
        self.assertEqual(resp.status_code, 302)
        hist = [x for x in calls if "/rest/v1/coins_historico" in x[0]]
        self.assertFalse(hist, "historico nao deveria ser gravado sem mudancas")

    def test_post_preco_zero_400(self):
        c = bot.app.test_client()
        _login(c)
        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch):
            resp = c.post(
                "/admin/coins/salvar",
                data={"_csrf": "tokenteste", "estoque": "100000", "preco_mil": "0",
                      "min_compra": "100", "max_compra": "50000", "status": "ativo"},
            )
        self.assertEqual(resp.status_code, 400)

    def test_post_min_maior_max_400(self):
        c = bot.app.test_client()
        _login(c)
        with mock.patch.object(painel, "_fetch_soft", side_effect=_fake_fetch):
            resp = c.post(
                "/admin/coins/salvar",
                data={"_csrf": "tokenteste", "estoque": "100000", "preco_mil": "90",
                      "min_compra": "50000", "max_compra": "100", "status": "ativo"},
            )
        self.assertEqual(resp.status_code, 400)

    def test_post_csrf_invalido_403(self):
        c = bot.app.test_client()
        _login(c)
        resp = c.post(
            "/admin/coins/salvar",
            data={"_csrf": "errado", "estoque": "100000", "preco_mil": "90",
                  "min_compra": "100", "max_compra": "50000", "status": "ativo"},
        )
        self.assertEqual(resp.status_code, 403)

    def test_post_sem_perm_gerenciar_403(self):
        c = bot.app.test_client()
        _login(c, "MODERADOR", "moderador@x.com", perms=["ver_coins"])
        resp = c.post(
            "/admin/coins/salvar",
            data={"_csrf": "tokenteste", "estoque": "100000", "preco_mil": "90",
                  "min_compra": "100", "max_compra": "50000", "status": "ativo"},
        )
        self.assertEqual(resp.status_code, 403)


class TestCoinsBot(unittest.TestCase):
    def setUp(self):
        bot._COINS_CACHE["ts"] = 0.0
        bot._COINS_CACHE["dados"] = None
        bot._PRECOS_CACHE["ts"] = 0.0
        bot._PRECOS_CACHE["dados"] = {}

    # ---------- calc_price ----------

    def test_calc_price_legado_sem_config(self):
        with mock.patch.object(bot, "_coins_config", return_value=None), \
             mock.patch.object(bot, "_precos_config", return_value=dict(bot.PRICES)):
            self.assertEqual(bot.calc_price(1000), "R$90,00")
            self.assertEqual(bot.calc_price(2500), "R$225,00")
            self.assertEqual(bot.calc_price(1500), "R$135,00")

    def test_calc_price_dinamico_com_preco_mil(self):
        with mock.patch.object(bot, "_coins_config",
                               return_value={"preco_mil": 80.0}):
            self.assertEqual(bot.calc_price(1000), "R$80,00")
            self.assertEqual(bot.calc_price(2500), "R$200,00")
            self.assertEqual(bot.calc_price(100), "R$8,00")

    # ---------- _coins_check ----------

    def test_check_sem_config_libera(self):
        with mock.patch.object(bot, "_coins_config", return_value=None):
            self.assertIsNone(bot._coins_check(5000))

    def test_check_pausado_bloqueia(self):
        with mock.patch.object(bot, "_coins_config",
                               return_value={"status": "pausado", "min_compra": 100,
                                            "max_compra": 50000}):
            msg = bot._coins_check(1000)
            self.assertIsNotNone(msg)
            self.assertIn("pausadas", msg)

    def test_check_limite_min(self):
        with mock.patch.object(bot, "_coins_config",
                               return_value={"status": "ativo", "min_compra": 1000,
                                            "max_compra": 50000}):
            msg = bot._coins_check(500)
            self.assertIsNotNone(msg)
            self.assertIn("1.000", msg)
            self.assertIsNone(bot._coins_check(2000))

    def test_check_limite_max(self):
        with mock.patch.object(bot, "_coins_config",
                               return_value={"status": "ativo", "min_compra": 100,
                                            "max_compra": 50000}):
            self.assertIsNone(bot._coins_check(50000))
            msg = bot._coins_check(60000)
            self.assertIsNotNone(msg)
            self.assertIn("50.000", msg)

    # ---------- tabelas de preço dinâmicas ----------

    def test_price_table_compact_dinamica(self):
        with mock.patch.object(bot, "_coins_config",
                               return_value={"preco_mil": 90.0}):
            txt = bot.price_table_compact()
        self.assertIn("1.000 RC - R$90,00", txt)
        self.assertIn("2.500 RC - R$225,00", txt)

    def test_price_table_text_dinamica(self):
        with mock.patch.object(bot, "_coins_config",
                               return_value={"preco_mil": 100.0}):
            txt = bot.price_table_text()
        self.assertIn("1.000 RC  — R$ 100,00", txt)
        self.assertIn("2.500 RC  — R$ 250,00", txt)

    def test_persona_precos_dinamicos(self):
        with mock.patch.object(bot, "_coins_config",
                               return_value={"preco_mil": 100.0}):
            txt = bot.load_persona()
        self.assertIn("1.000 RC — R$ 100,00", txt)
        self.assertIn("- 1000 RC: [R$100,00]", txt)
        self.assertNotIn("R$ 90,00", txt)


if __name__ == "__main__":
    unittest.main(verbosity=2)