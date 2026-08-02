"""LLM-assisted diagnosis query expansion for ICD retrieval.

The expander translates a Vietnamese medical diagnosis mention into a structured
set of English query variants + semantic anchors that the ICD retriever uses.

The LLM is used ONLY for translation/normalization. It must never output ICD codes.
Final code selection is always done by the local ICD KB retriever.

Expansion results are cached to avoid repeated LLM calls.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

_VI_TO_EN_RULES: list[tuple[re.Pattern[str], str, list[str], str, list[str]]] = []

def _rule(vi_pattern: str, english: str, synonyms: list[str], site: str, must: list[str]) -> None:
    _VI_TO_EN_RULES.append((re.compile(vi_pattern, re.IGNORECASE), english, synonyms, site, must))

# Each rule: (Vietnamese regex, English normalized, synonyms, body_site, must_have_terms)
_rule(r"bu[oô]ng tr[uứ]ng \u0111a nang|polycystic ovar", "polycystic ovary syndrome", ["PCOS", "Stein-Leventhal syndrome"], "ovary", ["ovary", "polycystic"])
_rule(r"ru[oộ]t k[iíị]ch th[iíị]ch|irritable bowel", "irritable bowel syndrome", ["IBS"], "bowel", ["bowel", "irritable"])
_rule(r"nghi[eệ]n r[uượ][oợ]u|l[eệ] thu[oộ]c r[uượ][oợ]u", "alcohol dependence", ["alcohol use disorder", "alcohol dependence syndrome"], "alcohol", ["alcohol"])
_rule(r"x[oơ] v[uữ][aâ] [d\u0111][o\u00f4]ng m[a\u1ea1]ch|atherosclerosis", "atherosclerosis", ["arteriosclerosis"], "artery", ["atherosclerosis"])
_rule(r"ung th[uư] bi[eể]u m[oô] t[eế] b[aà]o m[a\u1ead]t|cholangiocarcinoma|bile duct carcinoma", "cholangiocarcinoma", ["bile duct carcinoma", "intrahepatic cholangiocarcinoma"], "bile duct", ["bile", "duct", "cholangiocarcinoma"])
_rule(r"ung th[uư] tuy[eế]n gi[a\u00e1]p|thyroid cancer|thyroid carcinoma", "thyroid cancer", ["thyroid carcinoma", "papillary thyroid"], "thyroid", ["thyroid"])
_rule(r"vi[eê]m [d\u0111][a\u1ea1] d[aà]y ru[oộ]t.*virus|viral gastroenteritis", "viral gastroenteritis", ["viral enteritis"], "gastrointestinal", ["viral", "gastroenteritis"])
_rule(r"lo[eé]t t[aá] tr[aà]ng|duodenal ulcer", "duodenal ulcer", [], "duodenum", ["duodenal", "ulcer"])
_rule(r"thi[eế]u men g6pd|thiếu g6pd|g6pd deficiency", "glucose-6-phosphate dehydrogenase deficiency", ["G6PD deficiency"], "red blood cell", ["G6PD", "glucose-6-phosphate"])
_rule(r"s[oỏ]i th[aậ]n|kidney stone|renal calculus", "kidney stone", ["renal calculus", "nephrolithiasis"], "kidney", ["kidney", "calculus"])
_rule(r"vi[eê]m [db]ao t[uử]|vi[eê]m [d\u0111][a\u1ea1] d[aà]y|gastritis", "gastritis", [], "stomach", ["gastritis", "stomach"])
_rule(r"Kawasaki|kawasaki", "Kawasaki disease", ["mucocutaneous lymph node syndrome"], "coronary", ["Kawasaki"])
_rule(r"[pP]arkinson|h[oộ]i ch[uứ]ng Parkinson", "Parkinson disease", ["parkinsonism"], "brain", ["Parkinson"])
_rule(r"v[oô] sinh|infertility", "infertility", [], "reproduction", ["infertility"])
_rule(r"xu[aấ]t huy[eế]t d[uướ][oớ]i nh[eệ]n|subarachnoid hemorrhage", "subarachnoid hemorrhage", ["SAH"], "brain", ["subarachnoid", "hemorrhage"])
_rule(r"t[uụ] m[aá]u d[uướ][oớ]i m[aà]ng c[uứ]ng|subdural hematoma", "subdural hematoma", [], "brain", ["subdural", "hematoma"])
_rule(r"x[oơ] gan|cirrhosis|liver cirrhosis", "liver cirrhosis", ["hepatic cirrhosis"], "liver", ["cirrhosis"])
_rule(r"ti[eể]u \u0111[uướ][oờ]ng|diabetes mellitus|di[aậ]b[eệ]t", "diabetes mellitus", ["DM", "type 2 diabetes"], "pancreas", ["diabetes"])
_rule(r"t[aă]ng huy[eế]t [aá]p|hypertension|high blood pressure", "hypertension", ["high blood pressure"], "cardiovascular", ["hypertension"])
_rule(r"suy tim|heart failure|cardiac failure", "heart failure", ["cardiac failure", "CHF"], "heart", ["heart", "failure"])
_rule(r"nh[oồ]i m[aá]u c[oơ] tim|myocardial infarction|heart attack", "myocardial infarction", ["heart attack", "MI"], "heart", ["myocardial", "infarction"])
_rule(r"tai bi[eế]n m[a\u1ea1]ch m[aá]u n[a\u00e3]o|stroke|[d\u0111][oộ]t qu[y\u1ef5]", "stroke", ["cerebrovascular accident", "CVA"], "brain", ["stroke", "cerebrovascular"])
_rule(r"vi[eê]m ph[oổ]i|pneumonia", "pneumonia", [], "lung", ["pneumonia"])
_rule(r"lao ph[oổ]i|tuberculosis|lao|TB", "tuberculosis", ["TB", "pulmonary tuberculosis"], "lung", ["tuberculosis"])
_rule(r"ung th[uư] ph[oổ]i|lung cancer", "lung cancer", ["pulmonary carcinoma", "bronchogenic carcinoma"], "lung", ["lung", "cancer"])
_rule(r"ung th[uư] vú|breast cancer", "breast cancer", ["mammary carcinoma"], "breast", ["breast", "cancer"])
_rule(r"ung th[uư] c[oổ] t[uử] cung|cervical cancer", "cervical cancer", ["cervical carcinoma"], "cervix", ["cervical", "cancer"])
_rule(r"ung th[uư] d[a\u1ea1] d[aà]y|gastric cancer|stomach cancer", "gastric cancer", ["stomach cancer", "gastric carcinoma"], "stomach", ["gastric", "cancer"])
_rule(r"ung th[uư] [d\u0111][a\u1ea1]i tr[aà]ng|colon cancer|colorectal", "colorectal cancer", ["colon cancer", "colorectal carcinoma"], "colon", ["colorectal", "cancer"])
_rule(r"ung th[uư] gan|hepatocellular|liver cancer", "hepatocellular carcinoma", ["liver cancer", "HCC"], "liver", ["liver", "hepatocellular"])
_rule(r"vi[eê]m gan B|hepatitis B", "hepatitis B", ["HBV hepatitis"], "liver", ["hepatitis"])
_rule(r"vi[eê]m gan C|hepatitis C", "hepatitis C", ["HCV hepatitis"], "liver", ["hepatitis"])
_rule(r"s[oố]t xu[aấ]t huy[eế]t|dengue", "dengue hemorrhagic fever", ["dengue"], "systemic", ["dengue", "hemorrhagic"])
_rule(r"c[uú]m|influenza", "influenza", ["flu"], "respiratory", ["influenza"])
_rule(r"covid|SARS-CoV-2", "COVID-19", ["SARS-CoV-2"], "respiratory", ["COVID"])
_rule(r"tr[aầ]m c[a\u1ea3]m|depression|depressive", "depressive disorder", ["major depression"], "mental", ["depression", "depressive"])
_rule(r"lo [aâ]u|anxiety disorder", "anxiety disorder", [], "mental", ["anxiety"])
_rule(r"t[aâ]m th[aầ]n ph[aâ]n li[eệ]t|schizophrenia", "schizophrenia", [], "mental", ["schizophrenia"])
# Skin / soft tissue
_rule(r"vi[eê]m m[oô] t[eế] b[aà]o|cellulitis", "cellulitis", ["skin infection"], "skin", ["cellulitis", "skin"])
# Infectious disease
_rule(r"b[eệ]nh d[aạ]i|ch[oó]|l[yý]ssavirus|rabies", "rabies", ["lyssavirus"], "nervous system", ["rabies", "lyssavirus"])
_rule(r"virus vi[eê]m gan B|vi[eê]m gan vi r[uú]t B|hepatitis B virus|HBV", "hepatitis B", ["HBV", "HBV hepatitis"], "liver", ["hepatitis", "liver"])
_rule(r"virus vi[eê]m gan C|vi[eê]m gan vi r[uú]t C|hepatitis C virus|HCV", "hepatitis C", ["HCV", "HCV hepatitis"], "liver", ["hepatitis", "liver"])
# Metabolic / systemic
_rule(r"amyloidosis|tho[aá]i h[oó]a tinh b[oộ]t|r[oố]i lo[aạ]n chuy[eể]n h[oó]a tinh b[oộ]t", "amyloidosis", [], "systemic", ["amyloid"])
_rule(r"t[aă]ng lipid m[aá]u|hyperlipidemia|dyslipidemia", "hyperlipidemia", ["dyslipidemia"], "blood", ["lipid"])
_rule(r"b[eé]o ph[iì]|obesity", "obesity", [], "metabolic", ["obesity"])
# Neuro
_rule(r"xu[aấ]t huy[eế]t n[aã]o|intracerebral hemorrhage", "intracerebral hemorrhage", ["cerebral hemorrhage"], "brain", ["hemorrhage", "intracerebral"])
_rule(r"b[aà]n ch[aâ]n b[eẹ]t|flat foot|pes planus", "pes planus", ["flat foot"], "foot", ["pes", "planus", "foot"])
_rule(r"viêm nha chu|periodontitis", "periodontitis", [], "oral", ["periodontitis"])
_rule(r"t[hị][uụ]y [đd][aậ]u|varicella|thủy đậu|zona|herpes zoster", "varicella zoster", ["chickenpox", "herpes zoster"], "skin", ["varicella", "zoster"])


@dataclass
class QueryExpansion:
    """Structured representation of an expanded diagnosis query."""
    original: str
    normalized_english: str = ""
    synonyms: list[str] = field(default_factory=list)
    body_site: str = ""
    must_have_terms: list[str] = field(default_factory=list)
    confidence: str = "low"

    def all_queries(self) -> list[tuple[str, float]]:
        """Return weighted (query, weight) pairs for retrieval."""
        queries: list[tuple[str, float]] = [(self.original, 1.0)]
        if self.normalized_english:
            queries.append((self.normalized_english, 0.95))
        for syn in self.synonyms:
            queries.append((syn, 0.90))
        if self.body_site and self.normalized_english:
            queries.append((f"{self.normalized_english} {self.body_site}", 0.70))
        return queries


class QueryExpanderProtocol(Protocol):
    def expand(self, mention: str) -> QueryExpansion: ...


def _normalize_vi(text: str) -> str:
    import unicodedata

    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn").replace("đ", "d")


class RuleBasedQueryExpander:
    """Fast deterministic expander using the rule dictionary above."""

    def expand(self, mention: str) -> QueryExpansion:
        text = mention.strip()
        normalized = _normalize_vi(text)
        normalized_fallbacks = [
            ("buong trung da nang", "polycystic ovary syndrome", ["PCOS", "Stein-Leventhal syndrome"], "ovary", ["ovary", "polycystic"]),
            ("ruot kich thich", "irritable bowel syndrome", ["IBS"], "bowel", ["bowel", "irritable"]),
            ("nghien ruou", "alcohol dependence", ["alcohol use disorder", "alcohol dependence syndrome"], "alcohol", ["alcohol"]),
            ("xo vua dong mach", "atherosclerosis", ["arteriosclerosis"], "artery", ["atherosclerosis"]),
            ("ung thu bieu mo te bao mat", "cholangiocarcinoma", ["bile duct carcinoma", "intrahepatic cholangiocarcinoma"], "bile duct", ["bile", "duct", "cholangiocarcinoma"]),
            ("viem mo te bao", "cellulitis", ["skin infection"], "skin", ["cellulitis", "skin"]),
            ("benh dai", "rabies", ["lyssavirus"], "nervous system", ["rabies", "lyssavirus"]),
            ("virus viem gan b", "hepatitis B", ["HBV", "HBV hepatitis"], "liver", ["hepatitis", "liver"]),
            ("viem gan vi rut b", "hepatitis B", ["HBV", "HBV hepatitis"], "liver", ["hepatitis", "liver"]),
            ("virus viem gan c", "hepatitis C", ["HCV", "HCV hepatitis"], "liver", ["hepatitis", "liver"]),
            ("viem gan vi rut c", "hepatitis C", ["HCV", "HCV hepatitis"], "liver", ["hepatitis", "liver"]),
            ("amyloidosis", "amyloidosis", [], "systemic", ["amyloid"]),
            ("thoai hoa tinh bot", "amyloidosis", [], "systemic", ["amyloid"]),
            ("roi loan chuyen hoa tinh bot", "amyloidosis", [], "systemic", ["amyloid"]),
            ("tang lipid mau", "hyperlipidemia", ["dyslipidemia"], "blood", ["lipid"]),
            ("beo phi", "obesity", [], "metabolic", ["obesity"]),
            ("ban chan bet", "pes planus", ["flat foot"], "foot", ["pes", "planus", "foot"]),
            ("viem nha chu", "periodontitis", [], "oral", ["periodontitis"]),
            ("thuy dau", "varicella zoster", ["chickenpox", "herpes zoster"], "skin", ["varicella", "zoster"]),
        ]
        for needle, english, synonyms, site, must in normalized_fallbacks:
            if needle in normalized:
                return QueryExpansion(text, english, list(synonyms), site, list(must), "high")
        for pattern, english, synonyms, site, must in _VI_TO_EN_RULES:
            if pattern.search(text) or pattern.search(normalized):
                return QueryExpansion(
                    original=text,
                    normalized_english=english,
                    synonyms=list(synonyms),
                    body_site=site,
                    must_have_terms=list(must),
                    confidence="high",
                )
        return QueryExpansion(original=text, confidence="low")


class LLMQueryExpander:
    """Use the loaded Qwen LLM to translate/normalize a diagnosis mention."""

    SYSTEM_PROMPT = (
        "You are a medical terminology expert. "
        "Given a Vietnamese medical diagnosis, return a JSON object with fields: "
        "normalized_english (string), synonyms (list of strings), "
        "must_have_terms (list of strings - key distinguishing words that any "
        "correct ICD entry must contain), body_site (string), confidence (high/medium/low). "
        "Do NOT output any ICD codes. Output JSON only, no prose."
    )

    def __init__(self, llm_extractor: object, cache_path: Path | None = None) -> None:
        self._llm = llm_extractor
        self._cache_path = cache_path or Path("data/processed/query_expansion_cache.json")
        self._cache: dict[str, dict] = self._load_cache()

    def _load_cache(self) -> dict[str, dict]:
        if self._cache_path.exists():
            try:
                return json.loads(self._cache_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_cache(self) -> None:
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache_path.write_text(
            json.dumps(self._cache, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def expand(self, mention: str) -> QueryExpansion:
        text = mention.strip()
        normalized_key = " ".join(text.casefold().split())
        if normalized_key in self._cache:
            cached = self._cache[normalized_key]
            return QueryExpansion(
                original=text,
                normalized_english=cached.get("normalized_english", ""),
                synonyms=cached.get("synonyms", []),
                body_site=cached.get("body_site", ""),
                must_have_terms=cached.get("must_have_terms", []),
                confidence=cached.get("confidence", "medium"),
            )
        try:
            result = self._call_llm(text)
            self._cache[normalized_key] = result
            self._save_cache()
            return QueryExpansion(original=text, **result)
        except Exception:
            return QueryExpansion(original=text, confidence="low")

    def _call_llm(self, mention: str) -> dict:
        llm = self._llm
        # Access tokenizer/model from LLMExtractor internals
        llm.load()  # type: ignore[attr-defined]
        tokenizer = llm._tokenizer  # type: ignore[attr-defined]
        model = llm._model  # type: ignore[attr-defined]

        import torch
        prompt = (
            f"<|im_start|>system\n{self.SYSTEM_PROMPT}<|im_end|>\n"
            f"<|im_start|>user\n{mention}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            ids = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.eos_token_id,
            )
        output = tokenizer.decode(ids[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
        start = output.find("{")
        end = output.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(output[start:end])
        raise ValueError("no JSON in LLM output")


class CachingQueryExpander:
    """Layered expander: rule-based first, LLM fallback with cache."""

    def __init__(
        self,
        llm_expander: QueryExpanderProtocol | None = None,
        cache_path: Path | None = None,
    ) -> None:
        self._rule = RuleBasedQueryExpander()
        self._llm = llm_expander
        self._cache_path = cache_path

    def expand(self, mention: str) -> QueryExpansion:
        result = self._rule.expand(mention)
        if result.confidence == "high" or self._llm is None:
            return result
        return self._llm.expand(mention)


__all__ = [
    "CachingQueryExpander",
    "LLMQueryExpander",
    "QueryExpansion",
    "RuleBasedQueryExpander",
]
