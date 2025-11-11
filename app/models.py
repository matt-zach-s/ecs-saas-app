from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class MealTask(db.Model):
    """Model for Thanksgiving meal planning tasks"""
    __tablename__ = 'meal_tasks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # appetizer, main, side, dessert, prep
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed
    priority = db.Column(db.Integer, default=1)
    start_time = db.Column(db.String(10))  # e.g., "10:00 AM"
    duration_minutes = db.Column(db.Integer)
    assigned_to = db.Column(db.String(50))
    ingredients = db.Column(db.Text)  # Comma-separated list
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'status': self.status,
            'priority': self.priority,
            'start_time': self.start_time,
            'duration_minutes': self.duration_minutes,
            'assigned_to': self.assigned_to,
            'ingredients': self.ingredients.split(',') if self.ingredients else [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
