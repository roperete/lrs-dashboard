import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pycountry
from geopy.geocoders import Nominatim
from functools import lru_cache

class LRSParser:
    """Optimized parser for Lunar Regolith Simulant database"""
    
    def __init__(self, input_csv: str, output_dir: str = "."):
        self.input_csv = input_csv
        self.output_dir = Path(output_dir)
        self.df = pd.read_csv(input_csv)
        self.geolocator = Nominatim(user_agent="lrs_parser", timeout=10)
        
        # Pre-built country coordinates cache
        self.country_coords = self._init_country_coords()
        
    def _init_country_coords(self) -> Dict[str, Tuple[float, float]]:
        """Initialize country coordinates with common mappings"""
        return {
            # Major countries
            "USA": (38.9072, -77.0369), "US": (38.9072, -77.0369), 
            "United States": (38.9072, -77.0369),
            "China": (39.9042, 116.4074), "CN": (39.9042, 116.4074),
            "Japan": (35.6895, 139.6917), "JP": (35.6895, 139.6917),
            "Germany": (52.5200, 13.4050), "DE": (52.5200, 13.4050),
            "UK": (51.5074, -0.1278), "GB": (51.5074, -0.1278),
            "United Kingdom": (51.5074, -0.1278),
            "Canada": (45.4215, -75.6972), "CA": (45.4215, -75.6972),
            "Australia": (-35.2809, 149.1300), "AU": (-35.2809, 149.1300),
            "India": (28.6139, 77.2090), "IN": (28.6139, 77.2090),
            "South Korea": (37.5665, 126.9780), "KR": (37.5665, 126.9780),
            "Korea, South": (37.5665, 126.9780),
            "Russia": (55.7558, 37.6173), "RU": (55.7558, 37.6173),
            "Brazil": (-15.8267, -47.9218), "BR": (-15.8267, -47.9218),
            "France": (48.8566, 2.3522), "FR": (48.8566, 2.3522),
            "Italy": (41.9028, 12.4964), "IT": (41.9028, 12.4964),
            "Ital": (41.9028, 12.4964),
            "Spain": (40.4168, -3.7038), "ES": (40.4168, -3.7038),
            "Norway": (59.9139, 10.7522), "NO": (59.9139, 10.7522),
            "Thailand": (13.7563, 100.5018), "TH": (13.7563, 100.5018),
            "Turkey": (39.9334, 32.8597), "TR": (39.9334, 32.8597),
            "EU": (50.1109, 8.6821),
            "EU, Italy": (41.8719, 12.5674),
        }
    
    @lru_cache(maxsize=128)
    def _get_country_coords(self, country_code: str) -> Tuple[Optional[float], Optional[float]]:
        """Get coordinates for a country with caching"""
        if country_code in self.country_coords:
            return self.country_coords[country_code]
        
        # Try to geocode if not in cache
        try:
            country = pycountry.countries.get(alpha_2=country_code) or \
                     pycountry.countries.get(alpha_3=country_code) or \
                     pycountry.countries.get(name=country_code)
            
            if country:
                location = self.geolocator.geocode(country.name)
                if location:
                    coords = (location.latitude, location.longitude)
                    self.country_coords[country_code] = coords
                    return coords
        except:
            pass
        
        return (None, None)
    
    def parse_simulant(self) -> pd.DataFrame:
        """Parse simulant table"""
        simulant = self.df.rename(columns={
            "Simulant name": "name",
            "Type": "type",
            "Country": "country_code",
            "Institution": "institution",
            "Stage": "availability",
            "Release Date": "release_date",
            "Tons produced": "tons_produced_mt",
            "Notes": "notes"
        }).copy()
        
        # Generate IDs
        simulant.reset_index(inplace=True)
        simulant["simulant_id"] = simulant.index.map(lambda x: f"S{str(x+1).zfill(3)}")
        
        # Select columns
        return simulant[[
            "simulant_id", "name", "type", "country_code", "institution",
            "availability", "release_date", "tons_produced_mt", "notes"
        ]]
    
    def parse_composition(self, simulant_df: pd.DataFrame) -> pd.DataFrame:
        """Parse mineral composition data"""
        composition_rows = []
        comp_id = 1
        
        # Find mineral composition column
        mineral_cols = [c for c in self.df.columns if "Mineral Composition" in c]
        if not mineral_cols:
            return pd.DataFrame()
        
        mineral_col = mineral_cols[0]
        
        for idx, row in simulant_df.iterrows():
            sid = row["simulant_id"]
            comp_field = self.df.loc[idx, mineral_col] if idx < len(self.df) else None
            
            if pd.notna(comp_field):
                try:
                    data = json.loads(comp_field.replace("'", '"'))
                    
                    # Traverse nested structure
                    for category, minerals in data.items():
                        if isinstance(minerals, dict):
                            for mineral, val in minerals.items():
                                try:
                                    val = float(val)
                                    if val > 0:  # Only include non-zero values
                                        composition_rows.append({
                                            "composition_id": f"C{str(comp_id).zfill(3)}",
                                            "simulant_id": sid,
                                            "component_type": "mineral",
                                            "component_name": mineral,
                                            "value_pct": val
                                        })
                                        comp_id += 1
                                except (ValueError, TypeError):
                                    continue
                except json.JSONDecodeError:
                    continue
        
        return pd.DataFrame(composition_rows)
    
    def parse_chemical_composition(self, simulant_df: pd.DataFrame) -> pd.DataFrame:
        """Parse chemical (oxide) composition data"""
        chem_rows = []
        chem_id = 1
        
        for idx, row in simulant_df.iterrows():
            sid = row["simulant_id"]
            chem_field = self.df.loc[idx, "Chemical Composition"] if idx < len(self.df) else None
            
            if pd.notna(chem_field):
                try:
                    data = json.loads(chem_field.replace("'", '"'))
                    
                    if "Oxides" in data:
                        for oxide, val in data["Oxides"].items():
                            try:
                                val = float(val)
                                if val > 0:  # Only include non-zero values
                                    chem_rows.append({
                                        "composition_id": f"CH{str(chem_id).zfill(3)}",
                                        "simulant_id": sid,
                                        "component_type": "oxide",
                                        "component_name": oxide,
                                        "value_wt_pct": val
                                    })
                                    chem_id += 1
                            except (ValueError, TypeError):
                                continue
                except json.JSONDecodeError:
                    continue
        
        return pd.DataFrame(chem_rows)
    
    def parse_sites(self, simulant_df: pd.DataFrame) -> pd.DataFrame:
        """Parse site/location data"""
        site_rows = []
        
        for site_id, row in enumerate(simulant_df.itertuples(), start=1):
            country = str(row.country_code).strip() if pd.notna(row.country_code) else "Unknown"
            lat, lon = self._get_country_coords(country)
            
            site_rows.append({
                "site_id": f"X{str(site_id).zfill(3)}",
                "simulant_id": row.simulant_id,
                "site_name": row.institution if pd.notna(row.institution) else country,
                "site_type": "Lab",
                "country_code": country,
                "lat": lat,
                "lon": lon
            })
        
        return pd.DataFrame(site_rows)
    
    def parse_references(self, simulant_df: pd.DataFrame) -> pd.DataFrame:
        """Parse reference data"""
        ref_rows = []
        ref_id = 1
        
        for idx, row in simulant_df.iterrows():
            sid = row["simulant_id"]
            refs = self.df.loc[idx, "Reference"] if idx < len(self.df) else None
            
            if pd.notna(refs):
                # Split on multiple delimiters
                for delimiter in [";", "\n\n"]:
                    if delimiter in str(refs):
                        ref_list = str(refs).split(delimiter)
                        break
                else:
                    ref_list = [str(refs)]
                
                for ref in ref_list:
                    ref = ref.strip()
                    if ref:
                        ref_rows.append({
                            "reference_id": f"R{str(ref_id).zfill(3)}",
                            "simulant_id": sid,
                            "reference_text": ref
                        })
                        ref_id += 1
        
        return pd.DataFrame(ref_rows)
    
    def export_all(self):
        """Parse and export all tables to CSV and JSON"""
        print("🔄 Parsing database...")
        
        # Parse all tables
        simulant = self.parse_simulant()
        composition = self.parse_composition(simulant)
        chemical = self.parse_chemical_composition(simulant)
        sites = self.parse_sites(simulant)
        references = self.parse_references(simulant)
        
        # Export to CSV
        tables = {
            "simulant": simulant,
            "composition": composition,
            "chemical_composition": chemical,
            "site": sites,
            "references": references
        }
        
        print("\n📁 Exporting files...")
        for name, df in tables.items():
            csv_path = self.output_dir / f"{name}.csv"
            json_path = self.output_dir / f"{name}.json"
            
            df.to_csv(csv_path, index=False)
            df.to_json(json_path, orient="records", indent=2)
            
            print(f"   ✅ {name}.csv ({len(df)} rows)")
            print(f"   ✅ {name}.json")
        
        print("\n✨ All files exported successfully!")
        return tables


# Usage
if __name__ == "__main__":
    parser = LRSParser("Database - LRS Constituents - LRS types.csv")
    tables = parser.export_all()