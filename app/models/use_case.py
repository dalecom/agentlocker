from app import db

class UseCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # For storing icon class
    color = db.Column(db.String(7))  # For hex color code
    display_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<UseCase {self.name}>' 