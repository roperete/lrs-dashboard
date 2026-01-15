#!/usr/bin/env python3
"""
Spec Sheet / TDS PDF Extractor for Lunar Regolith Simulants

Designed to extract data from technical data sheets (TDS) and spec sheets.
Focuses on structured documents with known formats.

No API calls - uses local text/table parsing only.
"""
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
import pdfplumber

# Optional OCR dependencies
try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


@dataclass
class SimulantData:
    """Container for extracted simulant data"""
    simulant_id: str = ""
    name: str = ""
    source_file: str = ""

    # Basic info
    type: str = ""  # Mare, Highland, etc.
    series: str = ""
    nasa_fom_score: Optional[float] = None

    # Physical properties
    density_min: Optional[float] = None
    density_max: Optional[float] = None
    density_mean: Optional[float] = None
    particle_size_range: str = ""
    particle_size_median: Optional[float] = None
    particle_size_mean: Optional[float] = None
    aspect_ratio: Optional[float] = None
    circularity: Optional[float] = None
    cohesion_kpa: Optional[float] = None
    friction_angle_deg: Optional[float] = None
    magnetic_susceptibility: str = ""

    # Composition
    chemical_composition: Dict[str, float] = field(default_factory=dict)  # Oxides (wt%)
    mineral_composition: Dict[str, float] = field(default_factory=dict)   # Minerals (%)
    mineral_groups: Dict[str, float] = field(default_factory=dict)        # Grouped minerals

    # Raw materials
    raw_materials: List[str] = field(default_factory=list)

    # Metadata
    extraction_confidence: float = 0.0
    extraction_methods: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class SpecSheetExtractor:
    """Extract simulant data from technical data sheets and spec sheets"""

    # Standard oxide names with variations (handles PDF subscript formatting like "SiO\n2")
    OXIDE_PATTERNS = {
        'SiO2': [r'SiO[\s\n]*2', r'SiO2', r'Silicon\s*Dioxide'],
        'TiO2': [r'TiO[\s\n]*2', r'TiO2', r'Titanium\s*Dioxide'],
        'Al2O3': [r'Al[\s\n]*2[\s\n]*O[\s\n]*3', r'Al2O3', r'Aluminum\s*Oxide', r'Alumina'],
        'Fe2O3': [r'Fe[\s\n]*2[\s\n]*O[\s\n]*3', r'Fe2O3', r'Iron.*Oxide', r'Ferric\s*Oxide'],
        'FeO': [r'FeO(?![0-9\n])', r'Ferrous\s*Oxide'],
        'MgO': [r'MgO', r'Magnesium\s*Oxide', r'Magnesia'],
        'CaO': [r'CaO', r'Calcium\s*Oxide', r'Lime'],
        'Na2O': [r'Na[\s\n]*2[\s\n]*O', r'Na2O', r'Sodium\s*Oxide'],
        'K2O': [r'K[\s\n]*2[\s\n]*O', r'K2O', r'Potassium\s*Oxide'],
        'P2O5': [r'P[\s\n]*2[\s\n]*O[\s\n]*5', r'P2O5', r'Phosphorus\s*Pentoxide'],
        'MnO': [r'MnO', r'Manganese\s*Oxide'],
        'Cr2O3': [r'Cr[\s\n]*2[\s\n]*O[\s\n]*3', r'Cr2O3', r'Chromium\s*Oxide'],
        'NiO': [r'NiO', r'Nickel\s*Oxide'],
        'ZnO': [r'ZnO', r'Zinc\s*Oxide'],
        'SrO': [r'SrO', r'Strontium\s*Oxide'],
        'BaO': [r'BaO', r'Barium\s*Oxide'],
        'SO3': [r'SO[\s\n]*3', r'SO3', r'Sulfur\s*Trioxide'],
        'LOI': [r'LOI', r'Loss\s*on\s*Ignition'],
    }

    # Mineral patterns
    MINERAL_PATTERNS = {
        'anorthite': [r'anorthite'],
        'plagioclase': [r'plagioclase'],
        'augite': [r'augite'],
        'pyroxene': [r'pyroxene'],
        'clinopyroxene': [r'clinopyroxene', r'cpx'],
        'orthopyroxene': [r'orthopyroxene', r'opx'],
        'olivine': [r'olivine'],
        'forsterite': [r'forsterite', r'fosterite'],  # Common misspelling
        'fayalite': [r'fayalite'],
        'ilmenite': [r'ilmenite'],
        'glass': [r'glass', r'amorphous'],
        'basalt': [r'basalt'],
        'quartz': [r'quartz'],
        'feldspar': [r'feldspar'],
        'magnetite': [r'magnetite'],
        'hematite': [r'hematite'],
        'hornblende': [r'hornblende'],
        'analcime': [r'analcime'],
        'smectite': [r'smectite'],
        'illite': [r'illite'],
        'lizardite': [r'lizardite'],
        'serpentine': [r'serpentine'],
        'agglutinate': [r'agglutinate'],
    }

    def __init__(self):
        self.debug = False
        self.ocr_available = OCR_AVAILABLE

    def _extract_text_with_ocr(self, pdf_path: Path) -> str:
        """
        Extract text from PDF using OCR (for scanned documents).

        Returns extracted text or empty string if OCR is unavailable.
        """
        if not self.ocr_available:
            return ""

        try:
            # Convert PDF pages to images
            images = convert_from_path(pdf_path, dpi=300)

            ocr_text = ""
            for i, img in enumerate(images):
                # Extract text from each page image
                page_text = pytesseract.image_to_string(img)
                ocr_text += f"\n--- Page {i+1} ---\n"
                ocr_text += page_text

            return ocr_text
        except Exception as e:
            if self.debug:
                print(f"OCR extraction failed: {e}")
            return ""

    def extract_from_pdf(self, pdf_path: Path, use_ocr_fallback: bool = True) -> SimulantData:
        """Extract all data from a PDF spec sheet.

        Args:
            pdf_path: Path to the PDF file
            use_ocr_fallback: If True, use OCR when text extraction yields insufficient data
        """
        pdf_path = Path(pdf_path)
        data = SimulantData()
        data.source_file = pdf_path.name

        # Extract simulant name from filename
        data.name = self._extract_name_from_filename(pdf_path.name)

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Combine all text
                full_text = ""
                all_tables = []

                for page in pdf.pages:
                    text = page.extract_text() or ""
                    full_text += text + "\n"

                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)

                # Check if we have sufficient text (OCR fallback for scanned documents)
                if use_ocr_fallback and len(full_text.strip()) < 500 and self.ocr_available:
                    ocr_text = self._extract_text_with_ocr(pdf_path)
                    if ocr_text:
                        full_text = ocr_text
                        data.extraction_methods.append('ocr')
                        data.notes.append('Used OCR for text extraction (scanned document)')

                # Extract various data types
                self._extract_basic_info(full_text, data)
                self._extract_chemical_composition(full_text, all_tables, data)
                self._extract_mineral_composition(full_text, all_tables, data)
                self._extract_physical_properties(full_text, data)
                self._extract_raw_materials(full_text, data)

                # Calculate confidence
                data.extraction_confidence = self._calculate_confidence(data)

        except Exception as e:
            data.notes.append(f"Error during extraction: {str(e)}")

        return data

    def _extract_name_from_filename(self, filename: str) -> str:
        """Extract simulant name from filename"""
        # Remove extension
        name = filename.replace('.pdf', '').replace('.PDF', '')

        # Common patterns in TDS filenames
        patterns = [
            r'^([A-Z0-9]+-?[A-Z0-9]*(?:-[A-Z0-9]+)?)[_\s-]?(?:TDS|SDS|spec|sheet)',  # TLH-0_TDS.pdf
            r'^([A-Z0-9]+-?[A-Z0-9]*)[_\s-]',  # JSC-1A_...
            r'^([A-Z]{2,}[0-9-]+[A-Z0-9]*)',   # LMS-1, EAC-1A
        ]

        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return match.group(1).upper()

        # Fallback: first part before common separators
        for sep in ['_', ' - ', '-', ' ']:
            if sep in name:
                return name.split(sep)[0].strip()

        return name

    def _extract_basic_info(self, text: str, data: SimulantData):
        """Extract basic simulant info from text"""
        # Type (Mare, Highland, Low-Ti Mare, etc.) - capture full type including hyphens
        type_match = re.search(r'Type[:\s]+([A-Za-z]+(?:[-\s][A-Za-z]+)*)', text, re.IGNORECASE)
        if type_match:
            data.type = type_match.group(1).strip()
            data.extraction_methods.append('type_from_text')

        # Series
        series_match = re.search(r'Series[:\s]+([^\n]+)', text, re.IGNORECASE)
        if series_match:
            data.series = series_match.group(1).strip()

        # NASA FoM Score
        fom_patterns = [
            r'NASA\s+FoM\s+Score[:\s]+(\d+\.?\d*)\s*%?',
            r'FoM[:\s]+(\d+\.?\d*)\s*%?',
            r'Figures?\s+of\s+Merit[:\s]+(\d+\.?\d*)\s*%?',
            r'Mean\s+NASA\s+FoM\s+Score[:\s]+(\d+\.?\d*)\s*%?',
        ]
        for pattern in fom_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    data.nasa_fom_score = float(match.group(1))
                    data.extraction_methods.append('fom_from_text')
                    break
                except ValueError:
                    pass

    def _extract_chemical_composition(self, text: str, tables: List, data: SimulantData):
        """Extract chemical (oxide) composition"""
        # Method 1: Parse multi-line table format (common in TDS files)
        # Format: Line1=headers, Line2=subscripts, Line3=values
        self._parse_multiline_oxide_table(text, data)

        # Method 2: Parse from text using patterns (for inline data)
        if len(data.chemical_composition) < 5:
            chem_section = self._find_section(text, ['Chemical Composition', 'Oxide Composition', 'XRF'])
            search_text = chem_section if chem_section else text

            for oxide, patterns in self.OXIDE_PATTERNS.items():
                if oxide in data.chemical_composition:
                    continue  # Already found
                for pattern in patterns:
                    regex = rf'{pattern}[:\s]*(\d+\.?\d*)'
                    match = re.search(regex, search_text, re.IGNORECASE)
                    if match:
                        try:
                            value = float(match.group(1))
                            if 0 <= value <= 100:
                                data.chemical_composition[oxide] = value
                                break
                        except ValueError:
                            pass

        # Method 3: Parse pdfplumber tables for oxide data
        if len(data.chemical_composition) < 5:
            self._parse_oxide_tables(tables, data)

        if data.chemical_composition:
            data.extraction_methods.append('chemical_composition')

    def _parse_multiline_oxide_table(self, text: str, data: SimulantData):
        """Parse oxide table with headers, subscripts, and values on separate lines"""
        lines = text.split('\n')

        # Known oxide header patterns (without subscripts)
        oxide_headers = ['SiO', 'TiO', 'Al', 'Fe', 'MgO', 'CaO', 'Na', 'K', 'MnO', 'Cr', 'NiO', 'ZnO', 'SrO', 'P', 'BaO']

        for i, line in enumerate(lines):
            # Look for a line that contains multiple oxide names
            oxide_count = sum(1 for ox in oxide_headers if ox in line)
            if oxide_count >= 5:
                # This looks like an oxide header row
                # Check for values row (should be 1-3 lines below, skipping subscript line)
                for offset in [1, 2, 3]:
                    if i + offset >= len(lines):
                        break
                    values_line = lines[i + offset]

                    # Skip subscript lines (only single digits separated by spaces)
                    if self._is_subscript_line(values_line):
                        continue

                    # Check if this line contains actual values (numbers with decimals)
                    numbers = re.findall(r'(\d+\.?\d+)\*?', values_line)
                    if len(numbers) >= 5:
                        # Parse header and values together
                        self._match_oxide_headers_to_values(line, values_line, data)
                        if len(data.chemical_composition) >= 5:
                            return

    def _is_subscript_line(self, line: str) -> bool:
        """Check if a line is a subscript line (only single digits and spaces)"""
        # Remove spaces and check if only single digits remain
        cleaned = line.replace(' ', '')
        return cleaned.isdigit() and all(c in '0123456789' for c in cleaned) and len(cleaned) < 20

    def _match_oxide_headers_to_values(self, header_line: str, values_line: str, data: SimulantData):
        """Match oxide headers to their values using position alignment"""
        # Standard oxide order in most TDS tables
        oxide_order = [
            ('SiO', 'SiO2'), ('TiO', 'TiO2'), ('Al', 'Al2O3'), ('Fe', 'Fe2O3'),
            ('MgO', 'MgO'), ('CaO', 'CaO'), ('Na', 'Na2O'), ('K', 'K2O'),
            ('SrO', 'SrO'), ('MnO', 'MnO'), ('Cr', 'Cr2O3'), ('NiO', 'NiO'),
            ('ZnO', 'ZnO'), ('P', 'P2O5'), ('BaO', 'BaO')
        ]

        # Find positions of oxides in header
        header_positions = []
        for short_name, full_name in oxide_order:
            pos = header_line.find(short_name)
            if pos >= 0:
                header_positions.append((pos, full_name))

        # Sort by position
        header_positions.sort(key=lambda x: x[0])

        # Extract numeric values from values line
        values = re.findall(r'(\d+\.?\d*)\*?', values_line)

        # Match values to oxides (assuming same order)
        for idx, (pos, oxide_name) in enumerate(header_positions):
            if idx < len(values):
                try:
                    value = float(values[idx])
                    if 0 <= value <= 100:
                        data.chemical_composition[oxide_name] = value
                except ValueError:
                    pass

    def _extract_mineral_composition(self, text: str, tables: List, data: SimulantData):
        """Extract mineral composition"""
        # Method 1: Parse multi-line table format (common in TDS files)
        self._parse_multiline_mineral_table(text, data)

        # Method 2: Parse from text patterns (for inline data)
        if len(data.mineral_composition) < 3:
            mineral_section = self._find_section(text, ['Mineral Composition', 'Mineralogy', 'XRD'])
            search_text = mineral_section if mineral_section else text

            for mineral, patterns in self.MINERAL_PATTERNS.items():
                if mineral in data.mineral_composition:
                    continue
                for pattern in patterns:
                    regex = rf'{pattern}[:\s]*(\d+\.?\d*)\s*%?'
                    match = re.search(regex, search_text, re.IGNORECASE)
                    if match:
                        try:
                            value = float(match.group(1))
                            if 0 <= value <= 100:
                                data.mineral_composition[mineral] = value
                                break
                        except ValueError:
                            pass

        # Method 3: Parse pdfplumber tables for mineral data
        if len(data.mineral_composition) < 3:
            self._parse_mineral_tables(tables, data)

        # Method 4: Parse mineral groups section
        groups_section = self._find_section(text, ['Mineral Group', 'Group Classification'])
        if groups_section:
            for mineral, patterns in self.MINERAL_PATTERNS.items():
                for pattern in patterns:
                    regex = rf'{pattern}[:\s]*(\d+\.?\d*)\s*%?'
                    match = re.search(regex, groups_section, re.IGNORECASE)
                    if match:
                        try:
                            value = float(match.group(1))
                            if 0 <= value <= 100:
                                data.mineral_groups[mineral] = value
                                break
                        except ValueError:
                            pass

        if data.mineral_composition or data.mineral_groups:
            data.extraction_methods.append('mineral_composition')

    def _parse_multiline_mineral_table(self, text: str, data: SimulantData):
        """Parse mineral table with headers and values on separate lines"""
        lines = text.split('\n')

        # NASA standard mineral groups (for group classification table)
        nasa_groups = ['pyroxene', 'plagioclase', 'olivine', 'ilmenite', 'glass']

        # Detailed mineral header patterns (specific minerals, not groups)
        detailed_headers = ['Anorthite', 'Augite', 'Forsterite', 'Fosterite', 'Lizardite',
                           'Analcime', 'Smectite', 'Illite', 'Quartz', 'Hornblende', 'Amorphous',
                           'Enstatite']

        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Find values row (may be 1-2 lines below header)
            values_line = None
            values_offset = 0
            for offset in [1, 2]:
                if i + offset >= len(lines):
                    break
                candidate = lines[i + offset]
                numbers = re.findall(r'(\d+\.?\d*)', candidate)
                if len(numbers) >= 3 and not self._is_subscript_line(candidate):
                    # Check this isn't just "Table X:" or other text
                    if not candidate.lower().startswith('table'):
                        values_line = candidate
                        values_offset = offset
                        break

            if not values_line:
                continue

            # Combine header with continuation line if header wraps
            combined_header = line
            if values_offset == 2 and i + 1 < len(lines):
                # Header might wrap - combine lines
                next_line = lines[i + 1]
                if not re.match(r'^\d', next_line) and len(next_line) < 50:
                    combined_header = line + ' ' + next_line

            combined_lower = combined_header.lower()

            # Detect if this is a NASA mineral groups table (exactly 5 groups)
            nasa_count = sum(1 for g in nasa_groups if g in combined_lower)
            has_detailed = any(d.lower() in combined_lower for d in detailed_headers)

            if nasa_count >= 4 and not has_detailed:
                # This is a NASA mineral groups table - parse to mineral_groups
                self._match_mineral_groups_to_values(combined_header, values_line, data)
            elif has_detailed:
                # This is a detailed minerals table - parse to mineral_composition
                detailed_count = sum(1 for d in detailed_headers if d.lower() in combined_lower)
                if detailed_count >= 3:
                    self._match_mineral_headers_to_values(combined_header, values_line, data)

    def _match_mineral_groups_to_values(self, header_line: str, values_line: str, data: SimulantData):
        """Match NASA mineral group headers to values"""
        # Standard NASA mineral group order
        group_mapping = [
            ('pyroxene', 'Pyroxene'),
            ('plagioclase', 'Plagioclase Feldspar'),
            ('olivine', 'Olivine'),
            ('ilmenite', 'Ilmenite'),
            ('glass', 'Glass'),
        ]

        header_lower = header_line.lower()
        header_positions = []

        for keyword, group_name in group_mapping:
            pos = header_lower.find(keyword)
            if pos >= 0:
                header_positions.append((pos, group_name))

        header_positions.sort(key=lambda x: x[0])
        values = re.findall(r'(\d+\.?\d*)', values_line)

        for idx, (pos, group_name) in enumerate(header_positions):
            if idx < len(values):
                try:
                    value = float(values[idx])
                    if 0 <= value <= 100:
                        data.mineral_groups[group_name] = value
                except ValueError:
                    pass

    def _match_mineral_headers_to_values(self, header_line: str, values_line: str, data: SimulantData):
        """Match mineral headers to their values using position alignment"""
        # Map header keywords to mineral names
        mineral_mapping = {
            'anorthite': 'anorthite',
            'augite': 'augite',
            'enstatite': 'enstatite',
            'fosterite': 'forsterite',  # Handle common misspelling
            'forsterite': 'forsterite',
            'lizardite': 'lizardite',
            'analcime': 'analcime',
            'smectite': 'smectite',
            'illite': 'illite',
            'quartz': 'quartz',
            'hornblende': 'hornblende',
            'amorphous': 'glass',
            'glass': 'glass',
            'pyroxene': 'pyroxene',
            'plagioclase': 'plagioclase',
            'feldspar': 'feldspar',
            'olivine': 'olivine',
            'ilmenite': 'ilmenite',
        }

        # Find positions of minerals in header
        header_lower = header_line.lower()
        header_positions = []

        for keyword, mineral_name in mineral_mapping.items():
            pos = header_lower.find(keyword)
            if pos >= 0:
                header_positions.append((pos, mineral_name, keyword))

        # Sort by position and remove duplicates (keep first occurrence)
        header_positions.sort(key=lambda x: x[0])
        seen_positions = set()
        unique_positions = []
        for pos, mineral, keyword in header_positions:
            # Allow some overlap tolerance (e.g., "Amorphous/ Glass" has both amorphous and glass)
            if not any(abs(pos - p) < 3 for p in seen_positions):
                unique_positions.append((pos, mineral))
                seen_positions.add(pos)

        # Extract numeric values from values line
        values = re.findall(r'(\d+\.?\d*)', values_line)

        # Match values to minerals (assuming same order)
        for idx, (pos, mineral_name) in enumerate(unique_positions):
            if idx < len(values):
                try:
                    value = float(values[idx])
                    if 0 <= value <= 100:
                        # Don't overwrite if already have a value
                        if mineral_name not in data.mineral_composition:
                            data.mineral_composition[mineral_name] = value
                except ValueError:
                    pass

    def _extract_physical_properties(self, text: str, data: SimulantData):
        """Extract physical properties"""
        # Density patterns - process in specific order to avoid generic match overwriting specific
        density_patterns = [
            (r'Minimum\s+Density[:\s]*(\d+\.?\d*)\s*g/cm', 'density_min'),
            (r'Maximum\s+Density[:\s]*(\d+\.?\d*)\s*g/cm', 'density_max'),
            (r'Mean\s+Density[:\s]*(\d+\.?\d*)\s*g/cm', 'density_mean'),
        ]

        for pattern, attr in density_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    setattr(data, attr, float(match.group(1)))
                except ValueError:
                    pass

        # Fallback to generic density if mean not found
        if data.density_mean is None:
            fallback_patterns = [
                r'Bulk\s+Density[:\s]*(\d+\.?\d*)\s*g/cm',
                r'(?<!Minimum\s)(?<!Maximum\s)(?<!Mean\s)Density[:\s]*(\d+\.?\d*)\s*g/cm',
            ]
            for pattern in fallback_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        data.density_mean = float(match.group(1))
                        break
                    except ValueError:
                        pass

        # Particle size
        size_patterns = [
            (r'Range[:\s]*(\d+\.?\d*\s*-\s*\d+\.?\d*)\s*[µμ]m', 'particle_size_range'),
            (r'Median[:\s]*(\d+\.?\d*)\s*[µμ]m', 'particle_size_median'),
            (r'Mean[:\s]*(\d+\.?\d*)\s*[µμ]m', 'particle_size_mean'),
            (r'D50[:\s=]*(\d+\.?\d*)\s*[µμ]m', 'particle_size_median'),
        ]

        for pattern, attr in size_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1)
                if attr in ['particle_size_median', 'particle_size_mean']:
                    try:
                        setattr(data, attr, float(value))
                    except ValueError:
                        pass
                else:
                    setattr(data, attr, value)

        # Particle geometry
        aspect_match = re.search(r'Aspect\s+ratio[:\s]*(\d+\.?\d*)', text, re.IGNORECASE)
        if aspect_match:
            try:
                data.aspect_ratio = float(aspect_match.group(1))
            except ValueError:
                pass

        circ_match = re.search(r'Circularity[:\s]*(\d+\.?\d*)', text, re.IGNORECASE)
        if circ_match:
            try:
                data.circularity = float(circ_match.group(1))
            except ValueError:
                pass

        # Shear properties
        friction_match = re.search(r'(?:Internal\s+)?Angle\s+of\s+(?:Internal\s+)?Friction[^:]*[:\s]*(\d+\.?\d*)', text, re.IGNORECASE)
        if friction_match:
            try:
                data.friction_angle_deg = float(friction_match.group(1))
            except ValueError:
                pass

        cohesion_match = re.search(r'Cohesion[^:]*[:\s]*(\d+\.?\d*)\s*kPa', text, re.IGNORECASE)
        if cohesion_match:
            try:
                data.cohesion_kpa = float(cohesion_match.group(1))
            except ValueError:
                pass

        # Magnetic susceptibility
        mag_match = re.search(r'[χꭓ]\s*[=:]\s*([0-9.]+\s*x?\s*10[^m]*m[³3]/kg)', text, re.IGNORECASE)
        if mag_match:
            data.magnetic_susceptibility = mag_match.group(1).strip()

        if any([data.density_mean, data.particle_size_median, data.aspect_ratio]):
            data.extraction_methods.append('physical_properties')

    def _extract_raw_materials(self, text: str, data: SimulantData):
        """Extract raw material composition"""
        # Words that should not be raw materials
        exclude_words = ['mean', 'nasa', 'fom', 'score', 'european', 'sourced', 'manufactured',
                         'uses', 'type', 'series', 'overview', 'high-fidelity', 'general']

        # Look for composition section with bullet points
        comp_match = re.search(r'Composition[:\s]*\n((?:[•❖*-]\s*[A-Za-z\s]+\n?)+)', text, re.IGNORECASE)
        if comp_match:
            materials = comp_match.group(1)
            for line in materials.split('\n'):
                # Clean up bullet points and extract material name
                material = re.sub(r'^[•❖*-]\s*', '', line).strip()
                if material and len(material) > 2:
                    # Filter out false positives
                    material_lower = material.lower()
                    if not any(ex in material_lower for ex in exclude_words):
                        data.raw_materials.append(material)
            if data.raw_materials:
                data.extraction_methods.append('raw_materials')

    def _find_section(self, text: str, headers: List[str], max_length: int = 2000) -> Optional[str]:
        """Find a section of text by header"""
        for header in headers:
            pattern = rf'{header}[:\s]*\n([\s\S]*?)(?=\n\d+\.\s|\n[A-Z][a-z]+\s+[A-Z]|\Z)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)[:max_length]
        return None

    def _parse_oxide_tables(self, tables: List, data: SimulantData):
        """Parse tables for oxide composition data"""
        for table in tables:
            if not table or len(table) < 2:
                continue

            # Check if this looks like an oxide table
            header_row = ' '.join(str(cell) for cell in table[0] if cell)
            if any(ox in header_row for ox in ['SiO', 'TiO', 'Al2O', 'Fe']):
                # This is likely an oxide table
                self._parse_header_value_table(table, data.chemical_composition, self.OXIDE_PATTERNS)

    def _parse_mineral_tables(self, tables: List, data: SimulantData):
        """Parse tables for mineral composition data"""
        for table in tables:
            if not table or len(table) < 2:
                continue

            # Check if this looks like a mineral table
            header_row = ' '.join(str(cell) for cell in table[0] if cell)
            header_lower = header_row.lower()
            if any(m in header_lower for m in ['anorth', 'plagio', 'pyrox', 'olivine', 'glass']):
                self._parse_header_value_table(table, data.mineral_composition, self.MINERAL_PATTERNS)

    def _parse_header_value_table(self, table: List, target_dict: Dict, patterns: Dict):
        """Parse a table with headers in first row and values in second row"""
        if len(table) < 2:
            return

        header_row = table[0]
        value_row = table[1]

        # Build mapping of column index to component name
        col_mapping = {}
        for i, cell in enumerate(header_row):
            if not cell:
                continue
            cell_str = str(cell).strip()
            for component, component_patterns in patterns.items():
                for pattern in component_patterns:
                    if re.search(pattern, cell_str, re.IGNORECASE):
                        col_mapping[i] = component
                        break

        # Extract values
        for col_idx, component in col_mapping.items():
            if col_idx < len(value_row):
                cell = value_row[col_idx]
                if cell:
                    try:
                        value = float(str(cell).replace('*', '').strip())
                        if 0 <= value <= 100:
                            target_dict[component] = value
                    except ValueError:
                        pass

    def _calculate_confidence(self, data: SimulantData) -> float:
        """Calculate extraction confidence score"""
        score = 0.0

        # Name extracted from filename (usually reliable for TDS files)
        if data.name and len(data.name) > 2:
            score += 20

        # Type identified
        if data.type:
            score += 10

        # Chemical composition
        if len(data.chemical_composition) >= 5:
            score += 25
        elif len(data.chemical_composition) >= 3:
            score += 15
        elif len(data.chemical_composition) >= 1:
            score += 5

        # Mineral composition
        if len(data.mineral_composition) >= 5:
            score += 20
        elif len(data.mineral_composition) >= 3:
            score += 12
        elif len(data.mineral_composition) >= 1:
            score += 5

        # Physical properties
        if data.density_mean:
            score += 5
        if data.particle_size_median:
            score += 5
        if data.nasa_fom_score:
            score += 10

        # Composition reasonableness check
        total_oxides = sum(data.chemical_composition.values())
        if 90 <= total_oxides <= 105:
            score += 5

        return min(score, 100)

    def to_dict(self, data: SimulantData) -> Dict[str, Any]:
        """Convert SimulantData to dictionary"""
        return asdict(data)

    def to_json(self, data: SimulantData, indent: int = 2) -> str:
        """Convert SimulantData to JSON string"""
        return json.dumps(self.to_dict(data), indent=indent)


def main():
    """Test the extractor on TDS files"""
    import sys

    extractor = SpecSheetExtractor()

    # Find TDS files (deduplicate)
    pdf_dir = Path("/home/alvaro/Spring - Forest on the moon/DIRT/DIRT Papers/")
    tds_files = set(pdf_dir.glob("*TDS*.pdf")) | set(pdf_dir.glob("*_TDS.pdf"))
    tds_files = sorted(tds_files, key=lambda p: p.name)

    if not tds_files:
        print("No TDS files found. Checking for any PDFs...")
        tds_files = list(pdf_dir.glob("*.pdf"))[:3]

    print(f"Found {len(tds_files)} files to process\n")

    for pdf_path in tds_files:
        print(f"{'='*60}")
        print(f"Processing: {pdf_path.name}")
        print(f"{'='*60}")

        data = extractor.extract_from_pdf(pdf_path)

        print(f"\nSimulant: {data.name}")
        print(f"Type: {data.type}")
        print(f"NASA FoM Score: {data.nasa_fom_score}")
        print(f"Confidence: {data.extraction_confidence}%")
        print(f"Methods used: {', '.join(data.extraction_methods)}")

        if data.chemical_composition:
            print(f"\nChemical Composition ({len(data.chemical_composition)} oxides):")
            for oxide, value in sorted(data.chemical_composition.items()):
                print(f"  {oxide}: {value}%")

        if data.mineral_composition:
            print(f"\nMineral Composition ({len(data.mineral_composition)} minerals):")
            for mineral, value in sorted(data.mineral_composition.items()):
                print(f"  {mineral}: {value}%")

        if data.mineral_groups:
            print(f"\nMineral Groups:")
            for mineral, value in sorted(data.mineral_groups.items()):
                print(f"  {mineral}: {value}%")

        print(f"\nPhysical Properties:")
        print(f"  Density (mean): {data.density_mean} g/cm³")
        print(f"  Particle size (median): {data.particle_size_median} µm")
        print(f"  Aspect ratio: {data.aspect_ratio}")

        if data.raw_materials:
            print(f"\nRaw Materials: {', '.join(data.raw_materials)}")

        print()


if __name__ == "__main__":
    main()
