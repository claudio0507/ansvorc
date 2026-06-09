# Deploy — Sinalys

## Pré-requisitos

| Ferramenta         | Versão mínima | Verificar               |
|--------------------|---------------|-------------------------|
| Docker             | 24+           | `docker --version`      |
| Docker Compose     | v2.20+        | `docker compose version`|
| Git                | qualquer      | `git --version`         |
| Domínio (produção) | —             | DNS apontando para o servidor |

---

## Passo a passo — deploy inicial

### 1. Clonar o repositório

```bash
git clone https://github.com/claudiorf/ansvorc.git
cd ansvorc
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` e defina obrigatoriamente:

```bash
# Gere um secret seguro
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
echo "JWT_SECRET=${JWT_SECRET}" >> .env

# Senha do banco
echo "DB_PASSWORD=minha-senha-forte" >> .env

# Senhas dos usuários iniciais (opcional — se omitidas, são geradas no boot)
echo "ADMIN_PASSWORD=minha-senha-admin" >> .env
```

### 3. Subir os serviços

```bash
# Desenvolvimento (sem Caddy/HTTPS)
docker compose up -d

# Produção (com Caddy + HTTPS automático)
docker compose --profile production up -d
```

### 4. Verificar saúde

```bash
# Health check
curl http://localhost:8000/health
# {"status": "ok", "version": "1.0.0"}

# Logs do app
docker compose logs -f app

# Status dos containers
docker compose ps
```

### 5. Primeiro acesso

Abra `http://localhost:8000` (ou o domínio configurado).

As credenciais iniciais aparecem no log do container na primeira execução:
```
docker compose logs app | grep "Credenciais"
```

**Troque as senhas imediatamente após o primeiro login.**

---

## Atualizações

```bash
git pull
docker compose build --no-cache app
docker compose up -d app
```

---

## Variáveis de ambiente

| Variável         | Obrigatória | Default           | Descrição                                    |
|------------------|-------------|-------------------|----------------------------------------------|
| `JWT_SECRET`     | **Sim**     | —                 | HMAC-HS256 secret (mín. 32 caracteres)       |
| `DATABASE_URL`   | Não         | sqlite:///./sinalys.db | URL completa do banco                  |
| `DB_PASSWORD`    | Em produção | `sinalys`         | Senha do PostgreSQL                          |
| `DEBUG`          | Não         | `true`            | `false` em produção                          |
| `APP_VERSION`    | Não         | `1.0.0`           | Versão exibida no health check               |
| `ADMIN_EMAIL`    | Não         | admin@altanoroeste.com.br | E-mail do admin inicial            |
| `ADMIN_PASSWORD` | Não         | gerada            | Senha do admin (exibida no log se não setada)|

---

## Backup e restore

### Backup manual

```bash
./scripts/backup.sh
# Gera: backups/backup_2025-01-15_1430.sql.gz
```

### Backup automático (cron)

Adicione ao crontab do servidor:
```
0 2 * * * /caminho/para/ansvorc/scripts/backup.sh >> /var/log/sinalys-backup.log 2>&1
```

### Restore

```bash
gunzip -c backups/backup_2025-01-15_1430.sql.gz \
  | docker compose exec -T db psql -U sinalys sinalys
```

---

## HTTPS com Caddy

Edite `Caddyfile` e substitua `sinalys.altanoroeste.com.br` pelo domínio real:

```
meudominio.com.br {
    reverse_proxy app:8000
    ...
}
```

O Caddy obtém e renova o certificado Let's Encrypt automaticamente quando:
- A porta 80 e 443 estão acessíveis externamente
- O DNS do domínio aponta para o IP do servidor

---

## Troubleshooting

### App não sobe / crash no boot

```bash
docker compose logs app
```

Causas comuns:
- `JWT_SECRET` não definido → erro de validação no startup
- Banco não disponível → aguarda 30s automaticamente; se persistir, verifique `docker compose logs db`
- Porta 8000 em uso → `lsof -i :8000` ou mude a porta no `docker-compose.yml`

### Banco não aceita conexões

```bash
docker compose exec db pg_isready -U sinalys
docker compose restart db
```

### Reset completo (DESTRÓI DADOS)

```bash
docker compose down -v          # remove volumes
docker compose up -d            # recria tudo do zero
```

### Erro 401 em todas as rotas

Verifique se `JWT_SECRET` no `.env` é o mesmo usado para gerar os tokens. Tokens gerados com um secret não são válidos com outro.

---

## Segurança em produção

- [ ] `JWT_SECRET` com pelo menos 32 caracteres aleatórios
- [ ] `DB_PASSWORD` não usar o padrão `sinalys`
- [ ] `DEBUG=false`
- [ ] HTTPS ativo (Caddy configurado)
- [ ] Backup automático configurado no cron
- [ ] Senhas iniciais trocadas no primeiro login
- [ ] Firewall: expor apenas portas 80 e 443 externamente
