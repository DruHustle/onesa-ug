"""Explicit product boundaries for repository tooling, never runtime dependencies."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "DruHustle/onesa-ug"
PRODUCTS = {
    "portal": "onesa-company-portal",
    "platform": "onesa-ai-platform",
    "robot": "onesa-robot",
    "drone": "onesa-drone",
}
SOURCE_WORKFLOWS = {
    "portal": "verify.yml",
    "platform": "ci.yml",
    "robot": "scaffold.yml",
    "drone": "verify.yml",
}
# These public main commits were imported with their original ancestry. They are
# historical scan boundaries, not production deployment authorization.
IMPORTED_HEADS = {
    "onesa-company-portal": "dbd59ed292d29a96a99af5fb45e28b429cf9bea2",
    "onesa-ai-platform": "4d4222e3b549eb78dcf817c6cf13a8aa91087415",
    "onesa-robot": "26240cbdc20eea520cdb816d75247b87ae860fa4",
    "onesa-drone": "005a92fe687756d8552fd64284bc88866742a9f9",
}
FIELDS = (
    "backend",
    "frontend",
    "browser",
    "documentation",
    "containers",
    "tls",
    "edge",
)
CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP_PYTHON = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
UPLOAD_ARTIFACT = "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9"
