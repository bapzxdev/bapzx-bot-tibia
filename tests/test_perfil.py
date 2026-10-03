# Testes do /cliente/perfil expandido (v2.10.28): seções, avatar, selects
# (mundo do _MK_MUNDOS), preferências, toast, POST resiliente (fallback legado).
# Rodar: python tests/test_perfil.py (da raiz do projeto)

import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bot
import painel


def _user():
    return {"email": "cliente@x.com", "name": "Cliente Teste"}


PROFILE = {
    "email": "cliente@x.com",
    "personagem": "BapzTeste",
    "mundo": "Auroria",
    "apelido": "Bapz",
    "vocacao": "Knight",
    "discord": "bapz_01",
    "whatsapp": "(19) 98765-4321",
    "avatar_url": "https://x/avatares/a.png",
    "notif_pedidos": True,
    "notif_promos": False,
    "tema": "escuro",
    "idioma": "pt-BR",
}


class _FakeResp:
    def __init__(self, code=201):
        self.status_code = code
        self.text = ""


class _Arquivo:
    def __init__(self, blob, filename="foto.png", mimetype="image/png"):
        self._blob = blob
        self.filename = filename
        self.mimetype = mimetype

    def read(self):
        return self._blob


class TestPerfil(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bot.app.config["TESTING"] = True
        bot.app.secret_key = "teste-perfil"

    def _get(self, profile=None):
        with mock.patch.object(bot, "current_user", _user), \
             mock.patch.object(bot, "_cliente_profile", lambda email: dict(profile or {})), \
             mock.patch.object(bot, "_mk_vip_ativo", lambda email: False):
            c = bot.app.test_client()
            return c.get("/cliente/perfil"), c

    # ---------- GET ----------

    def test_get_tem_secoes_avatar_selects_e_prefs(self):
        resp, _ = self._get(PROFILE)
        self.assertEqual(resp.status_code, 200)
        corpo = resp.get_data(as_text=True)
        self.assertIn("Informações pessoais", corpo)
        self.assertIn("Dados de jogo", corpo)
        self.assertIn("Preferências", corpo)
        self.assertIn("type='file' name='avatar'", corpo)
        self.assertIn("name='apelido'", corpo)
        self.assertIn("name='vocacao'", corpo)
        self.assertIn("name='discord'", corpo)
        self.assertIn("name='notif_pedidos'", corpo)
        self.assertIn("name='notif_promos'", corpo)
        self.assertIn("name='tema'", corpo)
        self.assertIn("name='idioma'", corpo)
        self.assertIn("Verificado via Google", corpo)
        self.assertIn("alterações não salvas", corpo)
        self.assertIn("perfil-toast", corpo)
        self.assertIn("Salvando", corpo)

    def test_get_mundo_vem_do_banco_de_mundos(self):
        resp, _ = self._get({})
        corpo = resp.get_data(as_text=True)
        self.assertIn("<select name='mundo'", corpo)
        for mundo in ("Auroria", "Belaria", "Infernum I", "Vesperia"):
            self.assertIn(f">{mundo}<", corpo)

    def test_get_preserva_mundo_antigo_fora_da_lista(self):
        resp, _ = self._get({"mundo": "Antica"})
        corpo = resp.get_data(as_text=True)
        self.assertIn("Antica (antigo)", corpo)

    def test_get_toast_aparece_e_some_da_sessao(self):
        resp, c = self._get({})
        self.assertNotIn("id='perfil-toast'", resp.get_data(as_text=True))
        with mock.patch.object(bot, "current_user", _user), \
             mock.patch.object(bot, "_cliente_profile", lambda email: {}), \
             mock.patch.object(bot, "_mk_vip_ativo", lambda email: False):
            with c.session_transaction() as s:
                s["_perfil_msg"] = ["ok", "Perfil salvo com sucesso!"]
            resp2 = c.get("/cliente/perfil")
        corpo = resp2.get_data(as_text=True)
        self.assertIn("Perfil salvo com sucesso!", corpo)
        with c.session_transaction() as s:
            self.assertNotIn("_perfil_msg", s)

    # ---------- POST ----------

    def _post(self, data, profile=None, post_status=201, remote=True, arquivos=None):
        chamadas = []

        def fake_post(url, headers=None, json=None, timeout=None):
            chamadas.append(dict(json or {}))
            return _FakeResp(post_status() if callable(post_status) else post_status)

        with mock.patch.object(bot, "current_user", _user), \
             mock.patch.object(bot, "_csrf_ok", lambda: True), \
             mock.patch.object(bot, "_cliente_profile", lambda email: dict(profile or {})), \
             mock.patch.object(type(bot.STORE), "remote", new_callable=mock.PropertyMock, return_value=remote), \
             mock.patch.object(bot.requests, "post", fake_post):
            c = bot.app.test_client()
            kw = {"data": dict(data)}
            if arquivos:
                kw["data"].update(arquivos)
                kw["content_type"] = "multipart/form-data"
            resp = c.post("/cliente/perfil", **kw)
            with c.session_transaction() as s:
                flash = s.get("_perfil_msg")
        return resp, chamadas, flash

    def test_post_salva_tudo_e_toast_ok(self):
        resp, chamadas, flash = self._post(
            {
                "_csrf": "tokenteste",
                "apelido": "Bapz",
                "personagem": "BapzTeste",
                "mundo": "Auroria",
                "vocacao": "Knight",
                "discord": "bapz_01",
                "whatsapp": "(19) 98765-4321",
                "notif_pedidos": "1",
                "tema": "escuro",
                "idioma": "pt-BR",
            }
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(chamadas), 1)
        envio = chamadas[0]
        self.assertEqual(envio["apelido"], "Bapz")
        self.assertEqual(envio["vocacao"], "Knight")
        self.assertEqual(envio["mundo"], "Auroria")
        self.assertEqual(envio["notif_pedidos"], True)
        self.assertEqual(envio["notif_promos"], False)
        self.assertEqual(flash, ["ok", "Perfil salvo com sucesso!"])

    def test_post_fallback_legado_detalhado(self):
        status = [400, 201]

        def vez():
            return status.pop(0)

        resp, chamadas, flash = self._post(
            {
                "_csrf": "tokenteste",
                "apelido": "Bapz",
                "personagem": "BapzTeste",
                "mundo": "Belaria",
                "vocacao": "Druid",
                "discord": "x",
            },
            post_status=vez,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(chamadas), 2)
        self.assertIn("apelido", chamadas[0])
        self.assertNotIn("apelido", chamadas[1])
        self.assertEqual(
            set(chamadas[1].keys()),
            {"email", "name", "sub", "role", "personagem", "mundo"},
        )
        self.assertEqual(flash, ["ok", "Perfil salvo com sucesso!"])

    def test_post_sem_personagem_nao_salva(self):
        resp, chamadas, flash = self._post(
            {"_csrf": "tokenteste", "personagem": "", "mundo": "Auroria"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(chamadas, [])
        self.assertEqual(flash[0], "erro")

    def test_post_whatsapp_invalido_nao_salva(self):
        resp, chamadas, flash = self._post(
            {"_csrf": "tokenteste", "personagem": "X", "whatsapp": "123"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(chamadas, [])
        self.assertEqual(flash[0], "erro")

    def test_post_mundo_fora_da_lista_vira_vazio(self):
        resp, chamadas, _ = self._post(
            {"_csrf": "tokenteste", "personagem": "X", "mundo": "Narnia"}
        )
        self.assertEqual(chamadas[0]["mundo"], "")

    def test_post_csrf_invalido_403(self):
        with mock.patch.object(bot, "current_user", _user), \
             mock.patch.object(bot, "_csrf_ok", lambda: False):
            c = bot.app.test_client()
            resp = c.post("/cliente/perfil", data={"personagem": "X"})
        self.assertEqual(resp.status_code, 403)

    # ---------- upload de avatar ----------

    def test_avatar_extensao_invalida(self):
        url, erro = bot._cliente_avatar_upload(_Arquivo(b"abc", "foto.bmp"))
        self.assertIsNone(url)
        self.assertIn("Formato", erro)

    def test_avatar_maior_que_2mb(self):
        url, erro = bot._cliente_avatar_upload(_Arquivo(b"x" * (2 * 1024 * 1024 + 1)))
        self.assertIsNone(url)
        self.assertIn("2 MB", erro)

    def test_avatar_sobe_no_bucket_avatares(self):
        with mock.patch.object(painel, "SUPA_URL", "https://xyz.supabase.co"), \
             mock.patch.object(painel, "SUPA_KEY", "key123"), \
             mock.patch.object(bot.requests, "post") as fake:
            fake.return_value = _FakeResp(201)
            url, erro = bot._cliente_avatar_upload(_Arquivo(b"img", "foto.png"))
        self.assertIsNone(erro)
        self.assertTrue(url.startswith("https://xyz.supabase.co/storage/v1/object/public/avatares/"))
        chamada_url = fake.call_args[0][0]
        self.assertIn("/storage/v1/object/avatares/", chamada_url)


if __name__ == "__main__":
    unittest.main(verbosity=2)
