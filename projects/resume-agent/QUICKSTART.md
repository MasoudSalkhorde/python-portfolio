# 🚀 Quick Start Guide

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set Up Environment

Create a `.env` file in the project root (same level as `requirements.txt`):

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

Or if you already have one in `src/.env`, make sure it's accessible.

## Step 3: Set Up Resume Index

Create the directory structure and resume index file:

```bash
mkdir -p src/data/resumes
```

Create `src/data/resumes/resume_index.json`:

```json
[
  {
    "id": "resume1",
    "path": "src/data/resumes/my_resume.pdf",
    "label": "My Resume",
    "keywords": ["Python", "Machine Learning", "Data Science"]
  }
]
```

**Important**: Place your resume PDF file at the path specified in the index.

## Step 4: Run the Pipeline

### Option A: From a URL (Recommended)

```bash
python -m src.cli https://www.linkedin.com/jobs/view/1234567890
```

### Option B: From a Text File

1. Save the job description to a file (e.g., `job_description.txt`)
2. Run:
   ```bash
   python -m src.cli job_description.txt
   ```

### Option C: Generate PDF Output

```bash
python -m src.cli job_description.txt --pdf output.pdf
```

### Option D: Generate Google Doc

```bash
python -m src.cli job_description.txt --gdoc "My Tailored Resume"
```

## Output

The tailored resume will be saved to:
- **JSON**: `outputs/tailored_resume.json` (default)
- **PDF**: Path you specify with `--pdf`
- **Google Doc**: Created in your Google Drive (link shown in console)

## Troubleshooting

**"OPENAI_API_KEY environment variable is required"**
- Make sure your `.env` file is in the project root
- Check that the API key is correct

**"Resume index file not found"**
- Create `src/data/resumes/resume_index.json`
- Make sure the path is correct

**"Resume PDF not found"**
- Check that your PDF file exists at the path in `resume_index.json`
- Use absolute paths if relative paths don't work

## Example Workflow

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up .env file with your OpenAI API key

# 3. Create resume index with your resume PDF

# 4. Run the pipeline
python -m src.cli https://example.com/job-posting

# 5. Check outputs/tailored_resume.json for results
```
