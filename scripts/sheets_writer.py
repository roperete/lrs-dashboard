"""
Google Sheets API integration for writing validated data
"""
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, List, Optional
import json
from datetime import datetime
from config import GOOGLE_SHEET_ID, SHEET_NAME


class SheetsWriter:
    """Write validated data back to Google Sheets"""

    def __init__(self, credentials_file: str):
        """
        Initialize Google Sheets client

        Args:
            credentials_file: Path to Google service account JSON credentials
        """
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(GOOGLE_SHEET_ID)
        self.worksheet = self.spreadsheet.worksheet(SHEET_NAME)

    def get_header_mapping(self) -> Dict[str, int]:
        """Get column index for each header"""
        headers = self.worksheet.row_values(1)
        return {header: idx + 1 for idx, header in enumerate(headers)}

    def find_simulant_row(self, simulant_name: str) -> Optional[int]:
        """Find the row number for a simulant by name"""
        try:
            cell = self.worksheet.find(simulant_name)
            return cell.row if cell else None
        except Exception as e:
            print(f"⚠️  Error finding simulant {simulant_name}: {e}")
            return None

    def update_field(
        self,
        simulant_name: str,
        field_name: str,
        value: any,
        provenance: str = ""
    ) -> bool:
        """
        Update a single field for a simulant

        Args:
            simulant_name: Name of the simulant
            field_name: Field to update (must match column header)
            value: New value
            provenance: Source/reason for the update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Find simulant row
            row = self.find_simulant_row(simulant_name)
            if not row:
                print(f"⚠️  Simulant {simulant_name} not found in sheet")
                return False

            # Find column
            headers = self.get_header_mapping()

            # Map internal field names to sheet column names
            field_mapping = {
                "institution": "Institution",
                "availability": "Stage",
                "release_date": "Release Date",
                "tons_produced_mt": "Tons produced",
                "notes": "Notes",
                "type": "Type"
            }

            sheet_column = field_mapping.get(field_name, field_name)

            if sheet_column not in headers:
                print(f"⚠️  Column '{sheet_column}' not found in sheet")
                return False

            col = headers[sheet_column]

            # Check if field is already filled
            current_value = self.worksheet.cell(row, col).value
            if current_value and current_value.strip():
                print(f"   ⏭️  Field '{field_name}' already has value '{current_value}', skipping")
                return False

            # Update the cell
            self.worksheet.update_cell(row, col, value)

            # Optionally add provenance tracking
            # (you could add a "Data Source" or "Last Updated" column)
            if provenance:
                provenance_col = headers.get("Data Source")
                if provenance_col:
                    timestamp = datetime.now().strftime("%Y-%m-%d")
                    provenance_text = f"{provenance} ({timestamp})"
                    self.worksheet.update_cell(row, provenance_col, provenance_text)

            print(f"   ✅ Updated {field_name} = {value} for {simulant_name}")
            return True

        except Exception as e:
            print(f"   ❌ Error updating {field_name} for {simulant_name}: {e}")
            return False

    def update_simulant(
        self,
        simulant_name: str,
        updates: Dict[str, any],
        provenance: str = "AI-extracted"
    ) -> Dict[str, bool]:
        """
        Update multiple fields for a simulant

        Args:
            simulant_name: Name of the simulant
            updates: Dict of {field_name: value}
            provenance: Source/reason for updates

        Returns:
            Dict of {field_name: success_bool}
        """
        results = {}

        for field, value in updates.items():
            if value is not None:
                success = self.update_field(simulant_name, field, value, provenance)
                results[field] = success

        return results

    def batch_update_simulants(
        self,
        simulant_updates: Dict[str, Dict[str, any]]
    ) -> Dict[str, Dict[str, bool]]:
        """
        Update multiple simulants at once

        Args:
            simulant_updates: Dict of {simulant_name: {field: value}}

        Returns:
            Dict of {simulant_name: {field: success}}
        """
        all_results = {}

        for simulant_name, updates in simulant_updates.items():
            print(f"\n📝 Updating {simulant_name}...")
            results = self.update_simulant(simulant_name, updates)
            all_results[simulant_name] = results

        return all_results

    def add_provenance_column(self):
        """Add a "Data Source" column if it doesn't exist"""
        headers = self.get_header_mapping()

        if "Data Source" not in headers:
            # Add new column header
            last_col = len(headers) + 1
            self.worksheet.update_cell(1, last_col, "Data Source")
            print("✅ Added 'Data Source' column for provenance tracking")


if __name__ == "__main__":
    # Test (requires credentials file)
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sheets_writer.py <credentials.json>")
        print("Example test - would update JSC-1A institution field")
        sys.exit(0)

    writer = SheetsWriter(sys.argv[1])
    writer.add_provenance_column()

    # Test update
    success = writer.update_field(
        "JSC-1A",
        "institution",
        "Orbitec, Inc.",
        "AI-extracted from scientific paper"
    )
    print(f"Update success: {success}")
