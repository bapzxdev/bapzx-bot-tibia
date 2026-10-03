# Testes da reforma /admin/itens (v2.10.27): sem categoria, sem upload de
# imagem; nome com autocomplete do banco local + sprite automático (Wiki).
# Padrão dos testes anteriores: test client do painel com mocks.
# Rodar: python tests/test_itens_admin.py (da raiz do projeto)

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bot
import painel

ITEM = {
    "id": "11111111-2222-3333-4444-555555555555",
    "nome": "War Hammer",
    "preco": "R$ 20,00",
    "descricao": "Martelo",
    "imagem": "https://wiki/x/War_Hammer.gif",
    "categoria": "geral",
    "ativo": True,
}


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


class TestItensAdmin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bot.app.config["TESTING"] = True
        bot.app.secret_key = "teste-itens-admin"
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

    def test_nome_padrao_e_sprite_form(self):
        self.assertEqual(painel._itens_nome_padrao("WAR HAMMER"), "War Hammer")
        self.assertEqual(
            painel._itens_sprite_form("https://x/y.gif"), "https://x/y.gif"
        )
        self.assertEqual(painel._itens_sprite_form("javascript:1"), "")
        self.assertEqual(painel._itens_sprite_form(""), "")

    def test_sprite_auto_falha_soft(self):
        with mock.patch.object(
            bot, "_mk_itemsprite", side_effect=Exception("wiki fora")
        ):
            self.assertEqual(painel._itens_sprite_auto("War Hammer"), "")

    def test_recursos_trazem_autocomplete_e_sprite_js(self):
        css, js = painel._itens_ac_recursos()
        self.assertIn("mk-pub-ac-drop", css)
        self.assertIn("mk-pub-ac-drop", js)
        self.assertIn("__mkResolverSprite", js)
        self.assertIn("War Hammer", js)  # banco local embutido

    # ---------- GET /admin/itens ----------

    def test_lista_sem_categoria_sem_upload_com_autocomplete(self):
        with mock.patch.object(
            painel, "_fetch", lambda *a, **k: [dict(ITEM)]
        ):
            _login(self.client)
            resp = self.client.get("/admin/itens")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertIn("id='item_name'", corpo)
        self.assertIn("id='mk_sprite_url'", corpo)
        self.assertIn("mk-pub-ac-drop", corpo)
        self.assertNotIn("name='categoria'", corpo)
        self.assertNotIn('name="categoria"', corpo)
        self.assertNotIn("type='file'", corpo)
        self.assertNotIn('type="file"', corpo)
        # card sem categoria
        self.assertNotIn("geral ·", corpo)

    # ---------- POST /admin/itens/novo ----------

    def _post_novo(self, data, fetch=None):
        posted = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            posted["json"] = dict(json or {})
            return _FakeResp(201)

        with mock.patch.object(painel, "_fetch", fetch or (lambda *a, **k: [])):
            with mock.patch.object(painel.requests, "post", fake_post):
                with mock.patch.object(painel, "_audit", lambda *a, **k: None):
                    _login(self.client)
                    resp = self.client.post("/admin/itens/novo", data=data)
        return resp, posted

    def test_novo_usa_sprite_do_form_e_sem_categoria(self):
        resp, posted = self._post_novo(
            {
                "_csrf": "tokenteste",
                "nome": "war hammer",
                "preco": "R$ 20,00",
                "descricao": "d",
                "ativo": "1",
                "sprite": "https://x/y/War_Hammer.gif",
            }
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(posted["json"]["nome"], "War Hammer")
        self.assertEqual(posted["json"]["imagem"], "https://x/y/War_Hammer.gif")
        self.assertNotIn("categoria", posted["json"])

    def test_novo_sem_sprite_resolve_automatico(self):
        with mock.patch.object(
            bot, "_mk_itemsprite", return_value="https://wiki/War_Hammer.gif"
        ):
            with mock.patch.object(
                bot, "_mk_sprite_host", side_effect=lambda u: u
            ):
                resp, posted = self._post_novo(
                    {
                        "_csrf": "tokenteste",
                        "nome": "War Hammer",
                        "preco": "",
                        "descricao": "",
                        "ativo": "1",
                        "sprite": "",
                    }
                )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(posted["json"]["imagem"], "https://wiki/War_Hammer.gif")

    def test_novo_rejeita_sprite_invalido_e_resolve(self):
        with mock.patch.object(
            bot, "_mk_itemsprite", return_value="https://wiki/X.gif"
        ):
            with mock.patch.object(
                bot, "_mk_sprite_host", side_effect=lambda u: u
            ):
                resp, posted = self._post_novo(
                    {
                        "_csrf": "tokenteste",
                        "nome": "War Hammer",
                        "preco": "",
                        "descricao": "",
                        "ativo": "0",
                        "sprite": "javascript:alert(1)",
                    }
                )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(posted["json"]["imagem"], "https://wiki/X.gif")

    def test_novo_csrf_invalido_403(self):
        resp, _ = self._post_novo(
            {"_csrf": "errado", "nome": "War Hammer", "ativo": "1"}
        )
        self.assertEqual(resp.status_code, 403)

    def test_novo_sem_nome_400(self):
        resp, _ = self._post_novo({"_csrf": "tokenteste", "nome": "", "ativo": "1"})
        self.assertEqual(resp.status_code, 400)

    # ---------- GET+POST /admin/itens/<id> ----------

    def test_editar_form_sem_categoria_sem_upload(self):
        with mock.patch.object(
            painel, "_fetch", lambda *a, **k: [dict(ITEM)]
        ):
            _login(self.client)
            resp = self.client.get(f"/admin/itens/{ITEM['id']}")
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertIn("id='item_name'", corpo)
        self.assertIn("id='mk_sprite_url'", corpo)
        self.assertIn("War_Hammer.gif", corpo)  # preview da atual
        self.assertNotIn("name='categoria'", corpo)
        self.assertNotIn('name="categoria"', corpo)
        self.assertNotIn("type='file'", corpo)

    def test_editar_troca_nome_resolve_sprite_novo(self):
        patched = {}

        def fake_patch(url, headers=None, json=None, timeout=None):
            patched["json"] = dict(json or {})
            return _FakeResp(204)

        with mock.patch.object(
            painel, "_fetch", lambda *a, **k: [dict(ITEM)]
        ):
            with mock.patch.object(painel.requests, "patch", fake_patch):
                with mock.patch.object(painel, "_audit", lambda *a, **k: None):
                    with mock.patch.object(
                        bot, "_mk_itemsprite",
                        return_value="https://wiki/Golden_Helmet.gif",
                    ):
                        with mock.patch.object(
                            bot, "_mk_sprite_host", side_effect=lambda u: u
                        ):
                            _login(self.client)
                            resp = self.client.post(
                                f"/admin/itens/{ITEM['id']}",
                                data={
                                    "_csrf": "tokenteste",
                                    "nome": "Golden Helmet",
                                    "preco": "R$ 30,00",
                                    "descricao": "c",
                                    "ativo": "1",
                                    "sprite": "",
                                },
                            )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(patched["json"]["nome"], "Golden Helmet")
        self.assertEqual(
            patched["json"]["imagem"], "https://wiki/Golden_Helmet.gif"
        )
        self.assertNotIn("categoria", patched["json"])

    def test_editar_mesmo_nome_mantem_imagem_atual(self):
        patched = {}

        def fake_patch(url, headers=None, json=None, timeout=None):
            patched["json"] = dict(json or {})
            return _FakeResp(204)

        with mock.patch.object(
            painel, "_fetch", lambda *a, **k: [dict(ITEM)]
        ):
            with mock.patch.object(painel.requests, "patch", fake_patch):
                with mock.patch.object(painel, "_audit", lambda *a, **k: None):
                    _login(self.client)
                    resp = self.client.post(
                        f"/admin/itens/{ITEM['id']}",
                        data={
                            "_csrf": "tokenteste",
                            "nome": "War Hammer",
                            "preco": "R$ 20,00",
                            "descricao": "d",
                            "ativo": "1",
                            "sprite": "",
                        },
                    )
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn("imagem", patched["json"])

    # ---------- GET /api/itens ----------

    def test_api_itens_sem_categoria(self):
        with mock.patch.object(
            painel, "_fetch_public", lambda *a, **k: [dict(ITEM)]
        ):
            resp = self.client.get("/api/itens")
        self.assertEqual(resp.status_code, 200)
        dados = resp.get_json()
        self.assertTrue(dados["ok"])
        self.assertEqual(dados["itens"][0]["nome"], "War Hammer")
        self.assertEqual(
            dados["itens"][0]["imagem"], "https://wiki/x/War_Hammer.gif"
        )
        self.assertNotIn("categoria", dados["itens"][0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
