from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from .db import LifeOSRepository


@dataclass(frozen=True)
class CapacityProfile:
    day: date
    total_hours: int = 6
    deep_work_hours: int = 3
    high_energy_start: time = time(9, 0)
    high_energy_end: time = time(12, 0)


class SchedulingEngine:
    def __init__(self, repo: LifeOSRepository) -> None:
        self.repo = repo

    @staticmethod
    def priority_score(task) -> float:
        if task["has_blockers"]:
            return -1
        score = (
            0.35 * task["urgency"]
            + 0.35 * task["importance"]
            + 0.20 * task["expected_gain"]
            + 0.10 * task["consistency_weight"]
            - 0.20 * task["effort"]
            - 0.15 * task["cognitive_load"]
        )
        return round(score, 3)

    def schedule_day(self, profile: CapacityProfile) -> list[dict]:
        tasks = self.repo.get_open_tasks()
        scored = sorted(
            [t for t in tasks if not t["has_blockers"]],
            key=self.priority_score,
            reverse=True,
        )

        blocks: list[dict] = []
        day_start = datetime.combine(profile.day, time(8, 0))
        cursor = day_start
        remaining = profile.total_hours
        deep_remaining = profile.deep_work_hours

        for task in scored:
            if remaining <= 0:
                break
            duration = self._estimate_duration(task)
            if duration > remaining:
                continue

            in_peak = profile.high_energy_start <= cursor.time() < profile.high_energy_end
            needs_deep = task["cognitive_load"] >= 4
            if needs_deep and (not in_peak or deep_remaining <= 0):
                continue

            start = cursor
            end = start + timedelta(hours=duration)
            energy_band = "high" if in_peak else "moderate"
            self.repo.add_schedule_block(task["id"], start, end, energy_band)
            blocks.append({"task_id": task["id"], "start": start, "end": end})

            remaining -= duration
            if needs_deep:
                deep_remaining -= duration
            cursor = end + timedelta(minutes=15)

            pair_id = self._find_pair_candidate(task, scored)
            if pair_id is not None:
                blocks[-1]["paired_with"] = pair_id

        return blocks

    def _find_pair_candidate(self, task, scored_tasks) -> int | None:
        if not task["can_pair"]:
            return None
        for candidate in scored_tasks:
            if candidate["id"] == task["id"] or not candidate["can_pair"]:
                continue
            sensory_mismatch = task["sensory_requirement"] == candidate["sensory_requirement"] and task["sensory_requirement"] != "none"
            if sensory_mismatch:
                continue
            if abs(task["cognitive_load"] - candidate["cognitive_load"]) >= 2:
                return int(candidate["id"])
        return None

    @staticmethod
    def _estimate_duration(task) -> int:
        base = 1
        if task["effort"] >= 4:
            base += 1
        if task["cognitive_load"] >= 4:
            base += 1
        return min(base, 3)
