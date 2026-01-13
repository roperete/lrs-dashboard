# AI Pipeline Testing Guide

## Setup Complete

All dependencies have been installed in a virtual environment.

## What's Ready

- Virtual environment created at `scripts/venv/`
- All Python packages installed (anthropic, PyPDF2, beautifulsoup4, etc.)
- PDF directory configured: `/home/alvaro/Spring - Forest on the moon/DIRT`
- Found 10+ PDF files, including relevant papers about lunar regolith simulants
- Configuration file ready at `scripts/.env`

## Next Step: Get Claude API Key

You need a Claude API key to run the extraction pipeline.

### How to Get Your API Key

1. Go to: https://console.anthropic.com/
2. Sign up for an account (or log in)
3. Click on "API Keys" in the sidebar
4. Click "Create Key"
5. Copy the API key (starts with `sk-ant-api03-...`)

**Free Trial**: You get $5 credit on signup, enough to test extensively.

### Add Your API Key

Once you have your key, edit the `.env` file:

```bash
cd ~/lrs-dashboard/scripts
nano .env
```

Replace this line:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxx...your-key-here
```

With your actual key:
```
ANTHROPIC_API_KEY=sk-ant-api03-[your-actual-key]
```

Save and exit (Ctrl+X, then Y, then Enter).

## Running Your First Test

Once you have the API key configured, test on a single simulant:

```bash
cd ~/lrs-dashboard/scripts
source venv/bin/activate
python test_pipeline_csv.py "JSC-1A"
```

This will:
1. Search local PDFs for mentions of JSC-1A
2. Search the web for information
3. Extract structured data using Claude AI
4. Validate across multiple sources
5. Output results to CSV and JSON files

### What to Expect

The test will take 30-60 seconds and show you:
- How many sources were found (PDFs + web)
- What data was extracted from each source
- Validation results with confidence scores
- Which fields can be auto-filled vs. need manual review

### Output Files

After the test completes, you'll find:
- `extraction_results.csv` - Summary table with all fields and confidence scores
- `extraction_results_S047.json` - Detailed extraction data with source attribution

### Review the Results

Open the CSV file to see:
- Extracted values for each field
- Confidence scores (0.0 to 1.0)
- Number of sources that agreed
- Status: AUTO-FILL or REVIEW

If the results look good, you can:
1. Test on more simulants: `python test_pipeline_csv.py "EAC-1" "LHS-1"`
2. Process multiple simulants at once
3. Eventually set up Google Sheets integration for automatic population

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Make sure you edited the `.env` file with your actual API key
- Check there are no extra spaces or quotes around the key

### "No sources found"
- This is normal for obscure simulants
- Try a well-known one like "JSC-1A" or "EAC-1" first

### "API rate limit"
- You're making requests too fast
- Wait 30 seconds and try again
- Process simulants in smaller batches

## Questions?

Check the full documentation in `README-AI-PIPELINE.md`
