"""Armazenamento de objetos (S3/MinIO) para os anexos (seção 5.6).

`StorageService` é a interface (Protocol) com `salvar`, `abrir_stream` e `remover`.
`S3StorageService` implementa com boto3 apontando para o MinIO (path-style, s3v4).
Trocar de provedor é só configuração. A API cria os buckets no startup se não
existirem (idempotente).

Os testes usam um fake em memória (não dependem do MinIO).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.core.config import Configuracao


@runtime_checkable
class StorageService(Protocol):
    """Interface de armazenamento de objetos (seção 5.6)."""

    def salvar(self, chave: str, dados: bytes, *, content_type: str) -> None:
        """Grava os bytes sob a chave, com o content-type informado."""
        ...

    def abrir_stream(self, chave: str) -> Iterator[bytes]:
        """Abre o objeto para leitura em blocos (streaming do download)."""
        ...

    def remover(self, chave: str) -> None:
        """Remove o objeto (idempotente)."""
        ...


class S3StorageService:
    """Implementação com boto3 contra o MinIO (ou qualquer S3 compatível)."""

    def __init__(self, config: Configuracao) -> None:
        import boto3
        from botocore.config import Config as BotoConfig

        self._bucket = config.s3_bucket_anexos
        # path-style + s3v4; checksums "when_required" para compatibilidade com o
        # MinIO (boto3 1.36+ envia checksums automáticos por padrão — seção 5.6).
        self._cliente = boto3.client(
            "s3",
            endpoint_url=config.s3_endpoint_url,
            aws_access_key_id=config.s3_access_key,
            aws_secret_access_key=config.s3_secret_key,
            region_name=config.s3_regiao,
            config=BotoConfig(
                s3={"addressing_style": "path"},
                signature_version="s3v4",
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    def garantir_buckets(self, *buckets: str) -> None:
        """Cria os buckets informados se não existirem (idempotente, no startup)."""
        from botocore.exceptions import ClientError

        existentes = {b["Name"] for b in self._cliente.list_buckets().get("Buckets", [])}
        for bucket in buckets:
            if bucket in existentes:
                continue
            try:
                self._cliente.create_bucket(Bucket=bucket)
            except ClientError as exc:  # pragma: no cover - corrida/criação concorrente
                codigo = exc.response.get("Error", {}).get("Code", "")
                if codigo not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                    raise

    def salvar(self, chave: str, dados: bytes, *, content_type: str) -> None:
        self._cliente.put_object(
            Bucket=self._bucket, Key=chave, Body=dados, ContentType=content_type
        )

    def abrir_stream(self, chave: str) -> Iterator[bytes]:
        objeto = self._cliente.get_object(Bucket=self._bucket, Key=chave)
        corpo = objeto["Body"]
        try:
            yield from corpo.iter_chunks(chunk_size=64 * 1024)
        finally:
            corpo.close()

    def remover(self, chave: str) -> None:
        self._cliente.delete_object(Bucket=self._bucket, Key=chave)


class StorageMemoria:
    """Storage em memória para testes (não usa MinIO)."""

    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}

    def salvar(self, chave: str, dados: bytes, *, content_type: str) -> None:
        self.objetos[chave] = dados

    def abrir_stream(self, chave: str) -> Iterator[bytes]:
        yield self.objetos[chave]

    def remover(self, chave: str) -> None:
        self.objetos.pop(chave, None)


def criar_storage(config: Configuracao) -> S3StorageService:
    """Monta o storage S3 a partir da configuração."""
    return S3StorageService(config)
