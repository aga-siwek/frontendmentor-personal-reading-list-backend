from src.database import db

class User(db.Model):
    __tablename__ = "user_reading_list"
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(190), unique=True, nullable=False)
    user_password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    user_name = db.Column(db.String(128))


    books = db.relationship("UserBook", back_populates="user")
    reading_goals = db.relationship("ReadingGoal", back_populates="user")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "user_email": self.user_email,
            "is_admin": self.is_admin,
            "user_name": self.user_name
        }

    def is_administrator(self):
        return self.is_admin == 1

