# BAPZX ACCESS / BAPZX RBAC v2.0.0
# Controle de acesso baseado em cargos (níveis) + permissões individuais.
#
# Regras:
#   - MASTER é atribuído SOMENTE por e-mails fixos (MASTER_EMAILS). Ninguém
#     pode criar, promover ou rebaixar um MASTER pela interface.
#   - Cada cargo tem um conjunto padrão de permissões.
#   - Cada usuário pode ter uma lista individual de permissões (users.permissoes)
#     que SUBSTITUI o padrão do cargo quando não vazia.
#   - A ordem de precedência para decidir permissões efetivas é sempre:
#       1) e-mail MASTER  -> tudo;
#       2) lista individual explícita (se não vazia);
#       3) padrão do cargo.

CARGOS = {
    "MASTER": 100,
    "ADMIN": 80,
    "MANAGER": 70,
    "FINANCEIRO": 60,
    "OPERADOR": 50,
    "MODERADOR": 40,
    "SUPORTE": 30,
    "CLIENTE": 10,
}

CARGOS_LABEL = {
    "MASTER": "Master",
    "ADMIN": "Admin",
    "MANAGER": "Manager",
    "FINANCEIRO": "Financeiro",
    "OPERADOR": "Operador",
    "MODERADOR": "Moderador",
    "SUPORTE": "Suporte",
    "CLIENTE": "Cliente",
}

# Permissões disponíveis (rótulos usados no painel de usuários)
PERMISSOES_LABEL = {
    "ver_dashboard": "Ver dashboard",
    "ver_pedidos": "Ver pedidos",
    "marcar_pagamento": "Marcar pagamento (pago)",
    "marcar_entrega": "Marcar entrega (entregue)",
    "ver_clientes": "Ver clientes",
    "gerenciar_clientes": "Editar/bloquear clientes",
    "ver_pagamentos": "Ver pagamentos e valores",
    "ver_itens": "Ver itens",
    "gerenciar_itens": "Criar/editar/excluir itens",
    "ver_tickets": "Ver tickets",
    "responder_tickets": "Responder tickets",
    "encerrar_tickets": "Encerrar tickets",
    "excluir_tickets": "Excluir tickets",
    "ver_config": "Ver configurações",
    "editar_config": "Editar configurações",
    "ver_grupos": "Ver grupos",
    "gerenciar_grupos": "Gerenciar grupos",
    "ver_cupons": "Ver cupons",
    "gerenciar_cupons": "Criar/editar/ativar/excluir cupons",
    "ver_usuarios": "Ver usuários",
    "gerenciar_usuarios": "Gerenciar usuários",
    "ver_audit": "Ver auditoria",
}

PERM_TRACK = {
    "ver_dashboard": "dash",
    "ver_pedidos": "pedidos",
    "marcar_pagamento": "pagamentos",
    "marcar_entrega": "pedidos",
    "ver_clientes": "clientes",
    "gerenciar_clientes": "clientes",
    "ver_pagamentos": "pagamentos",
    "ver_itens": "itens",
    "gerenciar_itens": "itens",
    "ver_tickets": "tickets",
    "responder_tickets": "tickets",
    "encerrar_tickets": "tickets",
    "excluir_tickets": "tickets",
    "ver_config": "config",
    "editar_config": "config",
    "ver_grupos": "grupos",
    "gerenciar_grupos": "grupos",
    "ver_cupons": "cupons",
    "gerenciar_cupons": "cupons",
    "ver_usuarios": "usuarios",
    "gerenciar_usuarios": "usuarios",
    "ver_audit": "audit",
}

# Permissões padrão por cargo
_PADRAO = {
    "ADMIN": [
        "ver_dashboard", "ver_pedidos", "marcar_pagamento", "marcar_entrega",
        "ver_clientes", "gerenciar_clientes", "ver_pagamentos",
        "ver_itens", "gerenciar_itens",
        "ver_tickets", "responder_tickets", "encerrar_tickets", "excluir_tickets",
        "ver_config", "ver_grupos", "gerenciar_grupos", "ver_usuarios", "ver_audit",
        "ver_cupons", "gerenciar_cupons",
    ],
    "MANAGER": [
        "ver_dashboard", "ver_pedidos", "marcar_pagamento", "marcar_entrega",
        "ver_clientes", "gerenciar_clientes",
        "ver_itens", "gerenciar_itens",
        "ver_tickets", "responder_tickets", "encerrar_tickets",
        "ver_grupos", "gerenciar_grupos",
        "ver_cupons", "gerenciar_cupons",
    ],
    "FINANCEIRO": [
        "ver_dashboard", "ver_pedidos", "ver_pagamentos", "marcar_pagamento",
    ],
    "OPERADOR": [
        "ver_pedidos", "marcar_entrega", "ver_clientes",
        "ver_tickets", "responder_tickets",
    ],
    "MODERADOR": [
        "ver_pedidos", "ver_clientes", "gerenciar_clientes",
        "ver_tickets", "responder_tickets",
    ],
    "SUPORTE": [
        "ver_pedidos", "ver_tickets", "responder_tickets",
    ],
    "CLIENTE": [],
}

ALL_PERMISSOES = frozenset(PERMISSOES_LABEL.keys())


def nivel(cargo):
    return CARGOS.get((cargo or "").upper(), 0)


def cargo_valido(cargo):
    return (cargo or "").upper() in CARGOS


def cargo_label(cargo):
    return CARGOS_LABEL.get((cargo or "").upper(), (cargo or "").title())


def perms_padrao(cargo):
    cargo = (cargo or "").upper()
    return frozenset(_PADRAO.get(cargo, []))


def perms_efetivas(cargo, explicitas=None):
    """Permissões efetivas: lista individual (se não vazia) ou padrão do cargo."""
    cargo = (cargo or "").upper()
    if cargo == "MASTER":
        return ALL_PERMISSOES
    if explicitas:
        validadas = {p for p in explicitas if p in ALL_PERMISSOES}
        if validadas:
            return frozenset(validadas)
    return perms_padrao(cargo)


def eh_master(email, master_emails):
    return (email or "").strip().lower() in {e.strip().lower() for e in (master_emails or []) if e.strip()}


def tem_perm(cargo, perms, *requeridas):
    """True se cargo/permissões atendem TODAS as requeridas. MASTER sempre True."""
    cargo = (cargo or "").upper()
    if cargo == "MASTER":
        return True
    perms = set(perms or [])
    return all(p in perms for p in requeridas)


def tem_qualquer_perm(cargo, perms, *opcoes):
    """True se MASTER ou se tem ao menos UMA das permissões listadas."""
    cargo = (cargo or "").upper()
    if cargo == "MASTER":
        return True
    perms = set(perms or [])
    return any(p in perms for p in opcoes)