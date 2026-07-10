"""RAG Pipeline Audit Report

## Root Cause Analysis

The poor retrieval of factual questions (e.g., "What was the sample size?") is caused by:

### 1. Chunking Strategy Issues
- Current chunk size (180-300 words) is too large for factual retrieval
- Chunks mix unrelated information (methodology + insurance payouts in same chunk)
- No structure preservation - headings/slide titles not highlighted
- Important keywords get diluted across large chunks

### 2. Query Rewriting Limitations
- Heuristic rewriting only fixes spelling ("mumbay" → "Mumbai")
- Doesn't expand research-specific terminology ("sample size" could become "methodology sample size respondents")
- No entity recognition or query expansion

### 3. Evidence Formatting
- Context block doesn't highlight key fields
- No emphasis on numerical data or methodology sections

### 4. Lack of Debug Visibility
- Cannot see what chunks are retrieved
- Cannot see similarity scores
- Cannot diagnose why wrong chunks are returned

## Recommended Fixes

### Fix 1: Structure-Aware Chunking
- Smaller chunks (80-120 words) for better precision
- Detect and preserve document structure (headings, slide titles, sheet names)
- Add structure markers: "=== METHODOLOGY ===" or "SLIDE 3: Results"

### Fix 2: Query Expansion
- Expand research terminology in query rewriting
- Add synonyms: "sample size" → "sample size respondents n= methodology"
- Add context hints for different query types

### Fix 3: Improved Prompt Engineering
- Explicit instructions to only use provided context
- Numerical answer detection and formatting
- Clear refusal for unsupported questions

### Fix 4: Debug Mode
- Show retrieved chunks with scores
- Show final context passed to LLM
- Enable pipeline debugging
"""

# Implementation will be done via edit to knowledge_base.py
# Status: Ready for integration