from db.session import _enable_sqlite_foreign_keys


class FakeCursor:
    def __init__(self):
        self.queries = []
        self.closed = False

    def execute(self, query):
        self.queries.append(query)

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()

    def cursor(self):
        return self.cursor_obj


def test_sqlite_foreign_keys_are_enabled_on_connect() -> None:
    connection = FakeConnection()

    _enable_sqlite_foreign_keys(connection, None)

    assert connection.cursor_obj.queries == ["PRAGMA foreign_keys=ON"]
    assert connection.cursor_obj.closed is True
