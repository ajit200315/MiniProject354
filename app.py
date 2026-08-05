import sqlite3
from datetime import date, timedelta

DB = "library.db"
LOAN_PERIOD_DAYS = 21   

def connect():
    """Open the database with foreign keys enforced and dict-like rows."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row        
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def run_write(operation):
    conn = connect()
    try:
        cur = conn.cursor()
        result = operation(cur)
        conn.commit()
        return result
    except sqlite3.IntegrityError as e:
        conn.rollback()
        print(f"\n  Could not complete that: {e}")
        return None
    except sqlite3.Error as e:
        conn.rollback()
        print(f"\n  Database error (nothing was changed): {e}")
        return None
    finally:
        conn.close()


def ask(prompt):
    return input(prompt).strip()


def ask_int(prompt):
    raw = ask(prompt)
    if raw.lstrip("-").isdigit():
        return int(raw)
    print("  Please enter a number.")
    return None


# OPERATION 1 -> FIND AN ITEM
def find_item():
    print("\n--- Find an Item ---")
    term = ask("Search by title or author (leave blank to list all): ")
    conn = connect()
    like = f"%{term}%"
    rows = conn.execute(
        """SELECT item_id, title, author, format, status
           FROM Item
           WHERE title LIKE ? OR author LIKE ?
           ORDER BY title""",
        (like, like)).fetchall()
    conn.close()

    if not rows:
        print("  No items matched your search.")
        return
    print(f"\n  Found {len(rows)} item(s):")
    for r in rows:
        print(f"    #{r['item_id']:<4} {r['title']}  by {r['author'] or 'Unknown'}"
              f"  [{r['format']}]  -- {r['status']}")

# OPERATION 2 -> BORROW AN ITEM
def borrow_item():
    print("\n--- Borrow an Item ---")
    member_id = ask_int("Your member ID: ")
    if member_id is None:
        return
    item_id = ask_int("Item ID to borrow: ")
    if item_id is None:
        return

    def op(cur):
        if cur.execute("SELECT 1 FROM Member WHERE member_id=?", (member_id,)).fetchone() is None:
            print(f"\n  No member with ID {member_id}.")
            raise sqlite3.IntegrityError("member not found")

        item = cur.execute("SELECT title, status FROM Item WHERE item_id=?", (item_id,)).fetchone()
        if item is None:
            print(f"\n  No item with ID {item_id}.")
            raise sqlite3.IntegrityError("item not found")
        if item["status"] != "Available":
            print(f"\n  '{item['title']}' is currently {item['status']} and cannot be borrowed.")
            raise sqlite3.IntegrityError("item not available")

        borrow_date = date.today()
        due_date = borrow_date + timedelta(days=LOAN_PERIOD_DAYS)
        cur.execute(
            "INSERT INTO Borrow (member_id, item_id, borrow_date, due_date) VALUES (?,?,?,?)",
            (member_id, item_id, borrow_date.isoformat(), due_date.isoformat()))
        print(f"\n  Borrowed '{item['title']}'. Due back on {due_date.isoformat()}.")
        return True

    run_write(op)



# OPERATION 3 -> RETURN AN ITEM
def return_item():
    print("\n--- Return an Item ---")
    borrow_id = ask_int("Borrow ID to return: ")
    if borrow_id is None:
        return

    def op(cur):
        loan = cur.execute(
            """SELECT b.borrow_id, b.due_date, b.return_date, i.title
               FROM Borrow b JOIN Item i ON i.item_id = b.item_id
               WHERE b.borrow_id = ?""", (borrow_id,)).fetchone()
        if loan is None:
            print(f"\n  No borrow record with ID {borrow_id}.")
            raise sqlite3.IntegrityError("borrow not found")
        if loan["return_date"] is not None:
            print(f"\n  '{loan['title']}' was already returned on {loan['return_date']}.")
            raise sqlite3.IntegrityError("already returned")

        today = date.today().isoformat()
        cur.execute("UPDATE Borrow SET return_date=? WHERE borrow_id=?", (today, borrow_id))
        fine = cur.execute(
            "SELECT amount FROM Fine WHERE borrow_id=? AND reason='Late Return'",
            (borrow_id,)).fetchone()
        if fine:
            print(f"\n  Returned '{loan['title']}'. It was late -- a fine of "
                  f"${fine['amount']:.2f} has been added to the account.")
        else:
            print(f"\n  Returned '{loan['title']}'. No fine -- thanks for returning on time!")
        return True

    run_write(op)

# OPERATION 4 -> DONATE AN ITEM
def donate_item():
    print("\n--- Donate an Item ---")
    title = ask("Title of the item you are donating: ")
    if not title:
        print("  A title is required.")
        return
    author = ask("Author (optional): ") or None
    publisher = ask("Publisher (optional): ") or None
    genre = ask("Genre (optional): ") or None
    fmt = ask("Format [Print/Online/Magazine/Journal/Record]: ") or "Print"
    donor = ask("Your name (the donor): ") or None

    def op(cur):
        cur.execute(
            """INSERT INTO FutureItem
               (title, author, publisher, genre, format, acquisition_type, donor_name, order_status)
               VALUES (?,?,?,?,?, 'Donation', ?, 'Pending')""",
            (title, author, publisher, genre, fmt, donor))
        print(f"\n  Thank you! '{title}' has been logged as a donation "
              f"(pending librarian review).")
        return True

    run_write(op)

# OPERATION 5 -> FIND AN EVENT
def find_event():
    print("\nFind an Event")
    term = ask("Search by event name or type (leave blank to list all): ")
    conn = connect()
    like = f"%{term}%"
    rows = conn.execute(
        """SELECT e.event_id, e.event_name, e.event_type, e.event_date, e.event_time,
                  r.room_number, e.max_capacity,
                  (SELECT COUNT(*) FROM Registration rg WHERE rg.event_id = e.event_id) AS registered
           FROM Event e JOIN Room r ON r.room_id = e.room_id
           WHERE e.event_name LIKE ? OR e.event_type LIKE ?
           ORDER BY e.event_date""",
        (like, like)).fetchall()
    conn.close()

    if not rows:
        print("  No events matched your search.")
        return
    print(f"\n  Found {len(rows)} event(s):")
    for r in rows:
        seats_left = r["max_capacity"] - r["registered"]
        print(f"    #{r['event_id']:<4} {r['event_name']}  ({r['event_type']})"
              f"  {r['event_date']} {r['event_time']}  Room {r['room_number']}"
              f"  -- {seats_left} of {r['max_capacity']} seats left")


# OPERATION 6 -> REGISTER FOR AN EVENT
def register_event():
    print("\nRegister for an Event")
    member_id = ask_int("Your member ID: ")
    if member_id is None:
        return
    event_id = ask_int("Event ID to register for: ")
    if event_id is None:
        return

    def op(cur):
        if cur.execute("SELECT 1 FROM Member WHERE member_id=?", (member_id,)).fetchone() is None:
            print(f"\n  No member with ID {member_id}.")
            raise sqlite3.IntegrityError("member not found")
        ev = cur.execute("SELECT event_name FROM Event WHERE event_id=?", (event_id,)).fetchone()
        if ev is None:
            print(f"\n  No event with ID {event_id}.")
            raise sqlite3.IntegrityError("event not found")

        already = cur.execute(
            "SELECT 1 FROM Registration WHERE event_id=? AND member_id=?",
            (event_id, member_id)).fetchone()
        if already:
            print(f"\n  You are already registered for '{ev['event_name']}'.")
            raise sqlite3.IntegrityError("duplicate registration")
        cur.execute(
            "INSERT INTO Registration (event_id, member_id) VALUES (?,?)",
            (event_id, member_id))
        print(f"\n  You are registered for '{ev['event_name']}'. See you there!")
        return True

    run_write(op)

# OPERATION 7 -> VOLUNTEER FOR THE LIBRARY
def volunteer():
    print("\nVolunteer for the Library")
    first = ask("First name: ")
    last = ask("Last name: ")
    if not first or not last:
        print("  First and last name are required.")
        return
    email = ask("Email: ")
    if not email:
        print("  An email is required.")
        return
    address = ask("Address (optional): ") or None
    phone = ask("Phone (optional): ") or None

    def op(cur):
        if cur.execute("SELECT 1 FROM Person WHERE email=?", (email,)).fetchone():
            print(f"\n Someone is already registered with the email {email}.")
            raise sqlite3.IntegrityError("duplicate email")
        cur.execute(
            """INSERT INTO Person (first_name, last_name, address, phone, email, role)
               VALUES (?,?,?,?,?, 'Volunteer')""",
            (first, last, address, phone, email))
        person_id = cur.lastrowid
        cur.execute(
            "INSERT INTO Volunteer (person_id, start_date) VALUES (?,?)",
            (person_id, date.today().isoformat()))
        print(f"\n  Thank you for volunteering, {first}! You are signed up "
              f"as of {date.today().isoformat()}.")
        return True

    run_write(op)

# OPERATION 8 -> ASK FOR HELP FROM A LIBRARIAN
def ask_help():
    print("\nAsk for Help from a Librarian ")
    member_id = ask_int("Your member ID: ")
    if member_id is None:
        return
    topic = ask("What do you need help with (short topic)? ")
    if not topic:
        print("  A topic is required.")
        return
    description = ask("Any details (optional)? ") or None

    def op(cur):
        if cur.execute("SELECT 1 FROM Member WHERE member_id=?", (member_id,)).fetchone() is None:
            print(f"\n  No member with ID {member_id}.")
            raise sqlite3.IntegrityError("member not found")
        emp = cur.execute(
            "SELECT employee_id FROM Employee WHERE job_title LIKE '%Librarian%' LIMIT 1").fetchone()
        employee_id = emp["employee_id"] if emp else None

        cur.execute(
            """INSERT INTO HelpRequest (member_id, employee_id, topic, description)
               VALUES (?,?,?,?)""",
            (member_id, employee_id, topic, description))
        who = "a librarian" if employee_id else "the next available staff member"
        print(f"\n  Your request has been logged and will be handled by {who}.")
        return True

    run_write(op)


MENU = """
MAIN MENU 
  1. Find an item
  2. Borrow an item
  3. Return an item
  4. Donate an item
  5. Find an event
  6. Register for an event
  7. Volunteer for the library
  8. Ask for help from a librarian
  0. Quit
"""

ACTIONS = {
    "1": find_item,
    "2": borrow_item,
    "3": return_item,
    "4": donate_item,
    "5": find_event,
    "6": register_event,
    "7": volunteer,
    "8": ask_help,
}


def main():
    print("Welcome to the Community Library system.")
    while True:
        print(MENU)
        choice = ask("Choose an option (0-8): ")
        if choice == "0":
            print("\nHave a nice day!")
            break
        action = ACTIONS.get(choice)
        if action:
            action()
        else:
            print("  Invalid choice. Please pick a number from 0 to 8.")
        input("\n(press Enter to continue)")


if __name__ == "__main__":
    main()