import pytest
from unittest.mock import patch, Mock, MagicMock, ANY, call

from datetime import datetime

from src.utils.database import nmlDB, User, ImageSession
from src.utils.exceptions import UserAlreadyCreated

test_db = nmlDB(":memory:")
test_email = "test.email@email.com"
test_fname = "first"
test_lname = "last"
test_uuid = "test-uuid"
test_session_id = 1
test_datetime = datetime.now()


@patch("uuid.uuid4", return_value=test_uuid)
@patch("src.utils.database.nmlDB.get_uuid_by_email", return_value=None)
def test_insert_new_user_valid(get_uuid_mock, uuid_mock):
    result_uuid = test_db.insert_new_user(test_email, test_fname, test_lname)

    assert result_uuid == test_uuid
    get_uuid_mock.assert_called_once_with(test_email)
    uuid_mock.assert_called_once_with()


@patch("uuid.uuid4", return_value=test_uuid)
@patch("src.utils.database.nmlDB.get_uuid_by_email", return_value=test_uuid)
def test_insert_new_user_already_created(get_uuid_mock, uuid_mock):
    with pytest.raises(Exception) as e_info:
        # TODO: figure out why this cant be the proper exception
        result_uuid = test_db.insert_new_user(test_email, test_fname, test_lname)

    get_uuid_mock.assert_called_once_with(test_email)
    uuid_mock.assert_not_called()


def test_get_all_users_names():
    result_user_list = test_db.get_all_users_names()
    assert result_user_list == ["first_last"]


def test_get_all_user_emails():
    result_user_list = test_db.get_all_users_emails()
    assert result_user_list == ["test.email@email.com"]


def test_get_uuid_by_email_valid():
    uuid = test_db.get_uuid_by_email(test_email)

    assert uuid == test_uuid


def test_get_uuid_by_email_no_email_exists():
    uuid = test_db.get_uuid_by_email("no.email.in.db@email.com")

    assert uuid == None


@patch("time.time", return_value=test_session_id)
def test_insert_new_image_session(time_mock):
    session_id = test_db.insert_new_image_session(test_uuid)

    assert session_id == test_session_id
    time_mock.assert_called_once_with()


def test_get_all_img_sessions_for_uuid():
    result = test_db.get_all_img_sessions_for_uuid(test_uuid)

    for res in result:
        assert res.session_id == test_session_id
        assert res.user_uuid == test_uuid


def test_get_all_img_sessions_for_uuid_empty():
    result = test_db.get_all_img_sessions_for_uuid("bad-uuid")

    assert result == []


def test__get_users_all():
    result = test_db._get_users_all()

    for res in result:
        assert res.user_uuid == test_uuid
        assert res.user_email == test_email
        assert res.first_name == test_fname
        assert res.last_name == test_lname


def test__get_imgae_sessions_all():
    result = test_db._get_image_sessions_all()

    for res in result:
        assert res.session_id == test_session_id
        assert res.user_uuid == test_uuid
