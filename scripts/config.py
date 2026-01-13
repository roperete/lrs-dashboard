"""
Configuration for AI-powered data extraction pipeline
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys (stored in .env file)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "")

# Google Sheets configuration
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
SHEET_NAME = "LRS types"

# Data paths
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
PDF_DIRECTORY = Path(os.getenv("PDF_DIRECTORY", "~/Spring - Forest on the moon/DIRT")).expanduser()

# Extraction settings
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"  # Latest model
MAX_TOKENS = 4096
TEMPERATURE = 0.3  # Lower temperature for more factual extraction

# Validation settings
MIN_SOURCES_REQUIRED = 2  # Require at least 2 sources to auto-fill
CONFIDENCE_THRESHOLD = 0.8  # 80% confidence threshold for auto-fill

# Fields to extract
EXTRACTABLE_FIELDS = [
    "institution",
    "availability",
    "release_date",
    "tons_produced_mt",
    "notes",
    "type",  # Sometimes missing
]

# Supplier websites
SUPPLIER_SITES = {
    "Space Resources (Exolith Lab)": "https://exolithsimulants.com/",
    "Hispansion": "https://www.hispansion.com/",
    # Add more as needed
}

# Known simulant databases
SIMULANT_DATABASES = [
    "https://www.nasa.gov/",
    "https://www.esa.int/",
    # Add more official sources
]

# Extraction prompts
EXTRACTION_PROMPT_TEMPLATE = """You are a scientific data extraction assistant specializing in lunar regolith simulants.

Extract factual information about the following lunar simulant from the provided text.

Simulant Name: {simulant_name}
Simulant ID: {simulant_id}

Fields to extract (only fill if information is explicitly stated):
- institution: The institution or company that developed/produces this simulant
- availability: Current availability status (e.g., "Available", "Limited stock", "Production stopped")
- release_date: Year or date when the simulant was first released
- tons_produced_mt: Total tons produced (in metric tons), if mentioned
- notes: Any relevant notes about the simulant (composition, applications, special features)
- type: Simulant type (e.g., "Mare", "Highland", "Geotechnical Simulant")

Source Text:
{source_text}

Return ONLY a JSON object with the extracted fields. Use null for fields where no information is found.
Format: {{"institution": "...", "availability": "...", "release_date": "...", "tons_produced_mt": ..., "notes": "...", "type": "..."}}

Be precise and factual. Do not make assumptions."""

# Fact-checking prompt
FACT_CHECK_PROMPT = """You are verifying lunar simulant data extracted from multiple sources.

Simulant: {simulant_name}

Extracted data from {num_sources} sources:
{extracted_data}

Task: Resolve conflicts and determine the most reliable value for each field.

Rules:
1. If all sources agree, use that value with high confidence
2. If sources conflict, prefer more recent/official sources
3. If sources partially agree, note the discrepancy
4. Assign confidence score (0.0-1.0) for each field

Return JSON:
{{
  "field_name": {{
    "value": "resolved value or null",
    "confidence": 0.95,
    "sources_agree": true/false,
    "notes": "explanation if conflict"
  }},
  ...
}}"""
