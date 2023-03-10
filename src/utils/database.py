import os
import uuid
import time
from datetime import datetime
from typing import List, Optional, Union, Literal
from sqlalchemy import (
    create_engine,
    ForeignKey,
    Column,
    String,
    Integer,
    DateTime,
    LargeBinary,
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

from utils.exceptions import UserAlreadyCreated, UserNotFound, ImageSessionNotFound

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
    image_name = Column("image_name", String, default="", unique=False)
    crack_detected = Column("crack_detected", Integer, unique=False)
    user_uuid = Column(
        String,
        ForeignKey("users_table.user_uuid"),
    )
    user = relationship("User", back_populates="image_sessions")

    def __init__(
        self, session_id, date, user_uuid, image_name="", crack_detected=-1
    ) -> None:
        self.session_id = session_id
        self.user_uuid = user_uuid
        self.date = date
        self.image_name = image_name
        self.crack_detected = crack_detected

    def __repr__(self):
        return f"ImageSession=({self.session_id}, {self.image_name}, {self.date}, {self.user_uuid}, {self.crack_detected}))"


class MlData(Base):
    __tablename__ = "ml_data_table"

    entry_id = Column("entry_id", Integer, primary_key=True, unique=True)
    classifier = Column("classifier", Integer)
    img = Column("img", LargeBinary)

    def __init__(self, entry_id, classifier, img) -> None:
        self.entry_id = entry_id
        self.classifier = classifier
        self.img = img

    def __repr__(self) -> str:
        return f"MlData=({self.entry_id}, {self.classifier}, {self.img})"


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

    def insert_new_image_session(self, uuid: str, image_name: str = "") -> int:
        session_id = int(time.time() * 1000)
        img_session = ImageSession(session_id, datetime.now(), uuid, image_name)
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

    def update_img_session_crack_detection(
        self, img_session_id: int, crack_status: Union[Literal[0], Literal[1]]
    ) -> None:
        img_sess_res = (
            self.session.query(ImageSession)
            .filter(ImageSession.session_id == img_session_id)
            .first()
        )
        if not img_sess_res:
            raise ImageSessionNotFound("This image session was not found")

        img_sess_res.crack_detected = crack_status
        self.session.commit()

    @classmethod
    def get_base_filepath(cls, user_uuid: str) -> str:
        return os.path.abspath(f"nml_img/{user_uuid}/")

    @classmethod
    def check_set_filepath(cls, user_uuid: str) -> None:
        base_filepath = cls.get_base_filepath(user_uuid)
        if not os.path.isdir(os.path.join(base_filepath, "raw")):
            os.makedirs(os.path.join(base_filepath, "raw"))
            os.makedirs(os.path.join(base_filepath, "complete"))

    def insert_ml_data(self, img, classifier):
        # TODO: May Need to reword session id to be more unique
        entry_id = int(time.time() * 1000)
        img = bytes(img)
        ml_data = MlData(entry_id, classifier, img)
        self.session.add(ml_data)
        self.session.commit()

    def get_all_ml_data(
        self,
        classifier: Union[
            Literal["ALL"], Literal["CRACK"], Literal["NO_CRACK"]
        ] = "ALL",
    ):
        if classifier == "CRACK":
            results = self.session.query(MlData).filter(MlData.classifier == 1).all()
        elif classifier == "NO_CRACK":
            results = self.session.query(MlData).filter(MlData.classifier == 0).all()
        else:
            results = self.session.query(MlData).all()
        return results

    def get_first_ml_data(self):
        return self.session.query(MlData).first()

    def get_ml_data_len(self):
        ml_count = self.session.query(MlData).count()
        print(ml_count)
        return ml_count


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
