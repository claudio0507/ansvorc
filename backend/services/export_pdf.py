"""
Geração de PDF de proposta comercial via WeasyPrint.

Todas as formatações monetárias usam Decimal para evitar erros de float.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from html import escape

from backend.models.orcamento_models import Cliente, Orcamento, OrcamentoItem

_BLOCO_LABEL: dict[str, str] = {
    "servicos": "Serviços",
    "produtos": "Produtos",
    "operacional": "Operacional",
    "excepcionais": "Excepcionais",
}

_BLOCO_ORDER = ["servicos", "produtos", "operacional", "excepcionais"]


def _fmt_brl(value: Decimal | None) -> str:
    """Formata um Decimal como moeda brasileira (sem símbolo, com separadores)."""
    if value is None:
        return "—"
    # Força 2 casas decimais e formata com separadores BR
    quantized = value.quantize(Decimal("0.01"))
    parts = (
        f"{abs(quantized):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    return f"R$ {parts}" if quantized >= 0 else f"R$ -{parts}"


def _fmt_pct(value: Decimal | None) -> str:
    if value is None:
        return "—"
    pct = (value * Decimal("100")).quantize(Decimal("0.01"))
    return f"{pct}%"


def _fmt_qty(value: Decimal | None) -> str:
    if value is None:
        return "—"
    q = value.quantize(Decimal("0.01"))
    return str(q)


def _build_html(orc: Orcamento, itens: list[OrcamentoItem], cliente: Cliente) -> str:
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    criado_em_str = orc.criado_em.strftime("%d/%m/%Y") if orc.criado_em else hoje
    reidi_label = "Sim (REIDI)" if orc.beneficio_reidi else "Não"

    # Escapa todos os dados vindos do banco para evitar injeção HTML no PDF
    e_numero_proposta = escape(str(orc.numero_proposta or ""))
    e_versao = escape(str(orc.versao or ""))
    e_descricao_obra = escape(str(orc.descricao_obra or "—"))
    e_uf_execucao = escape(str(orc.uf_execucao or ""))
    e_status = escape(str(orc.status or "").capitalize())
    e_razao_social = escape(str(cliente.razao_social or "—"))
    e_cnpj = escape(str(cliente.cnpj or "—"))
    e_contato_nome = escape(str(cliente.contato_nome or "—"))
    e_contato_email = escape(str(cliente.contato_email or "—"))
    e_contato_telefone = escape(str(cliente.contato_telefone or "—"))
    e_uf_sede = escape(str(cliente.uf_sede or "—"))

    # Agrupa itens por bloco preservando a ordem definida
    blocos: dict[str, list[OrcamentoItem]] = {}
    for b in _BLOCO_ORDER:
        grupo = [i for i in itens if i.bloco == b]
        if grupo:
            blocos[b] = grupo

    # Gera linhas da tabela por bloco
    tabela_html = ""
    for bloco_key, bloco_itens in blocos.items():
        label = _BLOCO_LABEL.get(bloco_key, bloco_key.capitalize())
        tabela_html += f"""
        <tr class="bloco-header">
            <td colspan="8">{escape(label)}</td>
        </tr>"""
        for item in bloco_itens:
            bdi_pct = _fmt_pct(item.bdi_taxa)
            tabela_html += f"""
        <tr>
            <td class="center">{escape(label[:3].upper())}</td>
            <td>{escape(str(item.descricao or ""))}</td>
            <td class="center">{escape(str(item.unidade_medida or ""))}</td>
            <td class="right">{_fmt_qty(item.quantidade)}</td>
            <td class="right">{_fmt_brl(item.custo_direto_unitario)}</td>
            <td class="center">{bdi_pct}</td>
            <td class="right">{_fmt_brl(item.preco_venda_unitario)}</td>
            <td class="right">{_fmt_brl(item.preco_venda_total)}</td>
        </tr>"""

    margem_pct = _fmt_pct(orc.margem_liquida_real)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4 landscape;
    margin: 18mm 14mm 18mm 14mm;
  }}
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}
  body {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 9pt;
    color: #1e293b;
    background: #ffffff;
  }}

  /* ── Cabeçalho ── */
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 3px solid #1e40af;
    padding-bottom: 8px;
    margin-bottom: 12px;
  }}
  .header-left {{
    font-size: 13pt;
    font-weight: bold;
    color: #1e40af;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .header-left .subtitle {{
    font-size: 8pt;
    font-weight: normal;
    color: #64748b;
    text-transform: none;
    letter-spacing: normal;
    margin-top: 2px;
  }}
  .header-right {{
    text-align: right;
    font-size: 8.5pt;
    color: #475569;
  }}
  .header-right .proposta-num {{
    font-size: 11pt;
    font-weight: bold;
    color: #1e40af;
  }}

  /* ── Seções de dados ── */
  .secao {{
    margin-bottom: 10px;
  }}
  .secao-titulo {{
    background: #1e40af;
    color: #ffffff;
    font-weight: bold;
    font-size: 8pt;
    padding: 3px 7px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 4px;
  }}
  .dados-grid {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px 20px;
    padding: 4px 7px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 2px;
  }}
  .dado {{
    min-width: 200px;
  }}
  .dado-label {{
    font-size: 7pt;
    color: #64748b;
    text-transform: uppercase;
    font-weight: bold;
  }}
  .dado-valor {{
    font-size: 9pt;
    color: #1e293b;
  }}

  /* ── Tabela de itens ── */
  .tabela-titulo {{
    background: #1e40af;
    color: #ffffff;
    font-weight: bold;
    font-size: 8pt;
    padding: 3px 7px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 0;
  }}
  table.itens {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 10px;
    font-size: 8pt;
  }}
  table.itens thead tr {{
    background: #1e40af;
    color: #ffffff;
  }}
  table.itens thead th {{
    padding: 4px 5px;
    text-align: center;
    font-weight: bold;
    font-size: 7.5pt;
    border: 1px solid #1e3a8a;
  }}
  table.itens tbody tr:nth-child(even) {{
    background: #f8fafc;
  }}
  table.itens tbody tr:nth-child(odd) {{
    background: #ffffff;
  }}
  table.itens tbody td {{
    padding: 3px 5px;
    border: 1px solid #e2e8f0;
    vertical-align: middle;
  }}
  table.itens tbody tr.bloco-header td {{
    background: #dbeafe;
    color: #1e40af;
    font-weight: bold;
    font-size: 8pt;
    padding: 4px 7px;
    border-top: 1.5px solid #93c5fd;
    border-bottom: 1px solid #93c5fd;
  }}
  .center {{ text-align: center; }}
  .right  {{ text-align: right; }}
  .col-bloco {{ width: 5%; }}
  .col-desc  {{ width: 30%; }}
  .col-und   {{ width: 5%; }}
  .col-qtd   {{ width: 7%; }}
  .col-custo {{ width: 12%; }}
  .col-bdi   {{ width: 7%; }}
  .col-pvunit {{ width: 12%; }}
  .col-pvtot  {{ width: 12%; }}

  /* ── Rodapé / Totais ── */
  .rodape {{
    margin-top: 6px;
    border-top: 2px solid #1e40af;
    padding-top: 8px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}
  .rodape-info {{
    font-size: 7.5pt;
    color: #64748b;
  }}
  .totais {{
    text-align: right;
  }}
  .total-proposta {{
    font-size: 13pt;
    font-weight: bold;
    color: #1e40af;
  }}
  .total-label {{
    font-size: 8pt;
    color: #475569;
    text-transform: uppercase;
    font-weight: bold;
  }}
  .margem-label {{
    font-size: 8.5pt;
    color: #059669;
    font-weight: bold;
    margin-top: 2px;
  }}
</style>
</head>
<body>

<!-- Cabeçalho -->
<div class="header">
  <div class="header-left">
    Alta Noroeste Sinalização Viária
    <div class="subtitle">Proposta Comercial de Obra Viária</div>
  </div>
  <div class="header-right">
    <div class="proposta-num">Proposta {e_numero_proposta}</div>
    <div>Versão {e_versao} &nbsp;|&nbsp; Data: {criado_em_str}</div>
  </div>
</div>

<!-- Dados do Cliente -->
<div class="secao">
  <div class="secao-titulo">Dados do Cliente</div>
  <div class="dados-grid">
    <div class="dado">
      <div class="dado-label">Razão Social</div>
      <div class="dado-valor">{e_razao_social}</div>
    </div>
    <div class="dado">
      <div class="dado-label">CNPJ</div>
      <div class="dado-valor">{e_cnpj}</div>
    </div>
    <div class="dado">
      <div class="dado-label">Contato</div>
      <div class="dado-valor">{e_contato_nome}</div>
    </div>
    <div class="dado">
      <div class="dado-label">E-mail</div>
      <div class="dado-valor">{e_contato_email}</div>
    </div>
    <div class="dado">
      <div class="dado-label">Telefone</div>
      <div class="dado-valor">{e_contato_telefone}</div>
    </div>
    <div class="dado">
      <div class="dado-label">UF Sede</div>
      <div class="dado-valor">{e_uf_sede}</div>
    </div>
  </div>
</div>

<!-- Dados da Obra -->
<div class="secao">
  <div class="secao-titulo">Dados da Obra</div>
  <div class="dados-grid">
    <div class="dado" style="min-width:340px;">
      <div class="dado-label">Descrição da Obra</div>
      <div class="dado-valor">{e_descricao_obra}</div>
    </div>
    <div class="dado">
      <div class="dado-label">UF de Execução</div>
      <div class="dado-valor">{e_uf_execucao}</div>
    </div>
    <div class="dado">
      <div class="dado-label">Benefício REIDI</div>
      <div class="dado-valor">{reidi_label}</div>
    </div>
    <div class="dado">
      <div class="dado-label">Status</div>
      <div class="dado-valor">{e_status}</div>
    </div>
  </div>
</div>

<!-- Tabela de Itens -->
<div class="tabela-titulo">Composição do Orçamento</div>
<table class="itens">
  <thead>
    <tr>
      <th class="col-bloco">Bloco</th>
      <th class="col-desc">Descrição</th>
      <th class="col-und">Und</th>
      <th class="col-qtd">Qtd</th>
      <th class="col-custo">Custo Unit</th>
      <th class="col-bdi">BDI%</th>
      <th class="col-pvunit">Preço Unit</th>
      <th class="col-pvtot">Preço Total</th>
    </tr>
  </thead>
  <tbody>
    {tabela_html}
  </tbody>
</table>

<!-- Rodapé -->
<div class="rodape">
  <div class="rodape-info">
    <div>Gerado em: {hoje}</div>
    <div>Versão da proposta: {e_versao}</div>
    <div>Número da proposta: {e_numero_proposta}</div>
  </div>
  <div class="totais">
    <div class="total-label">Total da Proposta</div>
    <div class="total-proposta">{_fmt_brl(orc.total_proposta)}</div>
    <div class="margem-label">Margem Líquida Real: {margem_pct}</div>
  </div>
</div>

</body>
</html>"""

    return html


def gerar_pdf_proposta(
    orc: Orcamento,
    itens: list[OrcamentoItem],
    cliente: Cliente,
) -> bytes:
    """Gera o PDF da proposta e retorna os bytes.

    Não acessa URLs externas — utiliza apenas CSS inline.
    O import de weasyprint é lazy para não quebrar o startup em ambientes
    sem as bibliotecas nativas GTK/Pango instaladas.
    """
    from weasyprint import HTML  # lazy import — nativas GTK opcionais em dev

    html_str = _build_html(orc, itens, cliente)
    pdf_bytes: bytes = HTML(string=html_str).write_pdf()
    return pdf_bytes
