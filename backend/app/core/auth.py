"""Comptes de développement locaux et sessions opaques ; aucun rôle reçu du navigateur."""
import hashlib
import hmac
import json
import os
import secrets
import time
from threading import Lock

from fastapi import APIRouter, Request, Response
from pydantic import Field

from app.schemas.common import AccessContext, Contract
from .errors import AppError

router = APIRouter(prefix='/api/auth',tags=['Identité locale'])


class Login(Contract):
    username: str = Field(min_length=1,max_length=100)
    password: str = Field(min_length=1,max_length=200)


class LocalAuth:
    def __init__(self, state):
        self.state = state
        self.attempts = {}
        self.lock = Lock()

    def bootstrap(self):
        from app.data_access.synthetic import DESTINATIONS
        for username,modules,territories in [('direction',['reports','commercial','finance','performance'],DESTINATIONS),
                                              ('regional',['reports','commercial','performance'],['Agadir','Marrakech'])]:
            salt = secrets.token_hex(16)
            password = os.getenv('ONMT_LOCAL_PASSWORD','OnmtLocal!2026')
            access = AccessContext(user_id=username,roles=['report_editor','document_editor'],
                                   allowed_modules=modules,allowed_territories=territories)
            digest = self._digest(password,salt)
            with self.state.connect() as db:
                db.execute('INSERT OR IGNORE INTO users VALUES(?,?,?,?)',(username,salt,digest,access.model_dump_json()))

    @staticmethod
    def _digest(password, salt):
        return hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()

    def login(self, username, password, peer):
        with self.lock:
            now = time.time()
            recent = [t for t in self.attempts.get(peer,[]) if now-t < 60]
            if len(recent) >= 8:
                raise AppError('rate_limit','Trop de tentatives ; attendez une minute.',429)
            self.attempts[peer] = recent+[now]
        with self.state.connect() as db:
            row = db.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
            salt = row['salt'] if row else '00'*16
            digest = self._digest(password,salt)
            if not row or not hmac.compare_digest(digest,row['password_hash']):
                raise AppError('forbidden','Identifiants invalides.',401)
            token = secrets.token_urlsafe(32)
            db.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
            db.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),username,time.time()+8*3600))
        return token

    def resolve(self, request):
        token = request.cookies.get('onmt_session','')
        with self.state.connect() as db:
            row = db.execute('SELECT u.access FROM sessions s JOIN users u ON u.username=s.username WHERE s.token=? AND s.expires>?',
                             (hashlib.sha256(token.encode()).hexdigest(),time.time())).fetchone()
        if not row:
            raise AppError('forbidden','Connectez-vous à votre compte local.',401)
        return AccessContext.model_validate_json(row[0])


@router.post('/login')
def login(body: Login,request: Request,response: Response):
    token = request.app.state.auth.login(body.username,body.password,request.client.host if request.client else 'local')
    response.set_cookie('onmt_session',token,httponly=True,samesite='strict',secure=False,max_age=8*3600,path='/')
    return {'authenticated':True}


@router.get('/me')
def me(request: Request):
    return request.app.state.auth.resolve(request)


@router.post('/logout')
def logout(request: Request,response: Response):
    token = request.cookies.get('onmt_session','')
    with request.app.state.application_state.connect() as db:
        db.execute('DELETE FROM sessions WHERE token=?',(hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie('onmt_session',path='/')
    return {'authenticated':False}
