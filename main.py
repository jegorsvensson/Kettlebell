from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from database import DBGoal, DBProject, DBResource, DBTask, DBUserContext, get_db
from models import ChatMessage

app = FastAPI(title="Life OS API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class RawInput(BaseModel):
    text: str


def ensure_prefs(db: Session) -> DBUserContext:
    prefs = db.query(DBUserContext).first()
    if not prefs:
        prefs = DBUserContext(max_daily_deep_work_mins=240, core_lessons="Start with short focused sessions.")
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


def smart_scheduler(db: Session):
    prefs = ensure_prefs(db)
    tasks = db.query(DBTask).filter(DBTask.status == "To Do", DBTask.scheduled_start.is_(None)).order_by(DBTask.priority_score.desc()).all()
    if not tasks:
        return

    current_date = datetime.now().date() + timedelta(days=1)
    current_time = datetime.combine(current_date, datetime.min.time()).replace(hour=9, minute=0)
    daily_minutes_used = 0

    for task in tasks:
        if daily_minutes_used + (task.estimated_minutes or 30) > prefs.max_daily_deep_work_mins:
            current_date += timedelta(days=1)
            current_time = datetime.combine(current_date, datetime.min.time()).replace(hour=9, minute=0)
            daily_minutes_used = 0

        task.scheduled_start = current_time
        task.scheduled_end = current_time + timedelta(minutes=task.estimated_minutes or 30)
        current_time = task.scheduled_end + timedelta(minutes=10)
        daily_minutes_used += task.estimated_minutes or 30

    db.commit()


def lightweight_intake(text: str) -> dict:
    phrases = [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]
    goal = phrases[0] if phrases else "General Improvement"
    project = f"{goal.title()} Plan"

    tasks = []
    resources = []
    for p in phrases:
        lowered = p.lower()
        tasks.append({
            "title": p[:120],
            "life_area": "Growth" if "learn" in lowered else "Admin",
            "estimated_minutes": 45 if "learn" in lowered else 30,
            "priority_score": 7 if any(k in lowered for k in ["fix", "pay", "deadline", "urgent"]) else 5,
            "cognitive_load": "Deep Focus" if "learn" in lowered else "Active",
            "sensory_requirement": "Mixed",
            "can_pair": "listen" in lowered or "walk" in lowered,
        })
        if "http" in lowered:
            resources.append({"title": f"Reference: {p[:40]}", "url": p})

    return {
        "goal": {"title": goal.title(), "life_area": "Growth", "expected_gain": "Progress", "time_horizon": "3 Months"},
        "project": {"title": project, "life_area": "Growth", "expected_gain": "Momentum"},
        "tasks": tasks,
        "resources": resources,
        "summary": f"Created 1 goal, 1 project, {len(tasks)} tasks.",
    }


@app.post("/api/intake")
def process_intake(input_data: RawInput, db: Session = Depends(get_db)):
    plan = lightweight_intake(input_data.text)

    db_goal = DBGoal(**plan["goal"])
    db.add(db_goal)
    db.flush()

    db_project = DBProject(**plan["project"], goal_id=db_goal.id)
    db.add(db_project)
    db.flush()

    for t in plan["tasks"]:
        db.add(DBTask(project_id=db_project.id, **t))
    for r in plan["resources"]:
        db.add(DBResource(project_id=db_project.id, **r))

    db.commit()
    smart_scheduler(db)
    return {"status": "success", "summary": plan["summary"]}


@app.get("/api/projects")
def get_all_projects(db: Session = Depends(get_db)):
    return db.query(DBProject).filter(DBProject.status != "Done").all()


@app.get("/api/projects/{project_id}/details")
def get_project_details(project_id: int, db: Session = Depends(get_db)):
    project = db.query(DBProject).options(joinedload(DBProject.tasks), joinedload(DBProject.resources)).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "title": project.title,
        "area": project.life_area,
        "tasks": [{"id": t.id, "title": t.title, "status": t.status} for t in project.tasks],
        "resources": [{"title": r.title, "url": r.url} for r in project.resources],
    }


@app.post("/api/projects/{project_id}/adapt")
def reflect_and_adapt(project_id: int, input_data: RawInput, db: Session = Depends(get_db)):
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.add(DBTask(title=f"Adaptation: {input_data.text[:60]}", life_area=project.life_area, estimated_minutes=30, project_id=project.id))
    db.commit()
    smart_scheduler(db)
    return {"status": "success", "summary": "Added adaptation task."}


@app.post("/api/chat/{entity_type}/{entity_id}")
def contextual_chat(entity_type: str, entity_id: int, chat_in: ChatMessage, db: Session = Depends(get_db)):
    if entity_type == "task":
        task = db.query(DBTask).filter(DBTask.id == entity_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"reply": f"Break '{task.title}' into 2 small steps and do the first in 10 minutes.", "actions_taken": 0}
    if entity_type == "project":
        project = db.query(DBProject).filter(DBProject.id == entity_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        db.add(DBTask(title=f"AI Suggestion: {chat_in.message[:40]}", life_area=project.life_area, estimated_minutes=25, project_id=project.id))
        db.commit()
        return {"reply": "Added one actionable task to keep momentum.", "actions_taken": 1}
    raise HTTPException(status_code=400, detail="Invalid type")


@app.get("/api/insights")
def get_insights(db: Session = Depends(get_db)):
    prefs = ensure_prefs(db)
    return {"max_minutes": prefs.max_daily_deep_work_mins, "core_lessons": prefs.core_lessons}


@app.post("/api/insights/reflect")
def global_reflection(input_data: RawInput, db: Session = Depends(get_db)):
    prefs = ensure_prefs(db)
    if "tired" in input_data.text.lower():
        prefs.max_daily_deep_work_mins = max(120, prefs.max_daily_deep_work_mins - 30)
    prefs.core_lessons = f"{prefs.core_lessons}\n- {input_data.text[:120]}"
    db.commit()
    return {"status": "success", "reply": "Updated preferences based on reflection."}


@app.get("/api/calendar/events")
def get_calendar_events(db: Session = Depends(get_db)):
    tasks = db.query(DBTask).filter(DBTask.scheduled_start.is_not(None), DBTask.status != "Done").all()
    return [{"id": t.id, "title": f"[{t.priority_score}] {t.title}", "start": t.scheduled_start.isoformat(), "end": t.scheduled_end.isoformat()} for t in tasks]


@app.get("/api/timeline/events")
def get_timeline_events(db: Session = Depends(get_db)):
    projects = db.query(DBProject).all()
    out = []
    for p in projects:
        tasks = db.query(DBTask).filter(DBTask.project_id == p.id, DBTask.scheduled_start.is_not(None)).all()
        if tasks:
            start_date = min(t.scheduled_start for t in tasks)
            end_date = max(t.scheduled_end for t in tasks)
        else:
            start_date = datetime.now()
            end_date = start_date + timedelta(days=14)
        out.append({"id": f"Project_{p.id}", "name": p.title, "start": start_date.strftime("%Y-%m-%d"), "end": end_date.strftime("%Y-%m-%d"), "progress": 0, "dependencies": ""})
    return out


@app.get("/api/tasks/{task_id}")
def get_task_details(task_id: int, db: Session = Depends(get_db)):
    task = db.query(DBTask).options(joinedload(DBTask.resources)).filter(DBTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Not found")
    links = [{"title": r.title, "url": r.url} for r in task.resources]
    return {"id": task.id, "title": task.title, "minutes": task.estimated_minutes, "area": task.life_area, "links": links}


@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Not found")
    task.status = "Done"
    db.commit()
    return {"status": "success"}
