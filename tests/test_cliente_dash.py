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

    def test_cliente_visao_geral_no_dash(self):
        resp = self._get("/cliente")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self._assert_dash(corpo, "/cliente", "Visão Geral")
        # dados reaproveitados
        self.assertIn("Total de pedidos", corpo)
        self.assertIn("Meu perfil", corpo)

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

    def test_troca_segue_no_layout_antigo(self):
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
        self.assertNotIn("c-sidebar", corpo)
        self.assertNotIn("c-topbar", corpo)
        self.assertIn("Publicar anúncio", corpo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
