from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from backend.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    criar_refresh_token,
    criar_token,
    get_current_user,
    hash_senha,
    requer_papel,
    verificar_senha,
    verificar_token,
)
from backend.config import settings
from backend.database import get_db
from backend.models.usuario_models import Usuario
from backend.schemas.usuario_schemas import (
    PapelUpdate,
    RefreshRequest,
    TokenResponse,
    UsuarioAdminCreate,
    UsuarioCreate,
    UsuarioLogin,
    UsuarioRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])
# Rate limiting desabilitado em DEBUG/testes para evitar estado global entre test cases
_limiter = Limiter(key_func=get_remote_address, enabled=not settings.DEBUG)


@router.post(
    "/registro", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED
)
def registro(body: UsuarioCreate, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado.",
        )
    usuario = Usuario(
        nome=body.nome,
        email=body.email,
        senha_hash=hash_senha(body.senha),
        papel="orcamentista",  # sempre — jamais aceitar papel do body
        ativo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=TokenResponse)
@_limiter.limit("5/minute")
def login(request: Request, body: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == body.email).first()
    # Verifica senha ANTES de checar ativo para equalizar timing e evitar enumeração
    senha_ok = verificar_senha(body.senha, usuario.senha_hash) if usuario else False
    if not usuario or not senha_ok or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=criar_token(usuario.id, usuario.papel),
        refresh_token=criar_refresh_token(usuario.id, usuario.papel),
        papel=usuario.papel,
        usuario_id=usuario.id,
        nome=usuario.nome,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    payload = verificar_token(body.refresh_token, expected_type="refresh")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido."
        )
    usuario = db.get(Usuario, int(sub))
    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo."
        )
    return TokenResponse(
        access_token=criar_token(usuario.id, usuario.papel),
        refresh_token=criar_refresh_token(usuario.id, usuario.papel),
        papel=usuario.papel,
        usuario_id=usuario.id,
        nome=usuario.nome,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UsuarioRead)
def me(usuario: Usuario = Depends(get_current_user)):
    return usuario


# ── Endpoints administrativos ────────────────────────────────────────────────


@router.post(
    "/usuarios",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    tags=["admin"],
    dependencies=[Depends(requer_papel("gestor_bd", "sponsor"))],
)
def criar_usuario_admin(body: UsuarioAdminCreate, db: Session = Depends(get_db)):
    """Cria usuário com papel arbitrário. Restrito a gestor_bd e sponsor."""
    if db.query(Usuario).filter(Usuario.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado.",
        )
    usuario = Usuario(
        nome=body.nome,
        email=body.email,
        senha_hash=hash_senha(body.senha),
        papel=body.papel,
        ativo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.patch(
    "/usuarios/{usuario_id}/papel",
    response_model=UsuarioRead,
    tags=["admin"],
    dependencies=[Depends(requer_papel("gestor_bd", "sponsor"))],
)
def atualizar_papel(usuario_id: int, body: PapelUpdate, db: Session = Depends(get_db)):
    """Promove ou rebaixa o papel de um usuário. Restrito a gestor_bd e sponsor."""
    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado."
        )
    usuario.papel = body.papel
    db.commit()
    db.refresh(usuario)
    return usuario
