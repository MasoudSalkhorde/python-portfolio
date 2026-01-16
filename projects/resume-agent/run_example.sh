#!/bin/bash
# Example script to run the resume agent pipeline

echo "🚀 Resume Agent - Quick Run Example"
echo "===================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found in project root"
    echo "   Please create .env with your OPENAI_API_KEY"
    echo ""
fi

# Check if resume index exists
if [ ! -f "src/data/resumes/resume_index.json" ]; then
    echo "⚠️  Warning: Resume index not found"
    echo "   Please create src/data/resumes/resume_index.json"
    echo ""
fi

echo "To run the pipeline, use one of these commands:"
echo ""
echo "1. From URL:"
echo "   python -m src.cli https://example.com/job-posting"
echo ""
echo "2. From file:"
echo "   python -m src.cli job_description.txt"
echo ""
echo "3. With PDF output:"
echo "   python -m src.cli job_description.txt --pdf output.pdf"
echo ""
echo "4. With Google Doc output:"
echo "   python -m src.cli job_description.txt --gdoc 'My Resume'"
echo ""
echo "5. Verbose mode:"
echo "   python -m src.cli job_description.txt --verbose"
echo ""
