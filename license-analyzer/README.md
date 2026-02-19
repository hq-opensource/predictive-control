# License Analyzer Tool

This tool scans a repository for Python and Node.js dependencies, fetches their licenses from PyPI/NPM registries, and performs a compatibility check against the repository's main license.

## How it works
1. Scans for `pyproject.toml` and `package.json` files recursively.
2. Extracts package names.
3. Fetches license metadata via public APIs (no local installation required).
4. Generates a summary report.

## Usage

The process is divided into two parts to allow for human verification and cleanup in between.

### Step 1: Library Discovery & License Validation
1. Set your `GEMINI_API_KEY` in the `.env` file (see `.env.example`).
2. Run the discovery phase:
   - **Windows:** Run `.\run_first.ps1`
   - **Linux/macOS:** `python3 analyzer.py && python3 llm_validator.py`
3. This will generate `local_analysis.md`, `final_analysis.md`, and `references.md`.
4. **IMPORTANT**: Open `final_analysis.md` and manually group or clean the licenses if needed (e.g., merging "Apache 2" and "Apache-2.0").

### Step 2: GitHub Link Enrichment
1. Once `final_analysis.md` is cleaned and verified, run the linking phase:
   - **Windows:** Run `.\run_second.ps1`
   - **Linux/macOS:** `python3 llm_link_extractor.py`
2. This will generate `final_analysis_with_links.md`, which includes clickable GitHub repository links for every library in your inventory.

## Outputs
- `local_analysis.md`: Initial scan results using local files and basic registry metadata.
- `final_analysis.md`: The main clean report containing the consolidated library list.
- `references.md`: Detailed "Grounding" results from the LLM, including links and citations for all resolved licenses.
- `final_analysis_with_links.md`: The enriched final report with GitHub repository links.
- `licenses.json` & `licenses.yaml`: Machine-readable raw data.

## LLM Features
- **License Validation**: `llm_validator.py` uses Gemini Search Grounding to fix "Unknown" licenses.
- **Link Extraction**: `llm_link_extractor.py` uses Gemini Search Grounding to find official GitHub URLs for your dependencies.

## Compatibility Logic
The tool uses a simple heuristic for LiLiQ-P (permissive) compatibility:
- **Compatible:** MIT, Apache, BSD, etc.
- **Risk:** Copyleft licenses (GPL, AGPL) or Unknown licenses.
- **Untreated:** Licenses not recognized by the heuristic.
