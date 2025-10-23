
import pandas as pd
from sentence_transformers import SentenceTransformer, util

class SkillNormalizer:
    """Matches extracted multilingual skill terms to the official Belgian taxonomy."""

    def __init__(self, taxonomy_df: pd.DataFrame):
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.taxonomy = taxonomy_df
        self.skill_texts = (
            taxonomy_df["skill_nl"].fillna("").tolist()
            + taxonomy_df["skill_fr"].fillna("").tolist()
            + taxonomy_df["skill_en"].fillna("").tolist()
        )
        self.skill_texts = list(set([s for s in self.skill_texts if len(s) > 1]))
        self.embeddings = self.model.encode(self.skill_texts, convert_to_tensor=True)

    def normalize(self, extracted_skills: list, threshold=0.65):
        if not extracted_skills:
            return []
        query_embeds = self.model.encode(extracted_skills, convert_to_tensor=True)
        cosine_scores = util.cos_sim(query_embeds, self.embeddings)

        results = []
        for i, skill in enumerate(extracted_skills):
            best_idx = cosine_scores[i].argmax().item()
            best_score = cosine_scores[i][best_idx].item()
            if best_score >= threshold:
                best_skill = self.skill_texts[best_idx]
                # Find taxonomy row
                row = self.taxonomy[
                    (self.taxonomy["skill_nl"] == best_skill)
                    | (self.taxonomy["skill_fr"] == best_skill)
                    | (self.taxonomy["skill_en"] == best_skill)
                ].head(1)
                if not row.empty:
                    results.append({
                        "original": skill,
                        "standard_skill": best_skill,
                        "category": row["category"].iloc[0],
                        "score": round(best_score, 3),
                    })
        return results
