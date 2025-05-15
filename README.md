# Timesheet Analyzer

|Sybmol|Meaning|
|:----:|:-----:|
|?|Important|
|!|Urgent|
|,|Backburner|
|.|Done|

## TODO:
1. [?] Finish db.py
    - [.] Make sure SQL is valid before committing operations.
    - [.] Save to DB.
        - [.] Save user.
        - [.] Save Pay Period.
        - [.] Save Work Entry.
        - [,] Save Pay Period Comment.
    - [.] Read from DB
        - [.] Read user.
        - [.] Read Pay Period.
        - [.] Read Work Entry.
        - [.] Read Pay Period Comment.
    - [!] Get rid of app_backup.db process, just use the dump files. Uses less space and works way better.
        - [!] Create `backups` directory where dump files get automatically saved.
            - [!] Keep a maximum of 12 backups.
        - [!] Add option to use a previous back up that was created to file menu.
    - [?] Needs audit to see what else this needs work on.

2. [?] Finish Table widget
    - [.] Pull data from db (requires db.py to be done).
    - [.] Add interoperability between widgets.
    - [!] Remove graph
    - [!] Add OT calculation
    - [!] Pass data to Dashboard widget to print paystub
    - [!] Add way to do this in bulk.

3. [!] Finish Dashboard widget.
    - [!] Dashboard will now create paystub
    - [!] Create paystub
    - [!] Add way to do this in bulk.

4. [?] Clean up code.
    - [?] This will never be done, it is purpusefully an unreachable goal.
