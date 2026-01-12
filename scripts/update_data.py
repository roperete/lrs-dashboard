#!/usr/bin/env python3
"""
Update LRS Dashboard data from Google Sheets
Downloads the CSV from Google Sheets and runs the parser to generate JSON files
"""
import os
import sys
from pathlib import Path
import requests
from parser import LRSParser

# Google Sheets configuration
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")  # Will be set in GitHub secrets
SHEET_NAME = "LRS types"  # The sheet tab name

def download_csv_from_sheets(sheet_id: str, sheet_name: str, output_path: str):
    """Download CSV from Google Sheets"""
    # Using the public export URL (works if sheet is publicly readable)
    # Format: https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    print(f"📥 Downloading CSV from Google Sheets...")
    print(f"   Sheet ID: {sheet_id}")
    print(f"   Sheet Name: {sheet_name}")

    response = requests.get(url)
    response.raise_for_status()

    with open(output_path, 'wb') as f:
        f.write(response.content)

    print(f"   ✅ Downloaded to {output_path}")
    return output_path


def main():
    """Main execution"""
    print("=" * 60)
    print("LRS Dashboard Data Update")
    print("=" * 60)

    # Get sheet ID from environment
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        print("❌ Error: GOOGLE_SHEET_ID environment variable not set")
        sys.exit(1)

    # Paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    csv_path = script_dir / "temp_database.csv"
    output_dir = repo_root / "data"

    try:
        # Download CSV from Google Sheets
        download_csv_from_sheets(sheet_id, SHEET_NAME, str(csv_path))

        # Run parser
        print("\n🔄 Running parser...")
        parser = LRSParser(str(csv_path), str(output_dir))
        tables = parser.export_all()

        # Clean up temp file
        csv_path.unlink()

        print("\n" + "=" * 60)
        print("✅ Data update complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
