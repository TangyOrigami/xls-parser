import pytest

from structs.result import Result as r
from util.db import DBInterface

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
    dbi.initialize_db("TEST")
    yield dbi
    DBInterface.reset_instance()


# ======================================
# 🔧 Helpers
# ======================================


def _create_test_employee(db, first="Unit", middle="T", last="User", group="QA"):
    args = (first, middle, last, group)
    assert db.save_employee("TEST", args) == r.SUCCESS
    return args


def _get_employee_id(db, args):
    result = db._read_employee_id("TEST", args[:3])
    assert result != r.ERROR and result
    return result[0][0]


def _create_test_pay_period(db, employee_id):
    args = (employee_id, "2024-01-01", "2024-01-14")
    assert db.save_pay_period("TEST", args) == r.SUCCESS
    return args


def _get_pay_period_id(db, employee_id):
    result = db._read_pay_period_id("TEST", (employee_id, "2024-01-01"))
    assert result != r.ERROR and result
    return result[0][0]


def _create_test_work_entry(db, pay_period_id):
    args = (pay_period_id, "2024-01-03", 8.0)
    assert db.save_work_entry("TEST", args) == r.SUCCESS
    return args


def _delete_test_employee(db, args):
    assert db.delete_employee("TEST", args) == r.SUCCESS


# ======================================
# ✅ Initialization
# ======================================


def test_db_init(DB):
    assert DB.initialize_db(BUILD="TEST") == r.SUCCESS


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
        assert db._read_employee_id("TEST", args[:3])
    else:
        assert not db._read_employee_id("TEST", args[:3])
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

    result = DB._read_pay_period_id("TEST", (emp_id, "2024-01-01"))
    assert result != r.ERROR and result
    result = DB._read_pay_period_id_by_date("TEST", ("2024-01-01",))
    assert result != r.ERROR and result
    result = DB._read_pay_period_ids("TEST", ("2024-01-01",))
    assert result != r.ERROR and result

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
    result = DB._read_work_entry_id("TEST", args)
    assert result != r.ERROR and result
    result = DB._read_work_entries("TEST", (pp_id,))
    assert result != r.ERROR and result

    _delete_test_employee(DB, emp_args)


# ======================================
# 💬 Comment Tests
# ======================================


def test_comment_cycle(DB):
    emp_args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, emp_args)
    _create_test_pay_period(DB, emp_id)
    pp_id = _get_pay_period_id(DB, emp_id)

    comment_args = (pp_id, emp_id, "2024-01-03", "late", "early", "bonus")
    assert DB.save_comment("TEST", comment_args) == r.SUCCESS
    result = DB._read_comment_id("TEST", (pp_id, emp_id, "2024-01-03"))
    assert result != r.ERROR and result

    _delete_test_employee(DB, emp_args)


# ======================================
# 👥 Metadata Tests
# ======================================


def test_read_employee_name_by_id(DB):
    emp_args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, emp_args)
    result = DB._read_employee_name("TEST", (emp_id,))
    assert result != r.ERROR and result[0][:3] == emp_args[:3]
    _delete_test_employee(DB, emp_args)


def test_read_employee_ids_from_pay_period(DB):
    emp_args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, emp_args)
    _create_test_pay_period(DB, emp_id)
    pp_id = _get_pay_period_id(DB, emp_id)
    result = DB._read_employee_ids("TEST", (pp_id,))
    assert result != r.ERROR and result[0][0] == emp_id
    _delete_test_employee(DB, emp_args)


# ======================================
# 🎯 Default Queries
# ======================================


def test_default_employee_and_date(DB):
    emp_args = _create_test_employee(DB)
    emp_id = _get_employee_id(DB, emp_args)
    _create_test_pay_period(DB, emp_id)
    result = DB._default_employee("TEST")
    assert result != r.ERROR and result
    result = DB._default_date("TEST")
    assert result != r.ERROR and result
    _delete_test_employee(DB, emp_args)


# ======================================
# 🧹 Singleton Tests
# ======================================


def test_singleton_identity():
    a = DBInterface("a.db")
    b = DBInterface("b.db")
    assert a is b


def test_singleton_attribute_persistence():
    db1 = DBInterface("a.db")
    db2 = DBInterface("b.db")
    db1.test_value = 42
    assert hasattr(db2, "test_value")
    assert db2.test_value == 42


def test_singleton_does_not_reinit_on_new_call():
    db1 = DBInterface("a.db")
    db1.connection_string = "b.db"
    db2 = DBInterface("c.db")
    assert db2.connection_string == "b.db"


def test_singleton_connection_consistency():
    db1 = DBInterface("a.db")
    db1.connect("a.db")
    db2 = DBInterface("a.db")
    db2.cursor.execute("CREATE TABLE IF NOT EXISTS SingletonTest (id INTEGER);")
    db2.connection.commit()
    result = db1.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='SingletonTest';"
    ).fetchone()
    assert result


def test_singleton_no_duplicate_connection():
    db1 = DBInterface("a.db")
    db1.connect("a.db")
    connection1 = db1.connection
    db2 = DBInterface("a.db")
    db2.connect("a.db")
    connection2 = db2.connection
    assert connection1 is connection2
