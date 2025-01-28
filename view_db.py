from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/cambria.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

def view_database():
    with app.app_context():
        print("\n=== Users in Database ===")
        users = User.query.all()
        for user in users:
            print(f"\nUsername: {user.username}")
            print(f"ID: {user.id}")
            print(f"Is Admin: {user.is_admin}")
            print(f"Is Super Admin: {user.is_super_admin}")
            print(f"Created At: {user.created_at}")
            print("-" * 30)

if __name__ == "__main__":
    view_database() 