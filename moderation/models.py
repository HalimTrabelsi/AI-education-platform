from mongoengine import Document, StringField, BooleanField, FloatField, DateTimeField
from datetime import datetime

class Report(Document):
    title = StringField(required=True, max_length=100)
    description = StringField()
    resource_url = StringField()
    flagged_by = StringField(required=True)
    is_plagiarism = BooleanField(default=False)
    is_nsfw = BooleanField(default=False)
    ai_confidence = FloatField(default=0.0)
    ai_flags = StringField(default="")
    risk_label = StringField(default="Safe")  # Safe / Risky
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'reports', 'ordering': ['-created_at']}
