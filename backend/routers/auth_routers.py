from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth import criar_token, get_current_user, hash_senha, verificar_senha
from backend.database import get_db
from backend.models.usuario_models import Usuario
from backend.schemas.usuario_schemas import (
    TokenResponse,
    UsuarioCreate,
    UsuarioLogin,
    UsuarioRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])


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
        papel=body.papel,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=TokenResponse)
def login(body: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == body.email).first()
    if not usuario or not verificar_senha(body.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo.",
        )
    token = criar_token(usuario.id, usuario.papel)
    return TokenResponse(
        access_token=token,
        papel=usuario.papel,
        usuario_id=usuario.id,
        nome=usuario.nome,
    )


@router.get("/me", response_model=UsuarioRead)
def me(usuario: Usuario = Depends(get_current_user)):
    return usuario
