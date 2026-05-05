from src.database import db
from src.models.category import book_category


class Book(db.Model):
    __tablename__ = "book"

    isbn = db.Column(db.String(13), primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    author = db.Column(db.String(256), nullable=False)
    cover_small = db.Column(db.String(512))
    cover_medium = db.Column(db.String(512))
    cover_large = db.Column(db.String(512))
    description = db.Column(db.Text)
    number_of_pages = db.Column(db.Integer)
    publish_date = db.Column(db.String(64))
    publisher = db.Column(db.String(256))
    source_api_id = db.Column(db.String(256))

    users = db.relationship("UserBook", back_populates="book")
    categories = db.relationship("Category", secondary=book_category, back_populates="books")

    def to_dict(self):
        return {
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author,
            "cover": {
                "small": self.cover_small,
                "medium": self.cover_medium,
                "large": self.cover_large,
            },
            "description": self.description,
            "number_of_pages": self.number_of_pages,
            "publish_date": self.publish_date,
            "publisher": self.publisher,
            "source_api_id": self.source_api_id,
            "categories": [category.to_dict() for category in self.categories],
        }
