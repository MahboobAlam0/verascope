"""
CLI entry point for the GMC document intelligence pipeline.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from config.settings import settings
from src.extraction.llm_client import LLMConfigurationError, get_llm_client
from src.extraction.pipeline import process_document
from src.extraction.schema import GMCPolicyExtraction
from src.extraction.serialization import to_evidence_json, to_qms_json

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the GMC document intelligence pipeline.")
    parser.add_argument("--input", type=Path, default=settings.input_dir)
    parser.add_argument("--output", type=Path, default=settings.output_dir)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(args.input.glob("*.pdf"))
    if not pdf_files:
        logger.error("No PDF files found in %s", args.input)
        return 1

    try:
        llm_client = get_llm_client()
    except LLMConfigurationError as exc:
        logger.error(str(exc))
        return 1

    for pdf_path in pdf_files:
        logger.info("Processing %s ...", pdf_path.name)
        try:
            result = process_document(pdf_path, llm_client)
        except Exception:
            logger.exception("Failed to process %s", pdf_path.name)
            continue

        stem = pdf_path.stem
        if isinstance(result, GMCPolicyExtraction):
            qms_path = args.output / f"{stem}.final_output.json"
            evidence_path = args.output / f"{stem}.evidence.json"
            qms_path.write_text(json.dumps(to_qms_json(result), indent=2))
            evidence_path.write_text(json.dumps(to_evidence_json(result), indent=2))
            logger.info(
                "  -> GMC policy. Wrote %s and %s (%d processing note(s))",
                qms_path.name, evidence_path.name, len(result.processing_notes),
            )
        else:
            non_gmc_path = args.output / f"{stem}.non_gmc.json"
            non_gmc_path.write_text(json.dumps(result.model_dump(), indent=2))
            logger.info("  -> Not a GMC policy (%s). Wrote %s", result.reason, non_gmc_path.name)

    return 0


if __name__ == "__main__":
    sys.exit(main())
