PRAGMA foreign_keys = ON;

CREATE TABLE Item (
    item_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    publisher TEXT,
    genre TEXT,
    pub_year INTEGER,
    format TEXT NOT NULL
        CHECK (format IN ('Print','Online','Magazine','Journal','Record')),
    isbn TEXT,
    location TEXT,
    status TEXT NOT NULL DEFAULT 'Available'
                    CHECK (status IN ('Available','Borrowed','Reserved','Lost'))
);

CREATE TABLE FutureItem (
    future_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    publisher TEXT,
    genre TEXT,
    format TEXT NOT NULL
                CHECK (format IN ('Print','Online','Magazine','Journal','Record')),
    acquisition_type TEXT NOT NULL DEFAULT 'Purchase'
                            CHECK (acquisition_type IN ('Donation','Purchase')),
    donor_name TEXT,                 
    expected_arrival TEXT,                
    order_status  TEXT NOT NULL DEFAULT 'Pending'
                        CHECK (order_status IN ('Pending','Received','Rejected'))
);

CREATE TABLE Member (
    member_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    email TEXT NOT NULL UNIQUE,
    join_date TEXT NOT NULL DEFAULT (date('now'))
);

CREATE TABLE Person (
    person_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('Employee','Volunteer'))
);

CREATE TABLE Employee (
    employee_id INTEGER PRIMARY KEY,
    person_id   INTEGER NOT NULL UNIQUE
        REFERENCES Person(person_id) ON DELETE CASCADE,
    job_title   TEXT    NOT NULL,
    salary      REAL    CHECK (salary >= 0),
    hire_date   TEXT    NOT NULL
);

CREATE TABLE Volunteer (
    volunteer_id INTEGER PRIMARY KEY,
    person_id INTEGER NOT NULL UNIQUE
        REFERENCES Person(person_id) ON DELETE CASCADE,
    start_date TEXT NOT NULL,
    volunteer_hours REAL NOT NULL DEFAULT 0 CHECK (volunteer_hours >= 0)
);

CREATE TABLE Borrow (
    borrow_id INTEGER PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES Member(member_id),
    item_id INTEGER NOT NULL REFERENCES Item(item_id),
    borrow_date TEXT NOT NULL DEFAULT (date('now')),
    due_date TEXT NOT NULL,
    return_date TEXT,
    status TEXT NOT NULL DEFAULT 'Borrowed'
                CHECK (status IN ('Borrowed','Returned','Overdue','Lost')),
    CHECK (due_date > borrow_date),
    CHECK (return_date IS NULL OR return_date >= borrow_date)
);

CREATE TABLE Fine (
    fine_id INTEGER PRIMARY KEY,
    borrow_id INTEGER NOT NULL REFERENCES Borrow(borrow_id) ON DELETE CASCADE,
    amount REAL NOT NULL CHECK (amount >= 0),
    reason TEXT NOT NULL CHECK (reason IN ('Late Return','Lost Item')),
    payment_status TEXT NOT NULL DEFAULT 'Unpaid'
                        CHECK (payment_status IN ('Unpaid','Paid'))
);

CREATE TABLE Room (
    room_id  INTEGER PRIMARY KEY,
    room_number TEXT NOT NULL UNIQUE,
    room_type TEXT NOT NULL
                    CHECK (room_type IN ('Event Room','Group Study','Individual Study')),
    capacity INTEGER NOT NULL CHECK (capacity > 0)
);

CREATE TABLE Event (
    event_id INTEGER PRIMARY KEY,
    event_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_date TEXT NOT NULL,
    event_time TEXT NOT NULL,
    room_id INTEGER NOT NULL REFERENCES Room(room_id), 
    age_group TEXT,
    max_capacity INTEGER NOT NULL CHECK (max_capacity > 0),
    accessibility TEXT
);

CREATE TABLE Registration (
    registration_id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES Event(event_id) ON DELETE CASCADE,
    member_id INTEGER NOT NULL REFERENCES Member(member_id),
    registration_date TEXT NOT NULL DEFAULT (date('now')),
    UNIQUE (event_id, member_id)
);

CREATE TABLE HelpRequest (
    help_id INTEGER PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES Member(member_id),
    employee_id INTEGER REFERENCES Employee(employee_id),  -- assigned librarian
    topic TEXT NOT NULL,
    description TEXT,
    request_date TEXT NOT NULL DEFAULT (date('now')),
    status TEXT NOT NULL DEFAULT 'Open'
                CHECK (status IN ('Open','Resolved'))
);


CREATE TRIGGER trg_borrow_block_unavailable
BEFORE INSERT ON Borrow
FOR EACH ROW
WHEN (SELECT status FROM Item WHERE item_id = NEW.item_id) <> 'Available'
BEGIN
    SELECT RAISE(ABORT, 'Item is not available to borrow');
END;

CREATE TRIGGER trg_borrow_mark_item
AFTER INSERT ON Borrow
FOR EACH ROW
BEGIN
    UPDATE Item SET status = 'Borrowed' WHERE item_id = NEW.item_id;
END;

CREATE TRIGGER trg_return_item
AFTER UPDATE OF return_date ON Borrow
FOR EACH ROW
WHEN OLD.return_date IS NULL AND NEW.return_date IS NOT NULL
BEGIN
    UPDATE Item   SET status = 'Available' WHERE item_id = NEW.item_id;
    UPDATE Borrow SET status = 'Returned'  WHERE borrow_id = NEW.borrow_id;

    INSERT INTO Fine (borrow_id, amount, reason)
    SELECT NEW.borrow_id,
           MIN(CAST(julianday(NEW.return_date) - julianday(NEW.due_date) AS INTEGER) * 0.50, 20.00),
           'Late Return'
    WHERE julianday(NEW.return_date) > julianday(NEW.due_date);
END;

CREATE TRIGGER trg_registration_capacity
BEFORE INSERT ON Registration
FOR EACH ROW
WHEN (SELECT COUNT(*) FROM Registration WHERE event_id = NEW.event_id)
     >= (SELECT max_capacity FROM Event WHERE event_id = NEW.event_id)
BEGIN
    SELECT RAISE(ABORT, 'Event is full');
END;