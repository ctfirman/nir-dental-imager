import pytest
from unittest.mock import patch, Mock, ANY, call

from src.utils.database import nmlDB


mock_sqlite3_conn = Mock()
mock_sqlite3_cursor = Mock()

mock_sqlite3_conn.cursor.return_value = mock_sqlite3_cursor
mock_sqlite3_conn.commit

mock_sqlite3_cursor.execute


@patch("sqlite3.connect", return_value=mock_sqlite3_conn)
def test_nmlDB_init(sqllite3_connect_mock):
    db = nmlDB()

    sqllite3_connect_mock.assert_called_once_with("nml.db", detect_types=ANY)
    mock_sqlite3_conn.cursor.assert_called_once_with()
    mock_sqlite3_cursor.execute.assert_has_calls(
        [
            call(
                """CREATE TABLE IF NOT EXISTS users (
                user_uuid UUID PRIMARY KEY NOT NULL UNIQUE,
                user_email text NOT NULL UNIQUE,
                first_name text NOT NULL,
                last_name text NOT NULL
            );"""
            ),
            call(
                """CREATE TABLE IF NOT EXISTS image_sessions (
                session_id INT PRIMARY KEY NOT NULL UNIQUE,
                date text NOT NULL,
                user_uuid UUID NOT NULL UNIQUE,
                FOREIGN KEY (user_uuid) REFERENCES users(user_uuid)
            );"""
            ),
        ]
    )
    mock_sqlite3_conn.commit.assert_called_once_with()
