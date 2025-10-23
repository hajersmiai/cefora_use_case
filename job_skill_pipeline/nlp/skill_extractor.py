
"""Skill extractor using LangChain LLMs with import shims and language detection."""

import json
import os
import openai
from dotenv import load_dotenv
from langdetect import detect, DetectorFactory
from difflib import SequenceMatcher
from typing import List, Optional

# Fix deterministic language detection results
DetectorFactory.seed = 0

# --- LLM imports with backward compatibility ---
try:
    from langchain_core.prompts import PromptTemplate
except Exception:
    from langchain.prompts import PromptTemplate

try:
    from langchain.chains import LLMChain
except Exception:
    try:
        from langchain import LLMChain
    except Exception:
        LLMChain = None

try:
    from langchain.chat_models import ChatOpenAI
except Exception:
    try:
        from langchain.chat_models.openai import ChatOpenAI
    except Exception:
        try:
            from langchain_core.chat_models import ChatOpenAI
        except Exception:
            ChatOpenAI = None

# --- Optional Gemini (Google) backend ---
genai = None
try:
    import google.generativeai as genai_lib
    genai = genai_lib
except Exception:
    genai = None


class SkillExtractor:
    """Extracts and normalizes skill names from multilingual job descriptions."""

    def __init__(self, provider: str = "auto", model_name: Optional[str] = None, max_retries: int = 3):
        load_dotenv()
        # allow overriding model and provider
        self.model_name = model_name or "gemini-2.0-flash"
        self.temperature = 0
        self.use_genai = False
        self.forced_provider = provider
        self.max_retries = max(0, int(max_retries))

        # Prefer Gemini if key + client available (unless user forced provider)
        genai_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GENAI_API_KEY")
        if (self.forced_provider in ("auto", "gemini")) and genai is not None and genai_key:
            try:
                genai.configure(api_key=genai_key)
                self.use_genai = True
            except Exception:
                self.use_genai = False

        # Fallback: LangChain / OpenAI (if forced to use openai or openai key exists)
        if (self.forced_provider in ("auto", "openai")) and not self.use_genai and ChatOpenAI is not None:
            try:
                self.llm = ChatOpenAI(model=self.model_name, temperature=self.temperature)
                self.use_langchain = True
            except Exception:
                self.llm = None
                self.use_langchain = False
        else:
            self.llm = None
            self.use_langchain = False

        # Build prompt
        self.prompt = PromptTemplate(
            input_variables=["text"],
            template=(
                "You are an expert in multilingual job description analysis. "
                "Extract only professional, technical, and soft skills (tools, technologies, competencies, certifications, methodologies) from the following text. "
                "Do NOT list audiences, recipient groups, departments or people groups (for example: 'production', 'management', 'customers') when they are mentioned as recipients of an action (e.g. 'communicate with production people', 'report to management'). "
                "Respond only with a JSON array of skill names (strings) in the original language of the text. Do not include any explanation or extra text.\n\n"
                "Examples:\n"
                "Input: 'You are an AI expert and communicate with production people'\nOutput: [\"AI\"]\n\n"
                "Input: 'Responsible for reporting to production and managing release pipelines'\nOutput: [\"release pipelines\", \"reporting\"]\n\n"
                "Text:\n{text}\n\nJSON list:"
            ),
        )

        if LLMChain is not None and self.use_langchain:
            self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        else:
            self.chain = None

        # Load OpenAI key if needed
        # Prefer OpenAI if the key is present in the environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        self.use_openai = False
        if self.openai_api_key:
            try:
                # set for older code paths
                openai.api_key = self.openai_api_key
            except Exception:
                pass
            # prefer OpenAI when a key exists
            self.use_openai = True

    # ------------------------------------------------------------------
    # 🔹 Helper: Detect dominant language (NL, FR, EN)
    # ------------------------------------------------------------------
    def detect_language(self, text: str) -> str:
        try:
            lang = detect(text)
            return {"nl": "nl", "fr": "fr", "en": "en"}.get(lang, "en")
        except Exception:
            return "en"

    # ------------------------------------------------------------------
    # 🔹 Helper: Compute text similarity
    # ------------------------------------------------------------------
    def similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    # ------------------------------------------------------------------
    # 🔹 Core extractor
    # ------------------------------------------------------------------
    def extract(self, text: str, job_title: str = "", taxonomy_skills: dict = None) -> List[str]:
        """Extracts skills from the text, filters by language, excludes job title matches."""

        if self.chain is not None:
            result = self.chain.run({"text": text})
        else:
            prompt_text = self.prompt.format(text=text)
            result = self._run_llm(prompt_text)

        # Parse JSON safely
        try:
            skills = json.loads(result)
            extracted = [s.strip() for s in skills if isinstance(s, str)]
        except Exception:
            extracted = [s.strip() for s in result.split(",") if len(s.strip()) > 1]

        # ------------------------------------------------------------------
        # 🧠 Detect language of the job text
        # ------------------------------------------------------------------
        job_lang = self.detect_language(text)

        # ------------------------------------------------------------------
        # 🚫 Filter out job title duplicates
        # ------------------------------------------------------------------
        filtered = []
        for s in extracted:
            if self.similarity(s, job_title) < 0.85:
                filtered.append(s)

        # ------------------------------------------------------------------
        # 🧾 Context-aware audience filtering
        # If a candidate term is used as a recipient/audience in the text
        # (e.g. 'communicate with production people'), drop it as a skill.
        # ------------------------------------------------------------------
        def is_audience_mention(term: str, full_text: str) -> bool:
            import re
            t = re.escape(term.lower())
            txt = full_text.lower()

            # language-specific patterns
            lang = self.detect_language(full_text)
            patterns = []
            if lang == 'en':
                patterns = [
                    rf"\b(with|to|for|among|together with|work with|work closely with|communicat(?:e|ing|ed) with|liaise with|coordinate with|report to)\b(?:\s+\w+){{0,5}}\s+{t}\b",
                    rf"\b{t}\b\s+(people|team|department|colleagues|stakeholders|customers|clients)\b",
                ]
            elif lang == 'nl':
                # Dutch patterns: 'met', 'naar', 'voor', 'samen met', 'werken met', 'rapporteren aan', 'communiceren met', etc.
                patterns = [
                    rf"\b(met|naar|voor|samen met|werken met|werk samen met|communiceren met|rapporteren aan|contact met|afstemming met)\b(?:\s+\w+){{0,5}}\s+{t}\b",
                    rf"\b{t}\b\s+(mensen|team|afdeling|collega's|belanghebbenden|klanten)\b",
                ]
            elif lang == 'fr':
                # French patterns: 'avec', 'pour', 'auprès de', 'travailler avec', 'rapporter à', 'communiquer avec'
                patterns = [
                    rf"\b(avec|pour|auprès de|travailler avec|reporter à|communiquer avec|coordonner avec|prendre contact avec)\b(?:\s+\w+){{0,5}}\s+{t}\b",
                    rf"\b{t}\b\s+(personnes|équipe|département|collègues|parties prenantes|clients)\b",
                ]
            else:
                # fallback to English-like patterns
                patterns = [
                    rf"\b(with|to|for|among|together with|work with|communicat(?:e|ing|ed) with|report to)\b(?:\s+\w+){{0,5}}\s+{t}\b",
                    rf"\b{t}\b\s+(people|team|department|colleagues|stakeholders|customers|clients)\b",
                ]

            for p in patterns:
                if re.search(p, txt):
                    return True
            return False

        post_filtered = [s for s in filtered if not is_audience_mention(s, text)]

        # ------------------------------------------------------------------
        # 🎯 Match only taxonomy skills in same language
        # ------------------------------------------------------------------
        if taxonomy_skills:
            standardized = []
            for skill in post_filtered:
                best_match = None
                best_score = 0
                for tskill in taxonomy_skills.get(job_lang, []):
                    score = self.similarity(skill, tskill)
                    if score > best_score:
                        best_score = score
                        best_match = tskill
                if best_score > 0.75:  # threshold
                    standardized.append(best_match)
                else:
                    standardized.append(skill)  # keep as-is if not matched
            return standardized

        return post_filtered

    # ------------------------------------------------------------------
    # 🔹 Fallback LLM caller
    # ------------------------------------------------------------------
    def _run_llm(self, prompt_text: str) -> str:
        """Handles Gemini or OpenAI raw API calls."""
        import time
        backoff = 1.0
        last_exc = None
        attempts = max(1, self.max_retries + 1)
        for attempt in range(attempts):
            try:
                # If OpenAI key exists prefer OpenAI; otherwise use Gemini if configured
                if self.use_openai:
                    # Use the new OpenAI client (openai.OpenAI). The legacy
                    # `openai.ChatCompletion` API was removed in openai>=1.0.
                    Client = getattr(openai, "OpenAI", None)
                    if Client is None:
                        raise RuntimeError(
                            "OpenAI client not available: please install openai>=1.0 and set OPENAI_API_KEY, or pin to openai==0.28 to use legacy API."
                        )
                    client = Client(api_key=self.openai_api_key) if self.openai_api_key else Client()
                    resp = client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt_text}],
                        temperature=self.temperature,
                    )
                    # New client: resp.choices[0].message.content
                    try:
                        return resp.choices[0].message.content
                    except Exception:
                        # Fallback to dict-like access
                        return getattr(resp.choices[0].message, "content", str(resp))
                elif self.use_genai and genai is not None:
                    model = genai.GenerativeModel(self.model_name)
                    resp = model.generate_content(prompt_text)
                    if hasattr(resp, "text") and resp.text:
                        return resp.text
                    if getattr(resp, "candidates", None):
                        first = resp.candidates[0]
                        return getattr(first, "content", None) or getattr(first, "message", None) or str(first)
                    return str(resp)
                else:
                    resp = openai.ChatCompletion.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt_text}],
                        temperature=self.temperature,
                    )
                    return resp["choices"][0]["message"]["content"]
            except Exception as e:
                last_exc = e
                msg = str(e).lower()
                is_transient = any(k in msg for k in ("rate", "quota", "429", "resourceexhausted", "rate_limit"))
                if attempt < attempts - 1 and is_transient:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise RuntimeError(f"LLM request failed: {e}")
