from __future__ import annotations

import re
from dataclasses import dataclass

from .db import EntityInput, LifeOSRepository


CATEGORY_PATTERNS: dict[str, list[str]] = {
    "finance_admin": ["finance", "budget", "tax", "bank", "bill", "insurance"],
    "purchase": ["buy", "purchase", "order", "replace"],
    "goal": ["learn", "become", "improve", "master", "build habit"],
    "project": ["build", "launch", "plan", "create", "ship"],
    "task": ["fix", "clean", "call", "email", "write", "schedule", "book"],
    "resource": ["read", "watch", "article", "tutorial", "link", "course"],
    "reminder": ["remember", "remind", "don't forget"],
    "someday_maybe": ["someday", "maybe", "later", "eventually"],
}


@dataclass(frozen=True)
class ClassifiedSentence:
    sentence: str
    guessed_type: str
    confidence: float


class BrainDumpProcessor:
    """Turns raw user text into typed entities while preserving every sentence."""

    def __init__(self, repo: LifeOSRepository) -> None:
        self.repo = repo

    def process(self, raw_text: str, source: str = "manual") -> dict:
        inbox_id = self.repo.add_inbox_item(raw_text=raw_text, source=source)
        sentences = [s.strip(" -\n\t") for s in re.split(r"[\n,;.]+", raw_text) if s.strip()]
        classified = [self._classify_sentence(sentence) for sentence in sentences]

        links: list[tuple[str, str, float, int | None]] = []
        created = 0
        for item in classified:
            entity_id = self._upsert_entity(item)
            links.append((item.sentence, item.guessed_type, item.confidence, entity_id))
            if entity_id is not None:
                created += 1

        self.repo.add_classifications(inbox_id, links)
        self.repo.update_inbox_status(
            inbox_id,
            status="processed",
            notes=f"Processed {len(sentences)} segments; created/linked {created} entities",
        )

        return {
            "inbox_item_id": inbox_id,
            "segments": len(sentences),
            "entities_created_or_linked": created,
            "classifications": classified,
        }

    def _classify_sentence(self, sentence: str) -> ClassifiedSentence:
        normalized = sentence.lower()
        best_type = "task"
        best_score = 0

        for category, keywords in CATEGORY_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in normalized)
            if score > best_score:
                best_score = score
                best_type = category

        confidence = min(0.5 + best_score * 0.2, 0.95)
        return ClassifiedSentence(sentence=sentence, guessed_type=best_type, confidence=confidence)

    def _upsert_entity(self, item: ClassifiedSentence) -> int | None:
        type_map = {
            "goal": "goal",
            "project": "project",
            "task": "task",
            "resource": "resource",
            "reminder": "reminder",
            "finance_admin": "task",
            "purchase": "task",
            "someday_maybe": "someday",
        }
        entity_type = type_map[item.guessed_type]
        if item.guessed_type == "resource" and len(item.sentence.split()) < 2:
            return None

        urgency = 4 if item.guessed_type in {"task", "finance_admin"} else 2
        importance = 5 if item.guessed_type in {"goal", "project"} else 3
        expected_gain = 4 if item.guessed_type in {"goal", "project", "resource"} else 3
        effort = 2 if item.guessed_type in {"reminder", "purchase"} else 3

        return self.repo.add_entity(
            EntityInput(
                entity_type=entity_type,
                title=item.sentence[:120],
                description=f"Captured from inbox as {item.guessed_type}",
                urgency=urgency,
                importance=importance,
                expected_gain=expected_gain,
                effort=effort,
                cognitive_load=3,
                can_pair=item.guessed_type in {"purchase", "resource", "task"},
            )
        )
