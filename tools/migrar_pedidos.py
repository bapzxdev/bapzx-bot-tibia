import json
import os
import sys

import requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = os.path.join(BASE, "pedidos.json")


def load_env_key(var):
    value = os.environ.get(var)
    if value:
        return value
    env_path = os.path.join(BASE, ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(var + "=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip()
    return None


def main():
    url = (load_env_key("SUPABASE_URL") or "").strip().rstrip("/")
    key = (load_env_key("SUPABASE_KEY") or "").strip()
    if not url or not key:
        print("Supabase nao configurado (falta SUPABASE_URL/KEY). Nada a migrar.")
        return 1

    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    with open(FILE, "r", encoding="utf-8") as f:
        local = json.load(f)
    if not isinstance(local, list) or not local:
        print("pedidos.json vazio; nada a migrar.")
        return 0

    response = requests.get(f"{url}/rest/v1/pedidos?select=mensagem,chat_id", headers=headers, timeout=20)
    response.raise_for_status()
    existing = {(row.get("mensagem"), row.get("chat_id")) for row in response.json()}

    pendentes = [entry for entry in local if (entry.get("mensagem"), entry.get("chat_id")) not in existing]
    if not pendentes:
        print(f"Historico ja migrado ({len(local)} linhas locais; 0 pendentes).")
        return 0

    erros = 0
    for entry in pendentes:
        payload = {k: v for k, v in entry.items() if v is not None}
        resp = requests.post(f"{url}/rest/v1/pedidos", headers=headers, json=payload, timeout=20)
        if resp.status_code not in (200, 201):
            erros += 1
            print(f"ERRO ({resp.status_code}) ao inserir {entry.get('data')} "
                  f"{entry.get('mensagem')}: {resp.text[:120]}")
        else:
            print(f"inserido: data={entry.get('data')} chat={entry.get('chat_id')} msg={entry.get('mensagem')}")

    if erros == 0:
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        print(f"Migracao concluida: {len(pendentes)} inseridos; pedidos.json esvaziado.")
        return 0
    print(f"Migracao PARCIAL: {len(pendentes) - erros} de {len(pendentes)} inseridos; pedidos.json mantido.")
    return 1


if __name__ == "__main__":
    sys.exit(main())