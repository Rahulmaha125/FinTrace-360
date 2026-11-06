"""
FinTrace 360 - Custom Dataset Ingestion Module
Handles in-memory parsing, format detection, size enforcement, and encoding detection
for user-uploaded financial files (CSV, TSV, XLSX, XLS).
"""

from dataclasses import dataclass
import io
from pathlib import Path
from typing import Any
import pandas as pd
from src.utils.logger import setup_logger

logger = setup_logger("custom_loader")

MAX_FILE_SIZE_MB = 25.0
MAX_ROW_COUNT = 100000

@dataclass
class FileLoadResult:
    success: bool
    df: pd.DataFrame | None
    error_message: str | None
    metadata: dict[str, Any]

def parse_uploaded_file(
    file_bytes: bytes,
    filename: str,
    max_size_mb: float = MAX_FILE_SIZE_MB,
    max_rows: int = MAX_ROW_COUNT
) -> FileLoadResult:
    """
    Parses raw uploaded file bytes into a Pandas DataFrame completely in-memory.
    Never persists user bytes to disk.
    """
    size_mb = len(file_bytes) / (1024 * 1024)
    metadata = {
        "filename": filename,
        "size_mb": round(size_mb, 2),
        "extension": Path(filename).suffix.lower(),
        "row_count": 0,
        "col_count": 0,
        "truncated": False
    }

    if size_mb > max_size_mb:
        msg = f"File exceeds maximum allowed size ({size_mb:.2f} MB > {max_size_mb:.0f} MB). Please upload a smaller file."
        logger.warning(msg)
        return FileLoadResult(success=False, df=None, error_message=msg, metadata=metadata)

    ext = metadata["extension"]
    df = None

    try:
        if ext in [".csv", ".txt", ".tsv"]:
            delimiter = "\t" if ext == ".tsv" else ","
            # Try UTF-8 first, fallback to Latin-1
            for encoding in ["utf-8", "latin-1", "iso-8859-1", "cp1252"]:
                try:
                    df = pd.read_csv(
                        io.BytesIO(file_bytes),
                        sep=delimiter,
                        encoding=encoding,
                        nrows=max_rows + 1,
                        low_memory=False
                    )
                    metadata["encoding"] = encoding
                    break
                except (UnicodeDecodeError, pd.errors.ParserError):
                    continue

            if df is None:
                return FileLoadResult(
                    success=False, df=None,
                    error_message="Could not decode CSV file. Please ensure it is saved with UTF-8 or standard ASCII encoding.",
                    metadata=metadata
                )

        elif ext in [".xlsx", ".xls"]:
            try:
                import openpyxl  # noqa: F401
                df = pd.read_excel(io.BytesIO(file_bytes), nrows=max_rows + 1)
                metadata["encoding"] = "binary/excel"
            except ImportError:
                return FileLoadResult(
                    success=False, df=None,
                    error_message="Excel reading engine (openpyxl) is not available. Please export your file as CSV and upload.",
                    metadata=metadata
                )
            except Exception as e:
                return FileLoadResult(
                    success=False, df=None,
                    error_message=f"Error reading Excel sheet: {e}",
                    metadata=metadata
                )
        else:
            return FileLoadResult(
                success=False, df=None,
                error_message=f"Unsupported file format '{ext}'. Supported formats: .csv, .tsv, .xlsx, .xls",
                metadata=metadata
            )

        if df is None or df.empty:
            return FileLoadResult(
                success=False, df=None,
                error_message="The uploaded file contains no data rows or columns.",
                metadata=metadata
            )

        # Enforce Row Count Guardrail
        if len(df) > max_rows:
            df = df.iloc[:max_rows].copy()
            metadata["truncated"] = True
            metadata["original_rows"] = f">{max_rows:,}"
            logger.info(f"Dataset truncated to safety limit of {max_rows:,} rows.")

        metadata["row_count"] = len(df)
        metadata["col_count"] = len(df.columns)
        metadata["columns"] = list(df.columns)

        # Memory optimization: Downcast object types to category if cardinality is low
        for col in df.select_dtypes(include=["object"]).columns:
            num_unique = df[col].nunique()
            if num_unique < 50 and num_unique < len(df) * 0.2:
                df[col] = df[col].astype("category")

        logger.info(f"Successfully parsed {filename}: {len(df):,} rows, {len(df.columns)} columns.")
        return FileLoadResult(success=True, df=df, error_message=None, metadata=metadata)

    except Exception as e:
        logger.error(f"Unexpected error parsing file: {e}")
        return FileLoadResult(
            success=False, df=None,
            error_message=f"Failed to parse file: {str(e)}",
            metadata=metadata
        )
