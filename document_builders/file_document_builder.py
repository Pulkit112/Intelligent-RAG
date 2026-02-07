"""File document builder: 1 record -> 1 document."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from document_builders.base import BaseDocumentBuilder
from schemas.source_document import SourceDocument
from schemas.source_record import SourceRecord


class FileDocumentBuilder(BaseDocumentBuilder):
    """
    One record -> one document. Copies key metadata; sets record_ids=[record_id], built_at.

    Design allows chat/email builders to group many records into one document later.
    """

    def build(self, records: list[SourceRecord]) -> list[SourceDocument]:
        """Build one SourceDocument per SourceRecord; copy metadata and set built_at."""
        built_at = datetime.now(timezone.utc)
        result: list[SourceDocument] = []
        for r in records:
            doc_id = str(uuid.uuid4())
            result.append(
                SourceDocument(
                    doc_id=doc_id,
                    source_type=r.source_type,
                    source_uri=r.source_uri,
                    content_ref=r.content_ref,
                    content_type=r.content_type,
                    record_ids=[r.record_id],
                    checksum=r.checksum,
                    size_bytes=r.size_bytes,
                    metadata=dict(r.metadata),
                    version=r.version,
                    fetched_at=r.fetched_at,
                    built_at=built_at,
                )
            )
        return result
