import enum
from src.database import db


class BookStatus(str, enum.Enum):
    WANT_TO_READ = "want_to_read"
    CURRENTLY_READING = "currently_reading"
    FINISHED = "finished"
    RECOMMENDED = "recommended"
    REJECTED = "rejected"


class UserBook(db.Model):
    __tablename__ = "user_book"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    isbn = db.Column(db.String(13), db.ForeignKey("book.isbn"), nullable=False)
    status = db.Column(db.Enum(BookStatus), nullable=False, default=BookStatus.WANT_TO_READ)
    is_favourite = db.Column(db.Boolean, default=False)
    current_page = db.Column(db.Integer, default=0)

    user = db.relationship("User", back_populates="books")
    book = db.relationship("Book", back_populates="users")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "isbn": self.isbn,
            "status": self.status.value,
            "is_favourite": self.is_favourite,
            "current_page": self.current_page,
        }
