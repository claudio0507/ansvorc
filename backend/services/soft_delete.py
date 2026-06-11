"""Soft-delete seguro com verificação de dependências (BLOCO 3.2).

Regra: NUNCA excluir fisicamente itens com FK ativa. Se houver dependência,
retorna erro. Se não houver, marca ativo=False.

Uso nos routers:
    from backend.services.soft_delete import soft_delete, DependenciaError
    try:
        soft_delete(db, obj, verificador_func)
        db.commit()
    except DependenciaError as e:
        raise HTTPException(409, str(e))
"""

from sqlalchemy.orm import Session

from backend.models.bd_models import (
    BdBDI, BdRH, BdEPI, BdFerramental, BdFrotas, BdMateriais,
    BdEstrutura, BdDespesas,
)
from backend.models.ficha_models import (
    FichaEquipe, FichaEquipeItem, FichaProduto, FichaProdutoItem,
    FichaServico, FichaServicoRecurso,
)
from backend.models.orcamento_models import OrcamentoItem
from backend.models.param_models import UnidadeMedida, ParametroSeguimento, ParametroTipoEstrutura
from backend.models.produto_models import Produto, Componente, ItemFicha
from backend.models.extra_models import UsuarioOrcamentista


class DependenciaError(Exception):
    """Erro ao tentar excluir item com dependências ativas."""
    pass


def soft_delete(db: Session, obj, verificador=None) -> bool:
    """Executa soft-delete (ativo=False) após verificar dependências.

    Args:
        db: Sessão SQLAlchemy
        obj: Instância do model a ser excluído
        verificador: Callable(db, obj) → (bool, str). Retorna (pode_excluir, mensagem)

    Returns:
        True se o soft-delete foi executado

    Raises:
        DependenciaError: Se houver dependências que impeçam a exclusão
    """
    if verificador:
        pode, msg = verificador(db, obj)
        if not pode:
            raise DependenciaError(msg)

    obj.ativo = False
    return True


# ── Verificadores de dependência ──────────────────────────────────────────────

def verificar_bd_rh(db: Session, obj: BdRH) -> tuple[bool, str]:
    count = db.query(FichaEquipeItem).filter(
        FichaEquipeItem.rh_id == obj.id,
        FichaEquipeItem.ficha.has(FichaEquipe.ativo == True),
    ).count()
    if count:
        return False, (
            f"Não é possível excluir '{obj.cargo}'. "
            f"Ele é usado em {count} ficha(s) de equipe ativa(s). "
            f"Remova-o das fichas primeiro ou inative-o."
        )
    return True, ""


def verificar_bd_epi(db: Session, obj: BdEPI) -> tuple[bool, str]:
    count = db.query(FichaEquipeItem).filter(
        FichaEquipeItem.epi_id == obj.id,
        FichaEquipeItem.ficha.has(FichaEquipe.ativo == True),
    ).count()
    if count:
        return False, (
            f"Não é possível excluir '{obj.item}'. "
            f"Ele é usado em {count} ficha(s) de equipe ativa(s). "
            f"Remova-o das fichas primeiro ou inative-o."
        )
    return True, ""


def verificar_bd_ferramental(db: Session, obj: BdFerramental) -> tuple[bool, str]:
    count = db.query(FichaServicoRecurso).filter(
        FichaServicoRecurso.ferramental_id == obj.id,
        FichaServicoRecurso.ficha.has(FichaServico.ativo == True),
    ).count()
    if count:
        return False, (
            f"Não é possível excluir este ferramental. "
            f"Ele é usado em {count} ficha(s) de serviço ativa(s). "
            f"Remova-o das fichas primeiro ou inative-o."
        )
    return True, ""


def verificar_bd_frotas(db: Session, obj: BdFrotas) -> tuple[bool, str]:
    count = db.query(FichaServicoRecurso).filter(
        FichaServicoRecurso.frota_id == obj.id,
        FichaServicoRecurso.ficha.has(FichaServico.ativo == True),
    ).count()
    if count:
        return False, (
            f"Não é possível excluir esta frota. "
            f"Ela é usada em {count} ficha(s) de serviço ativa(s). "
            f"Remova-a das fichas primeiro ou inative-a."
        )
    return True, ""


def verificar_bd_materiais(db: Session, obj: BdMateriais) -> tuple[bool, str]:
    count = db.query(FichaProdutoItem).filter(
        FichaProdutoItem.material_id == obj.id,
        FichaProdutoItem.ficha.has(FichaProduto.ativo == True),
    ).count()
    if count:
        return False, (
            f"Não é possível excluir '{obj.material}'. "
            f"Ele é usado em {count} ficha(s) de produto ativa(s). "
            f"Remova-o das fichas primeiro ou inative-o."
        )
    return True, ""


def verificar_bd_estrutura(db: Session, obj: BdEstrutura) -> tuple[bool, str]:
    count = db.query(OrcamentoItem).filter(
        OrcamentoItem.tipo_origem == "operacional",
        OrcamentoItem.descricao.like(f"%{obj.item}%"),
    ).count()
    if count:
        return False, (
            f"Não é possível excluir '{obj.item}'. "
            f"Ele consta em {count} orçamento(s). Exclusão não permitida."
        )
    return True, ""


def verificar_unidade_medida(db: Session, obj: UnidadeMedida) -> tuple[bool, str]:
    from backend.models.produto_models import Produto, Componente
    count_prod = db.query(Produto).filter(Produto.unidade_id == obj.id).count()
    count_comp = db.query(Componente).filter(Componente.unidade_id == obj.id).count()
    total = count_prod + count_comp
    if total:
        return False, (
            f"Não é possível excluir a unidade '{obj.sigla}'. "
            f"Ela é usada em {total} produto(s)/componente(s). "
            f"Substitua-a nos cadastros primeiro ou inative-a."
        )
    return True, ""


def verificar_seguimento(db: Session, obj: ParametroSeguimento) -> tuple[bool, str]:
    feq = db.query(FichaEquipe).filter(
        FichaEquipe.seguimento == obj.nome, FichaEquipe.ativo == True
    ).count()
    fsv = db.query(FichaServico).filter(
        FichaServico.seguimento == obj.nome, FichaServico.ativo == True
    ).count()
    total = feq + fsv
    if total:
        return False, (
            f"Não é possível excluir o seguimento '{obj.nome}'. "
            f"Ele é usado em {total} ficha(s) ativa(s). "
            f"Substitua-o nas fichas primeiro ou inative-o."
        )
    return True, ""


def verificar_tipo_estrutura(db: Session, obj: ParametroTipoEstrutura) -> tuple[bool, str]:
    count = db.query(BdEstrutura).filter(
        BdEstrutura.tipo == obj.nome, BdEstrutura.ativo == True
    ).count()
    if count:
        return False, (
            f"Não é possível excluir o tipo '{obj.nome}'. "
            f"Ele é usado em {count} item(ns) de estrutura operacional. "
            f"Substitua-o primeiro ou inative-o."
        )
    return True, ""


def verificar_produto(db: Session, obj: Produto) -> tuple[bool, str]:
    itens = db.query(OrcamentoItem).filter(
        OrcamentoItem.produto_id == obj.id,
    ).count()
    fichas = db.query(ItemFicha).filter(
        ItemFicha.produto_id == obj.id,
    ).count()
    total = itens + fichas
    if total:
        return False, (
            f"Não é possível excluir '{obj.nome}'. "
            f"Ele consta em {itens} orçamento(s) e {fichas} ficha(s) técnica(s). "
            f"Exclusão não permitida. Inative-o se necessário."
        )
    return True, ""


def verificar_componente(db: Session, obj: Componente) -> tuple[bool, str]:
    fichas = db.query(ItemFicha).filter(
        ItemFicha.componente_id == obj.id,
    ).count()
    if fichas:
        return False, (
            f"Não é possível excluir '{obj.nome}'. "
            f"Ele é usado em {fichas} ficha(s) técnica(s). "
            f"Remova-o das fichas primeiro ou inative-o."
        )
    return True, ""


def verificar_ficha_equipe(db: Session, obj: FichaEquipe) -> tuple[bool, str]:
    count = db.query(FichaServicoRecurso).filter(
        FichaServicoRecurso.ficha_equipe_id == obj.id,
        FichaServicoRecurso.ficha.has(FichaServico.ativo == True),
    ).count()
    if count:
        return False, (
            f"Não é possível excluir a ficha de equipe '{obj.codigo}'. "
            f"Ela é usada em {count} ficha(s) de serviço ativa(s). "
            f"Remova-a dos serviços primeiro ou inative-a."
        )
    return True, ""


def verificar_ficha_produto(db: Session, obj: FichaProduto) -> tuple[bool, str]:
    svc = db.query(FichaServicoRecurso).filter(
        FichaServicoRecurso.ficha_produto_id == obj.id,
        FichaServicoRecurso.ficha.has(FichaServico.ativo == True),
    ).count()
    orc = db.query(OrcamentoItem).filter(
        OrcamentoItem.ficha_produto_id == obj.id,
    ).count()
    itf = db.query(ItemFicha).filter(
        ItemFicha.ficha_produto_id == obj.id,
    ).count()
    total = svc + orc + itf
    if total:
        return False, (
            f"Não é possível excluir a ficha de produto '{obj.codigo}'. "
            f"Ela é usada em {svc} serviço(s), {orc} orçamento(s) e {itf} "
            f"vínculo(s) de item. Remova as dependências primeiro ou inative-a."
        )
    return True, ""


def verificar_ficha_servico(db: Session, obj: FichaServico) -> tuple[bool, str]:
    orc = db.query(OrcamentoItem).filter(
        OrcamentoItem.ficha_servico_id == obj.id,
    ).count()
    itf = db.query(ItemFicha).filter(
        ItemFicha.ficha_servico_id == obj.id,
    ).count()
    total = orc + itf
    if total:
        return False, (
            f"Não é possível excluir a ficha de serviço '{obj.codigo}'. "
            f"Ela é usada em {orc} orçamento(s) e {itf} vínculo(s) de item. "
            f"Exclusão não permitida. Inative-a se necessário."
        )
    return True, ""


def verificar_orcamentista(db: Session, obj: UsuarioOrcamentista) -> tuple[bool, str]:
    # Orcamentistas não têm FK reversa ainda, podem ser excluídos
    return True, ""
