from app import app
from extensions import db
from model import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User.query.filter_by(email="admin@hostel.com").first()

    if admin:
        print("✅ Admin already exists")
    else:
        admin = User(
            full_name="Admin",
            email="admin@hostel.com",
            password_hash=generate_password_hash("admin#1M"), 
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin created successfully")
