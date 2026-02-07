"""Document builders: records -> documents. Design allows chat/email to group many records."""

from document_builders.base import BaseDocumentBuilder
from document_builders.file_document_builder import FileDocumentBuilder

__all__ = ["BaseDocumentBuilder", "FileDocumentBuilder"]
