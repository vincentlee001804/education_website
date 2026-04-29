from backend.app import create_app
from backend.extensions import db
from backend.models import (
    User, Subject, Course, Module, Resource, 
    BookCategory, Book, Inventory, 
    ForumTopic, ForumPost
)
import bcrypt

def seed_data():
    app = create_app()
    with app.app_context():
        # 1. Create a dummy user for forum posts if one doesn't exist
        user = User.query.filter_by(email="student@example.com").first()
        if not user:
            hashed = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user = User(email="student@example.com", password_hash=hashed, display_name="John Doe")
            db.session.add(user)
            db.session.commit()

        # 2. Seed Subjects and Courses
        if not Subject.query.filter_by(name="Computer Science").first():
            cs = Subject(name="Computer Science")
            db.session.add(cs)
            db.session.commit()

            course1 = Course(title="Introduction to Algorithms", description="Learn the fundamentals of algorithms and data structures.", subject_id=cs.id)
            course2 = Course(title="Machine Learning Basics", description="An introductory course to machine learning concepts and applications.", subject_id=cs.id)
            db.session.add_all([course1, course2])
            db.session.commit()

            mod1 = Module(course_id=course1.id, title="Sorting Algorithms", order_index=1)
            mod2 = Module(course_id=course1.id, title="Graph Theory", order_index=2)
            db.session.add_all([mod1, mod2])
            db.session.commit()

            res1 = Resource(module_id=mod1.id, title="Merge Sort Notes", resource_type="note", content_text="Merge sort is a divide and conquer algorithm...")
            res2 = Resource(module_id=mod1.id, title="Quick Sort Video", resource_type="video", content_url="https://youtube.com/watch?v=HoIXWE6EP4A")
            db.session.add_all([res1, res2])
            db.session.commit()

        # 3. Seed Bookstore
        if not BookCategory.query.filter_by(name="Textbooks").first():
            cat1 = BookCategory(name="Textbooks")
            cat2 = BookCategory(name="Reference")
            db.session.add_all([cat1, cat2])
            db.session.commit()

            book1 = Book(title="Introduction to Algorithms, 3rd Edition", author="Thomas H. Cormen", description="The comprehensive textbook on algorithms.", category_id=cat1.id, price=85.00, image_url="https://images.unsplash.com/photo-1544947950-fa07a98d237f?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80")
            book2 = Book(title="Clean Code", author="Robert C. Martin", description="A Handbook of Agile Software Craftsmanship.", category_id=cat2.id, price=45.50, image_url="https://images.unsplash.com/photo-1532012197267-da84d127e765?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80")
            book3 = Book(title="Artificial Intelligence: A Modern Approach", author="Stuart Russell", description="The most comprehensive, up-to-date introduction to the theory and practice of AI.", category_id=cat1.id, price=110.00, image_url="https://images.unsplash.com/photo-1455390582262-044cdead27d8?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80")
            db.session.add_all([book1, book2, book3])
            db.session.commit()

            inv1 = Inventory(book_id=book1.id, stock_count=50)
            inv2 = Inventory(book_id=book2.id, stock_count=30)
            inv3 = Inventory(book_id=book3.id, stock_count=10)
            db.session.add_all([inv1, inv2, inv3])
            db.session.commit()

        # 4. Seed Forum Topics
        if not ForumTopic.query.first():
            topic1 = ForumTopic(title="Help understanding Dijkstra's Algorithm", created_by=user.id)
            topic2 = ForumTopic(title="Best resources for learning React?", created_by=user.id)
            db.session.add_all([topic1, topic2])
            db.session.commit()

            post1 = ForumPost(topic_id=topic1.id, content="Can someone explain how the priority queue works in Dijkstra's?", created_by=user.id)
            post2 = ForumPost(topic_id=topic1.id, content="Sure! The priority queue keeps track of the node with the smallest tentative distance...", created_by=user.id)
            db.session.add_all([post1, post2])
            db.session.commit()

        print("Dummy data successfully seeded!")

if __name__ == "__main__":
    seed_data()
