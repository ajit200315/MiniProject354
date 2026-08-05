import sqlite3
from datetime import date, timedelta

DB = "library.db"
TODAY = date(2026, 8, 5)
LOAN_PERIOD_DAYS = 21


def d(dt):
    """date -> 'YYYY-MM-DD' text, matching the schema's date format."""
    return dt.isoformat()

# HARDCODED DATA
# Item: (title, author, publisher, genre, pub_year, format, isbn, location)
ITEMS = [
    ("The Hobbit", "J.R.R. Tolkien", "Allen & Unwin", "Fantasy", 1937, "Print", "9780547928227", "Shelf A-12"),
    ("A Brief History of Time", "Stephen Hawking", "Bantam Books", "Science", 1988, "Print", "9780553380163", "Shelf B-03"),
    ("Sapiens", "Yuval Noah Harari", "Harper", "History", 2011, "Print", "9780062316097", "Shelf C-21"),
    ("The Martian", "Andy Weir", "Crown", "Fiction", 2014, "Print", "9780553418026", "Shelf A-30"),
    ("Educated", "Tara Westover", "Random House", "Biography", 2018, "Print", "9780399590504", "Shelf D-08"),
    ("The Name of the Wind", "Patrick Rothfuss", "DAW Books", "Fantasy", 2007, "Print", "9780756404741", "Shelf A-15"),
    ("Cosmos", "Carl Sagan", "Random House", "Science", 1980, "Print", "9780345539434", "Shelf B-07"),
    ("Gone Girl", "Gillian Flynn", "Crown", "Mystery", 2012, "Print", "9780307588371", "Shelf E-02"),
    ("The Silk Roads", "Peter Frankopan", "Bloomsbury", "History", 2015, "Print", "9781101912379", "Shelf C-25"),
    ("Dune", "Frank Herbert", "Chilton Books", "Fiction", 1965, "Print", "9780441172719", "Shelf A-01"),
    ("Clean Code", "Robert C. Martin", "Prentice Hall", "Technology", 2008, "Print", "9780132350884", "Shelf F-11"),
    ("The Design of Everyday Things", "Don Norman", "Basic Books", "Technology", 2013, "Print", "9780465050659", "Shelf F-14"),
    ("Where the Crawdads Sing", "Delia Owens", "Putnam", "Fiction", 2018, "Online", "9780735219090", "Digital"),
    ("Atomic Habits", "James Clear", "Avery", "Technology", 2018, "Online", "9780735211292", "Digital"),
    ("The Midnight Library", "Matt Haig", "Viking", "Fiction", 2020, "Online", "9780525559474", "Digital"),
    ("Becoming", "Michelle Obama", "Crown", "Biography", 2018, "Online", "9781524763138", "Digital"),
    ("National Geographic", "Various", "NatGeo Society", "Science", 2024, "Magazine", None, "Rack 1"),
    ("The Economist", "Various", "The Economist Group", "History", 2024, "Magazine", None, "Rack 2"),
    ("Scientific American", "Various", "Springer Nature", "Science", 2024, "Magazine", None, "Rack 1"),
    ("Time Magazine", "Various", "Time USA", "History", 2024, "Magazine", None, "Rack 3"),
    ("Nature", "Various", "Springer Nature", "Science", 2023, "Journal", None, "Journals A"),
    ("The Lancet", "Various", "Elsevier", "Science", 2023, "Journal", None, "Journals B"),
    ("IEEE Spectrum", "Various", "IEEE", "Technology", 2023, "Journal", None, "Journals C"),
    ("Journal of Modern History", "Various", "Univ. of Chicago", "History", 2022, "Journal", None, "Journals A"),
    ("Kind of Blue", "Miles Davis", "Columbia", "Art", 1959, "Record", None, "Music M-04"),
    ("Abbey Road", "The Beatles", "Apple Records", "Art", 1969, "Record", None, "Music M-01"),
    ("Thriller", "Michael Jackson", "Epic", "Art", 1982, "Record", None, "Music M-09"),
    ("The Dark Side of the Moon", "Pink Floyd", "Harvest", "Art", 1973, "Record", None, "Music M-06"),
    ("Rumours", "Fleetwood Mac", "Warner Bros", "Art", 1977, "Record", None, "Music M-03"),
    ("Blue Train", "John Coltrane", "Blue Note", "Art", 1958, "Record", None, "Music M-11"),
]

# FutureItem: (title, author, publisher, genre, format, acquisition_type, donor_name, expected_arrival_offset_days, order_status)
FUTURE_ITEMS = [
    ("Project Hail Mary", "Andy Weir", "Ballantine", "Fiction", "Print", "Purchase", None, 20, "Pending"),
    ("The Anthropocene Reviewed", "John Green", "Dutton", "Biography", "Print", "Purchase", None, 35, "Pending"),
    ("Klara and the Sun", "Kazuo Ishiguro", "Knopf", "Fiction", "Print", "Purchase", None, 15, "Received"),
    ("A Promised Land", "Barack Obama", "Crown", "Biography", "Print", "Donation", "Margaret Chen", 5, "Received"),
    ("The Code Breaker", "Walter Isaacson", "Simon & Schuster", "Science", "Print", "Donation", "David Okafor", 8, "Pending"),
    ("Grandma's Cookbook", "Rosa Alvarez", "Self-published", "Art", "Print", "Donation", "Rosa Alvarez", 3, "Received"),
    ("Local History of Burnaby", "Heritage Society", "City Press", "History", "Print", "Donation", "Burnaby Heritage Soc.", 12, "Pending"),
    ("The Complete Jazz Collection", "Various", "Verve", "Art", "Record", "Donation", "James Wilson", 40, "Pending"),
    ("Introduction to Algorithms", "Cormen et al.", "MIT Press", "Technology", "Print", "Purchase", None, 25, "Pending"),
    ("The Vanishing Half", "Brit Bennett", "Riverhead", "Fiction", "Online", "Purchase", None, 18, "Pending"),
    ("An Old Encyclopedia Set", "Various", "Britannica", "History", "Print", "Donation", "Eleanor Park", 6, "Rejected"),
    ("Photography Basics", "Ana Ferreira", "Focal Press", "Art", "Print", "Purchase", None, 30, "Pending"),
]

# Member: (first, last, address, phone, email, join_offset_days_ago)
MEMBERS = [
    ("Sarah", "Johnson", "123 Maple St, Burnaby, BC", "604-555-0101", "sarah.johnson@email.com", 800),
    ("Michael", "Chen", "456 Oak Ave, Vancouver, BC", "604-555-0102", "m.chen@email.com", 650),
    ("Emily", "Rodriguez", "789 Pine Rd, Burnaby, BC", "604-555-0103", "emily.r@email.com", 420),
    ("David", "Kim", "321 Cedar Ln, Surrey, BC", "604-555-0104", "david.kim@email.com", 900),
    ("Jessica", "Patel", "654 Birch Dr, Burnaby, BC", "604-555-0105", "j.patel@email.com", 300),
    ("James", "Wilson", "987 Elm St, Vancouver, BC", "604-555-0106", "james.w@email.com", 550),
    ("Maria", "Garcia", "147 Spruce Ave, Coquitlam, BC", "604-555-0107", "maria.g@email.com", 210),
    ("Robert", "Brown", "258 Willow Rd, Burnaby, BC", "604-555-0108", "r.brown@email.com", 730),
    ("Linda", "Martinez", "369 Ash Ln, New West, BC", "604-555-0109", "linda.m@email.com", 480),
    ("William", "Davis", "741 Fir Dr, Burnaby, BC", "604-555-0110", "will.davis@email.com", 190),
    ("Aisha", "Okafor", "852 Alder St, Vancouver, BC", "604-555-0111", "aisha.o@email.com", 360),
    ("Daniel", "Lee", "963 Poplar Ave, Richmond, BC", "604-555-0112", "daniel.lee@email.com", 620),
    ("Sophia", "Nguyen", "159 Walnut Rd, Burnaby, BC", "604-555-0113", "sophia.n@email.com", 95),
    ("Christopher", "Taylor", "357 Hemlock Ln, Surrey, BC", "604-555-0114", "chris.t@email.com", 510),
    ("Olivia", "Anderson", "468 Sequoia Dr, Burnaby, BC", "604-555-0115", "olivia.a@email.com", 45),
]

# Employee person: (first, last, address, phone, email, job_title, salary, hire_offset_days_ago)
EMPLOYEES = [
    ("Patricia", "Moore", "12 Library Ln, Burnaby, BC", "604-555-0201", "p.moore@library.ca", "Branch Manager", 82000, 2500),
    ("Kevin", "Jackson", "34 Book St, Burnaby, BC", "604-555-0202", "k.jackson@library.ca", "Librarian", 68000, 1800),
    ("Nancy", "White", "56 Read Ave, Vancouver, BC", "604-555-0203", "n.white@library.ca", "Librarian", 66000, 1200),
    ("Steven", "Harris", "78 Page Rd, Burnaby, BC", "604-555-0204", "s.harris@library.ca", "Assistant Librarian", 52000, 900),
    ("Karen", "Clark", "90 Shelf Dr, Surrey, BC", "604-555-0205", "k.clark@library.ca", "Circulation Clerk", 45000, 600),
    ("Brian", "Lewis", "11 Index Ln, Burnaby, BC", "604-555-0206", "b.lewis@library.ca", "Archivist", 58000, 1500),
    ("Michelle", "Walker", "22 Volume St, Vancouver, BC", "604-555-0207", "m.walker@library.ca", "Librarian", 67000, 1100),
    ("Jason", "Hall", "33 Chapter Ave, Burnaby, BC", "604-555-0208", "j.hall@library.ca", "IT Support", 61000, 700),
    ("Amanda", "Young", "44 Preface Rd, Coquitlam, BC", "604-555-0209", "a.young@library.ca", "Circulation Clerk", 44000, 400),
    ("Eric", "King", "55 Binding Dr, Burnaby, BC", "604-555-0210", "e.king@library.ca", "Assistant Librarian", 51000, 350),
]

# Volunteer person: (first, last, address, phone, email, start_offset_days_ago, hours)
VOLUNTEERS = [
    ("George", "Wright", "66 Quiet St, Burnaby, BC", "604-555-0301", "g.wright@email.com", 500, 145.5),
    ("Helen", "Lopez", "77 Story Ave, Vancouver, BC", "604-555-0302", "h.lopez@email.com", 380, 98.0),
    ("Frank", "Hill", "88 Tale Rd, Surrey, BC", "604-555-0303", "f.hill@email.com", 260, 62.5),
    ("Ruth", "Scott", "99 Fable Dr, Burnaby, BC", "604-555-0304", "r.scott@email.com", 420, 130.0),
    ("Arthur", "Green", "10 Legend Ln, Vancouver, BC", "604-555-0305", "a.green@email.com", 150, 40.0),
    ("Dorothy", "Adams", "20 Myth St, Burnaby, BC", "604-555-0306", "d.adams@email.com", 600, 210.0),
    ("Henry", "Baker", "30 Verse Ave, Coquitlam, BC", "604-555-0307", "h.baker@email.com", 90, 25.5),
    ("Alice", "Nelson", "40 Prose Rd, Burnaby, BC", "604-555-0308", "a.nelson@email.com", 340, 88.0),
    ("Walter", "Carter", "50 Sonnet Dr, Vancouver, BC", "604-555-0309", "w.carter@email.com", 200, 55.0),
    ("Grace", "Mitchell", "60 Rhyme Ln, Burnaby, BC", "604-555-0310", "g.mitchell@email.com", 75, 18.0),
]

# Room: (room_number, room_type, capacity)
ROOMS = [
    ("101", "Event Room", 40), ("102", "Event Room", 30), ("103", "Event Room", 25),
    ("201", "Group Study", 8), ("202", "Group Study", 8), ("203", "Group Study", 6),
    ("204", "Group Study", 10), ("301", "Individual Study", 1), ("302", "Individual Study", 1),
    ("303", "Individual Study", 1), ("304", "Individual Study", 1), ("305", "Individual Study", 1),
]

# Event: (name, type, date_offset_days, time, room_number, age_group, max_capacity, accessibility)
EVENTS = [
    ("Mystery Book Club", "Book Club", 7, "18:00", "101", "Adults", 20, None),
    ("Toddler Storytime", "Storytime", 3, "10:00", "102", "Children", 15, "Wheelchair accessible"),
    ("Resume Writing Workshop", "Workshop", 14, "14:00", "103", "Adults", 25, None),
    ("Local Artists Showcase", "Art Show", 21, "17:00", "101", "All Ages", 30, "Wheelchair accessible"),
    ("Classic Film Night", "Film Screening", 10, "19:00", "102", "Adults", 25, "Sign language interpreter"),
    ("Teen Coding Club", "Workshop", 5, "16:00", "103", "Teens", 20, None),
    ("Community Garden Meetup", "Community Meetup", 12, "11:00", "101", "All Ages", 30, None),
    ("Poetry Reading Evening", "Book Club", 18, "18:30", "102", "Adults", 15, None),
    ("Kids Science Fair", "Workshop", 25, "13:00", "101", "Children", 30, "Wheelchair accessible"),
    ("Senior Tech Help", "Workshop", 2, "10:30", "103", "Seniors", 10, "Wheelchair accessible"),
    ("Author Q&A Session", "Book Club", -5, "17:00", "102", "All Ages", 25, None),
    ("Documentary Screening", "Film Screening", 15, "19:30", "101", "Adults", 20, "Sign language interpreter"),
]

# Registration: (event_number_1-based, [member_numbers_1-based])
REGISTRATIONS = [
    (1, [1, 3, 5, 8]),
    (2, [2, 7, 13]),
    (3, [1, 4, 9, 11, 14]),
    (4, [3, 6, 10, 12, 15]),
    (5, [2, 5, 8]),
    (6, [7, 13]),
    (7, [1, 4, 6, 9]),
    (8, [11, 14, 15]),
    (9, [2, 13]),
    (10, [4, 8, 10]),
    (11, [1, 3, 5, 7, 9, 12]),
    (12, [6, 11]),
]

# HelpRequest: (member_number, employee_number_or_None, topic, description, days_ago, status)
HELP_REQUESTS = [
    (1, 2, "Finding a book", "Looking for books on Canadian history.", 30, "Resolved"),
    (3, 3, "Research help", "Need help finding peer-reviewed sources.", 25, "Resolved"),
    (5, None, "Printer trouble", "The printer on floor 2 is jammed.", 20, "Open"),
    (2, 5, "Library card renewal", "My card expired last week.", 18, "Resolved"),
    (7, 4, "Database access", "Cannot log into the research database.", 15, "Resolved"),
    (9, 2, "Citation help", "How do I cite a website in APA?", 12, "Resolved"),
    (11, None, "Interlibrary loan", "Requesting a book from another branch.", 10, "Open"),
    (4, 7, "Study room booking", "Want to book a group study room.", 8, "Resolved"),
    (13, 8, "eBook download", "Trouble downloading an ebook to my tablet.", 6, "Open"),
    (6, 3, "Reading recommendation", "Looking for a good mystery novel.", 4, "Resolved"),
    (14, None, "Computer help", "Need help using the public computers.", 2, "Open"),
    (10, 2, "Genealogy research", "How do I start researching my family tree?", 1, "Open"),
]

# Loans: (item_number_1-based, member_number, borrowed_days_ago, outcome)
LOANS = [
    (1, 1, 10, "open"),
    (2, 3, 30, "ontime"),
    (3, 5, 40, "late"),
    (4, 2, 8, "open"),
    (5, 7, 50, "overdue"),
    (6, 4, 35, "ontime"),
    (7, 9, 45, "late"),
    (8, 11, 25, "ontime"),
    (9, 6, 60, "late"),
    (10, 13, 55, "overdue"),
    (11, 8, 38, "late"),
    (12, 10, 42, "ontime"),
    (13, 12, 33, "late"),
    (14, 14, 48, "lost"),
    (24, 2, 52, "late"),
    (25, 5, 28, "ontime"),
    (26, 7, 44, "late"),
    (27, 9, 58, "lost"),
    (28, 1, 36, "late"),
    (29, 3, 41, "lost"),
    (30, 15, 47, "overdue"),
    (23, 6, 22, "lost"),
]

def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    for t in ["HelpRequest", "Registration", "Fine", "Borrow", "Event", "Room",
              "Volunteer", "Employee", "Person", "Member", "FutureItem", "Item"]:
        cur.execute(f"DELETE FROM {t}")
    conn.commit()

    cur.executemany(
        """INSERT INTO Item (title,author,publisher,genre,pub_year,format,isbn,location)
           VALUES (?,?,?,?,?,?,?,?)""", ITEMS)
    item_ids = [r[0] for r in cur.execute("SELECT item_id FROM Item ORDER BY item_id")]

    cur.executemany(
        """INSERT INTO FutureItem
           (title,author,publisher,genre,format,acquisition_type,donor_name,expected_arrival,order_status)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        [(t, a, p, g, f, acq, donor, d(TODAY + timedelta(days=off)), st)
         for (t, a, p, g, f, acq, donor, off, st) in FUTURE_ITEMS])

    cur.executemany(
        """INSERT INTO Member (first_name,last_name,address,phone,email,join_date)
           VALUES (?,?,?,?,?,?)""",
        [(f, l, addr, ph, em, d(TODAY - timedelta(days=off)))
         for (f, l, addr, ph, em, off) in MEMBERS])
    member_ids = [r[0] for r in cur.execute("SELECT member_id FROM Member ORDER BY member_id")]

    employee_ids = []
    for (f, l, addr, ph, em, job, sal, off) in EMPLOYEES:
        cur.execute(
            "INSERT INTO Person (first_name,last_name,address,phone,email,role) VALUES (?,?,?,?,?,'Employee')",
            (f, l, addr, ph, em))
        pid = cur.lastrowid
        cur.execute(
            "INSERT INTO Employee (person_id,job_title,salary,hire_date) VALUES (?,?,?,?)",
            (pid, job, sal, d(TODAY - timedelta(days=off))))
        employee_ids.append(cur.lastrowid)

    for (f, l, addr, ph, em, off, hrs) in VOLUNTEERS:
        cur.execute(
            "INSERT INTO Person (first_name,last_name,address,phone,email,role) VALUES (?,?,?,?,?,'Volunteer')",
            (f, l, addr, ph, em))
        pid = cur.lastrowid
        cur.execute(
            "INSERT INTO Volunteer (person_id,start_date,volunteer_hours) VALUES (?,?,?)",
            (pid, d(TODAY - timedelta(days=off)), hrs))

    cur.executemany(
        "INSERT INTO Room (room_number,room_type,capacity) VALUES (?,?,?)", ROOMS)
    room_by_number = {num: rid for (rid, num) in
                      cur.execute("SELECT room_id,room_number FROM Room")}

    for (name, etype, off, tm, room_num, age, cap, access) in EVENTS:
        cur.execute(
            """INSERT INTO Event
               (event_name,event_type,event_date,event_time,room_id,age_group,max_capacity,accessibility)
               VALUES (?,?,?,?,?,?,?,?)""",
            (name, etype, d(TODAY + timedelta(days=off)), tm,
             room_by_number[room_num], age, cap, access))
    event_ids = [r[0] for r in cur.execute("SELECT event_id FROM Event ORDER BY event_id")]

    loans = []
    for (item_no, member_no, days_ago, outcome) in LOANS:
        item_id = item_ids[item_no - 1]
        member_id = member_ids[member_no - 1]
        bdate = TODAY - timedelta(days=days_ago)
        ddate = bdate + timedelta(days=LOAN_PERIOD_DAYS)
        cur.execute(
            "INSERT INTO Borrow (member_id,item_id,borrow_date,due_date) VALUES (?,?,?,?)",
            (member_id, item_id, d(bdate), d(ddate)))
        loans.append((cur.lastrowid, outcome, bdate, ddate, item_id))
    conn.commit()

   
    for (bid, outcome, bdate, ddate, item_id) in loans:
        if outcome == "ontime":
            cur.execute("UPDATE Borrow SET return_date=? WHERE borrow_id=?",
                        (d(ddate - timedelta(days=5)), bid))
        elif outcome == "late":
            cur.execute("UPDATE Borrow SET return_date=? WHERE borrow_id=?",
                        (d(ddate + timedelta(days=9)), bid))   # 9 days late -> $4.50
    conn.commit()

    
    lost_fees = [32.00, 28.50, 45.00, 26.00]
    fee_i = 0
    for (bid, outcome, bdate, ddate, item_id) in loans:
        if outcome == "lost":
            cur.execute("UPDATE Borrow SET status='Lost' WHERE borrow_id=?", (bid,))
            cur.execute("UPDATE Item SET status='Lost' WHERE item_id=?", (item_id,))
            cur.execute("INSERT INTO Fine (borrow_id,amount,reason) VALUES (?,?,?)",
                        (bid, lost_fees[fee_i % len(lost_fees)], "Lost Item"))
            fee_i += 1
    conn.commit()

    for (event_no, member_nos) in REGISTRATIONS:
        eid = event_ids[event_no - 1]
        for m_no in member_nos:
            mid = member_ids[m_no - 1]
            try:
                cur.execute("INSERT INTO Registration (event_id,member_id) VALUES (?,?)", (eid, mid))
            except sqlite3.IntegrityError:
                pass   
    conn.commit()

    for (member_no, emp_no, topic, desc, days_ago, status) in HELP_REQUESTS:
        mid = member_ids[member_no - 1]
        eid = employee_ids[emp_no - 1] if emp_no else None
        cur.execute(
            """INSERT INTO HelpRequest (member_id,employee_id,topic,description,request_date,status)
               VALUES (?,?,?,?,?,?)""",
            (mid, eid, topic, desc, d(TODAY - timedelta(days=days_ago)), status))
    conn.commit()

    print("Seeded row counts:")
    ok = True
    for t in ["Item", "FutureItem", "Member", "Person", "Employee", "Volunteer",
              "Room", "Event", "Borrow", "Fine", "Registration", "HelpRequest"]:
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        flag = ""
        if n < 10:
            flag = "   <-- UNDER 10"
            ok = False
        print(f"  {t:<14} {n}{flag}")

    fines = cur.execute("SELECT COUNT(*), ROUND(SUM(amount),2) FROM Fine").fetchone()
    overdue = cur.execute(
        "SELECT COUNT(*) FROM Borrow WHERE return_date IS NULL AND status='Borrowed' AND due_date < ?",
        (d(TODAY),)).fetchone()[0]
    print(f"\n  Fines: {fines[0]} rows, ${fines[1]} total")
    print(f"  Overdue loans still out: {overdue}")
    print("\n" + ("All tables have >= 10 rows." if ok else "WARNING: some table has < 10 rows."))
    conn.close()


if __name__ == "__main__":
    main()