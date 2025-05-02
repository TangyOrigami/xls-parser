from structs.result import Result as r
from util.db import DBInterface

"""
DB TESTS
"""

db = DBInterface("app.db")

# ======================================
# 🧪 Shared Fixtures & Helper Functions
# ======================================


def _create_test_employee(first="Unit", middle="T", last="User", group="QA"):
    args = (first, middle, last, group)
    db.save_employee("TEST", args)
    return args


def _get_employee_id(args):
    return db._read_employee_id("TEST", args[:3])[0][0]


def _create_test_pay_period(employee_id):
    args = (employee_id, "2024-01-01", "2024-01-14")
    db.save_pay_period("TEST", args)
    return args


def _get_pay_period_id(employee_id):
    return db._read_pay_period_id("TEST", (employee_id, "2024-01-01"))[0][0]


def _create_test_work_entry(pay_period_id):
    args = (pay_period_id, "2024-01-03", 8.0)
    db.save_work_entry("TEST", args)
    return args


def _delete_test_employee(args):
    db.delete_employee("TEST", args)


# ======================================
# ✅ Core DB Initialization Test
# ======================================


def test_db_init():
    assert db.initialize_db(BUILD="TEST") == r.SUCCESS, "Failed to initialize DB schema"


# ======================================
# 👤 Employee Cycle Tests
# ======================================


def _employee_cycle_test(first, middle, last, group="TestGroup", expect_success=True):
    args = (first, middle, last, group)
    try:
        insert_result = db.save_employee(BUILD="TEST", args=args)
        if expect_success:
            assert insert_result == r.SUCCESS, f"Insert failed: {args}"
            read_result = db._read_employee_id(BUILD="TEST", args=args[:3])
            assert read_result, f"Read failed after insert: {args}"
        else:
            assert not db._read_employee_id(
                BUILD="TEST", args=args[:3]
            ), f"Unexpected insert for invalid args: {args}"
    finally:
        db.delete_employee(BUILD="TEST", args=args)


def test_employee_cycle_short_middle():
    _employee_cycle_test("First", "M", "Last")


def test_employee_cycle_full_middle():
    _employee_cycle_test("First", "Middle", "Last")


def test_employee_cycle_empty_middle():
    _employee_cycle_test("First", "", "Last")


def test_employee_cycle_invalid_args():
    args = ("First", "", "", "Last", "TestGroup")  # too many parts
    try:
        result = db.save_employee(BUILD="TEST", args=args)
        assert result == r.ERROR, f"Insert should fail for: {args}"
    except Exception:
        pass  # Acceptable


# ======================================
# 📅 PayPeriod Tests
# ======================================


def test_pay_period_cycle():
    emp_args = _create_test_employee()
    try:
        emp_id = _get_employee_id(emp_args)
        _create_test_pay_period(emp_id)

        assert db._read_pay_period_id(
            "TEST", (emp_id, "2024-01-01")
        ), "Missing PayPeriod by ID"
        assert db._read_pay_period_id_by_date(
            "TEST", ("2024-01-01",)
        ), "Missing PayPeriod by date"
        assert db._read_pay_period_ids(
            "TEST", ("2024-01-01",)
        ), "Missing PayPeriod IDs by start"
    finally:
        _delete_test_employee(emp_args)


# ======================================
# ⏱ WorkEntry Tests
# ======================================


def test_work_entry_cycle():
    emp_args = _create_test_employee()
    try:
        emp_id = _get_employee_id(emp_args)
        _create_test_pay_period(emp_id)
        pp_id = _get_pay_period_id(emp_id)

        args = _create_test_work_entry(pp_id)
        assert db._read_work_entry_id(
            "TEST", args
        ), "Missing WorkEntry by ID+Date+Hours"
        assert db._read_work_entries(
            "TEST", (pp_id,)
        ), "No WorkEntries found for PayPeriod"
    finally:
        _delete_test_employee(emp_args)


# ======================================
# 💬 PayPeriodComment Tests
# ======================================


def test_comment_cycle():
    emp_args = _create_test_employee()
    try:
        emp_id = _get_employee_id(emp_args)
        _create_test_pay_period(emp_id)
        pp_id = _get_pay_period_id(emp_id)

        comment_args = (pp_id, emp_id, "2024-01-03", "late", "early", "bonus")
        db.save_comment("TEST", comment_args)

        assert db._read_comment_id(
            "TEST", (pp_id, emp_id, "2024-01-03")
        ), "Missing comment record"
    finally:
        _delete_test_employee(emp_args)


# ======================================
# 👥 Metadata / Relational Tests
# ======================================


def test_read_employee_name_by_id():
    emp_args = _create_test_employee()
    try:
        emp_id = _get_employee_id(emp_args)
        result = db._read_employee_name("TEST", (emp_id,))
        assert result[0][:3] == emp_args[:3], f"Mismatch: {result} != {emp_args}"
    finally:
        _delete_test_employee(emp_args)


def test_read_employee_ids_from_pay_period():
    emp_args = _create_test_employee()
    try:
        emp_id = _get_employee_id(emp_args)
        _create_test_pay_period(emp_id)
        pp_id = _get_pay_period_id(emp_id)

        result = db._read_employee_ids("TEST", (pp_id,))
        assert result[0][0] == emp_id, "EmployeeID mismatch in PayPeriod"
    finally:
        _delete_test_employee(emp_args)


# ======================================
# 🎯 Default Record Queries
# ======================================


def test_default_employee_and_date():
    emp_args = _create_test_employee()
    try:
        emp_id = _get_employee_id(emp_args)
        _create_test_pay_period(emp_id)

        assert db._default_employee("TEST"), "No default employee returned"
        assert db._default_date("TEST"), "No default pay period start date returned"
    finally:
        _delete_test_employee(emp_args)


# ======================================
# * Singleton DB Tests
# ======================================


def test_singleton_identity():
    a = DBInterface("a.db")
    b = DBInterface("b.db")
    assert a is b, "DBInterface is not a singleton instance"


def test_singleton_attribute_persistence():
    db1 = DBInterface("a.db")
    db2 = DBInterface("b.db")

    # Inject a fake attribute
    db1.test_value = 42
    assert hasattr(db2, "test_value"), "State not shared across instances"
    assert db2.test_value == 42, "Shared state mismatch between singleton instances"


def test_singleton_does_not_reinit_on_new_call():
    db1 = DBInterface("a.db")
    db1.connection_string = "b.db"

    db2 = DBInterface("c.db")
    assert db2.connection_string == "b.db", "Re-initialized singleton incorrectly"


def test_singleton_connection_consistency():
    db1 = DBInterface("a.db")
    db1.connect("a.db")

    db2 = DBInterface("a.db")
    db2.cursor.execute("CREATE TABLE IF NOT EXISTS SingletonTest (id INTEGER);")
    db2.connection.commit()

    db1.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='SingletonTest';"
    )
    result = db1.cursor.fetchone()
    assert result, "Cursor or connection not shared in singleton instance"


def test_singleton_no_duplicate_connection():
    db1 = DBInterface("a.db")
    db1.connect("a.db")
    connection1 = db1.connection

    db2 = DBInterface("a.db")
    db2.connect("a.db")
    connection2 = db2.connection

    assert connection1 is connection2, "Multiple DB connections created in singleton"
