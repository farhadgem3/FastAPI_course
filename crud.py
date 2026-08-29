from database_test import User , engine
from sqlalchemy.orm import sessionmaker

SessionFactory = sessionmaker(bind=engine)

session = SessionFactory()

# user = User(first_name = "kafka" , age=21)

# session.add(user)
# session.commit()

# users = [User(first_name = "Arefi" , age=22) , User(first_name = "zahra" , age=20)]

# session.add_all(users)
# session.commit()

# user = session.query(User).all()
# print(user)

# user =session.query(User).filter_by(first_name="kafka").all()
# print(user)

# user =session.query(User).filter_by(first_name="kafka").one_or_none()
# user.first_name = "Mohammed Reza"
# session.commit()

user =session.query(User).filter_by(first_name="Arefi").one_or_none()
session.delete(user)
session.commit()