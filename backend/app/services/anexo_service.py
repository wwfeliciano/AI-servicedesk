"""Service de anexos (F3.1; RF02, RN06, decisões B9/B10).

Regras:
- escopo do chamado (RN06): só anexa/lista/baixa anexos de chamado no escopo do
  perfil (CLIENTE só os seus); fora do escopo → NAO_ENCONTRADO (404);
- B9: no máximo 5 anexos por chamado e 10 MB por arquivo;
- B10: só `image/png`, `image/jpeg` e `application/pdf`, conferidos por **magic
  bytes** (não confia no content-type nem na extensão);
- `sha256` do conteúdo e chave `chamados/{id}/{uuid4}.{ext}` (o nome original fica
  só no banco).

Não conhece HTTP: levanta `ErroAnexo` com código estável para o controller.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

from app.core.storage import StorageService
from app.entities.anexo import Anexo
from app.entities.usuario import Usuario
from app.repositories.anexo_repository import AnexoRepository
from app.repositories.chamado_repository import ChamadoRepository
from app.services.chamado_service import escopo_solicitante

# Tipos aceitos (B10) → extensão da chave de objeto.
_EXT_POR_MIME = {"image/png": "png", "image/jpeg": "jpg", "application/pdf": "pdf"}


class ErroAnexo(Exception):
    """Erro de domínio dos anexos, com código estável para o controller."""

    def __init__(self, codigo: str, mensagem: str) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


@dataclass(frozen=True)
class AnexoBaixado:
    anexo: Anexo
    storage: StorageService


def detectar_mime(dados: bytes) -> str | None:
    """Detecta o tipo por magic bytes (B10). None se não for PNG/JPEG/PDF."""
    if dados.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if dados.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if dados.startswith(b"%PDF-"):
        return "application/pdf"
    return None


class AnexoService:
    def __init__(
        self,
        *,
        anexos: AnexoRepository,
        chamados: ChamadoRepository,
        storage: StorageService,
        max_bytes: int,
        max_por_chamado: int,
    ) -> None:
        self._anexos = anexos
        self._chamados = chamados
        self._storage = storage
        self._max_bytes = max_bytes
        self._max_por_chamado = max_por_chamado

    def _exigir_chamado_no_escopo(self, *, usuario: Usuario, id_chamado: int) -> None:
        linha = self._chamados.obter(id_chamado, id_solicitante=escopo_solicitante(usuario))
        if linha is None:
            raise ErroAnexo("NAO_ENCONTRADO", "Chamado não encontrado.")

    def anexar(
        self, *, usuario: Usuario, id_chamado: int, nome_original: str, conteudo: bytes
    ) -> Anexo:
        self._exigir_chamado_no_escopo(usuario=usuario, id_chamado=id_chamado)

        if not conteudo:
            raise ErroAnexo("ARQUIVO_VAZIO", "O arquivo está vazio.")
        if len(conteudo) > self._max_bytes:
            raise ErroAnexo("ARQUIVO_GRANDE", "Arquivo acima do limite de tamanho.")

        mime = detectar_mime(conteudo)
        if mime is None:
            raise ErroAnexo(
                "TIPO_ARQUIVO_INVALIDO", "Tipo de arquivo não permitido (use PNG, JPG ou PDF)."
            )

        # B9: no máximo N anexos por chamado.
        if self._anexos.contar_do_chamado(id_chamado) >= self._max_por_chamado:
            raise ErroAnexo(
                "LIMITE_ANEXOS",
                f"Limite de {self._max_por_chamado} anexos por chamado atingido.",
            )

        sha256 = hashlib.sha256(conteudo).hexdigest()
        ext = _EXT_POR_MIME[mime]
        chave = f"chamados/{id_chamado}/{uuid.uuid4().hex}.{ext}"

        # Grava no storage antes de persistir os metadados (se o metadado falhar, o
        # objeto órfão é inofensivo; se o storage falhar, nada é gravado no banco).
        self._storage.salvar(chave, conteudo, content_type=mime)
        return self._anexos.criar(
            id_chamado=id_chamado,
            id_autor=usuario.id_usuario,
            nome_original=nome_original[:255],
            chave_objeto=chave,
            mime_type=mime,
            tamanho_bytes=len(conteudo),
            sha256=sha256,
        )

    def listar(self, *, usuario: Usuario, id_chamado: int) -> list[Anexo]:
        self._exigir_chamado_no_escopo(usuario=usuario, id_chamado=id_chamado)
        return self._anexos.listar_do_chamado(id_chamado)

    def obter_para_download(self, *, usuario: Usuario, id_anexo: int) -> AnexoBaixado:
        anexo = self._anexos.obter(id_anexo)
        if anexo is None:
            raise ErroAnexo("NAO_ENCONTRADO", "Anexo não encontrado.")
        # Escopo pelo chamado do anexo (RN06): fora do escopo → 404.
        self._exigir_chamado_no_escopo(usuario=usuario, id_chamado=anexo.id_chamado)
        return AnexoBaixado(anexo=anexo, storage=self._storage)
