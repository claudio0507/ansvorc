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
