"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import db

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
app.mount("/static", StaticFiles(directory="./static"), name="static")


# Default activities to seed when the database is empty
DEFAULT_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
}


def _serialize_activity(activity: db.Activity) -> dict:
    return {
        "description": activity.description,
        "schedule": activity.schedule,
        "max_participants": activity.max_participants,
        "participants": [p.email for p in activity.participants],
    }


def _seed_activities(db_session: Session) -> None:
    """Seed the database with default activities if empty."""
    existing = db_session.query(db.Activity).count()
    if existing > 0:
        return

    for name, details in DEFAULT_ACTIVITIES.items():
        activity = db.Activity(
            name=name,
            description=details["description"],
            schedule=details["schedule"],
            max_participants=details["max_participants"],
        )
        db_session.add(activity)
        db_session.flush()  # get id

        for email in details["participants"]:
            participant = db.Participant(email=email, activity=activity)
            db_session.add(participant)

    db_session.commit()


@app.on_event("startup")
def on_startup():
    db.init_db()
    # Seed initial activities if the database is new/empty
    with db.SessionLocal() as session:
        _seed_activities(session)


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities(db_session: Session = Depends(db.get_db)):
    activities = db_session.query(db.Activity).all()
    return {activity.name: _serialize_activity(activity) for activity in activities}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, db_session: Session = Depends(db.get_db)):
    """Sign up a student for an activity"""
    activity = db_session.query(db.Activity).filter_by(name=activity_name).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if any(p.email == email for p in activity.participants):
        raise HTTPException(status_code=400, detail="Student is already signed up")

    if len(activity.participants) >= activity.max_participants:
        raise HTTPException(status_code=400, detail="Activity is already full")

    participant = db.Participant(email=email, activity=activity)
    db_session.add(participant)
    db_session.commit()

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, db_session: Session = Depends(db.get_db)):
    """Unregister a student from an activity"""
    activity = db_session.query(db.Activity).filter_by(name=activity_name).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    participant = next((p for p in activity.participants if p.email == email), None)
    if not participant:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    db_session.delete(participant)
    db_session.commit()

    return {"message": f"Unregistered {email} from {activity_name}"}
