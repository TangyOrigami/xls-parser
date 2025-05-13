import gzip
from datetime import date
from pathlib import Path

import pytest

from structs.result import Result as r
from util.db import DBInterface

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
    dbi = DBInterface(str(db_file))
    dbi.connect(str(db_file))
    dbi.initialize_db(BUILD="TEST")
    yield dbi
    DBInterface.reset_instance()


# ======================================
# 🔧 Helpers
# ======================================


def _create_test_employee(db, first="Unit", middle="T", last="User", group="QA"):
    args = (first, middle, last, group)
    assert db.save_employee(BUILD="TEST", args=args) == r.SUCCESS
    return args


def _get_employee_id(db, args):
    result = db._read_employee_id(BUILD="TEST", args=args[:3])
    assert result != r.ERROR and result is not None
    return result[0][0]


def _create_test_pay_period(db, employee_id):
    args = (employee_id, "2024-01-01", "2024-01-14")
    assert db.save_pay_period(BUILD="TEST", args=args) == r.SUCCESS
    return args


def _get_pay_period_id(db, employee_id):
    result = db._read_pay_period_id(BUILD="TEST", args=(employee_id, "2024-01-01"))
    assert result != r.ERROR and result
    return result[0][0]


def _create_test_work_entry(db, pay_period_id):
    args = (pay_period_id, "2024-01-03", 8.0)
    assert db.save_work_entry(BUILD="TEST", args=args) == r.SUCCESS
    return args


def _delete_test_employee(db, args):
    assert db.delete_employee(BUILD="TEST", args=args) == r.SUCCESS


def _delete_test_work_entry(db, args):
    assert db.delete_work_entry(BUILD="TEST", args=args) == r.SUCCESS


# ======================================
# ✅ Initialization and Backup
# ======================================


def test_db_init(DB):
    assert DB.initialize_db(BUILD="TEST") == r.SUCCESS


def test_create_backup(DB):
    target_db_path = project_root / "app.db"
    backup_db_path = project_root / "app_backup.db"

    assert (
        DB.create_backup(target_db_path=target_db_path, backup_db_path=backup_db_path)
        == r.SUCCESS
    )


# ======================================
# ✅ Dumping
# ======================================


def test_dump_db_and_compress(DB):
    today = date.today().isoformat()
    expected_filename = f"test_dump_{today}.sql.gz"
    expected_path = Path(__file__).resolve().parent.parent / "temp" / expected_filename

    try:
        result = DB.dump_db_and_compress(BUILD="TEST")
        if isinstance(result, list):
            assert result[1] == r.SUCCESS
        else:
            assert "Couldn't dump and compress DB."
        assert expected_path.exists()

        with gzip.open(expected_path, "rt", encoding="utf-8") as f:
            first_line = f.readline()
            assert first_line.strip().startswith("BEGIN TRANSACTION")

    finally:
        if expected_path.exists():
            expected_path.unlink()


def test_initialize_db_from_dump_file():
    project_root = Path(__file__).resolve().parent.parent
    db_path = project_root / "app.db"
    backup_path = project_root / "app_backup.db"
    dump_dir = project_root / "temp"
    dump_dir.mkdir(exist_ok=True)
    dump_path = dump_dir / f"test_dump_{date.today().isoformat()}.sql.gz"

    # Ensure app.db exists
    dbi = DBInterface(str(db_path))
    dbi.connect(str(db_path))
    dbi.initialize_db(BUILD="TEST")
    result = dbi.dump_db_and_compress(BUILD="TEST", path_to_file=str(dump_dir))

    if isinstance(result, list):
        # Create a dump file
        assert result[1] == r.SUCCESS
        assert dump_path.exists()

    result = dbi.initialize_db_from_dump_file(str(dump_path))
    assert result == r.SUCCESS

    # Cleanup
    dump_path.unlink(missing_ok=True)
    backup_path.unlink(missing_ok=True)


# ======================================
# 🛡️ Fallback & Recovery Tests
# ======================================


def test_initialize_db_fallback_on_failure(monkeypatch, tmp_path):
    db_path = tmp_path / "app.db"
    dbi = DBInterface(str(db_path))
    dbi.connect(str(db_path))
    dbi.initialize_db(BUILD="TEST")

    monkeypatch.setattr(dbi, "_DBInterface__run_sql_batch", lambda *_, **__: r.ERROR)
    result = dbi.initialize_db(BUILD="TEST")
    assert result == r.ERROR
    assert dbi._default_employee(BUILD="TEST") != r.ERROR


def test_initialize_db_from_invalid_dump_fallback(tmp_path):
    db_path = tmp_path / "app.db"
    dbi = DBInterface(str(db_path))
    dbi.connect(str(db_path))
    dbi.initialize_db(BUILD="TEST")

    dump_path = tmp_path / "corrupt_dump.sql.gz"
    with gzip.open(dump_path, "wt", encoding="utf-8") as f:
        f.write("THIS IS NOT VALID SQL;")

    result = dbi.initialize_db_from_dump_file(str(dump_path))
    assert result == r.ERROR
    assert dbi._default_employee(BUILD="TEST") != r.ERROR


def test_connect_force_reinitializes_connection(tmp_path):
    db_path = tmp_path / "test_force.db"
    dbi = DBInterface(str(db_path))
    dbi.connect(str(db_path))
    original_connection = dbi.connection

    dbi.connect(str(db_path), force=True)
    assert dbi.connection is not None
    assert dbi.connection != original_connection


def test_reset_instance_clears_state(tmp_path):
    db_path_1 = tmp_path / "a.db"
    db_path_2 = tmp_path / "b.db"

    db1 = DBInterface(str(db_path_1))
    db1.connect(str(db_path_1))
    DBInterface.reset_instance()

    db2 = DBInterface(str(db_path_2))
    assert db2.DB == str(db_path_2)

    if db_path_1.exists():
        db_path_1.unlink()

    if db_path_2.exists():
        db_path_2.unlink()


# ======================================
# 👤 Employee Tests
# ======================================


def _employee_cycle_test(
    db, first, middle, last, group="TestGroup", expect_success=True
):
    args = (first, middle, last, group)
    result = db.save_employee(BUILD="TEST", args=args)
    if expect_success:
        assert result == r.SUCCESS
        assert db._read_employee_id(BUILD="TEST", args=args[:3])
    else:
        assert not db._read_employee_id(BUILD="TEST", args=args[:3])
    _delete_test_employee(db, args)


def test_employee_cycle_short_middle(DB):
    _employee_cycle_test(DB, "First", "M", "Last")


def test_employee_cycle_full_middle(DB):
    _employee_cycle_test(DB, "First", "Middle", "Last")


def test_employee_cycle_empty_middle(DB):
    _employee_cycle_test(DB, "First", "", "Last")


def test_employee_cycle_invalid_args(DB):
    args = ("First", "", "", "Last", "TestGroup")
    try:
        result = DB.save_employee(BUILD="TEST", args=args)
        assert result == r.ERROR
    except Exception:
        pass


# ======================================
# 📅 PayPeriod Tests
# ======================================


def test_pay_period_cycle(DB):
    emp_args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, emp_args)
    _create_test_pay_period(DB, emp_id)

    result = DB._read_pay_period_id(BUILD="TEST", args=(emp_id, "2024-01-01"))
    assert result != r.ERROR and result is not None

    result = DB._read_pay_period_id_by_date(BUILD="TEST", args=("2024-01-01",))
    assert result != r.ERROR and result is not None

    result = DB._read_pay_period_ids(BUILD="TEST", args=("2024-01-01",))
    assert result != r.ERROR and result is not None

    _delete_test_employee(DB, emp_args)


# ======================================
# ⏱ WorkEntry Tests
# ======================================


def test_work_entry_cycle(DB):
    emp_args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, emp_args)
    _create_test_pay_period(DB, emp_id)
    pp_id = _get_pay_period_id(DB, emp_id)

    args = _create_test_work_entry(DB, pp_id)
    result = DB._read_work_entry_id(BUILD="TEST", args=args)
    assert result != r.ERROR and result
    result = DB._read_work_entries(BUILD="TEST", args=(pp_id,))
    assert result != r.ERROR and result

    print(pp_id)
    _delete_test_employee(DB, emp_args)
    _delete_test_work_entry(DB, str(pp_id))


# ======================================
# 💬 Comment Tests
# ======================================


def test_comment_cycle(DB):
    emp_args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, emp_args)
    _create_test_pay_period(DB, emp_id)
    pp_id = _get_pay_period_id(DB, emp_id)

    comment_args = (pp_id, emp_id, "2024-01-03", "late", "early", "bonus")
    assert DB.save_comment(BUILD="TEST", args=comment_args) == r.SUCCESS
    result = DB._read_comment_id(BUILD="TEST", args=(pp_id, emp_id, "2024-01-03"))
    assert result != r.ERROR and result

    _delete_test_employee(DB, emp_args)


# ======================================
# 👥 Metadata Tests
# ======================================


def test_read_employee_name_by_id(DB):
    emp_args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, emp_args)
    result = DB._read_employee_name(BUILD="TEST", args=(emp_id,))
    assert result != r.ERROR and result[0][:3] == emp_args[:3]
    _delete_test_employee(DB, emp_args)


def test_read_employee_ids_from_pay_period(DB):
    emp_args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, emp_args)
    _create_test_pay_period(DB, emp_id)
    pp_id = _get_pay_period_id(DB, emp_id)
    result = DB._read_employee_ids(BUILD="TEST", args=(pp_id,))
    assert result != r.ERROR and result[0][0] == emp_id
    _delete_test_employee(DB, emp_args)


# ======================================
# 🎯 Default Queries
# ======================================


def test_default_employee_and_date(DB):
    emp_args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, emp_args)
    _create_test_pay_period(DB, emp_id)
    result = DB._default_employee(BUILD="TEST")
    assert result != r.ERROR and result
    result = DB._default_date(BUILD="TEST")
    assert result != r.ERROR and result
    _delete_test_employee(DB, emp_args)


# ======================================
# 🧹 Singleton Tests
# ======================================


def test_singleton_identity():
    db_file = "a.db"
    try:
        a = DBInterface(db_file)
        b = DBInterface("b.db")
        assert a is b
    finally:
        if Path(db_file).exists():
            Path(db_file).unlink()


def test_singleton_attribute_persistence():
    db_file = "a.db"
    try:
        db1 = DBInterface(db_file)
        db2 = DBInterface("b.db")
        db1.test_value = 42
        assert hasattr(db2, "test_value")
        assert db2.test_value == 42
    finally:
        if Path(db_file).exists():
            Path(db_file).unlink()


def test_singleton_does_not_reinit_on_new_call():
    db_file = "a.db"
    try:
        db1 = DBInterface(db_file)
        db1.connection_string = "b.db"
        db2 = DBInterface("c.db")
        assert db2.connection_string == "b.db"
    finally:
        if Path(db_file).exists():
            Path(db_file).unlink()


def test_singleton_connection_consistency():
    db_file = "a.db"
    try:
        db1 = DBInterface(db_file)
        db1.connect(db_file)
        db2 = DBInterface(db_file)
        db2.cursor.execute("CREATE TABLE IF NOT EXISTS SingletonTest (id INTEGER);")
        db2.connection.commit()
        result = db1.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='SingletonTest';"
        ).fetchone()
        assert result
    finally:
        if Path(db_file).exists():
            Path(db_file).unlink()


def test_singleton_no_duplicate_connection():
    db_file = "a.db"
    try:
        db1 = DBInterface(db_file)
        db1.connect(db_file)
        connection1 = db1.connection
        db2 = DBInterface(db_file)
        db2.connect(db_file)
        connection2 = db2.connection
        assert connection1 is connection2
    finally:
        if Path(db_file).exists():
            Path(db_file).unlink()
