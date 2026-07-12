#!/usr/bin/env python3
"""Recreate an XLSX file from an AICA_EXACT_XLSX_CAPSULE JSON template."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import tempfile
import os


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def recreate(template_path: Path, output_path: Path) -> None:
    with template_path.open('r', encoding='utf-8') as f:
        template = json.load(f)

    if template.get('template_format') != 'AICA_EXACT_XLSX_CAPSULE':
        raise ValueError('Unsupported template format')
    if template.get('template_format_version') != 1:
        raise ValueError('Unsupported template format version')

    chunks = template.get('payload_chunks')
    if not isinstance(chunks, list) or not chunks:
        raise ValueError('Template has no payload_chunks')

    try:
        workbook_bytes = base64.b64decode(''.join(chunks), validate=True)
    except Exception as exc:
        raise ValueError(f'Invalid base64 workbook payload: {exc}') from exc

    expected_hash = template['reconstruction']['expected_output_sha256']
    actual_hash = sha256_bytes(workbook_bytes)
    if actual_hash != expected_hash:
        raise ValueError(
            f'Integrity check failed: expected SHA-256 {expected_hash}, got {actual_hash}'
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=output_path.name + '.', suffix='.tmp', dir=output_path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(workbook_bytes)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_name, output_path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise

    print(f'Created: {output_path}')
    print(f'SHA-256: {actual_hash}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('template_json', type=Path)
    parser.add_argument('output_xlsx', type=Path)
    args = parser.parse_args()
    recreate(args.template_json, args.output_xlsx)


if __name__ == '__main__':
    main()
