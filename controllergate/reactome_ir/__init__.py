"""Read-only Reactome release source ingestion and RPIR records."""

from .ingest import RPIR_VERSION, ingest_release

__all__ = ["RPIR_VERSION", "ingest_release"]
