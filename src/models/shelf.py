from src.database import db


class Shelf(db.Model):
    __tablename__ = "shelf"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user_reading_list.user_id"), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_default = db.Column(db.Boolean, default=False)

    user = db.relationship("User", backref="shelves")
    books = db.relationship("ShelfBook", back_populates="shelf", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "position": self.position,
            "is_default": self.is_default,
        }


class ShelfBook(db.Model):
    __tablename__ = "shelf_book"

    shelf_id = db.Column(db.Integer, db.ForeignKey("shelf.id"), primary_key=True)
    isbn = db.Column(db.String(13), db.ForeignKey("book.isbn"), primary_key=True)

    shelf = db.relationship("Shelf", back_populates="books")
    book = db.relationship("Book", backref="shelf_assignments")

    def to_dict(self):
        return {
            "shelf_id": self.shelf_id,
            "isbn": self.isbn,
        }
