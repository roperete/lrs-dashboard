# LRS Data Update Scripts

Automated pipeline for updating the LRS Dashboard data from Google Sheets.

## Files

- **parser.py** - LRSParser class that converts CSV to JSON files
- **update_data.py** - Main script that downloads CSV and runs parser
- **requirements.txt** - Python dependencies

## How It Works

```
Google Sheets
    ↓ (Download CSV via public URL)
scripts/update_data.py
    ↓ (Parse CSV)
scripts/parser.py
    ↓ (Generate JSON)
data/*.json
    ↓ (Auto-commit & push)
GitHub Pages (Live site updates)
```

## Setup

### 1. Make Your Google Sheet Publicly Readable

Your Google Sheet must be accessible via a public link:

1. Open your Google Sheet: "Database - LRS Constituents"
2. Click **Share** → **Change to anyone with the link**
3. Set to **Viewer** access
4. Copy the Sheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
   ```

### 2. Add Sheet ID to GitHub Secrets

1. Go to your GitHub repo: https://github.com/roperete/lrs-dashboard
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `GOOGLE_SHEET_ID`
5. Value: Paste your Sheet ID (just the ID, not the full URL)
6. Click **Add secret**

### 3. Trigger the Workflow

#### Manual Trigger (Recommended for testing)
1. Go to **Actions** tab in GitHub
2. Select **Update LRS Data** workflow
3. Click **Run workflow**
4. Click the green **Run workflow** button

The workflow will:
- Download CSV from your Google Sheet
- Run the parser
- Update JSON files in `/data`
- Commit and push changes
- GitHub Pages will auto-deploy the updated site

#### Automatic Schedule (Optional)
To enable automatic daily updates, edit `.github/workflows/update-data.yml` and uncomment these lines:
```yaml
schedule:
  - cron: '0 0 * * *'  # Daily at midnight UTC
```

## Local Testing

To test locally before pushing:

```bash
cd scripts

# Install dependencies
pip install -r requirements.txt

# Set your Google Sheet ID
export GOOGLE_SHEET_ID="your-sheet-id-here"

# Run the update
python update_data.py
```

This will download the CSV and generate updated JSON files in `../data/`.

## Troubleshooting

### "Sheet not found" or "Access denied"
- Make sure your Google Sheet is set to **Anyone with the link can view**
- Verify the Sheet ID is correct in GitHub secrets
- Check that the sheet tab name is exactly "LRS types" (case-sensitive)

### "No changes detected"
- This is normal if the data hasn't changed since the last run
- The workflow will skip the commit step

### Parser errors
- Check that your CSV has all required columns
- Review the parser logs in GitHub Actions for specific errors

## Monitoring

After running the workflow:
1. Go to **Actions** tab to see execution logs
2. Click on the workflow run to see detailed steps
3. Check the **Commit and push changes** step to see if data was updated

## Benefits

✅ No more manual CSV downloads
✅ No more running parser locally
✅ No more manual git commits
✅ One-click data updates
✅ Can schedule automatic updates
✅ Full audit trail in GitHub Actions logs
