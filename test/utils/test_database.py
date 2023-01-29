import pytest
from unittest.mock import patch, Mock, ANY, call

from src.utils.database import nmlDB
from src.utils.exceptions import UserAlreadyCreated, UserNotFound

base_mock = Mock()
base_mock.metadata.create_all

session_maker_mock = Mock()
session_maker_mock.add
session_maker_mock.commit
session_maker_mock.query


@patch("sqlalchemy.orm.sessionmaker", return_value=session_maker_mock)
@patch("sqlalchemy.orm.declarative_base", return_value=base_mock)
@patch("sqlalchemy.create_engine", return_value="test-engine")
def test_nml_init(sql_create_mock, sql_base_mock, sql_session_mock):
    db = nmlDB()

    sql_create_mock.assert_called_once_with()
    sql_base_mock.assert_called_once_with()
    sql_session_mock.assert_called_once_with()
