# run_pipeline.py
import sys
from pathlib import Path

# Ensure the project root is on sys.path so package imports like `nlp.*` work
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.skill_pipeline import SkillPipeline
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the skill extraction pipeline")
    parser.add_argument("--input", default="data/vdab_jobs_aiohttp_full_recent.json")
    parser.add_argument("--taxonomy", default="data/SkillsFramework.xlsx")
    parser.add_argument("--output", default="data/vdab_jobs_with_skills1.json")
    parser.add_argument("--delay", type=float, default=0.5, help="seconds to sleep after each LLM request")
    parser.add_argument("--save-every", type=int, default=1, help="save output after this many processed jobs")
    parser.add_argument("--provider", choices=["auto", "openai", "gemini"], default="auto", help="force LLM provider (auto = prefer OpenAI if key present)")
    parser.add_argument("--model", default=None, help="override model name to use for LLM calls (e.g. gpt-3.5-turbo, gemini-1)")
    parser.add_argument("--retries", type=int, default=3, help="number of retries for transient LLM errors (exponential backoff)")

    args = parser.parse_args()

    print("🚀 Starting Skill Extraction and Normalization Pipeline...\n")
    pipeline = SkillPipeline(
        args.input,
        args.taxonomy,
        args.output,
        per_request_delay=args.delay,
        save_every=args.save_every,
        provider=args.provider,
        model_name=args.model,
        max_retries=args.retries,
    )
    pipeline.process_jobs()
    print("\n🎯 Done — standardized multilingual skills dataset ready.")