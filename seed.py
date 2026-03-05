import models
from database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

def seed_templates():
    db = SessionLocal()

    templates_data = [
        {
            "type": "whatsapp_otp",
            "title": "",
            "body": "يا زميلي، كود الدخول بتاعك للابليكشن اهو: {{otp_code}} 🤫 متديهوش لحد عشان متتسوحش.",
            "placeholders": ["otp_code"]
        },
        {
            "type": "new_user_whatsapp",
            "title": "",
            "body": "يا رياسة! {{inviter_name}} بيلم الشلة وعمل جروب '{{group_name}}' على ابليكشن الشلل. خُش ظبط بروفايلك وسجل من اللينك ده عشان الخروجات اللي جاية: {{app_link}}",
            "placeholders": ["inviter_name", "group_name", "app_link"]
        },
        {
            "type": "new_hangout_push",
            "title": "خروجة طرش بتتنظم! 🔥",
            "body": "يا باشا {{creator_name}} بيعمل خروجة يوم {{date}} الساعة {{time}}.. هتنزل ولا هتأنتخ؟ خش شوف التفاصيل.",
            "placeholders": ["creator_name", "date", "time"]
        },
        {
            "type": "new_treat_push",
            "title": "عزومة جديدة! 🍔",
            "body": "{{creator_name}} عامل عظمة وعازمك يوم {{date}} الساعة {{time}}.. متكسفوش بقى وخش أكد حضورك.",
            "placeholders": ["creator_name", "date", "time"]
        },
        {
            "type": "cancel_warning_modal",
            "title": "تأكيد فكسان",
            "body": "تأكيد فكسان: متأكد مش هتيجي؟ هيفوتك حوارات وحاجات فشخية يعلم بيها ربنا! هندوس تأكيد؟",
            "placeholders": []
        },
        {
            "type": "member_update_push",
            "title": "أبديت الشلة 👀",
            "body": "{{status_body}}", # Frontend or Backend can inject specific "(لو وافق) / (لو رفض)" text here
            "placeholders": ["status_body"]
        },
        {
            "type": "end_of_day_review",
            "title": "ها يا رياسة.. روحت؟ 🤔",
            "body": "اليوم خلص، انزل قولنا روحت خروجة '{{group_name}}' بجد ولا سحبت؟ وقيم الدنيا.",
            "placeholders": ["group_name"]
        }
    ]

    for data in templates_data:
        existing = db.query(models.Template).filter(models.Template.type == data["type"]).first()
        if not existing:
            tpl = models.Template(**data)
            db.add(tpl)
            print(f"Added template: {data['type']}")

    db.commit()
    db.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed_templates()
