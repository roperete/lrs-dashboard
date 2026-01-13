# AI-Powered Data Extraction Pipeline

Automatically extract and populate missing simulant data from scientific literature, supplier websites, and databases using Claude AI.

## 🎯 What It Does

This pipeline automatically:
1. **Searches multiple sources** for information about each simulant:
   - Local PDF papers
   - Web search (DuckDuckGo)
   - Supplier websites (Exolith Lab, Hispansion, etc.)
   - Academic databases
2. **Extracts structured data** using Claude API (GPT-4 level AI)
3. **Validates across sources** with multi-source fact-checking
4. **Detects conflicts** and assigns confidence scores
5. **Auto-fills high-confidence data** directly to Google Sheets
6. **Flags low-confidence data** for manual review
7. **Tracks provenance** for all auto-filled data

## 📊 Current Data Gaps

Your database has these gaps (perfect for AI extraction):
- **98.7% missing**: Tons Produced (74/75 simulants)
- **92% missing**: Notes (69/75 simulants)
- **54.7% missing**: Institution (41/75 simulants)
- **49.3% missing**: Release Date (37/75 simulants)

## 🏗️ Architecture

```
Simulant List
    │
    ├─→ [PDF Search] ────┐
    ├─→ [Web Scraping] ──┤
    ├─→ [Supplier Sites] ─┤───→ [Claude API] ───→ [Multi-Source Validation]
    └─→ [Academic Search] ┘         Extract              ↓
                                                    [High Confidence?]
                                                          │
                                              ┌───────────┴───────────┐
                                              ↓                       ↓
                                         [Auto-Fill]          [Manual Review]
                                              ↓                       │
                                      [Google Sheets] ←───────────────┘
                                              ↓
                                      [Existing Workflow]
                                              ↓
                                      [Live Site Updated]
```

## 📦 Installation

### 1. Install Python Dependencies

```bash
cd scripts
pip install -r requirements-ai.txt
```

### 2. Set Up API Keys

#### A. Anthropic (Claude) API Key

1. Sign up at https://console.anthropic.com/
2. Create an API key
3. Copy your key

#### B. Google Sheets API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable **Google Sheets API** and **Google Drive API**
4. Create a **Service Account**:
   - Go to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Name it (e.g., "lrs-data-pipeline")
   - Grant it "Editor" role
   - Click "Create Key" → JSON format
   - Download the JSON file
5. Share your Google Sheet with the service account email:
   - Open your sheet
   - Click "Share"
   - Add the service account email (found in the JSON file)
   - Give it "Editor" access

### 3. Configure Environment

Create a `.env` file in the `scripts/` directory:

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-xxx...your-key
GOOGLE_SHEETS_CREDENTIALS=./path/to/credentials.json

# Google Sheet
GOOGLE_SHEET_ID=1DutKZ4k1owfu9uawZWi5yNUc1xRYCMecq7eduATsz64

# PDF Directory (optional, defaults shown)
PDF_DIRECTORY=~/Spring - Forest on the moon/DIRT

# Validation Settings
MIN_SOURCES_REQUIRED=2
CONFIDENCE_THRESHOLD=0.8
```

## 🚀 Usage

### Test on a Single Simulant

```bash
python ai_data_pipeline.py \
    --credentials ./google-credentials.json \
    --simulants "JSC-1A"
```

### Process First 5 Simulants (Testing)

```bash
python ai_data_pipeline.py \
    --credentials ./google-credentials.json \
    --limit 5
```

### Process All Simulants

```bash
python ai_data_pipeline.py \
    --credentials ./google-credentials.json
```

### Process Specific Simulants

```bash
python ai_data_pipeline.py \
    --credentials ./google-credentials.json \
    --simulants "JSC-1A" "EAC-1" "LHS-1"
```

## 📋 What Happens

For each simulant, the pipeline:

1. **Identifies missing fields** (institution, release date, etc.)
2. **Searches for information**:
   ```
   📄 Searching local PDFs...
   🌐 Searching web...
   🏢 Checking supplier sites...
   ```
3. **Extracts with Claude**:
   ```
   🤖 Extracting data with Claude API...
      Found: institution, availability, release_date
   ```
4. **Validates across sources**:
   ```
   🔍 Validating across 3 sources...
      ✅ institution: "Orbitec, Inc." (confidence: 1.0, 3/3 sources agree)
      ⚠️  availability: Conflict detected (2 sources say "Stopped", 1 says "Unavailable")
   ```
5. **Auto-fills high confidence** (≥80% confidence, ≥2 sources):
   ```
   📝 Writing 3 fields to Google Sheets...
      ✅ Updated institution
      ✅ Updated release_date
      ⏭️  availability (requires review - conflict detected)
   ```

## 🔍 Multi-Source Validation

The pipeline uses smart validation:

### Auto-Fill Criteria
- ✅ **Confidence ≥ 80%**
- ✅ **At least 2 sources agree**
- ✅ **Value is not null**

### Manual Review Triggers
- ⚠️ Confidence < 80%
- ⚠️ Sources conflict
- ⚠️ Only 1 source found
- ⚠️ Ambiguous data

### Example:

```json
{
  "institution": {
    "value": "Orbitec, Inc.",
    "confidence": 1.0,
    "sources_agree": true,
    "num_sources": 3,
    "action": "✅ AUTO-FILL"
  },
  "availability": {
    "value": "Production stopped",
    "confidence": 0.66,
    "sources_agree": false,
    "all_values": ["Production stopped", "Unavailable"],
    "action": "⚠️ MANUAL REVIEW"
  }
}
```

## 📊 Output

### Console Output
Real-time progress with detailed logging:
```
==================================================
Gathering sources for: JSC-1A
==================================================
📄 Searching local PDFs...
   Found 2 PDF excerpts
🌐 Searching web...
   Found 3 web pages
🏢 Checking supplier sites...
   Found 1 supplier page
✅ Found 6 sources total

🤖 Extracting data with Claude API...
   🤖 Extracting from: PDF: lunar_simulants_2010.pdf
   🤖 Extracting from: Website: exolithsimulants.com
   ✅ Extracted data from 6/6 sources

🔍 Validating across 6 extractions...
✅ Validation complete:
   Auto-fill ready: 4 fields
   Review required: 2 fields

📝 Writing 4 fields to Google Sheets...
   ✅ Updated institution
   ✅ Updated release_date
   ✅ Updated tons_produced_mt
   ✅ Updated notes
   ✅ Successfully updated 4/4 fields

⚠️  2 fields require manual review:
   - availability: {"confidence": 0.66, "conflict": true}
   - type: {"confidence": 0.50, "num_sources": 1}
```

### Results File
Detailed results saved to `pipeline_results.json`:
```json
{
  "JSC-1A": {
    "status": "processed",
    "auto_filled": {
      "institution": "Orbitec, Inc.",
      "release_date": "2006",
      "tons_produced_mt": "30",
      "notes": "Mare basalt simulant, production stopped"
    },
    "review_required": {
      "availability": {...},
      "type": {...}
    },
    "sources_found": 6
  }
}
```

## 🔐 Security & Privacy

- **API keys** stored in `.env` (gitignored)
- **Service account** credentials separate file (gitignored)
- **Only updates empty fields** - never overwrites existing data
- **Provenance tracking** - all AI-filled data marked with source
- **Local processing** - your PDFs never leave your machine

## 💰 Cost Estimates

### Anthropic Claude API
- **Model**: Claude 3.5 Sonnet
- **Cost**: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- **Per simulant**: ~5,000 tokens (6 sources × ~800 tokens each)
- **Estimated cost**: ~$0.02-0.05 per simulant
- **75 simulants**: **~$1.50-4.00 total**

Very affordable for the time saved!

## 📝 Manual Review Workflow

After the pipeline runs, review flagged fields:

1. Check `pipeline_results.json` for `review_required` fields
2. Open Google Sheets
3. Review AI suggestions and sources
4. Manually fill or correct as needed
5. Re-run pipeline to fill remaining gaps

## 🎯 Best Practices

1. **Start small**: Test with `--limit 5` first
2. **Review results**: Check a few auto-filled entries manually
3. **Adjust thresholds**: Edit `config.py` if needed:
   ```python
   MIN_SOURCES_REQUIRED = 3  # Require more sources
   CONFIDENCE_THRESHOLD = 0.9  # Higher confidence needed
   ```
4. **Add sources**: Place relevant PDFs in your PDF directory
5. **Iterate**: Run pipeline, review, add sources, repeat

## 🔄 Integration with Existing Workflow

The AI pipeline **complements** your existing workflow:

```
Manual Data Entry (Google Sheets)
         │
         ↓
   [AI Pipeline] ← Optional: Fill missing data
         │
         ↓
GitHub Actions (Auto-commit)
         │
         ↓
Live Site Updated
```

You can:
- Run AI pipeline **before** manual entry (pre-populate)
- Run AI pipeline **after** manual entry (fill gaps)
- Mix both approaches

## 🐛 Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Create `.env` file with your API key

### "Google Sheets access denied"
- Share sheet with service account email
- Check credentials file path

### "No PDFs found"
- Verify `PDF_DIRECTORY` path in `.env`
- Check PDF files exist

### "No sources found for simulant X"
- Simulant name might be uncommon
- Try adding PDFs manually
- Web search might be rate-limited (wait and retry)

### "Claude API error: rate limit"
- You hit the API rate limit
- Wait a few minutes and resume
- Use `--limit` to process in smaller batches

## 📚 Further Reading

- [Anthropic Claude API Docs](https://docs.anthropic.com/)
- [Google Sheets API Docs](https://developers.google.com/sheets/api)
- [LRS Dashboard Repo](https://github.com/roperete/lrs-dashboard)

## 🙏 Credits

- **Claude AI** by Anthropic for intelligent extraction
- **Google Sheets API** for data writing
- **Open-source libraries**: PyPDF2, BeautifulSoup4, gspread, scholarly

---

**Happy automating!** 🚀

Questions? Open an issue on GitHub or check the main `README.md`.
