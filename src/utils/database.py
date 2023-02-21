import os
import uuid
import time
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, ForeignKey, Column, String, Integer, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

from utils.exceptions import UserAlreadyCreated, UserNotFound

Base = declarative_base()

# ------------------- Database Table Schemas -------------------
class User(Base):
    __tablename__ = "users_table"

    user_uuid = Column("user_uuid", String, primary_key=True, unique=True)
    user_email = Column("user_email", String, unique=True)
    first_name = Column("first_name", String, unique=False)
    last_name = Column("last_name", String, unique=False)
    image_sessions = relationship(
        "ImageSession", back_populates="user", cascade="all, delete"
    )

    def __init__(self, user_uuid, user_email, first_name, last_name) -> None:
        self.user_uuid = user_uuid
        self.user_email = user_email
        self.first_name = first_name
        self.last_name = last_name

    def __repr__(self):
        return f"User=({self.user_uuid}, {self.user_email}, {self.first_name}, {self.last_name}))"

    def get_uuid(self) -> str:
        return str(self.user_uuid)

    def get_full_name(self) -> str:
        return f"{self.first_name}_{self.last_name}"

    def get_email(self) -> str:
        return str(self.user_email)


class ImageSession(Base):
    __tablename__ = "image_sessions_table"

    session_id = Column("session_id", Integer, primary_key=True, unique=True)
    date = Column("date", DateTime, default=datetime.now())
    user_uuid = Column(
        String,
        ForeignKey("users_table.user_uuid"),
    )
    user = relationship("User", back_populates="image_sessions")

    def __init__(self, session_id, date, user_uuid) -> None:
        self.session_id = session_id
        self.user_uuid = user_uuid
        self.date = date

    def __repr__(self):
        return f"ImageSession=({self.session_id}, {self.date}, {self.user_uuid}))"


# ------------------- Wrapper to use DB -------------------
class nmlDB:
    def __init__(self, db_name) -> None:
        engine = create_engine(f"sqlite:///{db_name}", echo=False)
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def _get_users_all(self) -> List[User]:
        results = self.session.query(User).all()
        print(results)
        return results

    def _get_image_sessions_all(self) -> List[ImageSession]:
        results = self.session.query(ImageSession).all()
        print(results)
        return results

    def insert_new_user(self, user_email: str, first_name: str, last_name: str) -> str:
        # If a user already exists, exit and raise error
        if self.get_uuid_by_email(user_email):
            raise UserAlreadyCreated

        user_uuid = str(uuid.uuid4())
        user = User(user_uuid, user_email, first_name.strip(), last_name.strip())
        self.session.add(user)
        self.session.commit()

        return user_uuid

    def get_all_users_names(self) -> List[str]:
        results = self.session.query(User).all()
        user_name_list = [user.get_full_name() for user in results]
        return user_name_list

    def get_all_users_emails(self) -> List[str]:
        results = self.session.query(User).all()
        user_name_list = [user.get_email() for user in results]
        return user_name_list

    def get_uuid_by_email(self, user_email: str) -> Optional[str]:
        """
        Returns the associated uuid of a user. If no user is regiserted, returns None
        """
        results = self.session.query(User).filter(User.user_email == user_email).first()
        if results:
            return results.get_uuid()
        else:
            return None

    def insert_new_image_session(self, uuid: str) -> int:
        # TODO: May Need to reword session id to be more unique
        session_id = int(time.time())
        img_session = ImageSession(session_id, datetime.now(), uuid)
        self.session.add(img_session)
        self.session.commit()

        return session_id

    def get_all_img_sessions_for_uuid(self, uuid: str) -> List[ImageSession]:
        results = (
            self.session.query(ImageSession)
            .filter(User.user_uuid == ImageSession.user_uuid)
            .filter(User.user_uuid == uuid)
            .all()
        )
        return results

    @classmethod
    def check_set_filepath(cls, user_uuid: str) -> None:
        if not os.path.isdir(os.path.abspath(f"tmp_vid/{user_uuid}/raw")):
            os.makedirs(os.path.abspath(f"tmp_vid/{user_uuid}/raw"))
            os.makedirs(os.path.abspath(f"tmp_vid/{user_uuid}/complete"))


if __name__ == "__main__":
    user_db = nmlDB("nml.db")
    try:
        new_user_uuid = user_db.insert_new_user("test.email@email.com", "ct", "firm")
        print(f"New user uuid = {new_user_uuid}, type = {type(new_user_uuid)}")

        new_user_uuid = user_db.insert_new_user("email.test@email.com", "user", "test")
        print(f"New user uuid = {new_user_uuid}, type = {type(new_user_uuid)}")
    except UserAlreadyCreated:
        print("These Users already have an account!")

    user_db._get_users_all()

    queried_user_uuid_1 = user_db.get_uuid_by_email("test.email@email.com")
    print(queried_user_uuid_1)

    queried_user_uuid_2 = user_db.get_uuid_by_email("email.tesat@email.com")
    print(queried_user_uuid_2)
    print("This user does not exist")

    if queried_user_uuid_1:
        user_img_session = user_db.insert_new_image_session(queried_user_uuid_1)
        print(user_img_session)

        all_user_img_session = user_db.get_all_img_sessions_for_uuid(
            queried_user_uuid_1
        )
        for img_ses in all_user_img_session:
            print(img_ses.session_id)
