import gzip
from datetime import date
from pathlib import Path

import pytest

from structs.result import Result
from util.db import DBInterface

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS

project_root = Path(__file__).resolve().parent.parent

# ======================================
# 🔁 Fixtures
# ======================================


@pytest.fixture(autouse=True)
def reset_db_interface_singleton():
    yield
    DBInterface.reset_instance()


@pytest.fixture
def DB(tmp_path):
    db_file = tmp_path / "test.db"
    dbi = DBInterface(temp_db=str(db_file))
    yield dbi
    DBInterface.reset_instance()


# ======================================
# 🔧 Helpers
# ======================================


def _create_test_employee(db, first="Unit", middle="T", last="User", group="QA"):
    args = (first, middle, last, group)
    assert db.save_employee(BUILD="TEST", args=args) == SUCCESS
    return args


def _get_employee_id(db, args):
    result = db._read_employee_id(BUILD="TEST", args=args[:3])
    assert result != ERROR and result is not None
    return result[0][0]


def _create_test_pay_period(db, employee_id):
    args = (employee_id, "2024-01-01", "2024-01-14")
    assert db.save_pay_period(BUILD="TEST", args=args) == SUCCESS
    return args


def _get_pay_period_id(db, employee_id):
    result = db._read_pay_period_id(BUILD="TEST", args=(employee_id, "2024-01-01"))
    assert result != ERROR and result
    return result[0][0]


def _create_test_work_entry(db, pay_period_id):
    args = (pay_period_id, "2024-01-03", 8.0)
    assert db.save_work_entry(BUILD="TEST", args=args) == SUCCESS
    return args


def _delete_test_employee(db, args):
    assert db.delete_employee(BUILD="TEST", args=args) == SUCCESS


def _delete_test_work_entry(db, pay_period_id):
    assert db.delete_work_entry(BUILD="TEST", args=(pay_period_id,)) == SUCCESS


# ======================================
# ✅ Core DB Tests
# ======================================


def test_initialize_db(DB):
    assert DB.initialize_db(BUILD="TEST") == SUCCESS


def test_singleton_identity():
    a = DBInterface("a.db")
    b = DBInterface("b.db")
    assert a is b


def test_reset_instance_clears_state(tmp_path):
    db1 = DBInterface(str(tmp_path / "a.db"))
    db1.connect()
    DBInterface.reset_instance()
    db2 = DBInterface(str(tmp_path / "b.db"))
    assert db2.DB == str(tmp_path / "b.db")


def test_ensure_connection_raises():
    dbi = DBInterface()
    dbi.connection = None
    dbi.DB = None
    with pytest.raises(ValueError):
        dbi._DBInterface__ensure_connection()


# ======================================
# 📄 Dump & Restore Tests
# ======================================


def test_dump_db_and_compress(DB):
    today = date.today().isoformat()
    expected_filename = f"test_dump_{today}.sql.gz"
    expected_path = project_root / "temp" / expected_filename
    try:
        result = DB.dump_db_and_compress(BUILD="TEST")
        assert isinstance(result, list) and result[1] == SUCCESS
        assert expected_path.exists()
        with gzip.open(expected_path, "rt", encoding="utf-8") as f:
            assert f.readline().strip().startswith("BEGIN TRANSACTION")
    finally:
        expected_path.unlink(missing_ok=True)


def test_initialize_db_from_invalid_dump_file(tmp_path):
    dbi = DBInterface(str(tmp_path / "app.db"))
    dbi.connect()
    dbi.initialize_db(BUILD="TEST")
    dump_path = tmp_path / "invalid.sql.gz"
    with gzip.open(dump_path, "wt", encoding="utf-8") as f:
        f.write("INVALID SQL")
    assert dbi.initialize_db_from_dump_file(str(dump_path)) == ERROR


def test_restore_from_backup_fails(monkeypatch):
    dbi = DBInterface()
    monkeypatch.setattr(dbi, "_DBInterface__get_latest_backup_path", lambda: ERROR)
    assert dbi._DBInterface__restore_from_backup() == ERROR


# ======================================
# 👤 Employee CRUD Tests
# ======================================


def test_employee_crud(DB):
    args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, args)
    assert emp_id
    _delete_test_employee(DB, args)


def test_duplicate_employee(DB):
    args = _create_test_employee(DB)
    assert DB.save_employee(BUILD="TEST", args=args) == SUCCESS
    _delete_test_employee(DB, args)


# ======================================
# 📅 Pay Period Tests
# ======================================


def test_pay_period_crud(DB):
    emp_args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, emp_args)
    _create_test_pay_period(DB, emp_id)
    assert DB._read_pay_period_id(BUILD="TEST", args=(emp_id, "2024-01-01"))
    _delete_test_employee(DB, emp_args)


# ======================================
# ⏱ Work Entry Tests
# ======================================


def test_work_entry_crud(DB):
    emp_args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, emp_args)
    _create_test_pay_period(DB, emp_id)
    pp_id = _get_pay_period_id(DB, emp_id)
    args = _create_test_work_entry(DB, pp_id)
    assert DB._read_work_entry_id(BUILD="TEST", args=args)
    _delete_test_work_entry(DB, pp_id)
    _delete_test_employee(DB, emp_args)


# ======================================
# 💬 Comment Tests
# ======================================


def test_comment_crud(DB):
    emp_args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, emp_args)
    _create_test_pay_period(DB, emp_id)
    pp_id = _get_pay_period_id(DB, emp_id)
    comment_args = (pp_id, emp_id, "2024-01-03", "late", "early", "bonus")
    assert DB.save_comment(BUILD="TEST", args=comment_args) == SUCCESS
    assert DB._read_comment_id(BUILD="TEST", args=(pp_id, emp_id, "2024-01-03"))
    _delete_test_employee(DB, emp_args)


# ======================================
# 🔎 Read / Meta Queries
# ======================================


def test_read_employee_name(DB):
    args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, args)
    result = DB._read_employee_name(BUILD="TEST", args=(emp_id,))
    assert result != ERROR and result[0][:3] == args[:3]
    _delete_test_employee(DB, args)


def test_schema_version(DB):
    result = DB._DBInterface__run_sql_read(
        "SELECT Value FROM Meta WHERE Key='SchemaVersion';", args=()
    )
    assert result != ERROR and result[0][0] == "1.0"
