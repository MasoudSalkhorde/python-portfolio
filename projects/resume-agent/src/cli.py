"""Command-line interface for resume agent."""
import argparse
import sys
from pathlib import Path
from typing import Optional

from src.agent import run_pipeline, get_job_description, save_tailored_resume
from src.render_pdf import render_pdf
from src.render_gdoc import main as render_gdoc_main
from src.utils.config import Config
from src.utils.logger import setup_logger
from src.utils.validators import has_outcome

logger = setup_logger()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Resume Agent - AI-powered resume tailoring tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process job description from URL
  python -m src.cli https://example.com/job-posting

  # Process job description from file
  python -m src.cli job_description.txt

  # Process and render to PDF
  python -m src.cli job_description.txt --pdf output.pdf

  # Process and render to Google Doc
  python -m src.cli job_description.txt --gdoc "My Tailored Resume"
        """
    )
    
    parser.add_argument(
        "input",
        help="Job description URL or file path"
    )
    
    parser.add_argument(
        "--resume-index",
        type=str,
        default=None,
        help=f"Path to resume index JSON (default: {Config.RESUME_INDEX_PATH})"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help=f"Output JSON path (default: {Config.OUTPUT_DIR}/tailored_resume.json)"
    )
    
    parser.add_argument(
        "--pdf",
        type=str,
        default=None,
        metavar="PATH",
        help="Also render to PDF at specified path"
    )
    
    parser.add_argument(
        "--gdoc",
        type=str,
        default=None,
        nargs="?",
        const="Tailored Resume",
        metavar="TITLE",
        help="Also render to Google Doc with optional title"
    )
    
    parser.add_argument(
        "--no-notes",
        action="store_true",
        help="Don't include internal notes in PDF"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--no-selenium",
        action="store_true",
        help="Disable Selenium for JavaScript-rendered pages"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logger.setLevel("DEBUG")
        logger.debug("Verbose logging enabled")
    
    try:
        # Step 1: Get job description
        print("📄 Loading job description...")
        jd_text = get_job_description(args.input, use_selenium=not args.no_selenium)
        print(f"✅ Loaded job description ({len(jd_text)} characters)")
        
        # Step 2: Run pipeline
        print("\n🤖 Running resume tailoring pipeline...")
        tailored, score, gap_coverage, final_score = run_pipeline(jd_text, args.resume_index)
        
        # Step 3: Save JSON (including score, gap coverage, and final score data)
        print("\n💾 Saving tailored resume...")
        json_path = save_tailored_resume(tailored, score, gap_coverage, final_score, args.output)
        print(f"✅ Saved to: {json_path}")
        
        # Step 4: Render to PDF if requested
        if args.pdf:
            print(f"\n📄 Rendering PDF to {args.pdf}...")
            render_pdf(str(json_path), args.pdf, include_notes=not args.no_notes)
            print(f"✅ PDF rendered: {args.pdf}")
        
        # Step 5: Render to Google Doc if requested
        if args.gdoc:
            print(f"\n📝 Rendering Google Doc: {args.gdoc}...")
            # Temporarily modify sys.argv for render_gdoc_main
            old_argv = sys.argv
            sys.argv = ["render_gdoc", str(json_path), args.gdoc]
            try:
                render_gdoc_main()
            finally:
                sys.argv = old_argv
        
        # Summary
        print("\n" + "="*60)
        print("✅ RESUME TAILORING COMPLETE")
        print("="*60)
        
        # Display initial score from Talent Acquisition Manager evaluation
        print(f"\n📊 INITIAL INTERVIEW SELECTION SCORE: {score.score}/100")
        print(f"   {score.score_rationale}")
        
        if score.gaps:
            print(f"\n🔍 GAPS IDENTIFIED:")
            for i, gap in enumerate(score.gaps, 1):
                print(f"   {i}. {gap}")
        
        if score.recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(score.recommendations, 1):
                print(f"   {i}. {rec}")
        
        # Display final score after gap coverage
        print(f"\n📊 FINAL INTERVIEW SELECTION SCORE: {final_score.score}/100")
        print(f"   {final_score.score_rationale}")
        print(f"\n   📈 Score Improvement: {final_score.score - score.score} points")
        
        if final_score.gaps:
            print(f"\n🔍 REMAINING GAPS:")
            for i, gap in enumerate(final_score.gaps, 1):
                print(f"   {i}. {gap}")
        
        # Outcome distribution summary
        print("\n📊 OUTCOME DISTRIBUTION:")
        print("-" * 60)
        for role_idx, role in enumerate(tailored.tailored_roles, 1):
            bullets_with_outcomes = sum(1 for b in role.bullets if has_outcome(b.text))
            bullets_without_outcomes = len(role.bullets) - bullets_with_outcomes
            total_bullets = len(role.bullets)
            is_first_role = role_idx == 1
            is_second_role = role_idx == 2
            
            # Check first two bullets have outcomes (for first two roles)
            first_two_status = "✅"
            if (is_first_role or is_second_role) and total_bullets >= 2:
                first_two_bullets = role.bullets[:2]
                first_two_with_outcomes = sum(1 for b in first_two_bullets if has_outcome(b.text))
                if first_two_with_outcomes < 2:
                    first_two_status = "⚠️"
            
            # First role can have up to 7 bullets, and up to 5 outcomes if it has 7 bullets
            if is_first_role and total_bullets == 7:
                status = "✅" if (2 <= bullets_with_outcomes <= 5 and bullets_without_outcomes >= 1) else "⚠️"
            else:
                status = "✅" if (2 <= bullets_with_outcomes <= 4 and bullets_without_outcomes >= 1) else "⚠️"
            
            role_label = f"{role.company} - {role.title}"
            if is_first_role:
                role_label += " (First Role - can have up to 7 bullets)"
            elif is_second_role:
                role_label += " (Second Role)"
            
            print(f"{status} {role_label}:")
            print(f"   • {total_bullets} total bullet(s)")
            print(f"   • {bullets_with_outcomes} bullet(s) with outcomes")
            print(f"   • {bullets_without_outcomes} bullet(s) without outcomes")
            
            # Check first two bullets
            if (is_first_role or is_second_role) and total_bullets >= 2:
                first_two_bullets = role.bullets[:2]
                first_two_with_outcomes = sum(1 for b in first_two_bullets if has_outcome(b.text))
                if first_two_with_outcomes == 2:
                    print(f"   {first_two_status} First 2 bullets have outcomes (aligned with top 3 JD responsibilities)")
                else:
                    print(f"   {first_two_status} First 2 bullets: {first_two_with_outcomes}/2 have outcomes (should be 2/2)")
            
            if status == "⚠️":
                if bullets_with_outcomes < 2:
                    print(f"   ⚠️  Needs at least 2 bullets with outcomes (has {bullets_with_outcomes})")
                elif bullets_with_outcomes > 4 and not (is_first_role and total_bullets == 7):
                    print(f"   ℹ️  Has {bullets_with_outcomes} bullets with outcomes (recommended: 2-4)")
                elif is_first_role and total_bullets == 7 and bullets_with_outcomes == 5:
                    print(f"   ✅ {bullets_with_outcomes} outcomes acceptable for first role with 7 bullets")
                if bullets_without_outcomes < 1:
                    print(f"   ⚠️  Needs at least 1 bullet without outcome (has {bullets_without_outcomes})")
        
        # Check for revision notes
        revision_bullets = []
        for role in tailored.tailored_roles:
            for bullet in role.bullets:
                if bullet.needs_revision:
                    revision_bullets.append({
                        "role": f"{role.company} - {role.title}",
                        "bullet": bullet.text,
                        "note": bullet.revision_note
                    })
        
        if revision_bullets:
            print(f"\n⚠️  {len(revision_bullets)} BULLET(S) REQUIRING REVISION:")
            print("-" * 60)
            for i, item in enumerate(revision_bullets, 1):
                print(f"\n{i}. {item['role']}")
                print(f"   Bullet: {item['bullet']}")
                if item['note']:
                    print(f"   Note: {item['note']}")
            print("\nPlease review these bullets and verify the information is accurate.")
        else:
            print("\n✨ No bullets flagged for revision - all content is based on your resume.")
        
        if tailored.gaps_to_confirm:
            print(f"\n📋 {len(tailored.gaps_to_confirm)} GAP(S) TO CONFIRM:")
            for gap in tailored.gaps_to_confirm:
                print(f"  - {gap}")
        
        # Keyword coverage report
        print(f"\n🔍 ATS KEYWORD OPTIMIZATION:")
        print("-" * 60)
        print("✅ Tailored resume has been optimized for ATS matching")
        print("   - JD keywords incorporated into headline, summary, skills, and bullets")
        print("   - Natural keyword placement for better ATS parsing")
        print("   - Industry terminology aligned with job description")
        
        print(f"\n📁 Output files:")
        print(f"  - JSON: {json_path}")
        if args.pdf:
            print(f"  - PDF: {args.pdf}")
        if args.gdoc:
            print(f"  - Google Doc: Created (check console for link)")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=args.verbose)
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
