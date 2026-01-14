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
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # Claude Sonnet 4.0 (tested and working)
MAX_TOKENS = 4096
TEMPERATURE = 0.3  # Lower temperature for more factual extraction

# Validation settings
MIN_SOURCES_REQUIRED = 2  # Require at least 2 sources to auto-fill
CONFIDENCE_THRESHOLD = 0.8  # 80% confidence threshold for auto-fill

# Fields to extract
EXTRACTABLE_FIELDS = [
    # Basic info
    "institution",
    "availability",
    "release_date",
    "tons_produced_mt",
    "notes",
    "type",
    # Physical properties
    "density_g_cm3",
    "specific_gravity",
    "particle_size_distribution",
    "particle_morphology",
    "particle_ruggedness",
    # Chemical/mineralogical properties
    "glass_content_percent",
    "ti_content_percent",
    "nanophase_iron_content",
    # Quality metrics
    "nasa_fom_score",
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

Fields to extract (only fill if information is EXPLICITLY stated in the text):

BASIC INFO:
- institution: The institution or company that developed/produces this simulant
- availability: Current availability status (e.g., "Available", "Limited stock", "Production stopped")
- release_date: Year when the simulant was first released (number only, e.g., 2018)
- tons_produced_mt: Total tons produced in metric tons (number only)
- notes: Any relevant notes about the simulant (composition, applications, special features)
- type: Simulant type (e.g., "Mare", "Highland", "Geotechnical Simulant")

PHYSICAL PROPERTIES:
- density_g_cm3: Bulk density in g/cm³ (number only, e.g., 1.56)
- specific_gravity: Specific gravity value (number only)
- particle_size_distribution: Particle size range or distribution (e.g., "<1mm", "45-500 μm", "D50=75μm")
- particle_morphology: Shape description (e.g., "angular", "sub-angular", "rounded", "irregular")
- particle_ruggedness: Surface texture or ruggedness description

CHEMICAL/MINERALOGICAL:
- glass_content_percent: Glass/agglutinate content as percentage (number only, e.g., 49.3)
- ti_content_percent: Titanium (TiO2) content as weight percentage (number only)
- nanophase_iron_content: Nanophase iron (np-Fe⁰) content description or percentage

QUALITY METRICS:
- nasa_fom_score: NASA Figures of Merit score if mentioned (number or description)

Source Text:
{source_text}

Return ONLY a valid JSON object. Use null for fields where no information is found.
Example format:
{{"institution": "NASA", "density_g_cm3": 1.56, "glass_content_percent": 49.3, "particle_morphology": "angular", ...}}

IMPORTANT: Be precise and factual. Only extract values that are explicitly stated for THIS specific simulant ({simulant_name}). Do not confuse with other simulants mentioned in the same text."""

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
