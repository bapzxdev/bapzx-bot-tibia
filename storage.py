import json
import os

import requests


class OrderStore:
    def __init__(self, file_path, url=None, key=None):
        self.file_path = file_path
        self.url = (url or os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
        self.key = (key or os.environ.get("SUPABASE_KEY") or "").strip()
        self.table = "pedidos"

    @property
    def remote(self):
        return bool(self.url and self.key)

    def _headers(self):
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

    def save(self, entry):
        if self.remote:
            payload = {k: v for k, v in entry.items() if v is not None}
            try:
                headers = {**self._headers(), "Prefer": "return=representation"}
                response = requests.post(
                    f"{self.url}/rest/v1/{self.table}",
                    headers=headers,
                    json=payload,
                    timeout=15,
                )
                if response.status_code not in (200, 201):
                    raise RuntimeError(f"Supabase {response.status_code}: {response.text[:200]}")
                rows = response.json()
                if isinstance(rows, list) and rows:
                    return rows[0]
                return entry
            except Exception as error:
                print(f"[storage] Supabase falhou, gravando em arquivo: {error}")
        return self._append_file(entry)

    def _append_file(self, entry):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                orders = json.load(f)
            if not isinstance(orders, list):
                orders = []
        except Exception:
            orders = []
        entry = dict(entry)
        entry.setdefault("id", (max((o.get("id") or 0 for o in orders), default=0)) + 1)
        orders.append(entry)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
        return entry

    def set_status(self, order_id, status, timestamp_field=None, timestamp=None):
        if not self.remote:
            print("[storage] set_status exige Supabase configurado")
            return None
        payload = {"status": status}
        if timestamp_field and timestamp:
            payload[timestamp_field] = timestamp
        response = requests.patch(
            f"{self.url}/rest/v1/{self.table}?id=eq.{order_id}",
            headers=self._headers(),
            json=payload,
            timeout=15,
        )
        if response.status_code not in (200, 204):
            raise RuntimeError(f"Supabase {response.status_code}: {response.text[:200]}")
        return status

    def save_email(self, order_id, email):
        email = (email or "").strip().lower()
        if self.remote:
            try:
                return self.update(order_id, {"email": email})
            except Exception as error:
                print(f"[storage] email nao salvo na nuvem: {error}")
        order = self.find(order_id)
        if order:
            order["email"] = email
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    orders = json.load(f)
                for i, item in enumerate(orders):
                    if item.get("id") == order_id:
                        orders[i]["email"] = email
                        break
                else:
                    return None
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(orders, f, ensure_ascii=False, indent=2)
                return email
            except Exception:
                return None
        return None

    def update(self, order_id, fields):
        if not self.remote:
            print("[storage] update exige Supabase configurado")
            return None
        response = requests.patch(
            f"{self.url}/rest/v1/{self.table}?id=eq.{order_id}",
            headers=self._headers(),
            json=fields,
            timeout=15,
        )
        if response.status_code not in (200, 204):
            raise RuntimeError(f"Supabase {response.status_code}: {response.text[:200]}")
        return fields

    def find(self, order_id):
        for order in self.list():
            if order.get("id") == order_id:
                return order
        return None

    def list(self):
        if self.remote:
            try:
                orders = []
                start = 0
                while True:
                    headers = {
                        **self._headers(),
                        "Range": f"{start}-{start + 999}",
                    }
                    response = requests.get(
                        f"{self.url}/rest/v1/{self.table}?select=*&order=data.asc",
                        headers=headers,
                        timeout=20,
                    )
                    if response.status_code != 200:
                        raise RuntimeError(f"Supabase {response.status_code}: {response.text[:200]}")
                    rows = response.json()
                    orders.extend(rows)
                    if not rows or len(rows) < 1000:
                        break
                    start += len(rows)
                return orders
            except Exception as error:
                print(f"[storage] Supabase indisponivel no list: {error}")
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
        except Exception:
            return []

    def count(self):
        if self.remote:
            try:
                response = requests.get(
                    f"{self.url}/rest/v1/{self.table}?select=id",
                    headers={**self._headers(), "Prefer": "count=exact", "Range": "0-0"},
                    timeout=15,
                )
                total = response.headers.get("content-range", "").split("/")[-1]
                if total.isdigit():
                    return int(total)
            except Exception as error:
                print(f"[storage] Supabase indisponivel no count: {error}")
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return len(json.load(f))
        except Exception:
            return 0