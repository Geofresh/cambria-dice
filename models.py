from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Add relationship to rolls
    rolls = db.relationship('Roll', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can_manage_users(self):
        return self.is_super_admin

    def __repr__(self):
        return f'<User {self.username}>'

class Roll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    max_range = db.Column(db.Integer, nullable=False)
    count = db.Column(db.Integer, nullable=False)
    numbers = db.Column(db.String(1000), nullable=False)  # Store as JSON string
    proofs = db.Column(db.Text, nullable=False)  # Store as JSON string
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def set_numbers(self, numbers):
        self.numbers = json.dumps(numbers)

    def get_numbers(self):
        return json.loads(self.numbers)

    def set_proofs(self, proofs):
        self.proofs = json.dumps(proofs)

    def get_proofs(self):
        return json.loads(self.proofs)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'max_range': self.max_range,
            'count': self.count,
            'numbers': self.get_numbers(),
            'proofs': self.get_proofs(),
            'user_id': self.user_id
        } 