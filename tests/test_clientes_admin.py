# Testes /admin/clientes completo (v2.10.36): busca+filtros, cards,
# plano derivado, WhatsApp clicavel, menu acoes, ficha completa, plano e nota.
# Rodar: python tests/test_clientes_admin.py (da raiz do projeto)

import os
import sys
import unittest
from unittest import mock
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bot
import painel


PROFILES = [
    {"email": "lucas@bapzx.com", "name": "Lucas", "whatsapp": "(19) 99999-9999",
     "role": "admin", "bloqueado": False, "created_at": "2026-09-01T10:00:00",
     "vip_until": None, "personagem": "Bap", "mundo": "Rubinot"},
    {"email": "prox@x.com", "name": "Cliente Pro", "whatsapp": "19988887777",
     "role": "cliente", "bloqueado": False, "created_at": "2026-09-02T10:00:00",
     "vip_until": (datetime.utcnow() + timedelta(days=10)).isoformat()},
    {"email": "bloq@x.com", "name": "Bloq", "whatsapp": "",
     "role": "cliente", "bloqueado": True, "created_at": "2026-09-03T10:00:00",
     "vip_until": None},
    {"email": "sem@x.com", "name": "Sem Pedido", "whatsapp": "",
     "role": "cliente", "bloqueado": False, "created_at": "2026-09-04T10:00:00",
     "vip_until": None},
]

ORDERS = [
    {"id": 1, "email": "lucas@bapzx.com", "usuario": "Lucas", "char": "Bap",
     "tc": "1000", "preco": "R$ 90,00", "mundo": "Rubinot",
     "status": "entregue", "data": "2026-09-10T10:00:00",
     "pix_confirmado_em": "2026-09-10T10:05:00"},
    {"id": 2, "email": "prox@x.com", "usuario": "Pro", "char": "ProChar",
     "tc": "500", "preco": "R$ 45,00", "mundo": "Rubinot",
     "status": "pago", "data": "2026-09-11T10:00:00",
     "pix_confirmado_em": "2026-09-11T10:05:00"},
    {"id": 3, "email": "so-pedido@x.com", "usuario": "SP", "char": "SPChar",
     "tc": "100", "preco": "R$ 9,00", "mundo": "Rubinot",
     "status": "pendente", "data": "2026-09-12T10:00:00"},
]


def _login(client, cargo="ADMINISTRADOR", email="admin@bapzx.com"):
    with client.session_transaction() as s:
        s["email"] = email
        s["cargo"] = cargo
        s["perms"] = ["ALL"] if cargo == "ADMINISTRADOR" else []
        s["_csrf"] = "tokenteste"


class _FakeResp:
    status_code = 200
    text = ""
    headers = {}

    def __init__(self, code=200):
        self.status_code = code

    def json(self):
        return []


class TestClientesAdmin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bot.app.config["TESTING"] = True
        bot.app.secret_key = "teste-clientes-admin"
        cls.client = bot.app.test_client()

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

    def test_plano_derivado(self):
        self.assertEqual(painel._clientes_plano(PROFILES[0]), "MASTER")
        self.assertEqual(painel._clientes_plano(PROFILES[1]), "PRO")
        self.assertEqual(painel._clientes_plano(PROFILES[3]), "Básico")

    def test_vip_ativo_fail_soft(self):
        self.assertTrue(painel._clientes_vip_ativo(PROFILES[1]))
        self.assertFalse(painel._clientes_vip_ativo(PROFILES[0]))
        self.assertFalse(painel._clientes_vip_ativo({}))
        self.assertFalse(painel._clientes_vip_ativo({"vip_until": "invalida"}))

    def test_whatsapp_clicavel(self):
        link = painel._clientes_whats_link("(19) 99999-9999")
        self.assertIn("https://wa.me/1999999999", link)
        self.assertIn("📱", link)
        self.assertEqual(painel._clientes_whats_link(""), "-")
        self.assertEqual(painel._clientes_whats_link("-"), "-")

    def test_stats_uniao_profiles_e_so_pedidos(self):
        por, ped, emails = painel._clientes_stats(PROFILES, ORDERS)
        # 4 perfis + 1 só-pedido = 5
        self.assertEqual(len(emails), 5)
        self.assertIn("so-pedido@x.com", emails)
        self.assertEqual(ped["lucas@bapzx.com"]["pedidos"], 1)

    # ---------- GET /admin/clientes ----------

    def _get_clientes(self, qs=""):
        def fake_fetch(table, select="*", order="", query="", range_="0-999"):
            if table == "profiles":
                return [dict(p) for p in PROFILES]
            if table == "pedidos":
                return [dict(o) for o in ORDERS]
            return []

        with mock.patch.object(painel, "_fetch", fake_fetch):
            with mock.patch.object(painel, "_ultimos_acessos", lambda: {}):
                _login(self.client)
                return self.client.get(f"/admin/clientes{qs}")

    def test_lista_cards_e_coluna_plano(self):
        resp = self._get_clientes()
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertIn("Total clientes", corpo)
        self.assertIn("Compradores", corpo)
        self.assertIn("Faturamento", corpo)
        self.assertIn("<th>Plano</th>", corpo)
        self.assertIn("⭐ MASTER", corpo)
        self.assertIn("⭐ PRO", corpo)
        self.assertIn("wa.me/1999999999", corpo)
        self.assertIn("⋮", corpo)
        self.assertIn("Ver perfil", corpo)
        self.assertIn("Alterar plano", corpo)
        self.assertIn("Nota interna", corpo)
        # sem o card antigo inconsistente
        self.assertNotIn(">Perfis</div>", corpo)

    def test_busca_filtra(self):
        resp = self._get_clientes("?busca=prox")
        corpo = resp.get_data(as_text=True)
        self.assertIn("prox@x.com", corpo)
        self.assertNotIn("bloq@x.com", corpo)

    def test_filtro_bloqueados(self):
        resp = self._get_clientes("?filtro=bloqueados")
        corpo = resp.get_data(as_text=True)
        self.assertIn("bloq@x.com", corpo)
        self.assertNotIn("prox@x.com", corpo)

    def test_filtro_sem_pedidos(self):
        resp = self._get_clientes("?filtro=sem_pedidos")
        corpo = resp.get_data(as_text=True)
        self.assertIn("sem@x.com", corpo)
        self.assertNotIn("prox@x.com", corpo)

    def test_filtro_com_pedidos_inclui_so_pedido(self):
        resp = self._get_clientes("?filtro=com_pedidos")
        corpo = resp.get_data(as_text=True)
        self.assertIn("so-pedido@x.com", corpo)
        self.assertNotIn("sem@x.com", corpo)

    # ---------- GET /admin/clientes/<email> ----------

    def test_detalhe_ficha_completa(self):
        def fake_fetch(table, select="*", order="", query="", range_="0-999"):
            if table == "profiles":
                return [dict(PROFILES[0])]
            if table == "pedidos":
                return [dict(o) for o in ORDERS]
            return []

        with mock.patch.object(painel, "_fetch", fake_fetch):
            with mock.patch.object(painel, "_fetch_soft", lambda *a, **k: []):
                with mock.patch.object(painel, "_ultimos_acessos", lambda: {}):
                    _login(self.client)
                    resp = self.client.get("/admin/clientes/lucas@bapzx.com")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertIn("👤 Informações", corpo)
        self.assertIn("💰 Financeiro", corpo)
        self.assertIn("Total gasto", corpo)
        self.assertIn("Pedido médio", corpo)
        self.assertIn("Última compra", corpo)
        self.assertIn("Último pagamento", corpo)
        self.assertIn("⭐ Plano", corpo)
        self.assertIn("🛒 Pedidos do cliente", corpo)
        self.assertIn("🎫 Tickets", corpo)
        self.assertIn("⚙️ Serviços", corpo)
        self.assertIn("Notas internas", corpo)
        self.assertIn("(19) 99999-9999", corpo)

    # ---------- POST plano / editar ----------

    def test_plano_pro_grava_vip(self):
        posted = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            posted["json"] = dict(json or {})
            return _FakeResp(200)

        _login(self.client)
        with mock.patch.object(painel.requests, "post", fake_post):
            with mock.patch.object(painel, "_audit", lambda *a, **k: None):
                resp = self.client.post(
                    "/admin/clientes/prox@x.com/plano",
                    data={"_csrf": "tokenteste", "plano": "pro", "dias": "30"},
                )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("vip_until", posted["json"])

    def test_plano_basico_limpa_vip(self):
        patched = {}

        def fake_patch(url, headers=None, json=None, timeout=None):
            patched["json"] = dict(json or {})
            return _FakeResp(200)

        _login(self.client)
        with mock.patch.object(painel.requests, "patch", fake_patch):
            with mock.patch.object(painel, "_audit", lambda *a, **k: None):
                resp = self.client.post(
                    "/admin/clientes/prox@x.com/plano",
                    data={"_csrf": "tokenteste", "plano": "basico"},
                )
        self.assertEqual(resp.status_code, 302)
        self.assertIsNone(patched["json"]["vip_until"])

    def test_editar_salva_nota(self):
        posted = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            posted["json"] = dict(json or {})
            return _FakeResp(200)

        _login(self.client)
        with mock.patch.object(painel.requests, "post", fake_post):
            with mock.patch.object(painel, "_audit", lambda *a, **k: None):
                resp = self.client.post(
                    "/admin/clientes/sem@x.com/editar",
                    data={"_csrf": "tokenteste", "name": "Sem Pedido",
                          "whatsapp": "", "personagem": "", "mundo": "",
                          "role": "cliente",
                          "nota_interna": "Cliente recorrente."},
                )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(posted["json"].get("nota_interna"), "Cliente recorrente.")

    def test_conteudo_admin_largura_total(self):
        # O .content nao pode travar em 1200px (site comprimido em monitor wide).
        self.assertNotIn("max-width:1200px", painel.LAYOUT_HEAD)
        self.assertIn(".content", painel.LAYOUT_HEAD)

    def test_css_compacto_global_e_frow(self):
        # Compacto em tudo: labels coladas + helpers frow.
        self.assertIn("margin:8px 0 4px", painel.LAYOUT_HEAD)
        self.assertIn(".frow.c2", painel.LAYOUT_HEAD)
        self.assertIn(".frow.c3", painel.LAYOUT_HEAD)

    def _login_admin(self, client):
        with client.session_transaction() as s:
            s["email"] = "admin@bapzx.com"
            s["cargo"] = "ADMINISTRADOR"
            s["perms"] = ["ALL"]
            s["_csrf"] = "tokenteste"

    def _base_patches(self):
        return [
            mock.patch.object(painel, "_sessao_ativa", lambda sid: True),
            mock.patch.object(painel, "_notificacoes", lambda _u: ([], [], 0)),
            mock.patch.object(painel, "ADMIN_IP_ALLOWLIST", ""),
        ]

    def test_form_cliente_detalhe_em_grid(self):
        prof = {"email": "c@x.com", "name": "C", "role": "cliente",
                "bloqueado": False, "created_at": "2026-09-01T10:00:00"}

        def fake_fetch(table, select="*", order="", query="", range_="0-999"):
            if table == "profiles":
                return [dict(prof)]
            return []

        for p in self._base_patches():
            p.start()
            self.addCleanup(p.stop)
        with mock.patch.object(painel, "_fetch", fake_fetch):
            with mock.patch.object(painel, "_fetch_soft", lambda *a, **k: []):
                with mock.patch.object(painel, "_ultimos_acessos", lambda: {}):
                    client = bot.app.test_client()
                    self._login_admin(client)
                    resp = client.get("/admin/clientes/c@x.com")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertIn("frow c2", corpo)
        for campo in ("name='name'", "name='whatsapp'", "name='personagem'",
                      "name='mundo'", "name='role'", "name='nota_interna'",
                      "name='plano'", "name='dias'"):
            self.assertIn(campo, corpo)

    def test_logo_admin_link_home(self):
        for p in self._base_patches():
            p.start()
            self.addCleanup(p.stop)
        with mock.patch.object(painel, "_fetch_soft", lambda *a, **k: []):
            with mock.patch.object(painel, "_cupons_lista_referencias",
                                   lambda: ([], [], [])):
                client = bot.app.test_client()
                self._login_admin(client)
                resp = client.get("/admin/cupons")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertIn("brand-home", corpo)
        self.assertIn(painel.PORTFOLIO_URL, corpo)

    def test_form_cupons_em_grid(self):
        for p in self._base_patches():
            p.start()
            self.addCleanup(p.stop)
        with mock.patch.object(painel, "_fetch_soft", lambda *a, **k: []):
            with mock.patch.object(painel, "_cupons_lista_referencias",
                                   lambda: ([], [], [])):
                client = bot.app.test_client()
                self._login_admin(client)
                resp = client.get("/admin/cupons")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertIn("frow c3", corpo)
        for campo in ("name='codigo'", "name='tipo'", "name='valor'",
                      "name='validade'", "name='limite_usos'", "name='produto_id'",
                      "name='servico_id'", "name='grupo_id'"):
            self.assertIn(campo, corpo)

    def test_form_usuarios_grupos_em_grid(self):
        for p in self._base_patches():
            p.start()
            self.addCleanup(p.stop)
        with mock.patch.object(painel, "_fetch_soft",
                               lambda *a, **k: [{"id": 1, "nome": "G",
                                                "link": "", "ativo": True,
                                                "ordem": 1}]):
                client = bot.app.test_client()
                self._login_admin(client)
                r1 = client.get("/admin/usuarios/novo")
                r2 = client.get("/admin/grupos/1")
        for resp in (r1, r2):
            self.assertEqual(resp.status_code, 200)
        c1 = r1.get_data(as_text=True)
        self.assertIn("frow c2", c1)
        for campo in ("name='email'", "name='nome'", "name='cargo'"):
            self.assertIn(campo, c1)
        c2 = r2.get_data(as_text=True)
        self.assertIn("frow c2", c2)
        for campo in ("name='nome'", "name='link'", "name='ordem'"):
            self.assertIn(campo, c2)

    def test_editar_csrf_403(self):
        _login(self.client)
        with mock.patch.object(painel, "_audit", lambda *a, **k: None):
            resp = self.client.post(
                "/admin/clientes/sem@x.com/editar",
                data={"_csrf": "errado", "name": "X"},
            )
        self.assertEqual(resp.status_code, 403)


if __name__ == "__main__":
    unittest.main(verbosity=2)
