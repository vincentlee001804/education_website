from backend.app import create_app
from backend.extensions import db
from backend.models import (
    User, Subject, Course, Module, Resource, 
    BookCategory, Book, Inventory, 
    ForumTopic, ForumPost
)
import bcrypt

def seed_more_data():
    app = create_app()
    with app.app_context():
        # 1. Ensure user exists
        user = User.query.filter_by(email="student@example.com").first()
        if not user:
            hashed = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user = User(email="student@example.com", password_hash=hashed, display_name="John Doe")
            db.session.add(user)
            db.session.commit()
            
        user2 = User.query.filter_by(email="admin@example.com").first()
        if not user2:
            hashed = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user2 = User(email="admin@example.com", password_hash=hashed, display_name="Dr. Admin")
            db.session.add(user2)
            db.session.commit()

        # 2. Seed More Subjects and Courses
        cs = Subject.query.filter_by(name="Computer Science").first()
        if not cs:
            cs = Subject(name="Computer Science")
            db.session.add(cs)
            db.session.commit()
            
        phil = Subject.query.filter_by(name="Philosophy").first()
        if not phil:
            phil = Subject(name="Philosophy")
            db.session.add(phil)
            db.session.commit()

        # Add more modules to Course 2 (Machine Learning Basics) which was empty
        course2 = Course.query.filter_by(title="Machine Learning Basics").first()
        if course2:
            if not Module.query.filter_by(course_id=course2.id).first():
                mod_ml_1 = Module(course_id=course2.id, title="Introduction to Neural Networks", order_index=1)
                mod_ml_2 = Module(course_id=course2.id, title="Support Vector Machines", order_index=2)
                db.session.add_all([mod_ml_1, mod_ml_2])
                db.session.commit()

                res_ml_1 = Resource(module_id=mod_ml_1.id, title="Perceptron Notes", resource_type="note", content_text="A perceptron is an algorithm for supervised learning of binary classifiers...")
                res_ml_2 = Resource(module_id=mod_ml_1.id, title="Neural Net Architecture Video", resource_type="video", content_url="https://www.youtube.com/watch?v=aircAruvnKk")
                res_ml_3 = Resource(module_id=mod_ml_2.id, title="SVM Kernel Trick", resource_type="note", content_text="The kernel trick allows SVM to form non-linear boundaries...")
                db.session.add_all([res_ml_1, res_ml_2, res_ml_3])
                db.session.commit()

        # Add new courses
        if not Course.query.filter_by(title="Ethics in the Post-Digital Era").first():
            course3 = Course(title="Ethics in the Post-Digital Era", description="An examination of moral philosophy as applied to artificial intelligence, data privacy, and modern tech conglomerates.", subject_id=phil.id)
            course4 = Course(title="Advanced Operating Systems", description="Deep dive into OS kernel architecture, concurrency, and file systems.", subject_id=cs.id)
            db.session.add_all([course3, course4])
            db.session.commit()

            mod_phil_1 = Module(course_id=course3.id, title="The Morality of Autonomous Agents", order_index=1)
            mod_phil_2 = Module(course_id=course3.id, title="Data Privacy & Surveillance Capitalism", order_index=2)
            db.session.add_all([mod_phil_1, mod_phil_2])
            db.session.commit()

            res_phil_1 = Resource(module_id=mod_phil_1.id, title="Trolley Problem Revisited", resource_type="note", content_text="How should self-driving cars be programmed when facing unavoidable accidents?")
            res_phil_2 = Resource(module_id=mod_phil_2.id, title="Panopticon Theory", resource_type="note", content_text="Foucault's Panopticon serves as a powerful metaphor for modern digital surveillance...")
            db.session.add_all([res_phil_1, res_phil_2])
            db.session.commit()

        # 3. Seed More Bookstore Items
        cat3 = BookCategory.query.filter_by(name="Philosophy").first()
        if not cat3:
            cat3 = BookCategory(name="Philosophy")
            db.session.add(cat3)
            db.session.commit()
            
        cat_text = BookCategory.query.filter_by(name="Textbooks").first()

        if not Book.query.filter_by(title="The Age of Surveillance Capitalism").first():
            book4 = Book(title="The Age of Surveillance Capitalism", author="Shoshana Zuboff", description="The fight for a human future at the new frontier of power.", category_id=cat3.id, price=25.00, image_url="https://images.unsplash.com/photo-1589998059171-988d887df646?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80")
            book5 = Book(title="Operating System Concepts, 10th Edition", author="Abraham Silberschatz", description="The 'Dinosaur Book' provides a solid theoretical foundation for understanding operating systems.", category_id=cat_text.id, price=115.00, image_url="https://images.unsplash.com/photo-1555066931-4365d14bab8c?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80")
            book6 = Book(title="Critique of Pure Reason", author="Immanuel Kant", description="One of the most influential works in the history of philosophy.", category_id=cat3.id, price=18.50, image_url="https://images.unsplash.com/photo-1544716278-e513176f20b5?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80")
            db.session.add_all([book4, book5, book6])
            db.session.commit()

            inv4 = Inventory(book_id=book4.id, stock_count=15)
            inv5 = Inventory(book_id=book5.id, stock_count=5)
            inv6 = Inventory(book_id=book6.id, stock_count=8)
            db.session.add_all([inv4, inv5, inv6])
            db.session.commit()

        # 4. Seed More Forum Topics
        if not ForumTopic.query.filter_by(title="Differences between microkernel and monolithic kernel?").first():
            topic3 = ForumTopic(title="Differences between microkernel and monolithic kernel?", created_by=user.id)
            topic4 = ForumTopic(title="Is AI consciousness theoretically possible?", created_by=user.id)
            db.session.add_all([topic3, topic4])
            db.session.commit()

            post3 = ForumPost(topic_id=topic3.id, content="I'm struggling to understand the performance tradeoffs between the two architectures. Can someone explain?", created_by=user.id)
            post4 = ForumPost(topic_id=topic3.id, content="A monolithic kernel runs all OS services in the same memory space, which is faster but less secure. A microkernel runs them in user space, passing messages.", created_by=user2.id)
            post5 = ForumPost(topic_id=topic4.id, content="According to functionalism, if a system can replicate the exact functional state of a human brain, it should have consciousness. What do you all think?", created_by=user.id)
            db.session.add_all([post3, post4, post5])
            db.session.commit()

        print("More dummy data successfully seeded!")

if __name__ == "__main__":
    seed_more_data()
