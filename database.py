from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./lifeos_v6.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
    priority_score = Column(Integer, default=5)
    estimated_minutes = Column(Integer, default=30)
    energy_required = Column(String, default="Medium")
    cognitive_load = Column(String, default="Active")
    sensory_requirement = Column(String, default="Mixed")
    can_pair = Column(Boolean, default=False)
    paired_with_task_id = Column(Integer, nullable=True)
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


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
