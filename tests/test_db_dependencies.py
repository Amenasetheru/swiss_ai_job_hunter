from unittest.mock import MagicMock, patch  # Import test doubles and patching utilities

from app.db.dependencies import get_db_session  # Import the FastAPI database dependency


def test_get_db_session_closes_session_after_use() -> None:
    """Verify that the database dependency always closes its session."""

    mocked_session = MagicMock()

    with patch(
        "app.db.dependencies.SessionFactory",
        return_value=mocked_session,
    ):
        dependency = get_db_session()
        yielded_session = next(dependency)

        assert yielded_session is mocked_session

        try:
            next(dependency)
        except StopIteration:
            pass

    mocked_session.close.assert_called_once_with()
