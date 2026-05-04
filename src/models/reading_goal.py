from src.database import db


class ReadingGoal(db.Model):
    __tablename__ = "reading_goal"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    goal = db.Column(db.Integer, nullable=False)

    user = db.relationship("User", back_populates="reading_goals")

    __table_args__ = (
        db.UniqueConstraint("user_id", "year", name="uq_user_year"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "year": self.year,
            "goal": self.goal,
        }
