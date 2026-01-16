# 🤖 Resume Agent

An AI-powered tool that automatically tailors your resume to match specific job descriptions using Large Language Models (LLMs). The agent intelligently selects the best base resume, extracts structured data, matches requirements, and generates a tailored resume while preserving factual accuracy and flagging content that needs your review.

## ✨ Features

- **🎯 Intelligent Resume Selection**: Automatically selects the best matching resume from your collection based on keyword matching
- **🌐 Web Scraping**: Supports job descriptions from URLs (LinkedIn, Indeed, company websites, etc.) or local files
- **🔍 Multi-Step Pipeline**: 
  - Extracts structured data from job descriptions and resumes
  - Matches requirements to your experience
  - Intelligently tailors content while preserving facts
- **⚠️ Revision Flags**: Automatically flags bullets that are far off from your original resume, requiring your review
- **📄 Multiple Output Formats**: Generate JSON, PDF, or Google Docs
- **🛡️ Validation**: Ensures no fabricated information (companies, dates, metrics)
- **📊 Progress Tracking**: Clear progress indicators and detailed logging
- **🔄 Retry Logic**: Robust error handling with automatic retries for API calls

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- (Optional) Google Cloud credentials for Google Docs rendering

## 🚀 Installation

1. **Clone the repository** (or navigate to the project directory)

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
   OPENAI_TEMPERATURE=0.2    # Optional, defaults to 0.2
   
   # Optional: Google Docs settings
   GOOGLE_TEMPLATE_DOC_ID=your_template_doc_id
   GOOGLE_CREDENTIALS_PATH=credentials.json
   GOOGLE_TOKEN_PATH=token.json
   ```

4. **Set up resume index**:
   Create `src/data/resumes/resume_index.json`:
   ```json
   [
     {
       "id": "resume1",
       "path": "path/to/resume1.pdf",
       "label": "Software Engineer Resume",
       "keywords": ["Python", "Django", "AWS", "PostgreSQL"]
     },
     {
       "id": "resume2",
       "path": "path/to/resume2.pdf",
       "label": "Data Scientist Resume",
       "keywords": ["Python", "Machine Learning", "TensorFlow", "Pandas"]
     }
   ]
   ```

## 📖 Usage

### Basic Usage

**From URL:**
```bash
python -m src.cli https://www.linkedin.com/jobs/view/1234567890
```

**From file:**
```bash
python -m src.cli job_description.txt
```

### Advanced Usage

**Generate PDF:**
```bash
python -m src.cli job_description.txt --pdf output.pdf
```

**Generate Google Doc:**
```bash
python -m src.cli job_description.txt --gdoc "My Tailored Resume"
```

**Full pipeline with all outputs:**
```bash
python -m src.cli https://example.com/job --pdf resume.pdf --gdoc "Tailored Resume"
```

**Verbose logging:**
```bash
python -m src.cli job_description.txt --verbose
```

**Custom resume index:**
```bash
python -m src.cli job_description.txt --resume-index custom_index.json
```

### Programmatic Usage

```python
from src.agent import run_pipeline, get_job_description, save_tailored_resume

# Get job description from URL or file
jd_text = get_job_description("https://example.com/job-posting")

# Run the pipeline
tailored = run_pipeline(jd_text)

# Save to file
output_path = save_tailored_resume(tailored)
print(f"Saved to: {output_path}")
```

## 📁 Project Structure

```
resume-agent/
├── src/
│   ├── agent.py              # Main pipeline logic
│   ├── cli.py                # Command-line interface
│   ├── render_pdf.py         # PDF rendering
│   ├── render_gdoc.py        # Google Docs rendering
│   └── utils/
│       ├── config.py         # Configuration management
│       ├── logger.py         # Logging setup
│       ├── schemas.py        # Pydantic data models
│       ├── prompts.py        # LLM prompts
│       ├── resume_selector.py # Resume selection logic
│       ├── io_pdf.py         # PDF text extraction
│       ├── validators.py     # Validation utilities
│       ├── web_scraper.py    # Web scraping for job descriptions
│       └── input_validator.py # Input validation
├── outputs/                  # Generated resumes (gitignored)
├── src/data/                 # Data files (gitignored)
│   └── resumes/              # Resume PDFs and index
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (gitignored)
└── README.md
```

## 🔧 How It Works

1. **Input**: Job description (URL or file)
2. **Resume Selection**: Selects best matching resume from your collection
3. **Extraction**: Extracts structured data from both JD and resume using LLMs
4. **Matching**: Matches JD requirements to your experience
5. **Tailoring**: Intelligently rewrites resume bullets to match the job
6. **Validation**: Ensures no fabricated information
7. **Output**: Generates tailored resume in JSON/PDF/Google Docs

### Revision Flagging

The agent automatically flags bullets that contain information significantly different from your original resume. These bullets will:
- Be marked with `needs_revision: true` in the JSON
- Include a `revision_note` explaining what needs review
- Be highlighted in red in PDF output
- Include revision notes in Google Docs

**When bullets are flagged:**
- New technologies/tools not in original resume
- New responsibilities outside the role's scope
- New metrics/numbers not in original
- New companies/partners not mentioned
- Skills or achievements that are completely new

## ⚙️ Configuration

Configuration is managed through environment variables and `src/utils/config.py`. Key settings:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: Model to use (default: `gpt-4o-mini`)
- `OPENAI_TEMPERATURE`: Temperature for generation (default: `0.2`)
- `OPENAI_MAX_RETRIES`: Max retry attempts (default: `3`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## 🛠️ Development

### Running Tests

```bash
# Add tests as needed
pytest tests/
```

### Code Structure

- **Error Handling**: Comprehensive try/except blocks with logging
- **Retry Logic**: Exponential backoff for API calls
- **Type Safety**: Pydantic models for all data structures
- **Logging**: Structured logging throughout

## 📝 Output Format

The tailored resume JSON includes:

```json
{
  "tailored_headline": "...",
  "tailored_summary": ["...", "..."],
  "tailored_skills": ["...", "..."],
  "tailored_roles": [
    {
      "company": "...",
      "title": "...",
      "dates": "...",
      "bullets": [
        {
          "text": "...",
          "source_bullet_ids": ["..."],
          "needs_revision": false,
          "revision_note": null
        }
      ]
    }
  ],
  "change_log": ["..."],
  "questions_for_user": ["..."],
  "gaps_to_confirm": ["..."]
}
```

## 🐛 Troubleshooting

**"OPENAI_API_KEY environment variable is required"**
- Make sure you have a `.env` file with your API key

**"Resume index file not found"**
- Create `src/data/resumes/resume_index.json` with your resume information

**"Failed to scrape job description"**
- The URL might be protected or require authentication
- Try copying the job description to a text file instead

**"Rate limit exceeded"**
- The agent will automatically retry with exponential backoff
- Consider using a model with higher rate limits

## 📄 License

You are free to use, modify, and distribute this project.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## ⚠️ Disclaimer

This tool is designed to help tailor your resume, but you should always:
- Review all generated content for accuracy
- Verify flagged bullets that need revision
- Ensure the tailored resume accurately represents your experience
- Customize the output to match your personal style

The agent preserves factual information but may need your input for content that's far from your original resume.
