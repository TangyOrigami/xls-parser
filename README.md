# Timesheet Analyzer

## TODO:
1. [.] Finish setting up the '-d' flag to run the application in debug mode.
    - [.] Flag should activate the loggers that are spread all throught the code base. 
    - [,] Add more loggers throught the code base. This will have to happen as the app is developed.

2. [?] Finish db.py
    - [.] Make sure SQL is valid before committing operations.
    - [.] Save to DB.
        - [.] Save user.
        - [.] Save Pay Period.
        - [.] Save Work Entry.
        - [,] Save Pay Period Comment.
    - [!] Read from DB
        - [!] Read user.
        - [!] Read Pay Period.
        - [!] Read Work Entry.
        - [!] Read Pay Period Comment.
    - [!] Needs audit to see what else this needs work on.

3. [?] Finish Table widget
    - [?] Pull data from db (requires db.py to be done).
    - [?] Add interoperability between widgets.

4. [?] Finish Dashboard widget.
    - [?] There's nothing done on this. Heavy WIP.

5. [?] Clean up code.
    - [?] This will never be done, it is purpusefully an unreachable goal.


|Sybmol|Meaning|
|:----:|:-----:|
|?|Important|
|!|Urgent|
|,|Backburner|
|.|Done|
