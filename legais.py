# BAPZX v2.0.0 - Páginas legais (LGPD) e PDF
# Conteúdo das políticas: Privacidade, Termos de Uso e Reembolso.
# PDF gerado com reportlab (requirements.txt).

from io import BytesIO


BRAND = "BAPZX"
WHATSAPP_DISPLAY = "(19) 99181-3598"
WHATSAPP_LINK = "https://wa.me/5519991813598"


def _bloco_sections(sections):
    """Sections: lista de (titulo, [paragrafos])."""
    out = ""
    for titulo, paragrafos in sections:
        out += f"<h2>{titulo}</h2>"
        out += "".join(f"<p>{p}</p>" for p in paragrafos)
    return out


def privacidade_html():
    sections = [
        (
            "1. Quem somos",
            [
                "Estas regras valem para o serviço de vendas de itens, moedas e "
                "intermediações in-game oferecido pela marca BAPZX, atuando em jogos "
                "como Tibia e em comunidades como Coroa, Rubinot, Pokepixel e PokeIdle.",
            ],
        ),
        (
            "2. Dados que coletamos",
            [
                "Ao usar nossos serviços, podemos coletar e tratar: e-mail (contas "
                "Google usadas para login), nome, personagens e mundos informados no "
                "perfil, registros de pedidos, conversas de suporte e dados técnicos "
                "como IP e páginas visitadas no site.",
            ],
        ),
        (
            "3. Finalidades do tratamento",
            [
                "Seus dados são usados para: atender pedidos e entregas, confirmar "
                "pagamentos, oferecer suporte por ticket ou WhatsApp, prevenir fraudes, "
                "cumprir obrigações legais e melhorar nossos serviços.",
            ],
        ),
        (
            "4. Base legal",
            [
                "Tratamos seus dados com base na LGPD (Lei nº 13.709/2018): mediante "
                "seu consentimento, para a execução do contrato (pedidos), para o "
                "exercício regular de direitos e para o atendimento de obrigações legais.",
            ],
        ),
        (
            "5. Com quem compartilhamos",
            [
                "Não vendemos seus dados. Compartilhamos informações apenas quando "
                "necessário com provedores de infraestrutura (hospedagem, pagamento) e "
                "autoridades, quando exigido por lei.",
            ],
        ),
        (
            "6. Seus direitos",
            [
                "Você pode, a qualquer momento: acessar seus dados, corrigi-los, pedir "
                "a portabilidade, a eliminação e revogar o consentimento. Para exercer "
                "seus direitos, fale conosco pelo WhatsApp " + WHATSAPP_DISPLAY + ".",
            ],
        ),
        (
            "7. Segurança",
            [
                "Adotamos medidas técnicas e organizacionais para proteger seus dados "
                "contra acessos não autorizados, perda e alteração. Sessões usam HTTPS e "
                "senhas/tokens nunca são gravados em texto plano.",
            ],
        ),
        (
            "8. Armazenamento",
            [
                "Os dados são armazenados enquanto a conta estiver ativa e pelos prazos "
                "legais cabíveis. Ao solicitar a exclusão, removemos ou anonimizamos os "
                "dados, exceto o que a lei exigir que conservemos.",
            ],
        ),
        (
            "9. Menores de idade",
            [
                "Nossos serviços exigem idade mínima para uso (maiores de 18 anos). Não "
                "coletamos conscientemente dados de menores sem autorização dos pais ou "
                "responsáveis.",
            ],
        ),
        (
            "10. Alterações desta política",
            [
                "Podemos atualizar esta Política a qualquer momento. A versão vigente "
                "estará sempre disponível nesta página, com a data de atualização.",
            ],
        ),
        (
            "11. Contato (Encarregado de dados)",
            [
                "Dúvidas sobre privacidade e proteção de dados: WhatsApp " + WHATSAPP_DISPLAY +
                " ou pelo nosso site oficial.",
            ],
        ),
    ]
    return _bloco_sections(sections)


def termos_html():
    sections = [
        (
            "1. Do serviço",
            [
                "A BAPZX intermedia e realiza vendas de itens e moedas in-game. Ao "
                "comprar, você declara ter capacidade legal e estar de acordo com os "
                "termos do jogo e desta página.",
            ],
        ),
        (
            "2. Sobre os pedidos",
            [
                "Os pedidos são atendidos após a confirmação do pagamento, em até 10 "
                "minutos na maioria dos casos. Prazos maiores podem ocorrer em horários "
                "de alta demanda e serão comunicados.",
            ],
        ),
        (
            "3. Valores e pagamentos",
            [
                "Os preços exibidos (em reais) incluem as taxas indicadas. O pagamento é "
                "feito via Pix e a confirmação é automática quando possível.",
            ],
        ),
        (
            "4. Comunicação",
            [
                "O atendimento oficial é realizado pelo Telegram e pelo WhatsApp. "
                "Desconfie de contatos solicitando senhas ou dados além do necessário.",
            ],
        ),
        (
            "5. Conduta proibida",
            [
                "É proibido usar nossos serviços para fraudes, invasões ou qualquer "
                "atividade ilícita. Infrações podem levar ao bloqueio da conta e ao "
                "cancelamento de pedidos.",
            ],
        ),
        (
            "6. Limitação de responsabilidade",
            [
                "Fazemos o melhor para entregar corretamente, mas não nos "
                "responsabilizamos por decisões unilaterais da administração dos jogos "
                "sobre contas, itens ou moedas negociados.",
            ],
        ),
        (
            "7. Contato",
            [
                "Para dúvidas sobre estes Termos, fale conosco pelo WhatsApp " + WHATSAPP_DISPLAY + ".",
            ],
        ),
    ]
    return _bloco_sections(sections)


def reembolso_html():
    sections = [
        (
            "1. Direito de arrependimento",
            [
                "Conforme o CDC, você pode solicitar o reembolso em até 7 dias corridos "
                "após a compra, caso o pedido ainda não tenha sido entregue.",
            ],
        ),
        (
            "2. Entrega já realizada",
            [
                "Após a entrega, o pedido é considerado concluído. Reembolsos por itens "
                "ou moedas já entregues são analisados caso a caso e dependem de "
                "comprovação de problema na entrega.",
            ],
        ),
        (
            "3. Como solicitar",
            [
                "Para pedir reembolso, abra um chamado, fale com o suporte ou envie "
                "mensagem no WhatsApp " + WHATSAPP_DISPLAY + " informando o número do pedido "
                "e o motivo.",
            ],
        ),
        (
            "4. Prazo de devolução",
            [
                "Estando aprovado, o reembolso é processado na mesma forma de pagamento "
                "em até 7 dias úteis.",
            ],
        ),
        (
            "5. Casos não reembolsáveis",
            [
                "Compras concluídas (entrega realizada) sem defeito, valores perdidos por "
                "culpa do jogador (troca/transferência para a conta errada) e pedidos "
                "cancelados por violação dos Termos não são reembolsáveis.",
            ],
        ),
    ]
    return _bloco_sections(sections)


def _pagina_legal_html(titulo, intro, conteudo, updated):
    return (
        "<section>"
        "<h2 style='font-size:20px'>" + titulo + "</h2>"
        "<p class='size-note'>Atualizado em: " + updated + "</p>"
        "<p style='color:#8ea0b8'>" + intro + "</p>"
        + conteudo
        + "<p style='margin-top:18px'><a class='big' href='/privacidade/pdf' "
        "style='background:#60a5fa;color:#0f172a'>Baixar PDF da Política de Privacidade</a></p>"
        "</section>"
    )


def _render_legal_page(titulo, pag, intro, updated, top=""):
    body = _pagina_legal_html(titulo, intro, pag, updated)
    return body, top


# ---------------------------------------------------------------------------
# PDF (reportlab)
# ---------------------------------------------------------------------------
def privacidade_pdf_bytes():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        PageTemplate,
        Paragraph,
        Spacer,
    )

    estilos = {
        "titulo": ParagraphStyle(
            "titulo",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=21,
            textColor="#0f172a",
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=16,
            textColor="#1e293b",
            spaceBefore=10,
            spaceAfter=3,
        ),
        "p": ParagraphStyle(
            "p",
            fontName="Helvetica",
            fontSize=10,
            leading=14.5,
            textColor="#334155",
            alignment=TA_LEFT,
            spaceAfter=5,
        ),
        "rodape": ParagraphStyle(
            "rodape",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor="#94a3b8",
        ),
    }

    buf = BytesIO()

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColorRGB(0.58, 0.66, 0.78)
        canvas.drawString(
            20 * mm,
            12 * mm,
            "BAPZX - Política de Privacidade (LGPD) - " + WHATSAPP_DISPLAY,
        )
        canvas.restoreState()

    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="pag", frames=[frame], onPage=rodape)])

    story = [Paragraph("BAPZX - Política de Privacidade (LGPD)", estilos["titulo"])]
    linha = None
    import re
    for tag in re.split(r"<h2>|</h2>|<p>|</p>", privacidade_html()):
        tag = tag.strip()
        if not tag:
            continue
        if tag in ("", None):
            continue
        if tag.startswith("<") or tag.endswith(">"):
            continue
        if tag.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "11.")):
            story.append(Paragraph(tag, estilos["h2"]))
            linha = None
        else:
            story.append(Paragraph(tag, estilos["p"]))
            linha = None
    story.append(Spacer(1, 6 * mm))
    doc.build(story)
    return buf.getvalue()