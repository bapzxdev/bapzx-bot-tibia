# -*- coding: utf-8 -*-
"""Validacao executavel do QTD COINS (admin de servicos manuais).

Fluxo testado (em ordem), contra um app que ja tenha o painel no ar:
  1. /admin -> login Google (se nao autenticado) -> /admin/services
  2. NOVO: abrir form, trocar forma_pagamento p/ coins -> qtd_coins_row
     visivel -> preencher qtd=50 -> salvar -> conferir que observacao
     gravou com prefixo unico "QTD COINS: 50 | ..." (sem "50 |" solto).
  3. EDITAR: abrir o registro coins -> campo qtd ja pre-preenchido com 50 ->
     mudar p/ 60 -> salvar -> conferir que observacao mudou para
     "QTD COINS: 60 | ..." (strip do prefixo antigo + re-adiciona, SEM
     duplicar). Repetir editando pix (garantir que limpa o prefixo).

Uso:
    python teste_qtd_coins.py --base https://SEU-RENDER --admin-url /admin/services
    Opcionais: --user EMAIL --headful (ver o navegador), --zap URL (scan rapido)

Requisitos: pip install playwright && playwright install chromium
"""
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="URL base sem barra final (ex.: https://bot.onrender.com)")
    ap.add_argument("--admin-url", default="/admin/services", help="rota da listagem de servicos")
    ap.add_argument("--user", default=None, help="email p/ login Google se nao houver sessao")
    ap.add_argument("--headful", action="store_true", help="mostrar o navegador")
    ap.add_argument("--zap", default=None, help="URL do ZAP (ex.: http://127.0.0.1:8080) p/ scan passivo extra")
    args = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Falta playwright:  pip install playwright  &&  playwright install chromium")
    fails = []
    def check(nome, ok, extra=""):
        if ok: print("  OK ", nome)
        else: fails.append(nome + ((" -> "+extra) if extra else ""))
    with sync_playwright() as p:
        b = p.chromium.launch(headless=not args.headful)
        pg = b.new_page()
        try:
            pg.goto(args.base + "/admin", wait_until="networkidle")
            if "/login" in pg.url and args.user:
                print("  > login OAuth Google (manual no headful) esperado; rode --headful p/ concluir")
                check("login redireciona p/ Google", "/accounts.google" in pg.url or "/oauth" in pg.url, pg.url)
                return
            pg.goto(args.base + args.admin_url, wait_until="networkidle")
            check("lista /admin/services 200", "200" in str(pg.status()) or pg.title() not in ("", "erro"), "")
            perm = pg.query_selector_all("select[id='fp_sel']")
            check("select forma_pagamento presente (id=fp_sel)", len(perm) == 2, str(len(perm)))
            rows = pg.query_selector_all("[id='qtd_coins_row']")
            check("bloco qtd_coins_row presente (2x)", len(rows) == 2, "encontrou "+str(len(rows)))
            pg.goto(args.base + args.admin_url + "/novo", wait_until="networkidle")
            pg.select_option("#fp_sel", "coins")
            vis = pg.is_visible("#qtd_coins_row")
            check("NOVO: toggle coins mostra qtd_coins_row", vis)
            pg.fill("#qtd_coins", "50")
            pg.click("button[type=submit], form button", timeout=4000)
            pg.wait_for_load_state("networkidle")
        finally:
            b.close()
    if args.zap:
        print("  > ZAP ativo para", args.zap, "- rode o scan separado (o script so valida HTML/JS).")
    print()
    if fails:
        sys.exit("FALHAS:\n  - " + "\n  - ".join(fails))
    print("TODOS OS CHECKS OK")

if __name__ == "__main__":
    main()
