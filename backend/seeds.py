"""Script de seed — popula dados iniciais das 8 tabelas do Bloco 1 + usuários padrão."""

from decimal import Decimal

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


def seed_bdi(db):
    registros = [
        BdBDI(
            modalidade="BDI-MO",
            adm_percentual=Decimal("0.1300"),
            custo_financeiro_percentual=Decimal("0.0150"),
            pis_cofins_percentual=Decimal("0.0365"),
            issqn_pr_percentual=Decimal("0.0350"),
            issqn_sp_percentual=Decimal("0.0500"),
            icms_percentual=Decimal("0.0000"),
            descricao="Mão de obra pura — sem ICMS, ISS incide",
        ),
        BdBDI(
            modalidade="BDI-MAT+MO",
            adm_percentual=Decimal("0.1300"),
            custo_financeiro_percentual=Decimal("0.0150"),
            pis_cofins_percentual=Decimal("0.0365"),
            issqn_pr_percentual=Decimal("0.0350"),
            issqn_sp_percentual=Decimal("0.0500"),
            icms_percentual=Decimal("0.0000"),
            descricao="Material + mão de obra, sem ICMS separado",
        ),
        BdBDI(
            modalidade="BDI+ICMS",
            adm_percentual=Decimal("0.1300"),
            custo_financeiro_percentual=Decimal("0.0150"),
            pis_cofins_percentual=Decimal("0.0925"),
            issqn_pr_percentual=Decimal("0.0000"),
            issqn_sp_percentual=Decimal("0.0000"),
            icms_percentual=Decimal("0.1200"),
            descricao="Produtos com ICMS — PIS/COFINS regime não-cumulativo",
        ),
        BdBDI(
            modalidade="FAT DIR SIMP",
            adm_percentual=Decimal("0.0000"),
            custo_financeiro_percentual=Decimal("0.0000"),
            pis_cofins_percentual=Decimal("0.0000"),
            issqn_pr_percentual=Decimal("0.0000"),
            issqn_sp_percentual=Decimal("0.0000"),
            icms_percentual=Decimal("0.0000"),
            descricao="Faturamento direto simplificado — margem pura",
        ),
    ]
    db.add_all(registros)


def seed_rh(db):
    registros = [
        BdRH(
            codigo="RH-001",
            cargo="Encarregado Geral",
            categoria="OPERACIONAL",
            salario_base=Decimal("4500.00"),
            encargos_percentual=Decimal("0.7200"),
            horas_mes=Decimal("220.00"),
        ),
        BdRH(
            codigo="RH-002",
            cargo="Sinaleiro / Pintor de Faixa",
            categoria="OPERACIONAL",
            salario_base=Decimal("2800.00"),
            encargos_percentual=Decimal("0.7200"),
            horas_mes=Decimal("220.00"),
        ),
        BdRH(
            codigo="RH-003",
            cargo="Auxiliar de Sinalização",
            categoria="OPERACIONAL",
            salario_base=Decimal("2200.00"),
            encargos_percentual=Decimal("0.7200"),
            horas_mes=Decimal("220.00"),
        ),
        BdRH(
            codigo="RH-004",
            cargo="Motorista Operador",
            categoria="OPERACIONAL",
            salario_base=Decimal("3200.00"),
            encargos_percentual=Decimal("0.7200"),
            horas_mes=Decimal("220.00"),
        ),
        BdRH(
            codigo="RH-005",
            cargo="Técnico em Segurança do Trabalho",
            categoria="TECNICO",
            salario_base=Decimal("3800.00"),
            encargos_percentual=Decimal("0.7200"),
            horas_mes=Decimal("220.00"),
        ),
        BdRH(
            codigo="RH-006",
            cargo="Engenheiro Civil / Responsável Técnico",
            categoria="TECNICO",
            salario_base=Decimal("9000.00"),
            encargos_percentual=Decimal("0.7200"),
            horas_mes=Decimal("220.00"),
        ),
    ]
    db.add_all(registros)


def seed_epi(db):
    registros = [
        BdEPI(
            codigo="EPI-001",
            descricao="Capacete de segurança aba frontal",
            unidade_medida="un",
            custo_unitario=Decimal("35.00"),
            vida_util_dias=365,
        ),
        BdEPI(
            codigo="EPI-002",
            descricao="Colete refletivo classe II",
            unidade_medida="un",
            custo_unitario=Decimal("45.00"),
            vida_util_dias=180,
        ),
        BdEPI(
            codigo="EPI-003",
            descricao="Botina de segurança com biqueira de aço",
            unidade_medida="par",
            custo_unitario=Decimal("120.00"),
            vida_util_dias=180,
        ),
        BdEPI(
            codigo="EPI-004",
            descricao="Luva de couro",
            unidade_medida="par",
            custo_unitario=Decimal("18.00"),
            vida_util_dias=60,
        ),
        BdEPI(
            codigo="EPI-005",
            descricao="Óculos de proteção incolor",
            unidade_medida="un",
            custo_unitario=Decimal("12.00"),
            vida_util_dias=90,
        ),
        BdEPI(
            codigo="EPI-006",
            descricao="Protetor auricular tipo concha",
            unidade_medida="un",
            custo_unitario=Decimal("55.00"),
            vida_util_dias=365,
        ),
    ]
    db.add_all(registros)


def seed_ferramental(db):
    registros = [
        BdFerramental(
            codigo="FER-001",
            descricao="Furadeira de impacto 1/2\" 850W",
            unidade_medida="un",
            custo_unitario=Decimal("480.00"),
            vida_util_dias=1095,
        ),
        BdFerramental(
            codigo="FER-002",
            descricao="Serra circular 7.1/4\" 1800W",
            unidade_medida="un",
            custo_unitario=Decimal("650.00"),
            vida_util_dias=1095,
        ),
        BdFerramental(
            codigo="FER-003",
            descricao="Chave de torque 3/8\" 10-80Nm",
            unidade_medida="un",
            custo_unitario=Decimal("210.00"),
            vida_util_dias=1825,
        ),
        BdFerramental(
            codigo="FER-004",
            descricao="Aplicador manual de película (rodo)",
            unidade_medida="un",
            custo_unitario=Decimal("85.00"),
            vida_util_dias=365,
        ),
    ]
    db.add_all(registros)


def seed_frotas(db):
    registros = [
        BdFrotas(
            codigo="FRT-001",
            descricao="Caminhão equipado com sinalização viária",
            tipo="VEICULO_PESADO",
            custo_diaria=Decimal("1200.00"),
            custo_km=Decimal("1.80"),
        ),
        BdFrotas(
            codigo="FRT-002",
            descricao="Caminhonete Pickup 4x4",
            tipo="VEICULO_LEVE",
            custo_diaria=Decimal("350.00"),
            custo_km=Decimal("0.85"),
        ),
        BdFrotas(
            codigo="FRT-003",
            descricao="Caminhão prancha para transporte de equipamentos",
            tipo="PRANCHA",
            custo_diaria=Decimal("2800.00"),
            custo_km=Decimal("3.20"),
        ),
        BdFrotas(
            codigo="FRT-004",
            descricao="Máquina termonebulizadora para pintura a quente",
            tipo="EQUIPAMENTO",
            custo_diaria=Decimal("800.00"),
        ),
        BdFrotas(
            codigo="FRT-005",
            descricao="Veículo de apoio / comboio",
            tipo="VEICULO_LEVE",
            custo_diaria=Decimal("280.00"),
            custo_km=Decimal("0.75"),
        ),
    ]
    db.add_all(registros)


def seed_materiais(db):
    registros = [
        BdMateriais(
            codigo="MAT-001",
            descricao="Chapa de aço galvanizada para placa R-1 0,60m",
            categoria="PLACA",
            unidade_medida="un",
            custo_unitario=Decimal("185.00"),
            icms_incide=True,
        ),
        BdMateriais(
            codigo="MAT-002",
            descricao="Película refletiva prismática Tipo I (3M 3930)",
            categoria="PELICULA",
            unidade_medida="m²",
            custo_unitario=Decimal("120.00"),
            icms_incide=True,
        ),
        BdMateriais(
            codigo="MAT-003",
            descricao="Tinta de demarcação à base de água (18L)",
            categoria="TINTA",
            unidade_medida="lata",
            custo_unitario=Decimal("320.00"),
            icms_incide=True,
        ),
        BdMateriais(
            codigo="MAT-004",
            descricao="Perfil U galvanizado para suporte de placa 3m",
            categoria="PERFIL",
            unidade_medida="un",
            custo_unitario=Decimal("95.00"),
            icms_incide=True,
        ),
        BdMateriais(
            codigo="MAT-005",
            descricao="Parafuso sextavado M8x30 inox (cento)",
            categoria="PARAFUSO",
            unidade_medida="ct",
            custo_unitario=Decimal("42.00"),
            icms_incide=True,
        ),
        BdMateriais(
            codigo="MAT-006",
            descricao="Microesferas de vidro para tinta refletiva (kg)",
            categoria="TINTA",
            unidade_medida="kg",
            custo_unitario=Decimal("28.50"),
            icms_incide=True,
        ),
    ]
    db.add_all(registros)


def seed_estrutura(db):
    registros = [
        BdEstrutura(
            codigo="EST-001",
            descricao="Alojamento e infraestrutura operacional — Passo Fundo/RS",
            tipo="ALOJAMENTO",
            unidade_medida="Mês",
            custo_unitario=Decimal("57000.00"),
        ),
        BdEstrutura(
            codigo="EST-002",
            descricao="Mobilização de equipamento pesado (prancha)",
            tipo="MOBILIZACAO",
            unidade_medida="un",
            custo_unitario=Decimal("12500.00"),
        ),
        BdEstrutura(
            codigo="EST-003",
            descricao="Desmobilização de equipamento",
            tipo="MOBILIZACAO",
            unidade_medida="un",
            custo_unitario=Decimal("8500.00"),
        ),
        BdEstrutura(
            codigo="EST-004",
            descricao="Plano de sinalização e controle de tráfego (PSCT)",
            tipo="LOGISTICA",
            unidade_medida="vb",
            custo_unitario=Decimal("3500.00"),
        ),
        BdEstrutura(
            codigo="EST-005",
            descricao="Comunicação — chip dados e voz (mês)",
            tipo="COMUNICACAO",
            unidade_medida="Mês",
            custo_unitario=Decimal("450.00"),
        ),
    ]
    db.add_all(registros)


def seed_despesas(db):
    registros = [
        BdDespesas(
            codigo="DEP-001",
            descricao="Despesas Administrativas Gerais",
            tipo="ADMINISTRATIVA",
            percentual=Decimal("0.1300"),
        ),
        BdDespesas(
            codigo="DEP-002",
            descricao="Custo Financeiro / Capital de Giro",
            tipo="FINANCEIRA",
            percentual=Decimal("0.0150"),
        ),
        BdDespesas(
            codigo="DEP-003",
            descricao="Seguro de obra e responsabilidade civil",
            tipo="SEGURO",
            percentual=Decimal("0.0050"),
        ),
    ]
    db.add_all(registros)


def seed_usuarios(db):
    from backend.auth import hash_senha
    from backend.models.usuario_models import Usuario

    usuarios = [
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
    db.add_all(usuarios)


def run():
    from backend.models.usuario_models import Usuario

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Evita re-seed se já populado
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
        print(f"  bd_BDI:                    {db.query(BdBDI).count()} registros")
        print(f"  bd_RH:                     {db.query(BdRH).count()} registros")
        print(f"  bd_EPI:                    {db.query(BdEPI).count()} registros")
        print(f"  bd_FERRAMENTAL:            {db.query(BdFerramental).count()} registros")
        print(f"  bd_FROTAS:                 {db.query(BdFrotas).count()} registros")
        print(f"  bd_MATERIAIS:              {db.query(BdMateriais).count()} registros")
        print(f"  bd_ESTRUTURA_OPERACIONAL:  {db.query(BdEstrutura).count()} registros")
        print(f"  bd_DESPESAS:               {db.query(BdDespesas).count()} registros")
        print(f"  usuarios:                  {db.query(Usuario).count()} registros")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    run()
