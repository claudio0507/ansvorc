"""Script de seed (DEV) — popula os 8 BDs + usuários padrão, conforme docs/02 + docs/04.

ATENÇÃO: exclusivo para desenvolvimento/testes. Em produção use seeds_prod.py.
"""

import os
import sys
from decimal import Decimal

if os.getenv("ENV") == "production" or os.getenv("DATABASE_URL", "").startswith(
    "postgresql"
):
    sys.exit(
        "ERRO: seeds.py contém credenciais de desenvolvimento e não pode rodar em "
        "produção. Use seeds_prod.py."
    )

from backend.database import Base, SessionLocal, engine
from backend.models.bd_models import (
    BdBDI,
    BdDespesas,
    BdEPI,
    BdEstrutura,
    BdFerramental,
    BdFrotas,
    BdMateriais,
    BdRH,
)

# Alíquotas de referência (docs/04)
PIS = Decimal("0.0065")
COFINS = Decimal("0.0300")
ISSQN_PR = Decimal("0.0350")
ISSQN_SP = Decimal("0.0500")
ICMS = Decimal("0.1200")
CF = Decimal("0.0150")
ADM = Decimal("0.1300")
IRPJ = Decimal("0.0200")
CSLL = Decimal("0.0108")


def _bdi(modalidade, uf, *, icms, cofins, pis, issqn) -> BdBDI:
    return BdBDI(
        modalidade=modalidade,
        uf=uf,
        icms=icms,
        cofins=cofins,
        pis=pis,
        issqn=issqn,
        custo_financeiro=CF,
        irpj=IRPJ,
        csll=CSLL,
        despesas_adm=ADM,
    )


def seed_bdi(db):
    z = Decimal("0")
    registros = []
    for uf, issqn in (("PR", ISSQN_PR), ("SP", ISSQN_SP)):
        registros += [
            _bdi("BDI-MO", uf, icms=z, cofins=COFINS, pis=PIS, issqn=issqn),
            _bdi("BDI-MAT+MO", uf, icms=z, cofins=COFINS, pis=PIS, issqn=issqn),
            _bdi("BDI+ICMS", uf, icms=ICMS, cofins=COFINS, pis=PIS, issqn=z),
            _bdi("FAT DIR SIMP", uf, icms=z, cofins=z, pis=z, issqn=z),
        ]
    db.add_all(registros)


def seed_rh(db):
    db.add_all(
        [
            BdRH(cargo="Encarregado", custo_diario=Decimal("327.27")),
            BdRH(cargo="Operador Bate Estaca", custo_diario=Decimal("254.55")),
            BdRH(cargo="Operador Pintura", custo_diario=Decimal("254.55")),
            BdRH(cargo="Motorista", custo_diario=Decimal("232.73")),
            BdRH(cargo="Auxiliar", custo_diario=Decimal("200.00")),
        ]
    )


def seed_epi(db):
    db.add_all(
        [
            BdEPI(item="Kit EPI Encarregado", custo_diario=Decimal("3.50")),
            BdEPI(item="Kit EPI Operador", custo_diario=Decimal("3.20")),
            BdEPI(item="Kit EPI Auxiliar", custo_diario=Decimal("2.80")),
            BdEPI(item="Kit EPI Motorista", custo_diario=Decimal("2.50")),
        ]
    )


def seed_ferramental(db):
    db.add_all(
        [
            BdFerramental(seguimento="EPS", custo_diario=Decimal("271.05")),
            BdFerramental(seguimento="HORIZONTAL", custo_diario=Decimal("35.90")),
            BdFerramental(seguimento="VERTICAL", custo_diario=Decimal("24.56")),
            BdFerramental(seguimento="OBRA CIVIL", custo_diario=Decimal("45.00")),
        ]
    )


def seed_frotas(db):
    db.add_all(
        [
            BdFrotas(seguimento="EPS", custo_diario=Decimal("1368.54")),
            BdFrotas(seguimento="HORIZONTAL", custo_diario=Decimal("735.34")),
            BdFrotas(seguimento="VERTICAL", custo_diario=Decimal("1032.56")),
            BdFrotas(seguimento="APOIO", custo_diario=Decimal("280.00")),
        ]
    )


def seed_materiais(db):
    db.add_all(
        [
            BdMateriais(
                material="Chapa de Aço 1,00",
                unidade="und",
                destinacao="FABRICA",
                valor_unitario=Decimal("25.50"),
            ),
            BdMateriais(
                material="Cantoneira Modulada",
                unidade="und",
                destinacao="FABRICA",
                valor_unitario=Decimal("10.00"),
            ),
            BdMateriais(
                material="Película Refletiva",
                unidade="und",
                destinacao="FABRICA",
                valor_unitario=Decimal("90.50"),
            ),
            BdMateriais(
                material="Fixação 1",
                unidade="und",
                destinacao="FABRICA",
                valor_unitario=Decimal("2.50"),
            ),
            BdMateriais(
                material="Tinta à Base d'Água",
                unidade="L",
                destinacao="HORIZONTAL",
                valor_unitario=Decimal("8.13"),
            ),
        ]
    )


def seed_estrutura(db):
    db.add_all(
        [
            BdEstrutura(
                item="Base de Apoio Operacional",
                unidade="Mês",
                tipo="Base_de_Apoio",
                valor_unitario=Decimal("57000.00"),
            ),
            BdEstrutura(
                item="Moradia / Alojamento",
                unidade="Mês",
                tipo="Moradia",
                valor_unitario=Decimal("12000.00"),
            ),
            BdEstrutura(
                item="Mobilização de Equipamento",
                unidade="und",
                tipo="Logística",
                valor_unitario=Decimal("12500.00"),
            ),
            BdEstrutura(
                item="Plano de Sinalização (PSCT)",
                unidade="vb",
                tipo="Administrativo",
                valor_unitario=Decimal("3500.00"),
            ),
        ]
    )


def seed_despesas(db):
    db.add_all(
        [
            BdDespesas(
                seguimento="EPS",
                epc=Decimal("15.00"),
                refeicao=Decimal("35.00"),
                hospedagem=Decimal("50.00"),
            ),
            BdDespesas(
                seguimento="HORIZONTAL",
                epc=Decimal("12.00"),
                refeicao=Decimal("35.00"),
                hospedagem=Decimal("45.00"),
            ),
            BdDespesas(
                seguimento="VERTICAL",
                epc=Decimal("10.00"),
                refeicao=Decimal("35.00"),
                hospedagem=Decimal("45.00"),
            ),
            BdDespesas(
                seguimento="APOIO",
                epc=Decimal("8.00"),
                refeicao=Decimal("30.00"),
                hospedagem=Decimal("40.00"),
            ),
        ]
    )


def seed_usuarios(db):
    from backend.auth import hash_senha
    from backend.models.usuario_models import Usuario

    db.add_all(
        [
            Usuario(
                nome="Sponsor",
                email="sponsor@altanoroeste.com.br",
                senha_hash=hash_senha("sponsor123"),
                papel="sponsor",
            ),
            Usuario(
                nome="Administrador",
                email="admin@altanoroeste.com.br",
                senha_hash=hash_senha("admin123"),
                papel="gestor_bd",
            ),
            Usuario(
                nome="Parametrizador",
                email="param@altanoroeste.com.br",
                senha_hash=hash_senha("param123"),
                papel="parametrizador",
            ),
            Usuario(
                nome="Orçamentista",
                email="orc@altanoroeste.com.br",
                senha_hash=hash_senha("orc123"),
                papel="orcamentista",
            ),
        ]
    )


def seed_parametros(db):
    from backend.models.param_models import (
        ParametroSeguimento,
        ParametroTipoEstrutura,
        UnidadeMedida,
    )

    unidades = [
        ("m", "Metro"),
        ("mm", "Milímetro"),
        ("m²", "Metro Quadrado"),
        ("und", "Unidade"),
        ("L", "Litro"),
        ("mL", "Mililitro"),
        ("kg", "Quilograma"),
        ("dia", "Dia"),
        ("mês", "Mês"),
        ("h", "Hora"),
        ("R$", "Real"),
        ("vb", "Verba"),
    ]
    db.add_all([UnidadeMedida(sigla=s, nome=n) for s, n in unidades])
    db.add_all(
        [
            ParametroSeguimento(nome=n)
            for n in ("EPS", "HORIZONTAL", "VERTICAL", "APOIO")
        ]
    )
    db.add_all(
        [
            ParametroTipoEstrutura(nome=n)
            for n in (
                "Base_de_Apoio",
                "Moradia",
                "Administrativo",
                "Operacional",
                "Logística",
            )
        ]
    )


_FOR077_CLAUSULA_TRIBUTARIA = (
    "Os preços apresentados nesta proposta contemplam a carga tributária atual "
    "exigida pela legislação pertinente. Eventuais contratos com execuções ou "
    "vigência posterior a 31/12/2026 estarão sujeitos a revisão e renegociação "
    "obrigatória, visando o repasse dos impactos tributários causados pela "
    "transição da Reforma Tributária (IBS/CBS)."
)

_FOR077_REAJUSTAMENTO = (
    "Os preços poderão ser atualizados anualmente, mediante aplicação do índice de "
    "menor variação acumulada no período entre o Índice Nacional de Preços ao "
    "Consumidor Amplo – IPCA ou o Índice Geral de Preços do Mercado – IGPM. A "
    "data-base para fins de reajuste será a data de assinatura do contrato."
)

_FOR077_DECLARACOES = "\n".join(
    [
        "Que respeita integralmente as condições estabelecidas na TR.ENG.{numero}.",
        "Que possui conhecimento das Políticas de Meio Ambiente, corporativa sobre "
        "Mudanças Climáticas e de Responsabilidade Social.",
        "Que possui conhecimento e que cumpre a legislação anticorrupção e, em "
        "especial a Lei 12.846/13;",
        "Que executará os serviços de acordo com o projeto e suas modificações, ordem "
        "de serviço, e de acordo com as normas e especificações técnicas;",
        "Que se obriga a dispor, para emprego imediato, de todos os recursos "
        "necessários para a execução dos serviços contratados, no prazo estipulado, "
        "sem custos adicionais;",
        "Que tem pleno conhecimento das condições locais necessárias para a formação "
        "dos preços;",
        "Que não possui em seu quadro de empregados, menor de 18 anos em trabalho "
        "noturno, insalubre ou perigoso, e, ainda, não possuir empregado menor de 16 "
        "anos;",
        "Que a proponente não mantém qualquer relação ou vínculo de qualquer natureza "
        "com a Contratante ou empresas do mesmo Conglomerado econômico a qual "
        "pertence;",
        "Que conhece o Código de Ética e Integridade, constantes nos documentos "
        "recebidos.",
        "Se comprometer a estar instalado e pronto para o início dos serviços no prazo "
        "imposto no termo de referência;",
        "Que em seu preço estão inclusas todas as despesas com a prestação dos "
        "serviços, equipamentos, mão-de-obra, tributos, encargos, impostos, lucro, e "
        "as demais despesas diretas e indiretas que possam recair sobre a presente "
        "prestação de serviços;",
        "Que executará todos os serviços de acordo com o preço e o prazo, estipulados "
        "nesta carta;",
        "Que tem pleno conhecimento sobre a retenção de X% das medições sobre o valor "
        "bruto da medição a título de caução.",
    ]
)


def seed_extra(db):
    """Config do sistema + orçamentista exemplo (v2)."""
    from backend.models.extra_models import ConfigSistema, UsuarioOrcamentista

    db.add(
        ConfigSistema(
            nome_empresa="ALTA NOROESTE",
            cnpj="20.945.724/0001-15",
            banco="Bradesco",
            agencia="0110",
            conta_corrente="0287852-6",
            diretor_cpf="277.540.838-92",
            contato_comercial_nome="Milaini Carvalho Miranda",
            contato_comercial_funcao="Comercial",
            contato_comercial_fone="(18) 99683-6472",
            contato_comercial_email="comercial@altanoroeste.com.br",
            garantia_retencao_padrao_pct=Decimal("5"),
            garantia_devolucao_padrao_dias=60,
            clausula_tributaria_padrao=_FOR077_CLAUSULA_TRIBUTARIA,
            reajustamento_padrao=_FOR077_REAJUSTAMENTO,
            declaracoes_padrao=_FOR077_DECLARACOES,
        )
    )
    db.add(
        UsuarioOrcamentista(
            nome_completo="Cláudio Rodrigo",
            funcao="Orçamentista Sênior",
            email="orc@altanoroeste.com.br",
            telefone="(41) 9 9999-9999",
        )
    )


def run():
    from backend.models.usuario_models import Usuario

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(BdBDI).count() > 0:
            print("Seed já executado anteriormente. Abortando.")
            return

        seed_bdi(db)
        seed_rh(db)
        seed_epi(db)
        seed_ferramental(db)
        seed_frotas(db)
        seed_materiais(db)
        seed_estrutura(db)
        seed_despesas(db)
        seed_parametros(db)
        seed_extra(db)
        seed_usuarios(db)
        db.commit()

        print("Seed concluído com sucesso.")
        for nome, modelo in [
            ("bd_BDI", BdBDI),
            ("bd_RH", BdRH),
            ("bd_EPI", BdEPI),
            ("bd_FERRAMENTAL", BdFerramental),
            ("bd_FROTAS", BdFrotas),
            ("bd_MATERIAIS", BdMateriais),
            ("bd_ESTRUTURA_OPERACIONAL", BdEstrutura),
            ("bd_DESPESAS", BdDespesas),
            ("usuarios", Usuario),
        ]:
            print(f"  {nome:26s} {db.query(modelo).count()} registros")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    run()
