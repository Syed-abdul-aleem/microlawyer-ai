from __future__ import annotations

import logging
import os
import re
import threading

import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer
from supabase import Client, create_client

from app.config import settings


logger = logging.getLogger(__name__)

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
_embedding_model: "OnnxEmbeddingModel | None" = None
_embedding_model_lock = threading.Lock()


PROVINCE_DOMAINS = {"tenancy", "labor", "consumer"}
CRIMINAL_RETRIEVAL_COUNT = 15
DEFAULT_RETRIEVAL_COUNT = 5


def _retrieval_query(message: str, domain: str | None) -> str:
    if domain == "criminal":
        return (
            f"{message}\n"
            "FIR registration refusal, police station information, cognizable offence, "
            "Section 154, Code of Criminal Procedure 1898, police duty to record information"
        )
    return message


def _is_fir_registration_question(message: str) -> bool:
    text = message.lower()
    return any(term in text for term in ("fir", "register", "registration", "cognizable", "cognisable"))


def _deduplicate_and_rerank(sources: list[dict], message: str, domain: str | None) -> list[dict]:
    unique: dict[tuple[str, str], dict] = {}
    for source in sources:
        key = (source.get("source_act", ""), source.get("section_ref", ""))
        existing = unique.get(key)
        if existing is None or source.get("similarity", 0) > existing.get("similarity", 0):
            unique[key] = source

    results = list(unique.values())
    if domain == "criminal" and _is_fir_registration_question(message):
        for source in results:
            content = source.get("content", "").lower()
            boost = 0.0
            if re.search(r"(?:section\s*)?154\.", content):
                boost += 2.0
            if "information in cognizable cases" in content or "information in cognisable cases" in content:
                boost += 1.0
            if "police station" in content or "officer incharge" in content:
                boost += 0.2
            source["_retrieval_score"] = source.get("similarity", 0) + boost
        results.sort(key=lambda source: source.get("_retrieval_score", source.get("similarity", 0)), reverse=True)
        for source in results:
            source.pop("_retrieval_score", None)
    return results


class OnnxEmbeddingModel:
    def __init__(self) -> None:
        model_path = hf_hub_download(settings.embedding_onnx_model, "model.onnx")
        tokenizer_path = hf_hub_download(settings.embedding_onnx_model, "tokenizer.json")
        self.tokenizer = Tokenizer.from_file(tokenizer_path)
        self.tokenizer.enable_truncation(max_length=128)
        self.session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
            sess_options=self._session_options(),
        )
        self.input_names = {item.name for item in self.session.get_inputs()}

    @staticmethod
    def _session_options() -> ort.SessionOptions:
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
        return options

    def encode(self, text: str) -> list[float]:
        encoded = self.tokenizer.encode(text)
        inputs = {
            "input_ids": np.asarray([encoded.ids], dtype=np.int64),
            "attention_mask": np.asarray([encoded.attention_mask], dtype=np.int64),
            "token_type_ids": np.asarray([encoded.type_ids], dtype=np.int64),
        }
        outputs = self.session.run(None, {name: value for name, value in inputs.items() if name in self.input_names})
        embedding = np.asarray(outputs[0], dtype=np.float32).reshape(-1)
        embedding /= max(np.linalg.norm(embedding), 1e-12)
        return embedding.tolist()


def get_embedding_model() -> OnnxEmbeddingModel:
    global _embedding_model
    if _embedding_model is None:
        with _embedding_model_lock:
            if _embedding_model is None:
                logger.info("Loading ONNX embedding model on CPU: %s", settings.embedding_onnx_model)
                _embedding_model = OnnxEmbeddingModel()
                logger.info("ONNX embedding model loaded: %s", settings.embedding_onnx_model)
    return _embedding_model


def get_supabase() -> Client:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Supabase is not configured")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def retrieve(message: str, jurisdictions: list[str], domain: str | None) -> list[dict]:
    query_embedding = get_embedding_model().encode(_retrieval_query(message, domain))
    match_count = CRIMINAL_RETRIEVAL_COUNT if domain == "criminal" else DEFAULT_RETRIEVAL_COUNT
    response = get_supabase().rpc(
        "match_legal_docs",
        {
            "query_embedding": query_embedding,
            "match_jurisdictions": jurisdictions,
            "match_domain": domain,
            "match_count": match_count,
        },
    ).execute()
    raw_sources = response.data or []
    sources = _deduplicate_and_rerank(raw_sources, message, domain)
    source_acts = sorted({source.get("source_act", "unknown") for source in sources})
    section_refs = [source.get("section_ref", "unknown") for source in sources[:9]]
    message = (
        f"RAG retrieved {len(raw_sources)} raw / {len(sources)} unique chunks for jurisdictions={jurisdictions} "
        f"domain={domain} match_count={match_count} source_acts={source_acts} "
        f"top_sections={section_refs}"
    )
    logger.info(message)
    print(message, flush=True)
    return sources