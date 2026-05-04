from src.database import db

book_category = db.Table(
    "book_category",
    db.Column("isbn", db.String(13), db.ForeignKey("book.isbn"), primary_key=True),
    db.Column("category_id", db.Integer, db.ForeignKey("category.id"), primary_key=True),
)


class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), unique=True, nullable=False)

    books = db.relationship("Book", secondary=book_category, back_populates="categories")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }
