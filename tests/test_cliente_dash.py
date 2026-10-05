# Testes do dashboard do cliente (v2.10.30): /cliente, /perfil, /suporte e
# detalhe usam sidebar+topbar; /cliente/troca segue no layout antigo.
# Rodar: python tests/test_cliente_dash.py (da raiz do projeto)

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bot


def _user():
    return {"email": "cliente@x.com", "name": "Cliente Teste"}


class _FakeResp:
    def __init__(self, code=200, payload=None):
        self.status_code = code
        self._payload = payload if payload is not None else []

    def json(self):
        return self._payload


class TestClienteDash(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bot.app.config["TESTING"] = True
        bot.app.secret_key = "teste-cliente-dash"

    def _base(self):
        return [
            mock.patch.object(bot, "current_user", _user),
            mock.patch.object(bot, "_mk_vip_ativo", lambda email: False),
            mock.patch.object(bot, "_cliente_profile", lambda email: {}),
            mock.patch.object(bot, "_cliente_tickets", lambda email: []),
        ]

    def _get(self, path, extra=None):
        patches = self._base() + (extra or [])
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        return bot.app.test_client().get(path)

    def _assert_dash(self, corpo, ativo_href, page_title):
        self.assertIn("c-sidebar", corpo)
        self.assertIn("c-topbar", corpo)
        self.assertIn("c-hamburger", corpo)
        self.assertIn("c-scrim", corpo)
        self.assertIn(f"<a class='c-side-item active' href='{ativo_href}'", corpo)
        self.assertIn(f"<h1>{page_title}</h1>", corpo)
        self.assertIn("Área do Cliente", corpo)
        self.assertNotIn("<nav class='nav'", corpo)
        self.assertNotIn("@@", corpo)
        self.assertNotIn("_blank", corpo)

    def test_cliente_visao_geral_no_dash(self):
        resp = self._get("/cliente")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self._assert_dash(corpo, "/cliente", "Visão Geral")
        # 7 blocos, sem poluição
        self.assertIn("Conta ativa", corpo)
        self.assertIn("Atividade recente", corpo)
        self.assertIn("Acesso rápido", corpo)
        self.assertIn("Seu plano", corpo)
        self.assertIn("Avisos", corpo)
        self.assertIn("Status dos serviços", corpo)
        self.assertIn("Gerenciar plano", corpo)
        self.assertNotIn("Últimos pedidos", corpo)
        self.assertNotIn("Precisa de ajuda?", corpo)

    def test_pedidos_pagina_propria(self):
        extra = [mock.patch.object(bot.STORE, "list", lambda: [])]
        resp = self._get("/cliente/pedidos", extra)
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self._assert_dash(corpo, "/cliente/pedidos", "Meus Pedidos")
        self.assertIn("mesmo e-mail", corpo)

    def test_perfil_no_dash(self):
        resp = self._get("/cliente/perfil")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self._assert_dash(corpo, "/cliente/perfil", "Meu Perfil")
        self.assertIn("Informações pessoais", corpo)
        self.assertIn("id='perfil-form'", corpo)

    def test_suporte_no_dash(self):
        resp = self._get("/cliente/suporte")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self._assert_dash(corpo, "/cliente/suporte", "Suporte")
        self.assertIn("Meus chamados", corpo)

    def test_suporte_detalhe_no_dash(self):
        ticket = {
            "id": 7,
            "criado_em": "2026-10-03T10:00:00",
            "assunto": "Duvida",
            "mensagem": "Oi",
            "status": "aberto",
            "resposta": "",
        }
        extra = [
            mock.patch.object(
                type(bot.STORE), "remote",
                new_callable=mock.PropertyMock, return_value=True,
            ),
            mock.patch.object(
                bot.requests, "get",
                lambda *a, **k: _FakeResp(200, [dict(ticket)]),
            ),
        ]
        resp = self._get("/cliente/suporte/7", extra)
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self._assert_dash(corpo, "/cliente/suporte", "Suporte")
        self.assertIn("Chamado #7", corpo)

    def test_troca_com_sidebar_sincronizada(self):
        extra = [
            mock.patch.object(bot, "_cliente_header", lambda user, x: "top-mock"),
            mock.patch.object(bot, "_mk_ativo", lambda: True),
            mock.patch.object(bot, "_mk_profile", lambda email: {}),
            mock.patch.object(bot, "_marketplace_config", lambda: None),
            mock.patch.object(bot, "_mk_minhas_listings", lambda email: []),
            mock.patch.object(bot, "_mk_meus_pagamentos", lambda email: []),
        ]
        resp = self._get("/cliente/troca", extra)
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertIn("c-sidebar", corpo)
        self.assertIn("c-topbar", corpo)
        self.assertIn("<a class='c-side-item active' href='/cliente/troca'", corpo)
        self.assertIn("MARKTRADE", corpo)
        self.assertNotIn("@@", corpo)
        self.assertNotIn("_blank", corpo)
        self.assertIn("Publicar anúncio", corpo)


PEDIDO = {
    "id": 5, "email": "cliente@x.com", "tc": "1500",
    "preco": "R$ 135,00", "mundo": "Auroria",
    "status": "pago", "data": "2026-10-01T10:00:00",
}


class TestClienteNovasPaginas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bot.app.config["TESTING"] = True
        bot.app.secret_key = "teste-cliente-dash"

    def _get(self, path, extra=None):
        patches = [
            mock.patch.object(bot, "current_user", _user),
            mock.patch.object(bot, "_mk_vip_ativo", lambda email: False),
            mock.patch.object(bot, "_cliente_profile", lambda email: {}),
            mock.patch.object(bot, "_cliente_tickets", lambda email: []),
            mock.patch.object(bot.STORE, "list", lambda: [dict(PEDIDO)]),
            mock.patch.object(bot, "_marketplace_config", lambda: {"preco_vip": 12.99}),
            mock.patch.object(bot, "_mk_meus_pagamentos", lambda email: []),
            mock.patch.object(bot, "_mk_profile", lambda email: {}),
            mock.patch.object(bot, "_cliente_servicos_meus", lambda wpp: []),
            mock.patch.object(bot, "_cliente_servicos_catalogo", lambda: []),
        ] + (extra or [])
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        return bot.app.test_client().get(path)

    def _assert_dash(self, corpo, ativo_href, page_title):
        self.assertIn("c-sidebar", corpo)
        self.assertIn(f"<a class='c-side-item active' href='{ativo_href}'", corpo)
        self.assertIn(f"<h1>{page_title}</h1>", corpo)
        self.assertNotIn("@@", corpo)
        self.assertNotIn("_blank", corpo)

    def test_pagamentos_mostra_faturas(self):
        resp = self._get("/cliente/pagamentos")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self._assert_dash(corpo, "/cliente/pagamentos", "Pagamentos")
        self.assertIn("Faturas", corpo)
        self.assertIn("#5", corpo)
        self.assertIn("Pix", corpo)
        self.assertIn("Total pago", corpo)

    def test_automacoes_toggles_e_post(self):
        resp = self._get("/cliente/automacoes")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self._assert_dash(corpo, "/cliente/automacoes", "Automações")
        self.assertIn("Confirmação automática de Pix", corpo)
        self.assertIn("name='notif_pedidos'", corpo)

    def test_automacoes_post_salva(self):
        chamadas = []

        def fake_patch(url, headers=None, json=None, timeout=None):
            chamadas.append(dict(json or {}))
            r = mock.Mock()
            r.status_code = 204
            return r

        with mock.patch.object(bot, "current_user", _user), \
             mock.patch.object(bot, "_csrf_ok", lambda: True), \
             mock.patch.object(type(bot.STORE), "remote",
                               new_callable=mock.PropertyMock, return_value=True), \
             mock.patch.object(bot.requests, "patch", fake_patch):
            c = bot.app.test_client()
            resp = c.post("/cliente/automacoes",
                          data={"_csrf": "x", "notif_pedidos": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("salvo=1", resp.headers["Location"])
        self.assertEqual(chamadas[0]["notif_pedidos"], True)
        self.assertEqual(chamadas[0]["notif_promos"], False)

    def test_bot_bloqueado_sem_vip(self):
        resp = self._get("/cliente/bot")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self._assert_dash(corpo, "/cliente/bot", "Meu Bot")
        self.assertIn("plano VIP", corpo)
        self.assertIn("/cliente/troca/vip", corpo)

    def test_bot_liberado_com_vip(self):
        patches = [
            mock.patch.object(bot, "current_user", _user),
            mock.patch.object(bot, "_mk_vip_ativo", lambda email: True),
            mock.patch.object(bot, "_marketplace_config", lambda: {"preco_vip": 12.99}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        resp = bot.app.test_client().get("/cliente/bot")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertIn("Bot liberado", corpo)
        self.assertIn("t.me/bapzx_bot", corpo)

    def test_servicos_vazio_mais_catalogo(self):
        extra = [mock.patch.object(
            bot, "_cliente_servicos_catalogo",
            lambda: [{"nome": "Upar level", "preco": "R$ 20/h", "descricao": "d"}],
        )]
        resp = self._get("/cliente/servicos", extra)
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self._assert_dash(corpo, "/cliente/servicos", "Meus Serviços")
        self.assertIn("Nenhum serviço contratado", corpo)
        self.assertIn("Upar level", corpo)

    def test_plano_basico_com_tabela(self):
        resp = self._get("/cliente/plano")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self._assert_dash(corpo, "/cliente/plano", "Meu Plano")
        self.assertIn("Básico", corpo)
        self.assertIn("VIP Pro", corpo)
        self.assertIn("/cliente/troca/vip", corpo)

    def test_notificacoes_feed(self):
        resp = self._get("/cliente/notificacoes")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self._assert_dash(corpo, "/cliente/notificacoes", "Notificações")
        self.assertIn("Pagamento do pedido #5 confirmado.", corpo)
        self.assertIn("Complete seu perfil", corpo)




class TestVoltarCards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bot.app.config["TESTING"] = True
        bot.app.secret_key = "teste-voltar-cards"

    def _get(self, path, extra=None):
        patches = [
            mock.patch.object(bot, "current_user", _user),
            mock.patch.object(bot, "_mk_vip_ativo", lambda email: False),
            mock.patch.object(bot, "_cliente_profile", lambda email: {}),
            mock.patch.object(bot, "_cliente_tickets", lambda email: []),
            mock.patch.object(bot.STORE, "list", lambda: []),
            mock.patch.object(bot, "_marketplace_config", lambda: {"preco_vip": 12.99}),
            mock.patch.object(bot, "_mk_meus_pagamentos", lambda email: []),
            mock.patch.object(bot, "_mk_profile", lambda email: {}),
            mock.patch.object(bot, "_cliente_servicos_meus", lambda wpp: []),
            mock.patch.object(bot, "_cliente_servicos_catalogo", lambda: []),
        ] + (extra or [])
        for pc in patches:
            pc.start()
            self.addCleanup(pc.stop)
        return bot.app.test_client().get(path)

    def test_cards_dashboard(self):
        for path in ("/cliente/pedidos", "/cliente/perfil", "/cliente/suporte",
                     "/cliente/pagamentos", "/cliente/automacoes", "/cliente/bot",
                     "/cliente/servicos", "/cliente/plano", "/cliente/notificacoes"):
            resp = self._get(path)
            self.assertEqual(resp.status_code, 200, path)
            self.assertIn("Voltar ao Dashboard", resp.get_data(as_text=True), path)

    def test_hub_sem_card(self):
        resp = self._get("/cliente")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertNotIn("Voltar ao Dashboard", corpo)
        self.assertNotIn("Voltar ao Suporte", corpo)

    def test_detalhe_volta_ao_suporte(self):
        ticket = {"id": 7, "criado_em": "2026-10-03T10:00:00", "assunto": "D",
                  "mensagem": "Oi", "status": "aberto", "resposta": ""}

        class _R:
            status_code = 200

            def json(self):
                return [dict(ticket)]

        extra = [
            mock.patch.object(type(bot.STORE), "remote",
                              new_callable=mock.PropertyMock, return_value=True),
            mock.patch.object(bot.requests, "get", lambda *a, **k: _R()),
        ]
        resp = self._get("/cliente/suporte/7", extra)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Voltar ao Suporte", resp.get_data(as_text=True))

    def test_troca_com_voltar_dashboard(self):
        extra = [
            mock.patch.object(bot, "_cliente_header", lambda user, x: "top-mock"),
            mock.patch.object(bot, "_mk_ativo", lambda: True),
            mock.patch.object(bot, "_mk_profile", lambda email: {}),
            mock.patch.object(bot, "_marketplace_config", lambda: None),
            mock.patch.object(bot, "_mk_minhas_listings", lambda email: []),
            mock.patch.object(bot, "_mk_meus_pagamentos", lambda email: []),
        ]
        resp = self._get("/cliente/troca", extra)
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertIn("Voltar ao Dashboard", corpo)
        self.assertNotIn("_blank", corpo)


class TestLarguraSite(unittest.TestCase):
    # Site inteiro fluido (v2.10.35 bot + v2.10.37 painel): nenhum main/.content
    # pode travar em 900/1080/1200px centralizado (aspecto comprimido no wide).
    @classmethod
    def setUpClass(cls):
        bot.app.config["TESTING"] = True
        bot.app.secret_key = "teste-largura-site"

    def test_auth_layout_fluido(self):
        self.assertNotIn("max-width: 1080px", bot.AUTH_LAYOUT)

    def test_cliente_dash_css_fluido(self):
        self.assertNotIn("max-width:1080px", bot._CLIENTE_DASH_CSS)

    def test_acesso_sem_voltar_ao_site(self):
        with mock.patch.object(bot, "current_user",
                               lambda: {"email": "c@x.com", "name": "C",
                                         "cargo": "CLIENTE", "perms": []}):
            resp = bot.app.test_client().get("/acesso")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertNotIn("Voltar ao site", corpo)
        self.assertIn("Sair", corpo)

    def test_legais_sem_voltar_ao_site(self):
        client = bot.app.test_client()
        for path in ("/privacidade", "/termos", "/reembolso"):
            resp = client.get(path)
            self.assertEqual(resp.status_code, 200, path)
            self.assertNotIn("Voltar ao site", resp.get_data(as_text=True), path)
        self.assertIn("WhatsApp", client.get("/privacidade").get_data(as_text=True))

    def test_dashboard_vendas_fluido(self):
        with mock.patch.object(bot, "dashboard_allowed", lambda: True):
            with mock.patch.object(bot.STORE, "list", lambda: []):
                resp = bot.app.test_client().get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertNotIn("max-width: 900px", corpo)
        self.assertNotIn("max-width:900px", corpo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
