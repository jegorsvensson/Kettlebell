from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

Base = declarative_base()


class DBUserContext(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True, index=True)
    preferred_deep_work_time = Column(String, default="Morning")
    max_daily_deep_work_mins = Column(Integer, default=240)
    core_lessons = Column(Text, default="No specific habits learned yet. Observe the user.")


class DBTimeBlock(Base):
    __tablename__ = "time_blocks"
    id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(String)
    start_time = Column(String)
    end_time = Column(String)
    life_area = Column(String)


class DBGoal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    life_area = Column(String)
    expected_gain = Column(String)
    time_horizon = Column(String)
    projects = relationship("DBProject", back_populates="goal")


class DBProject(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    life_area = Column(String)
    expected_gain = Column(String)
    status = Column(String, default="Not Started")
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    goal = relationship("DBGoal", back_populates="projects")
    tasks = relationship("DBTask", back_populates="project")
    resources = relationship("DBResource", back_populates="project")


class DBTask(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    life_area = Column(String)
    expected_gain = Column(String)
    status = Column(String, default="To Do")
    priority_score = Column(Float, default=0)
    estimated_minutes = Column(Integer, default=60)
    energy_required = Column(String, default="medium")

    cognitive_load = Column(String, default="medium")
    sensory_requirement = Column(String, default="none")
    can_pair = Column(Boolean, default=False)
    paired_with_task_id = Column(Integer, nullable=True)

    urgency = Column(Integer, default=3)
    importance = Column(Integer, default=3)
    effort = Column(Integer, default=3)
    consistency_weight = Column(Float, default=1.0)

    hard_deadline = Column(Date, nullable=True)
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    project = relationship("DBProject", back_populates="tasks")

    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    sub_tasks = relationship("DBTask", backref="parent", remote_side=[id])

    resources = relationship("DBResource", back_populates="task")


class DBResource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    url = Column(String)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    project = relationship("DBProject", back_populates="resources")
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    task = relationship("DBTask", back_populates="resources")


class DBTaskDependency(Base):
    __tablename__ = "task_dependencies"
    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    depends_on_task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    dependency_type = Column(String, default="finish_to_start")


class DBRecurrenceRule(Base):
    __tablename__ = "recurrence_rules"
    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    rrule = Column(String, nullable=False)
    next_occurrence = Column(Date, nullable=True)


class DBInboxItem(Base):
    __tablename__ = "inbox_items"
    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text, nullable=False)
    source = Column(String, default="manual")
    captured_at = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String, default="new")
    processing_notes = Column(Text, default="")


class DBInboxClassification(Base):
    __tablename__ = "inbox_classifications"
    id = Column(Integer, primary_key=True, index=True)
    inbox_item_id = Column(Integer, ForeignKey("inbox_items.id"), nullable=False)
    sentence = Column(Text, nullable=False)
    guessed_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    linked_entity_type = Column(String, nullable=True)
    linked_entity_id = Column(Integer, nullable=True)


class DBScheduleBlock(Base):
    __tablename__ = "schedule_blocks"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    block_type = Column(String, default="focus")
    energy_band = Column(String, default="moderate")


class DBBehaviorSignal(Base):
    __tablename__ = "behavior_signals"
    id = Column(Integer, primary_key=True, index=True)
    signal_date = Column(Date, nullable=False)
    hour_of_day = Column(Integer, nullable=False)
    focus_score = Column(Float, nullable=False)
    fatigue_score = Column(Float, nullable=False)
    completion_ratio = Column(Float, nullable=False)
    notes = Column(Text, default="")


@dataclass(frozen=True)
class EntityInput:
    entity_type: str
    title: str
    description: str = ""
    parent_id: int | None = None
    life_area: str | None = None
    urgency: int = 3
    importance: int = 3
    expected_gain: int = 3
    effort: int = 3
    energy_required: int = 3
    cognitive_load: int = 3
    consistency_weight: float = 1.0
    sensory_requirement: str = "none"
    can_pair: bool = True
    due_date: date | None = None


class LifeOSRepository:
    def __init__(self, db_url: str = "sqlite:///./lifeos_v6.db") -> None:
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        self.engine = create_engine(db_url, connect_args=connect_args)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def close(self) -> None:
        self.engine.dispose()

    @contextmanager
    def session_scope(self):
        db: Session = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def add_entity(self, entity: EntityInput) -> int:
        with self.session_scope() as db:
            if entity.entity_type == "goal":
                model = DBGoal(title=entity.title, life_area=entity.life_area, expected_gain=str(entity.expected_gain), time_horizon="mid")
            elif entity.entity_type == "project":
                model = DBProject(title=entity.title, life_area=entity.life_area, expected_gain=str(entity.expected_gain))
            elif entity.entity_type == "resource":
                model = DBResource(title=entity.title, url=entity.description)
            else:
                model = DBTask(
                    title=entity.title,
                    life_area=entity.life_area,
                    expected_gain=str(entity.expected_gain),
                    urgency=entity.urgency,
                    importance=entity.importance,
                    effort=entity.effort,
                    estimated_minutes=max(30, entity.effort * 30),
                    energy_required=self._energy_to_band(entity.energy_required),
                    cognitive_load=self._load_to_band(entity.cognitive_load),
                    sensory_requirement=entity.sensory_requirement,
                    can_pair=entity.can_pair,
                    consistency_weight=entity.consistency_weight,
                    hard_deadline=entity.due_date,
                    parent_id=entity.parent_id,
                )
            db.add(model)
            db.flush()
            return int(model.id)

    def add_dependency(self, task_id: int, depends_on_task_id: int) -> None:
        with self.session_scope() as db:
            db.merge(DBTaskDependency(task_id=task_id, depends_on_task_id=depends_on_task_id))

    def set_recurrence(self, entity_id: int, rrule: str, next_occurrence: date | None = None) -> None:
        with self.session_scope() as db:
            db.merge(DBRecurrenceRule(task_id=entity_id, rrule=rrule, next_occurrence=next_occurrence))

    def add_inbox_item(self, raw_text: str, source: str = "manual") -> int:
        with self.session_scope() as db:
            item = DBInboxItem(raw_text=raw_text, source=source)
            db.add(item)
            db.flush()
            return int(item.id)

    def add_classifications(self, inbox_item_id: int, records: Iterable[tuple[str, str, float, int | None]]) -> None:
        with self.session_scope() as db:
            for sentence, guessed_type, confidence, linked_entity_id in records:
                db.add(
                    DBInboxClassification(
                        inbox_item_id=inbox_item_id,
                        sentence=sentence,
                        guessed_type=guessed_type,
                        confidence=confidence,
                        linked_entity_type="task" if linked_entity_id else None,
                        linked_entity_id=linked_entity_id,
                    )
                )

    def update_inbox_status(self, inbox_item_id: int, status: str, notes: str = "") -> None:
        with self.session_scope() as db:
            item = db.get(DBInboxItem, inbox_item_id)
            if item:
                item.processing_status = status
                item.processing_notes = notes

    def get_open_tasks(self) -> list[dict]:
        with self.session_scope() as db:
            tasks = db.execute(select(DBTask).where(DBTask.status != "Done")).scalars().all()
            rows: list[dict] = []
            for task in tasks:
                has_blockers = (
                    db.execute(
                        select(DBTaskDependency).join(DBTask, DBTask.id == DBTaskDependency.depends_on_task_id).where(
                            DBTaskDependency.task_id == task.id,
                            DBTask.status != "Done",
                        )
                    ).first()
                    is not None
                )
                rows.append(
                    {
                        "id": task.id,
                        "urgency": task.urgency,
                        "importance": task.importance,
                        "expected_gain": int(task.expected_gain or 3),
                        "effort": task.effort,
                        "cognitive_load": self._band_to_load(task.cognitive_load),
                        "consistency_weight": task.consistency_weight,
                        "can_pair": task.can_pair,
                        "sensory_requirement": task.sensory_requirement or "none",
                        "estimated_minutes": task.estimated_minutes or 60,
                        "has_blockers": has_blockers,
                    }
                )
            return rows

    def add_schedule_block(self, entity_id: int, starts_at: datetime, ends_at: datetime, energy_band: str, block_type: str = "focus") -> None:
        with self.session_scope() as db:
            db.add(DBScheduleBlock(task_id=entity_id, starts_at=starts_at, ends_at=ends_at, energy_band=energy_band, block_type=block_type))

    def get_schedule_blocks(self, day: date) -> list[DBScheduleBlock]:
        with self.session_scope() as db:
            start = datetime.combine(day, datetime.min.time())
            end = datetime.combine(day, datetime.max.time())
            return db.execute(
                select(DBScheduleBlock).where(DBScheduleBlock.starts_at >= start, DBScheduleBlock.starts_at <= end)
            ).scalars().all()

    @staticmethod
    def _energy_to_band(v: int) -> str:
        return "high" if v >= 4 else "medium" if v >= 2 else "low"

    @staticmethod
    def _load_to_band(v: int) -> str:
        return "high" if v >= 4 else "medium" if v >= 2 else "low"

    @staticmethod
    def _band_to_load(v: str) -> int:
        return {"high": 5, "medium": 3, "low": 1}.get(v or "medium", 3)


def get_db(repo: LifeOSRepository):
    db = repo.SessionLocal()
    try:
        yield db
    finally:
        db.close()
