import os
import requests
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import engine, Base, get_db
from fcm_utils import send_fcm_notification
import models, schemas
import auth

app = FastAPI(title="Shala PWA API")

def get_template(db: Session, t_type: str, fallback_title: str, fallback_body: str, **kwargs) -> tuple:
    tpl = db.query(models.Template).filter(models.Template.type == t_type).first()
    title = tpl.title if tpl and tpl.title else fallback_title
    body = tpl.body if tpl and tpl.body else fallback_body

    for key, val in kwargs.items():
        placeholder = f"{{{{{key}}}}}"
        if title: title = title.replace(placeholder, str(val))
        if body: body = body.replace(placeholder, str(val))
    return title, body

# --------- CRON JOB ENDPOINT ---------
@app.get("/api/cron/check-attendance")
def check_attendance_job(db: Session = Depends(get_db)):
    print("Running post-event attendance verification CRON job...")
    today = datetime.now().strftime("%Y-%m-%d")
    events_today = db.query(models.Event).filter(models.Event.date == today).all()
    notifications_sent = 0

    for event in events_today:
        title, body = get_template(
            db, "end_of_day_review",
            "ها يا رياسة.. روحت؟ 🤔",
            f"اليوم خلص، انزل قولنا روحت خروجة '{{group_name}}' بجد ولا سحبت؟ وقيم الدنيا.",
            group_name=event.group.name
        )

        for participant in event.participants:
            if participant.status == "Accepted" and participant.user.device_tokens:
                send_fcm_notification(participant.user.device_tokens, title, body)
                notifications_sent += 1

    return {"message": "Attendance checked.", "notifications_sent": notifications_sent}

# --------- AUTH ENDPOINTS ---------
@app.post("/auth/request-otp")
def request_otp(phone: str, db: Session = Depends(get_db)):
    whatsapp_url = "https://api.message-pro.com/api/v2/messages"
    token = os.environ.get("WHATSAPP_API_TOKEN")
    instance = os.environ.get("WHATSAPP_INSTANCE_ID", "instance4552")

    code = auth.generate_otp(phone, db)

    _, msg_body = get_template(
        db, "whatsapp_otp",
        "",
        "يا زميلي، كود الدخول بتاعك للابليكشن اهو: {{otp_code}} 🤫 متديهوش لحد عشان متتسوحش.",
        otp_code=code
    )

    if not token:
        print(f"[MOCK WHATSAPP] OTP {code} sent to {phone}.")
        return {"message": "OTP sent via WhatsApp"}

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"phone": phone, "message": msg_body, "instance_id": instance}
    response = requests.post(whatsapp_url, headers=headers, json=data)

    if response.status_code == 200:
        return {"message": "OTP sent via WhatsApp"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send OTP via WhatsApp")

@app.post("/auth/verify-otp")
def verify_otp(phone: str, code: str, db: Session = Depends(get_db)):
    if not auth.verify_otp_code(phone, code, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP code")

    user = db.query(models.User).filter(models.User.phone == phone).first()
    if not user:
        user = models.User(phone=phone, name=f"User {phone[-4:]}")
        db.add(user)
        db.commit()
        db.refresh(user)

    token = auth.create_access_token({"user_id": user.id, "phone": user.phone})
    return {"token": token, "user_id": user.id}

@app.get("/users/me")
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# --------- GROUP ENDPOINTS ---------
@app.post("/groups/create")
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    user_groups_count = db.query(models.GroupMember).filter(models.GroupMember.user_id == current_user.id).count()
    if user_groups_count >= 5: raise HTTPException(status_code=400, detail="You have reached the maximum of 5 groups.")

    final_phones = set(group.phones)
    final_phones.add(current_user.phone)
    if len(final_phones) > 100: raise HTTPException(status_code=400, detail="A group can have a maximum of 100 members.")

    new_group = models.Group(name=group.name, creator_id=current_user.id)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    whatsapp_url = "https://api.message-pro.com/api/v2/messages"
    whatsapp_token = os.environ.get("WHATSAPP_API_TOKEN")
    instance = os.environ.get("WHATSAPP_INSTANCE_ID", "instance4552")

    _, invite_msg = get_template(
        db, "new_user_whatsapp", "",
        "يا رياسة! {{inviter_name}} بيلم الشلة وعمل جروب '{{group_name}}' على ابليكشن الشلل. خُش سجل: {{app_link}}",
        inviter_name=current_user.name or 'صاحبك',
        group_name=group.name,
        app_link="https://shala-app.vercel.app/"
    )

    for phone in final_phones:
        user = db.query(models.User).filter(models.User.phone == phone).first()
        is_creator = (phone == current_user.phone)
        role = "Admin" if is_creator else "Member"

        if user:
            if not is_creator:
                send_fcm_notification(user.device_tokens, "Added to Group!", f"You were added to {group.name}")
        else:
            user = models.User(phone=phone)
            db.add(user)
            db.commit()
            db.refresh(user)

            if whatsapp_token:
                headers = {"Authorization": f"Bearer {whatsapp_token}", "Content-Type": "application/json"}
                requests.post(whatsapp_url, headers=headers, json={"phone": phone, "message": invite_msg, "instance_id": instance})
            else:
                print(f"[MOCK WHATSAPP] Invite sent to {phone} for group {group.name}")

        member = models.GroupMember(group_id=new_group.id, user_id=user.id, role=role)
        db.add(member)

    db.commit()
    return {"id": new_group.id, "name": new_group.name, "message": "Group created"}

@app.get("/groups/{group_id}/stats")
def get_group_stats(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    group_events = db.query(models.Event).filter(models.Event.group_id == group_id).all()
    successful, cancelled = 0, 0
    creator_counts = {}

    for event in group_events:
        attended_count = db.query(models.EventParticipant).filter(models.EventParticipant.event_id == event.id, models.EventParticipant.attended == True).count()
        if attended_count >= 2:
            successful += 1
            if event.creator_id: creator_counts[event.creator_id] = creator_counts.get(event.creator_id, 0) + 1
        elif attended_count == 0: cancelled += 1

    top_creator_ids = sorted(creator_counts, key=creator_counts.get, reverse=True)[:3]
    top_creators = [{"name": u.name or u.phone, "successful_events": creator_counts[u.id]} for uid in top_creator_ids if (u := db.query(models.User).filter(models.User.id == uid).first())]

    event_ids = [e.id for e in group_events]
    attendee_counts = db.query(models.EventParticipant.user_id, func.count(models.EventParticipant.id).label('total')).filter(models.EventParticipant.event_id.in_(event_ids), models.EventParticipant.attended == True).group_by(models.EventParticipant.user_id).order_by(func.count(models.EventParticipant.id).desc()).limit(3).all()
    top_attendees = [{"name": u.name or u.phone, "attended": total} for uid, total in attendee_counts if (u := db.query(models.User).filter(models.User.id == uid).first())]

    return {"successful_events": successful, "cancelled_events": cancelled, "leaderboard": {"top_creators": top_creators, "top_attendees": top_attendees}}

@app.get("/groups")
def list_groups(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    user_memberships = db.query(models.GroupMember).filter(models.GroupMember.user_id == current_user.id).all()
    groups = [membership.group for membership in user_memberships]
    return [{"id": g.id, "name": g.name, "member_count": len(g.members)} for g in groups]

# --------- EVENT ENDPOINTS ---------
@app.post("/events/create")
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    new_event = models.Event(
        title=event.title, group_id=event.group_id, creator_id=current_user.id, type=event.type,
        date=event.date, time=event.time, dynamic_fields=event.dynamic_fields, itinerary=event.itinerary,
        has_restaurant=event.has_restaurant, min_cost=event.min_cost, max_cost=event.max_cost
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    group = db.query(models.Group).filter(models.Group.id == event.group_id).first()
    if group:
        tokens = []
        for member in group.members:
            if member.user.device_tokens and member.user.id != current_user.id: tokens.extend(member.user.device_tokens)

        t_type = "new_treat_push" if event.type == "Treat" else "new_hangout_push"
        f_title = "عزومة جديدة! 🍔" if event.type == "Treat" else "خروجة طرش بتتنظم! 🔥"
        f_body = "{{creator_name}} عامل عظمة وعازمك يوم {{date}} الساعة {{time}}" if event.type == "Treat" else "يا باشا {{creator_name}} بيعمل خروجة يوم {{date}} الساعة {{time}}"

        title, body = get_template(db, t_type, f_title, f_body, creator_name=current_user.name or current_user.phone, date=event.date, time=event.time)
        send_fcm_notification(tokens, title, body)

    return {"id": new_event.id, "title": event.title, "group_id": event.group_id, "type": event.type, "message": "Event created"}

@app.post("/events/{event_id}/respond")
def respond_event(event_id: int, response: schemas.EventRespond, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    participant = db.query(models.EventParticipant).filter(models.EventParticipant.event_id == event_id, models.EventParticipant.user_id == current_user.id).first()
    if participant: participant.status = response.status
    else:
        participant = models.EventParticipant(event_id=event_id, user_id=current_user.id, status=response.status)
        db.add(participant)
    db.commit()

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if event:
        tokens = [p.user.device_tokens for p in event.participants if p.user_id != current_user.id and p.user.device_tokens]
        flat_tokens = [item for sublist in tokens for item in sublist]

        status_text = "ودي وجاي معانا" if response.status == "Accepted" else "فكس"
        f_body = "(لو وافق): عاش! {{user_name}} داس 'ودي' وجاي معانا الخروجة." if response.status == "Accepted" else "الصحبة باظت! {{user_name}} فكس للخروجة دي."
        title, body = get_template(db, "member_update_push", "أبديت الشلة 👀", f_body, user_name=current_user.name or current_user.phone)

        send_fcm_notification(flat_tokens, title, body)

    return {"message": f"Participant status updated to {response.status}"}

@app.post("/events/{event_id}/attendance")
def confirm_attendance(event_id: int, payload: schemas.EventAttendance, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    participant = db.query(models.EventParticipant).filter(models.EventParticipant.event_id == event_id, models.EventParticipant.user_id == current_user.id).first()
    if not participant: raise HTTPException(status_code=404, detail="You are not a participant in this event.")
    participant.attended = payload.attended
    if payload.review: participant.review = payload.review
    db.commit()
    return {"message": "Attendance and review updated."}

@app.get("/events")
def list_events(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    user_groups = db.query(models.GroupMember.group_id).filter(models.GroupMember.user_id == current_user.id).subquery()
    events = db.query(models.Event).filter(models.Event.group_id.in_(user_groups)).all()
    return [{"id": e.id, "title": e.title, "group_id": e.group_id, "group_name": e.group.name if e.group else "Unknown Group", "creator_name": e.creator.name if e.creator else "Unknown Creator", "type": e.type, "date": e.date, "time": e.time} for e in events]

# --------- ADMIN ENDPOINTS ---------
@app.get("/admin/users")
def admin_get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return [{"id": u.id, "phone": u.phone, "name": u.name} for u in users]

@app.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user: db.delete(user); db.commit()
    return {"message": "User deleted"}

@app.get("/admin/groups")
def admin_get_groups(db: Session = Depends(get_db)):
    groups = db.query(models.Group).all()
    return [{"id": g.id, "name": g.name, "members": len(g.members)} for g in groups]

@app.delete("/admin/groups/{group_id}")
def admin_delete_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if group: db.delete(group); db.commit()
    return {"message": "Group deleted"}

@app.get("/admin/events")
def admin_get_events(db: Session = Depends(get_db)):
    events = db.query(models.Event).all()
    return [{"id": e.id, "title": e.title, "type": e.type} for e in events]

@app.delete("/admin/events/{event_id}")
def admin_delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if event: db.delete(event); db.commit()
    return {"message": "Event deleted"}

@app.get("/admin/templates")
def admin_get_templates(db: Session = Depends(get_db)):
    return db.query(models.Template).all()

@app.post("/admin/templates")
def admin_create_template(template: schemas.TemplateCreate, db: Session = Depends(get_db)):
    new_tpl = models.Template(type=template.type, title=template.title, body=template.body, placeholders=template.placeholders)
    db.add(new_tpl); db.commit(); db.refresh(new_tpl)
    return new_tpl

@app.put("/admin/templates/{template_id}")
def admin_update_template(template_id: int, template: schemas.TemplateCreate, db: Session = Depends(get_db)):
    tpl = db.query(models.Template).filter(models.Template.id == template_id).first()
    if tpl: tpl.type = template.type; tpl.title = template.title; tpl.body = template.body; tpl.placeholders = template.placeholders; db.commit()
    return {"message": "Template updated"}

@app.delete("/admin/templates/{template_id}")
def admin_delete_template(template_id: int, db: Session = Depends(get_db)):
    tpl = db.query(models.Template).filter(models.Template.id == template_id).first()
    if tpl: db.delete(tpl); db.commit()
    return {"message": "Template deleted"}

# Serve PWA UI statically later
app.mount("/", StaticFiles(directory="static", html=True), name="static")
