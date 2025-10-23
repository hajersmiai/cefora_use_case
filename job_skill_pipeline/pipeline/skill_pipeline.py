
import json
import time
import tempfile
import os
from tqdm import tqdm
from nlp.skill_extractor import SkillExtractor
from nlp.normalize_skills import SkillNormalizer
from nlp.taxonomy_loader import TaxonomyLoader
from nlp.placeholders import PlaceholderManager

class SkillPipeline:
    """Pipeline for extracting and normalizing multilingual job skills."""

    def __init__(
        self,
        input_file: str,
        taxonomy_excel: str,
        output_file: str,
        per_request_delay: float = 0.5,
        save_every: int = 1,
        provider: str = "auto",
        model_name: str | None = None,
        max_retries: int = 3,
    ):
        self.input_file = input_file
        self.output_file = output_file
        # seconds to sleep after each LLM request to avoid rate limits
        self.per_request_delay = float(per_request_delay)
        # flush/save output after this many processed jobs (1 = save after every job)
        self.save_every = max(1, int(save_every))

        taxonomy_loader = TaxonomyLoader(taxonomy_excel)
        taxonomy_df = taxonomy_loader.load_all()

        # Initialize extractor with provider/model preferences and retry settings
        self.extractor = SkillExtractor(provider=provider, model_name=model_name, max_retries=max_retries)
        self.normalizer = SkillNormalizer(taxonomy_df)

    def combine_fields(self, job: dict) -> str:
        fields = [
            "functieomschrijving",
            "profiel",
            "professionele_vaardigheden",
            "persoonlijke_vaardigheden",
        ]
        return " ".join(str(job.get(f, "")) for f in fields if job.get(f)).strip()

    def process_jobs(self):
        with open(self.input_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        enriched = []
        total = len(jobs)
        for i, job in enumerate(tqdm(jobs, desc="Processing jobs"), start=1):
            text = self.combine_fields(job)
            if not text:
                continue

            extracted = self.extractor.extract(text)
            normalized = self.normalizer.normalize(extracted)

            job["raw_skills"] = [n["original"] for n in normalized]
            job["standard_skills"] = [n["standard_skill"] for n in normalized]
            job["skill_categories"] = [n["category"] for n in normalized]
            job["skill_mapping"] = normalized
            enriched.append(job)
            # Sleep between requests to reduce hitting rate limits
            if self.per_request_delay and self.per_request_delay > 0:
                time.sleep(self.per_request_delay)

            # Save incrementally every `save_every` jobs (atomic write)
            if i % self.save_every == 0 or i == total:
                dir_name = os.path.dirname(self.output_file) or "."
                with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name, encoding="utf-8") as tf:
                    json.dump(enriched, tf, ensure_ascii=False, indent=2)
                    temp_name = tf.name
                os.replace(temp_name, self.output_file)

        print(f"\n✅ Processed {len(enriched)} jobs → {self.output_file}")
