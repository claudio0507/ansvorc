# Plano de Fases — Sinalys

## Fase 1: Fundação (Core)
- [ ] Estrutura FastAPI + SQLAlchemy + SQLite
- [ ] Models: 8 tabelas BD + 6 tabelas Ficha
- [ ] CRUD endpoints para todos os BD
- [ ] CRUD endpoints para fichas técnicas
- [ ] Seeds com dados iniciais

## Fase 2: Motor e Orçamento
- [ ] Motor BDI (BDI Sombra + BDI Completo + Fator K)
- [ ] REIDI
- [ ] CRUD orçamentos + itens
- [ ] Endpoint de cálculo em tempo real
- [ ] Snapshot ao aprovar
- [ ] Versionamento
- [ ] Desconto sobre total com rateio
- [ ] Testes: UF × REIDI × MOD FAT × Margem

## Fase 3: Autenticação e Segurança
- [ ] JWT + RBAC por papel
- [ ] Middleware de autorização
- [ ] Validação Pydantic
- [ ] Rate limiting

## Fase 4: CRM e Relatórios
- [ ] CRUD clientes
- [ ] Exportar PDF de proposta comercial
- [ ] Dashboard de margens

## Fase 5: Deploy
- [ ] Docker + docker-compose
- [ ] PostgreSQL produção
- [ ] CI/CD GitHub Actions
- [ ] HTTPS + backup
