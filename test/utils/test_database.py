import os
import pytest
from unittest.mock import patch, Mock, MagicMock, ANY, call

from datetime import datetime
import numpy as np

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


@patch("time.time", return_value=1)
def test_insert_new_image_session(time_mock):
    session_id = test_db.insert_new_image_session(test_uuid)

    assert session_id == 1 * 1000
    time_mock.assert_called_once_with()


@patch("time.time", return_value=2)
def test_insert_new_image_session_with_name(time_mock):
    session_id = test_db.insert_new_image_session(test_uuid, "test_image")

    assert session_id == 2 * 1000
    time_mock.assert_called_once_with()


def test_get_all_img_sessions_for_uuid():
    result = test_db.get_all_img_sessions_for_uuid(test_uuid)

    for count, res in enumerate(result, 1):
        assert res.session_id == count * 1000
        assert res.user_uuid == test_uuid

        assert res.image_name in ["", "test_image"]


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

    for count, res in enumerate(result, 1):
        assert res.session_id == count * 1000
        assert res.user_uuid == test_uuid

        assert res.image_name in ["", "test_image"]


@patch(
    "src.utils.database.nmlDB.get_base_filepath",
    return_value="base-filepath-test_check_set_filepath_exists",
)
@patch("os.makedirs")
@patch("os.path.isdir", return_value=True)
def test_check_set_filepath_exists(isdir_mock, makedirs_mock, get_base_filepath_mock):
    test_db.check_set_filepath("test-uuid-filepath-exist")

    isdir_mock.assert_called_once()
    get_base_filepath_mock.assert_called_once_with("test-uuid-filepath-exist")
    makedirs_mock.assert_not_called()


@patch(
    "src.utils.database.nmlDB.get_base_filepath",
    return_value="base-filepath-test_check_set_filepath_doesnt_exist",
)
@patch("os.makedirs")
@patch("os.path.isdir", return_value=False)
def test_check_set_filepath_doesnt_exist(
    isdir_mock, makedirs_mock, get_base_filepath_mock
):
    test_db.check_set_filepath("test-uuid-filepath-not-exist")

    isdir_mock.assert_called_once()
    get_base_filepath_mock.assert_called_once_with("test-uuid-filepath-not-exist")
    makedirs_mock.assert_has_calls(
        [
            call(
                os.path.normpath(
                    "base-filepath-test_check_set_filepath_doesnt_exist/raw"
                )
            ),
            call(
                os.path.normpath(
                    "base-filepath-test_check_set_filepath_doesnt_exist/complete"
                )
            ),
        ]
    )


def test_get_base_filepath():
    ret = test_db.get_base_filepath("test-uuid-get-base-filepath")

    assert ret == os.path.abspath("nml_img/test-uuid-get-base-filepath/")


ml_img_0 = np.arange(1, 10, dtype=np.uint8).reshape(3, 3)
ml_img_1 = 2 * np.arange(1, 10, dtype=np.uint8).reshape(3, 3)


def test_insert_ml_data():
    test_db.insert_ml_data(ml_img_0.tobytes(), 0)
    test_db.insert_ml_data(ml_img_1.tobytes(), 1)


def test_get_ml_data_len():
    ret = test_db.get_ml_data_len()
    assert ret == 2


def test_get_first_ml_data():
    ret = test_db.get_first_ml_data()
    after_img = np.frombuffer(ret.img, dtype=np.uint8)
    assert ret.classifier == 0
    assert np.array_equal(after_img, ml_img_0.flatten())


def test_get_all_ml_data_no_class():
    ret = test_db.get_all_ml_data()
    for count, entry in enumerate(ret):
        after_img = np.frombuffer(entry.img, dtype=np.uint8)
        assert entry.classifier == count
        if count == 0:
            assert np.array_equal(after_img, ml_img_0.flatten())
        else:
            assert np.array_equal(after_img, ml_img_1.flatten())


def test_get_all_ml_data_crack_class():
    ret = test_db.get_all_ml_data("CRACK")
    for entry in ret:
        after_img = np.frombuffer(entry.img, dtype=np.uint8)
        assert entry.classifier == 1
        assert np.array_equal(after_img, ml_img_1.flatten())


def test_get_all_ml_data_no_crack_class():
    ret = test_db.get_all_ml_data("NO_CRACK")
    for entry in ret:
        after_img = np.frombuffer(entry.img, dtype=np.uint8)
        assert entry.classifier == 0
        assert np.array_equal(after_img, ml_img_0.flatten())
