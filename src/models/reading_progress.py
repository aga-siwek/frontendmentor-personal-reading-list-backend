from datetime import datetime
from src.database import db


class ReadingProgress(db.Model):
    __tablename__ = "reading_progress"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user_reading_list.user_id"), nullable=False)
    isbn = db.Column(db.String(13), db.ForeignKey("book.isbn"), nullable=False)
    current_page = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref="reading_progress")
    book = db.relationship("Book", backref="reading_progress")

    def to_dict(self):
        total_pages = self.book.number_of_pages if self.book else None
        percentage = round(self.current_page / total_pages * 100, 1) if total_pages else None
        return {
            "id": self.id,
            "user_id": self.user_id,
            "isbn": self.isbn,
            "current_page": self.current_page,
            "percentage": percentage,
            "date": self.date.isoformat(),
        }
