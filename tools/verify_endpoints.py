#!/usr/bin/env python3
"""
Endpoint verification utility.

Usage:
    python tools/verify_endpoints.py

Outputs a JSON report to stdout and saves report to ./endpoint_report.json
"""
from utils.logging_config import setup_logging
setup_logging()

import sys
import pathlib
# Ensure project root is on sys.path so "utils" package is importable when script run directly
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import logging
logger = logging.getLogger(__name__)

import requests
import time
import json
import os
from urllib.parse import urljoin
from typing import Dict, Any
from utils import config

DEFAULT_SAMPLE_PAIR = "BTC/USDT"

def _format_path(path: str, pair: str) -> str:
    """Format example path patterns with pair converted to exchange-specific symbol.
    Supports named placeholders: {base}, {noslash}, {dash}, {pair} and legacy '{}' -> noslash."""
    base = pair.split('/')[0]
    noslash = pair.replace('/', '')
    dash = pair.replace('/', '-')
    # If user provided named placeholders, prefer them
    if any(k in path for k in ('{base}', '{noslash}', '{dash}', '{pair}')):
        try:
            return path.format(base=base, noslash=noslash, dash=dash, pair=pair)
        except Exception:
            pass
    # Legacy single-brace placeholder -> replace with noslash
    if '{}' in path:
        return path.format(noslash)
    return path

def check_endpoint(name: str, entry: Dict[str, Any], sample_pair: str = DEFAULT_SAMPLE_PAIR) -> Dict[str, Any]:
    """
    Use DataEngine.rest_fetch_ticker when possible to validate endpoint and parsing.
    Falls back to simple HTTP GET check if DataEngine is unavailable.
    """
    base = entry.get('base_url')
    path = entry.get('public_ticker_path', '')
    checked_url = urljoin(base, _format_path(path, sample_pair)) if base and path else base

    result = {
        'exchange': name,
        'base_url': base,
        'checked_url': checked_url,
        'ok': False,
        'status_code': None,
        'latency_ms': None,
        'error': None
    }

    # Prefer using DataEngine.rest_fetch_ticker for realistic parsing/params
    try:
        from core.data_engine import DataEngine
        engine = DataEngine()
        start = time.time()
        parsed = engine.rest_fetch_ticker(name, sample_pair)
        latency = (time.time() - start) * 1000.0
        result['latency_ms'] = round(latency, 2)
        if parsed and isinstance(parsed, dict) and parsed.get('last') is not None:
            result['ok'] = True
            result['status_code'] = 200
        else:
            # If this endpoint requires an API key and none is configured, skip raw GET to avoid false negatives.
            if entry.get('requires_api_key'):
                # Check common env vars used by DataEngine for CMC
                if not (os.getenv('COINMARKETCAP_API_KEY') or os.getenv('CMC_API_KEY')):
                    result['error'] = 'requires_api_key_missing'
                    return result
            # If this exchange is configured to prefer ccxt for public data, skip raw GET.
            if entry.get('prefer_ccxt'):
                result['error'] = 'prefer_ccxt'
                return result
            # fallback: attempt raw HTTP GET to the configured path
            start = time.time()
            try:
                resp = requests.get(checked_url, timeout=5)
                latency = (time.time() - start) * 1000.0
                result['status_code'] = resp.status_code
                result['latency_ms'] = round(latency, 2)
                result['ok'] = resp.status_code == 200
            except Exception as http_e:
                result['error'] = str(http_e)
    except Exception as e:
        # If DataEngine import or rest_fetch_ticker fails, fallback to raw request
        try:
            start = time.time()
            resp = requests.get(checked_url, timeout=5)
            latency = (time.time() - start) * 1000.0
            result['status_code'] = resp.status_code
            result['latency_ms'] = round(latency, 2)
            result['ok'] = resp.status_code == 200
        except Exception as http_e:
            result['error'] = str(http_e)
    return result

def main():
    endpoints = config.EXCHANGE_ENDPOINTS
    report = []
    for name, entry in endpoints.items():
        report.append(check_endpoint(name, entry))
    out = {
        'timestamp': time.time(),
        'results': report
    }
    with open('endpoint_report.json', 'w') as f:
        json.dump(out, f, indent=2)
    logger.info(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()