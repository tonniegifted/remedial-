from tkinter import*
from tkinter import ttk
from tkinter import messagebox
from CTkMessagebox import CTkMessagebox
import mysql.connector
from openpyxl import Workbook
from openpyxl.styles import Font
from decimal import Decimal
import customtkinter as ctk
from datetime import date
import ttkbootstrap as tb
#connecting to mysql
#connecting to database
my_db=mysql.connector.connect(host="localhost",
                              user="root",
                              password="print()",
                              database="remedial")

# creating cursor
cur=my_db.cursor()
#creating connection for sqlite3    "C:/Users/Administrator/Documents"
#"C:/Users/Administrator/Documents/Remedial App/Remedial App.db"

path="C:/Users/Administrator/Documents/Remedial App/Remedial App.db"
# my_db = sqlite3.connect(path)
#creating cursor
cur=my_db.cursor()
root= ctk.CTk()
# ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
width=root.winfo_width()
height=root.winfo_height()
root.title("Remedial App")
path="C:/Users/Administrator/Documents/Remedial App/Resources/remedial convert.ico"
root.iconbitmap(path)
# root.geometry(f"{width}x{height}+0+0")
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
# Set the window size
window_width = 680
window_height = 600
# Calculate position to center horizontally and start at the top
position_x = (screen_width - window_width) // 2
position_y = 10  # Start at the top
root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
root.resizable(width=False, height=False)
#color blue
blue="#4582EC"



#FUNCTIONS 
def undo_promotion():
    try:
        resp=messagebox.askyesno("Remedial App","Do you want to undo Learner Move?")
        if resp:
            # Step 1: Revert learners from Grade 9 back to Grade 8
            cur.execute("""
                UPDATE learner
                SET grade = 'Eight'
                WHERE grade = 'Nine'
            """)

            # Step 2: Revert learners from Grade 8 back to Grade 7
            cur.execute("""
                UPDATE learner
                SET grade = 'Seven'
                WHERE grade = 'Eight'
            """)

            # Commit the rollback
            my_db.commit()
            messagebox.showinfo("Undo Promotion", "Learner promotion has been successfully undone.")
            display_learners()
        else:
            pass

    except Exception as e:
        my_db.rollback()  # Rollback changes in case of an error
        messagebox.showerror("Error", f"An error occurred: {e}")

def promote_learners_func():
    try:
        resp=messagebox.askyesno("Remedial App","Are you sure you want to\nmove learners to next grades?")
        if resp:
        # Step 1: Update learners from Grade 7 to Grade 8
            cur.execute("""
                UPDATE learner
                SET grade = 'Eight'
                WHERE grade = 'Seven'
            """)

            # Step 2: Update learners from Grade 8 to Grade 9
            cur.execute("""
                UPDATE learner
                SET grade = 'Nine'
                WHERE grade = 'Eight'
            """)

            # Commit the changes
            my_db.commit()
            messagebox.showinfo("Move", "Learners have been successfull\nmoved to the next grade.")
            display_learners()
        else:
            pass
    except Exception as e:
        my_db.rollback()  # Rollback changes in case of an error
        messagebox.showerror("Error", f"An error occurred:\n{e}")


#search function
def binding(e):
    learner_menu.tk_popup(e.x,e.y)

    #deleting learners
def delete_transaction():
    try:
        adm = []  # List to hold learner_ids for deletion
        tuples = []  # List to hold parameters for database query
        pos = learner_tree.selection()  # Get selected rows in learner_tree

        if not pos:
            messagebox.showwarning("Remedial App", "Select records before attempting to delete")
        else:
            root.bell()
            resp = messagebox.askyesno("Remedial App", "Are sure you want to delete\nSelected PAYMENT record(s)\nPermanently?")
            
            if resp == 1:  # Proceed if user confirms
                for items in pos:
                    values = learner_tree.item(items, "values")
                    adm.append(values[1])  # Extract learner_id from the tree view
                    learner_tree.delete(items)  # Delete the item from the learner_tree

                # Prepare the tuples for the SQL query
                for a in adm:
                    tuples.append((a,))

                # Step 1: Fetch the most recent transaction_id for each learner
                for learner_id in adm:
                    cur.execute("""
                        SELECT t.transaction_id
                        FROM transactions t
                        JOIN transaction_history th ON t.transaction_id = th.transaction_id
                        WHERE t.learner_id = %s
                        AND t.term_id = (SELECT term_id FROM term WHERE is_active = 1)
                        ORDER BY th.trans_time DESC
                        LIMIT 1
                    """, (learner_id,))  # Pass each learner_id one by one

                    # Step 2: Fetch the transaction_id to delete
                    transaction_id_to_delete = cur.fetchone()

                    # Step 3: If transaction_id exists, delete it
                    if transaction_id_to_delete:
                        cur.execute("""
                            DELETE FROM transactions
                            WHERE transaction_id = %s
                        """, (transaction_id_to_delete[0],))

                        my_db.commit()  # Commit the changes

            else:
                pass  # If user cancels, do nothing
    except Exception as e:
        messagebox.showerror("Remedial App"f"{e}")

#deleting learners
def delete_learner():
        adm=[]
        tuples=[]
        pos=learner_tree.selection()
        if not pos:
            messagebox.showwarning("Remedial App","Select records before attempting to delete")
        else:
            root.bell()
            resp=messagebox.askyesno("Remedial App","Are sure you want to delete\n LEARNER(S) permanently?")
            if resp==1:
                for items in pos:
                    values=learner_tree.item(items,"values") 
                    adm.append(values[1])
                    #deleting from learner_tree
                    learner_tree.delete(items)
                for a in adm:
                    tuples.append((a,))
                cur.executemany("DELETE FROM learner WHERE learner_id=%s",tuples)
                my_db.commit()
            else:
                pass

# Treeview to display results
def search_func(e=None):
    search_term = learner_search_entry.get().strip().lower()  # Get and normalize the search term
    search_by = search_by_combo.get()  # Get the search criteria (Adm No or Name)
    selected_grade = disp_bal_combo.get().strip().lower()  # Get and normalize the selected grade

    # Check if search criteria is not selected
    if search_by == "Search By":
        messagebox.showinfo("Select Criteria", "Please select a search criteria to proceed.")
        return

    try:
        # Clear the treeview before inserting new results
        learner_tree.delete(*learner_tree.get_children())

        if search_by == "Adm No":
            # Convert search_term to integer for Adm No search
            try:
                search_term = int(search_term)
            except ValueError:
                messagebox.showwarning("Input Error", "Admission Number must be a number.")
                return

            # Search by Admission Number (with or without grade filter)
            if selected_grade == "display all learners":
                query = """
                SELECT 
                    l.learner_id,
                    l.grade,
                    l.first,
                    l.second,
                    l.surname,
                    IFNULL(SUM(t.amount_paid), 0) AS amount_paid,
                    (SELECT lnr_pay FROM termly_pay WHERE term_id=(SELECT term_id FROM term WHERE is_active=1)) - IFNULL(SUM(t.amount_paid), 0) AS balance
                FROM learner l
                LEFT JOIN transactions t 
                    ON l.learner_id = t.learner_id 
                    AND t.term_id = (SELECT term_id FROM term WHERE is_active = 1)
                WHERE l.learner_id = %s
                GROUP BY l.learner_id
                """
                cur.execute(query, (search_term,))
            else:
                query = """
                SELECT 
                    l.learner_id,
                    l.grade,
                    l.first,
                    l.second,
                    l.surname,
                    IFNULL(SUM(t.amount_paid), 0) AS amount_paid,
                    (SELECT lnr_pay FROM termly_pay WHERE term_id=(SELECT term_id FROM term WHERE is_active=1)) - IFNULL(SUM(t.amount_paid), 0) AS balance
                FROM learner l
                LEFT JOIN transactions t 
                    ON l.learner_id = t.learner_id 
                    AND t.term_id = (SELECT term_id FROM term WHERE is_active = 1)
                WHERE l.learner_id = %s AND LOWER(l.grade) = %s
                GROUP BY l.learner_id
                """
                cur.execute(query, (search_term, selected_grade))
        else:
            # Search by Name (with or without grade filter)
            if selected_grade == "display all learners":
                query = """
                SELECT 
                    l.learner_id,
                    l.grade,
                    l.first,
                    l.second,
                    l.surname,
                    IFNULL(SUM(t.amount_paid), 0) AS amount_paid,
                    (SELECT lnr_pay FROM termly_pay WHERE term_id=(SELECT term_id FROM term WHERE is_active=1)) - IFNULL(SUM(t.amount_paid), 0) AS balance
                FROM learner l
                LEFT JOIN transactions t 
                    ON l.learner_id = t.learner_id 
                    AND t.term_id = (SELECT term_id FROM term WHERE is_active = 1)
                WHERE LOWER(l.first) LIKE %s OR LOWER(l.second) LIKE %s OR LOWER(l.surname) LIKE %s
                GROUP BY l.learner_id
                """
                search_pattern = f"%{search_term}%"  # Wildcarded search term
                cur.execute(query, (search_pattern, search_pattern, search_pattern))
            else:
                query = """
                SELECT 
                    l.learner_id,
                    l.grade,
                    l.first,
                    l.second,
                    l.surname,
                    IFNULL(SUM(t.amount_paid), 0) AS amount_paid,
                    (SELECT lnr_pay FROM termly_pay WHERE term_id=(SELECT term_id FROM term WHERE is_active=1)) - IFNULL(SUM(t.amount_paid), 0) AS balance
                FROM learner l
                LEFT JOIN transactions t 
                    ON l.learner_id = t.learner_id 
                    AND t.term_id = (SELECT term_id FROM term WHERE is_active = 1)
                WHERE (LOWER(l.first) LIKE %s OR LOWER(l.second) LIKE %s OR LOWER(l.surname) LIKE %s) AND LOWER(l.grade) = %s
                GROUP BY l.learner_id
                """
                search_pattern = f"%{search_term}%"  # Wildcarded search term
                cur.execute(query, (search_pattern, search_pattern, search_pattern, selected_grade))

        results = cur.fetchall()  # Get all results

        if results:
            # Use enumerate with start=1 to display learner numbers
            for index, row in enumerate(results, start=1):
                learner_tree.insert(
                    "",
                    "end",
                    values=(
                        index,  # Learner number
                        row[0],  # Learner ID
                        row[1],  # Grade
                        f"{row[2].title()} {row[3].title()} {row[4].title()}",  # Full Name
                        row[5],  # Amount Paid
                        row[6]   # Balance
                    )
                )
        else:
            # messagebox.showinfo("Search Results", "Not found")
            display_learners()
            search_label.configure(text="Not found")
            search_label.after(4000,lambda:search_label.configure(text=""))

    except Exception as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")
def make_payment(e=None):
    try:
        #select learner id from the learner treeview
        pos=learner_tree.selection()
        adm=learner_tree.item(pos,"values")
        learner_id=adm[1]
        # display_learner()
        amount_paid = amount_entry.get()
        amount_paid = float(amount_paid)


        # Retrieve the current term's number
        cur.execute("SELECT term_number FROM term WHERE is_active = 1")
        term_no = cur.fetchone()
        if term_no:
            current_term_number = term_no[0]
        else:
            messagebox.showwarning("Remedial App", "No active term found. Please check term setup.")
            return
        
        # If the current term is term one, skip previous term balance checks
        if current_term_number == 1:
            prev_term_id = None  # No previous term exists for term one
        else:
            # Retrieve the previous term ID
            cur.execute("SELECT term_id FROM term WHERE term_number = %s", (current_term_number - 1,))
            prev_id = cur.fetchone()
            prev_term_id = prev_id[0] if prev_id else None
            
            if not prev_term_id:
                messagebox.showwarning("Remedial App", "Could not find previous term details. Please verify terms.")
                return
            
            # Check if the learner has any balance for the previous term
            cur.execute("""SELECT amount_paid, balance FROM transactions 
                            WHERE learner_id = %s AND term_id = %s""", (learner_id, prev_term_id))
            balance = cur.fetchone()
            
            if balance:
                prev_amount_paid = balance[0]  # Amount already paid for the previous term
                prev_balance = balance[1]     # Remaining balance for the previous term
            else:
                prev_amount_paid = 0
                prev_balance = 0  # No record means no payments made
            
            # If the learner has not fully cleared the previous term's balance, block payment
            if prev_balance > 0 or prev_amount_paid == 0:
                cur.execute("SELECT first, second, surname FROM learner WHERE learner_id = %s", (learner_id,))
                name = cur.fetchone()
                fullname = f"\n{name[0].title()} {name[1].title()} {name[2].title()}"
                messagebox.showwarning(
                    "Remedial App", 
                    f"{fullname} has not cleared\ntheir previous term fees."
                    f"Amount paid so\nfar is: KSH {prev_amount_paid:.2f}.")
                return
        
        # Retrieve termly pay for the learner's grade
        cur.execute("SELECT grade FROM learner WHERE learner_id = %s", (learner_id,))
        grade_data = cur.fetchone()
        if not grade_data:
            messagebox.showwarning("Remedial App", "Learner grade not found. Please verify learner details.")
            return    
        cur.execute("""SELECT lnr_pay FROM termly_pay WHERE 
                        term_id = (SELECT term_id FROM term WHERE is_active = 1)""")
        amt = cur.fetchone()
        tot = float(amt[0]) if amt else 0
        
        if tot < 1:
            cur.execute("SELECT selected_term FROM term WHERE is_active = 1")
            is_active = cur.fetchone()[0]
            messagebox.showwarning("Remedial App", f"Set Fee payable for {is_active}")
            return
        
        # Check for existing transaction records for the current term
        cur.execute("""SELECT amount_paid, balance FROM transactions
                        WHERE learner_id = %s AND term_id = (SELECT term_id FROM term WHERE is_active = 1)""", (learner_id,))
        record = cur.fetchone()
        
        if record:
            new_amount = float(record[0]) + amount_paid
            new_balance = float(record[1]) - amount_paid
        else:
            new_amount = amount_paid
            new_balance = tot - amount_paid
        
        # Ensure the amount paid doesn't exceed the termly fee
        if new_amount > tot:
            messagebox.showwarning("Remedial App", "Amount Paid cannot exceed termly\npayable amount")
            return
        
        # Retrieve the current term ID
        cur.execute("SELECT term_id FROM term WHERE is_active = 1")
        active = cur.fetchone()[0]
        
        # Insert or update the transaction
        cur.execute("""INSERT INTO transactions(amount_paid, learner_id, term_id, balance)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        amount_paid = VALUES(amount_paid),
                        balance = VALUES(balance)""", (new_amount, learner_id, active, new_balance))
        my_db.commit()
        
        # Record transaction history
        comment = (From_entry.get()).title()
        if len(comment)>25:
            raise ValueError("Comment exceeds 25 characters")
        cur.execute("SELECT transaction_id FROM transactions ORDER BY transaction_id DESC LIMIT 1")
        item = cur.fetchone()
        transaction_id = item[0] if item else None
        
        cur.execute("""INSERT INTO transaction_history(learner_id, amount, balance, term_id, comment, transaction_id)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (learner_id, new_amount, new_balance, active, comment, transaction_id))
        my_db.commit()
        
        # Clean up old records if the balance is cleared
        cur.execute("""DELETE FROM transaction_history WHERE learner_id = (
                        SELECT learner_id FROM transactions WHERE balance = 0 AND learner_id = %s 
                        AND term_id = (SELECT term_id FROM term WHERE is_active = 1))""", (learner_id,))
        my_db.commit()
        
        # Clear input and notify success
        amount_entry.delete(0, END)
        disp_label.configure(text="Payment saved successfully")
        disp_label.after(4000, lambda: disp_label.configure(text=""))
        display_learners()
    except Exception as ex:
        messagebox.showerror("Remedial App", f"An error occurred: {ex}")


def disable_combo(e):
    global tr_title_combo,reg_grade_combo,person_type_combo
    if person_type_combo.get()=="Learner":
        tr_title_combo.configure(state=DISABLED)
        reg_grade_combo.configure(state=NORMAL)
    else:
        if person_type_combo.get()=="Teacher":
            tr_title_combo.configure(state=NORMAL)
            reg_grade_combo.configure(state=DISABLED)
    
#display learners
def display_teachers():
    global teacher_tree
    #retrieving learners from database
    cur.execute("""SELECT teacher_id,title,first,second,surname FROM teacher""")
    teacher=cur.fetchall()
    if teacher:
        for index,teacher in enumerate (teacher,start=1):
            teacher_tree.insert("",END,values=(index,teacher[0],f"{teacher[1].title() } {teacher[2].title()} {teacher[3].title()} {teacher[4].title()}"))
    else:
        messagebox.showinfo("Remedial App","No records for teachers")     
def display_learners(e=None):
    try:
        selected_option = disp_bal_combo.get()

        # Determine if displaying all learners or learners from a specific grade
        if selected_option == "Display all Learners":
            # Query to retrieve all learners and their balances
            cur.execute("""
            SELECT 
                learner.learner_id, 
                learner.grade, 
                learner.first, 
                learner.second, 
                learner.surname, 
                IFNULL(SUM(transactions.amount_paid), 0) AS amount_paid, 
                (SELECT lnr_pay FROM termly_pay WHERE term_id=(SELECT term_id FROM term WHERE is_active=1)) - IFNULL(SUM(transactions.amount_paid), 0) AS balance
            FROM learner
            LEFT JOIN transactions 
                ON learner.learner_id = transactions.learner_id 
                AND transactions.term_id = (SELECT term_id FROM term WHERE is_active = 1)
            GROUP BY learner.learner_id
            """)
        else:
            # Query to retrieve learners from a specific grade and their balances
            cur.execute("""
            SELECT 
                l.learner_id,
                l.grade,
                l.first,
                l.second,
                l.surname,
                IFNULL(SUM(t.amount_paid), 0) AS amount_paid,
                (SELECT lnr_pay FROM termly_pay WHERE term_id=(SELECT term_id FROM term WHERE is_active=1)) - IFNULL(SUM(t.amount_paid), 0) AS balance
            FROM learner l
            LEFT JOIN transactions t 
                ON l.learner_id = t.learner_id 
                AND t.term_id = (SELECT term_id FROM term WHERE is_active = 1)
            WHERE l.grade = %s
            GROUP BY l.learner_id
            """, (selected_option,))

        learners = cur.fetchall()

        # Clear the treeview before inserting new data
        learner_tree.delete(*learner_tree.get_children())

        if learners:
            for index, learner in enumerate(learners, start=1):
                learner_tree.insert(
                    "",
                    "end",
                    values=(
                        index,
                        learner[0],  # Learner ID
                        learner[1],  # Grade
                        f"{learner[2].title()} {learner[3].title()} {learner[4].title()}",  # Full Name
                        learner[5],  # Amount Paid
                        learner[6]   # Balance
                    )
                )
        else:
            if selected_option == "Display all Learners":
                messagebox.showinfo("Remedial App", "No records found for any learners.")
            else:
                messagebox.showinfo("Remedial App", f"No records found for grade {selected_option}.")

    except Exception as e:
        messagebox.showerror("Remedial App", f"An error occurred: {e}")
                 
#clear person_win boxes
def clear_person_win():
    global number_entry,first_entry,second_entry,surname_entry
    number_entry.delete(0,END)
    first_entry.delete(0,END)
    second_entry.delete(0,END)
    surname_entry.delete(0,END)
#clearing fields in term win
def clear_term_win():
    global term_combo,set_term_label,lnr_amount_entry,tr_weekend_entry,tr_week_entry
    lnr_amount_entry.delete(0,END)
    tr_weekend_entry.delete(0,END)
    tr_week_entry.delete(0,END)

def clear_learner_tree():
    learner_tree.delete(*learner_tree.get_children())
#deleting function(learner,teacher)
def delete_person(person):  
    try:
        global person_type_combo,number_entry,reg_grade_combo,tr_title_combo,first_entry,second_entry,surname_entry,reg_person_label 
        id_number=number_entry.get()
        id_number=int(id_number)
        person=person_type_combo.get()
        if not person:
            root.bell()
            # messagebox.showwarning("Register Persons","Select person type to proceed")
            CTkMessagebox(title="Register Persons",message="Select person type to proceed",icon="warning")
            return
        #deleting learner
        if person=="Learner":
            #access learner before asking to delete
            cur.execute("""SELECT first,second,surname FROM learner WHERE learner_id=%s
                        """,(id_number,))
            lnr=cur.fetchone()
            if lnr:
                learner=f"{lnr[0]} {lnr[1]} {lnr[2]} "
            else:
                reg_person_label.configure(text=f"Learner ID {id_number} not found")
                reg_person_label.after(4000,lambda:reg_person_label.configure(text=""))
                return
            if learner:
                root.bell()
                resp=messagebox.askyesno("Register Persons",f"Are you sure you want to delete\n{learner}?")
                if resp:
                    cur.execute("DELETE FROM learner WHERE learner_id=%s",(id_number,))
                    my_db.commit()
                    clear_learner_tree()
                    display_learners()
                    reg_person_label.configure(text="Learner details deleted successfully")
                    reg_person_label.after(4000,lambda:reg_person_label.configure(text=""))
        else:
            person=="Teacher"
            #access learner before asking to delete
            cur.execute("""SELECT title,first,second,surname FROM teacher WHERE teacher_id=%s
                        """,(id_number,))
            tr=cur.fetchone()
            if tr:
                teacher=f"{tr[0]} {tr[1]} {tr[2]} {tr[3]} "
            else:
                reg_person_label.configure(text=f"Teacher ID {id_number} not found")
                reg_person_label.after(4000,lambda:reg_person_label.configure(text=""))
                return
            if teacher:
                root.bell()
                resp=messagebox.askyesno("Register Persons",f"Are you sure you want to delete\n{teacher}?")
                if resp:
                    cur.execute("DELETE FROM teacher WHERE teacher_id=%s",(id_number,))
                    my_db.commit()
                    reg_person_label.configure(text="Teacher details deleted successfully")
                    reg_person_label.after(4000,lambda:reg_person_label.configure(text=""))
    except Exception as ex:
        # messagebox.showerror("Register Persons",f"{ex}")
        CTkMessagebox(title="Register Persons",message=f"{ex}",icon="error")
# 
def add_person(person):
    try:
        global person_type_combo, number_entry, reg_grade_combo, tr_title_combo, first_entry, second_entry, surname_entry, reg_person_label
        person = person_type_combo.get()
        id_number = number_entry.get()

        # Ensure ID is an integer
        try:
            id_number = int(id_number)
        except ValueError:
            CTkMessagebox(title="Register Persons", message="ID number must be an integer.", icon="warning")
            return

        grade = reg_grade_combo.get()
        title = tr_title_combo.get()
        first = first_entry.get().strip().title()
        second = second_entry.get().strip().title()
        surname = surname_entry.get().strip().title()

        if not person:
            root.bell()
            CTkMessagebox(title="Register Persons", message="Select Person type to proceed", icon="warning")
            return

        if person == "Learner":
            if all([id_number, grade, first, second]):
                # Checking whether learner ID exists
                cur.execute("SELECT learner_id FROM learner WHERE learner_id=%s", (id_number,))
                learner_id = cur.fetchone()
                learner_id = learner_id[0] if learner_id else None

                # Inserting learner if ID does not exist
                if not learner_id:
                    cur.execute(
                        "INSERT INTO learner (learner_id, first, second, surname, grade) VALUES (%s, %s, %s, %s, %s)",
                        (id_number, first, second, surname, grade),
                    )
                    my_db.commit()
                    reg_person_label.configure(text="Learner details saved successfully")
                    reg_person_label.after(4000, lambda: reg_person_label.configure(text=""))
                    clear_person_win()
                    clear_learner_tree()
                    display_learners()
                # Updating learner details if ID exists
                else:
                    root.bell()
                    resp = messagebox.askyesno(
                        "Register Persons", f"Learner ID {id_number} exists. Do you want to overwrite?"
                    )
                    if resp:
                        cur.execute(
                            "UPDATE learner SET first=%s, second=%s, surname=%s, grade=%s WHERE learner_id=%s",
                            (first, second, surname, grade, id_number),
                        )
                        my_db.commit()
                        reg_person_label.configure(text="Learner details updated successfully")
                        clear_learner_tree()
                        display_learners()
                        clear_person_win()
                        reg_person_label.after(4000, lambda: reg_person_label.configure(text=""))
            else:
                root.bell()
                messagebox.showwarning(
                    "Register Persons", "Ensure that you have filled all the necessary fields for person type: Learner"
                )

        elif person == "Teacher":
            if all([id_number, title, first, second]):
                # Checking whether teacher ID exists
                cur.execute("SELECT teacher_id FROM teacher WHERE teacher_id=%s", (id_number,))
                teacher_id = cur.fetchone()
                teacher_id = teacher_id[0] if teacher_id else None

                # Inserting teacher record if ID does not exist
                if not teacher_id:
                    cur.execute(
                        "INSERT INTO teacher (teacher_id, title, first, second, surname) VALUES (%s, %s, %s, %s, %s)",
                        (id_number, title, first, second, surname),
                    )
                    my_db.commit()
                    reg_person_label.configure(text="Teacher details saved successfully")
                    reg_person_label.after(4000, lambda: reg_person_label.configure(text=""))
                    clear_person_win()
                else:
                    root.bell()
                    resp = messagebox.askyesno(
                        "Register Persons", f"Teacher ID {id_number} exists. Do you want to overwrite?"
                    )
                    if resp:
                        cur.execute(
                            "UPDATE teacher SET title=%s, first=%s, second=%s, surname=%s WHERE teacher_id=%s",
                            (title, first, second, surname, id_number),
                        )
                        my_db.commit()
                        reg_person_label.configure(text="Teacher details updated successfully")
                        clear_person_win()
                        reg_person_label.after(4000, lambda: reg_person_label.configure(text=""))
            else:
                root.bell()
                messagebox.showwarning(
                    "Register Persons", "Ensure that you have filled all the necessary fields for person type: Teacher"
                )
        else:
            CTkMessagebox(title="Register Persons", message="Invalid person type selected.", icon="warning")
    except Exception as ex:
        CTkMessagebox(title="Register Persons", message=f"An error occurred: {ex}", icon="warning")
        
#accessing grades
def grades_list():
    grades=["Display all Learners","Seven","Eight","Nine"]
    return grades
    
#terms function
def term_list():
    terms=["Term One,2025",
        "Term Two, 2025",
        "Term Three, 2025",
        "Term One,2026",
        "Term Two, 2026",
        "Term Three, 2026",
        "Term One, 2027",
        "Term Two, 2027",
        "Term Three, 2027",
        "Term One, 2028",
        "Term Two, 2028",
        "Term Three, 2028",
        "Term One, 2029",
        "Term Two, 2029",
        "Term Three, 2029",
        "Term One, 2030",
        "Term Two, 2030",
        "Term Three,2030"]
    return terms

# def disp_pay_hist():
#     global pay_hist_tree
#     # Clearing the tree
#     pay_hist_tree.delete(*pay_hist_tree.get_children())

#     # Retrieving from the database using a join
#     cur.execute("""SELECT l.learner_id, l.grade, l.first, l.second, l.surname,
#                 th.amount, th.balance, th.trans_time, th.comment
#                 FROM learner l JOIN transaction_history th ON 
#                 l.learner_id = th.learner_id WHERE term_id = (
#                 SELECT term_id FROM term WHERE is_active = 1)""")
#     hist = cur.fetchall()

#     if hist:
#         for index, hist in enumerate(hist, start=1):
#             learner_id = hist[0]
#             learner_grade = hist[1]
#             learner_name = f"{hist[2]} {hist[3]} {hist[4]}".title()
#             amount_paid = hist[5]
#             balance = hist[6]

#             # Extracting the date part only and formatting it as DD-MM-YY
#             date = hist[7]  # 'trans_time' field
#             # if date and len(date) >= 10:  # Ensure it's valid and has at least the date part
#             #     formatted_date = f"{date[8:10]}-{date[5:7]}-{date[2:4]}"
            
            
#             formatted_date=date.strftime("%d/%m/%Y")

#             comment = hist[8]

#             # Inserting into the Treeview
#             pay_hist_tree.insert(
#                 "",
#                 END,
#                 values=(
#                     index, 
#                     learner_id, 
#                     learner_grade, 
#                     learner_name, 
#                     amount_paid, 
#                     balance, 
#                     formatted_date,  # Formatted date only
#                     comment
#                 )
#             )
def disp_pay_hist(e=None):  
    global search_hist_entry,pay_hist_tree,search_hist_disp
    pay_hist_tree.delete(*pay_hist_tree.get_children()) 
    try:       
        learner_id=search_hist_entry.get()
        learner_id=int(learner_id)
        
    #displaying transaction history
        #displaying all history
        cur.execute("""SELECT l.learner_id,l.grade,l.first,l.second,l.surname,
                    th.amount,th.balance,th.trans_time,th.comment FROM learner l
                    JOIN transaction_history th ON l.learner_id=th.learner_id
                     WHERE l.learner_id=%s ORDER BY trans_time DESC""",(learner_id,))
        h=cur.fetchall()
        if h:
            for index,h in enumerate(h,start=1):
                time=h[7]
                formatted_date=time.strftime("%d-%m-%Y")
                pay_hist_tree.insert("",END,values=(index,h[0],h[1],f"{h[2]} {h[3]} {h[4]}".title(),h[5],h[6],formatted_date,h[8]))
        else:
            search_hist_disp.configure(text=f"Record with Adm {search_hist_entry.get()} not found")
            search_hist_disp.after(4000,lambda:search_hist_disp.configure(text=""))
        
            search_hist_entry.delete(0,END)
    except Exception as e:
        messagebox.showerror("Remedial App",f"{e}")
# #setting termly pay
# #windows functions
#payment_history_func
def payment_history_func():
    global pay_hist_tree,search_hist_entry,search_hist_disp
    #learner treeview (# name,adm,grade,paid,bal,date,comment)
    #style 
    pay_hist_win=ctk.CTkToplevel(root)
    pay_hist_win.geometry("950x400+50+10")
    pay_hist_win.resizable(width=False,height=False)
    pay_hist_win.transient(root)
    pay_hist_win.grab_set()
    pay_hist_win.title("Monitor Tr. Attendance")
    pay_hist_win.after(100, lambda: pay_hist_win.lift())  # Delay lifting the window
    pay_hist_win.after(200, lambda: pay_hist_win.focus_force())  # Delay forcing 
    pay_hist_tree_frame=ctk.CTkFrame(pay_hist_win)
    pay_hist_tree_scroll=Scrollbar(pay_hist_tree_frame,orient=VERTICAL)
    pay_hist_tree_scroll.pack(side=RIGHT,fill=Y)
    pay_hist_tree_frame.place(x=20,y=30)
    pay_hist_tree=ttk.Treeview(pay_hist_tree_frame,yscrollcommand=learner_tree_scroll.set,height=12,
    selectmode="extended") # name,id,grade,paid,bal,date,comment
    pay_hist_tree_scroll.configure(command=pay_hist_tree.yview)
    pay_hist_tree["columns"]=("no","ID","grade","name","paid","balance","date","comment")
    pay_hist_tree.column("#0",width=0,stretch=NO)
    pay_hist_tree.column("no",width=40,anchor="center",minwidth="35")
    pay_hist_tree.column("ID",width=40,minwidth=80,anchor=CENTER)
    pay_hist_tree.column("grade",width=80,minwidth=60,anchor=CENTER)
    pay_hist_tree.column("name",width=220,minwidth=100,anchor=W)
    pay_hist_tree.column("paid",width=80,minwidth=75,anchor=CENTER)
    pay_hist_tree.column("balance",width=60,minwidth=75,anchor=CENTER)
    pay_hist_tree.column("date",width=100,minwidth=45,anchor=CENTER)
    pay_hist_tree.column("comment",width=280,minwidth=45,anchor=W)
    #headings
    pay_hist_tree.heading("#0",text="")
    pay_hist_tree.heading("no",text="#",anchor=CENTER)
    pay_hist_tree.heading("ID",text="Adm",anchor=CENTER)
    pay_hist_tree.heading("grade",text="Grade",anchor=CENTER)
    pay_hist_tree.heading("name",text="Name",anchor=W)
    pay_hist_tree.heading("paid",text="Paid",anchor=CENTER)
    pay_hist_tree.heading("balance",text="Bal",anchor=CENTER)
    pay_hist_tree.heading("date",text="Date",anchor=CENTER)
    pay_hist_tree.heading("comment",text="Comment",anchor=CENTER)
    pay_hist_tree.pack()
    #displaying all history
    cur.execute("""SELECT l.learner_id,l.grade,l.first,l.second,l.surname,
                th.amount,th.balance,th.trans_time,th.comment FROM learner l
                JOIN transaction_history th ON l.learner_id=th.learner_id
                ORDER BY trans_time DESC""")
    h=cur.fetchall()
    if h:
        for index,h in enumerate(h,start=1):
            time=h[7]
            formatted_date=time.strftime("%d-%m-%Y")
            pay_hist_tree.insert("",END,values=(index,h[0],h[1],f"{h[2]} {h[3]} {h[4]}".title(),h[5],h[6],formatted_date,h[8]))
    else:
        messagebox.showinfo("Remedial App","No transaction history records")
    pay_hist_w_frame=ctk.CTkFrame(pay_hist_win) 
    pay_hist_w_frame.place(x=150,y=315)
    search_hist_entry=ctk.CTkEntry(pay_hist_w_frame,font=("Helvetica",16),width=100
                                  ,border_color=blue,placeholder_text="Enter Adm"
                                  )
    search_hist_entry.grid(row=0,column=0,sticky=W)
    search_hist_button=ctk.CTkButton(pay_hist_w_frame,text="Search",command=disp_pay_hist
                         ,width=60)
    search_hist_button.grid(row=0,column=1,padx=5)
    search_hist_disp=ctk.CTkLabel(pay_hist_w_frame,text="",font=("Helvetica",16))
    search_hist_disp.grid(row=0,column=2)
#teacher display
def teacher_win_func():
    global teacher_tree
    teacher_win=ctk.CTkToplevel(root)
    teacher_win.geometry("600x450+600+10")
    # teacher_win.resizable(width=False,height=False)
    teacher_win.transient(root)
    teacher_win.grab_set()
    teacher_win.title("Monitor Tr. Attendance")
    teacher_win.after(100, lambda: teacher_win.lift())  # Delay lifting the window
    teacher_win.after(200, lambda: teacher_win.focus_force())  # Delay forcing 
    teacher_tree_frame=ctk.CTkFrame(teacher_win)
    teacher_tree_scroll=Scrollbar(teacher_tree_frame,orient=VERTICAL)
    teacher_tree_scroll.pack(side=RIGHT,fill=Y)
    teacher_tree_frame.place(x=20,y=30)
    teacher_tree=ttk.Treeview(teacher_tree_frame,yscrollcommand=learner_tree_scroll.set,height=12,
    selectmode="extended")
    teacher_tree_scroll.configure(command=teacher_tree.yview)
    teacher_tree["columns"]=("no","ID","name","paid","balance")
    teacher_tree.column("#0",width=0,stretch=NO)
    teacher_tree.column("no",width=40,anchor="center",minwidth="35")
    teacher_tree.column("ID",width=100,minwidth=80,anchor=CENTER)
    teacher_tree.column("name",width=250,minwidth=180,anchor=W)
    teacher_tree.column("paid",width=80,minwidth=75,anchor=CENTER)
    teacher_tree.column("balance",width=80,minwidth=75,anchor=CENTER)
    #headings
    teacher_tree.heading("#0",text="")
    teacher_tree.heading("no",text="#",anchor=CENTER)
    teacher_tree.heading("ID",text="ID",anchor=CENTER)
    teacher_tree.heading("name",text="NAME",anchor=CENTER)
    teacher_tree.heading("paid",text="PAID",anchor=CENTER)
    teacher_tree.heading("balance",text="BAL",anchor=CENTER)
    teacher_tree.pack()
    #tr_win_widgets
    tr_win_w_frame=ctk.CTkFrame(teacher_win)
    tr_win_w_frame.place(x=20,y=320)
    session_label=ctk.CTkLabel(tr_win_w_frame,text="Session",font=("Helvetica",16))
    session_label.grid(row=0,column=0)
    session_combo=ctk.CTkComboBox(tr_win_w_frame,font=("Helvetica",16),width=110,state="readonly",button_color=blue,values=("Morning","Evening","Saturday"))
    session_combo.grid(row=0,column=1,padx=10)
    grade_label=ctk.CTkLabel(tr_win_w_frame,text="Grade",font=("Helvetica",16))
    grade_label.grid(row=1,column=0,pady=10)
    #accessing grades 
    grades=grades_list()
    grade_combo=ctk.CTkComboBox(tr_win_w_frame,font=("Helvetica",16),width=110,state="readonly",button_color=blue,values=(grades))
    grade_combo.grid(row=1,column=1,padx=10)
    subjects=["MATHS","ENG","KISW","INT","SST","AGRI","CAS","CRE","PTC","PPI"]
    subject_label=ctk.CTkLabel(tr_win_w_frame,text="Subject",font=("Helvetica",16))
    subject_label.grid(row=2,column=0)
    subject_combo=ctk.CTkComboBox(tr_win_w_frame,font=("Helvetica",16),width=110,state="readonly",button_color=blue,values=(subjects))
    subject_combo.grid(row=2,column=1,padx=10)
    display_teachers()
#setting term(term/year,termly pay teacher pay,promoting learnes)
def set_term_func():
    global term_combo,set_term_label,lnr_amount_entry,lnr_amount_entry,tr_weekend_entry,tr_week_entry
    #accessing terms from term func
    terms=term_list()
    set_term_win=ctk.CTkToplevel(root)
    path="D:/Tonniegifted/Remedial App/Resources/remedial convert.ico"
    set_term_win.iconbitmap(path)
    set_term_win.geometry("320x350+800+10")
    set_term_win.resizable(width=False,height=False)
    set_term_win.transient(root)
    set_term_win.grab_set()
    set_term_win.title("Set Term")
    set_term_win.after(100, lambda: set_term_win.lift())  # Delay lifting the window
    set_term_win.after(200, lambda: set_term_win.focus_force())  # Delay forcing focus
    #set term win widgets
    term_label=ctk.CTkLabel(set_term_win,text="Term",font=("Helvetica",16))
    term_combo=ctk.CTkComboBox(set_term_win,values=terms,width=180,height=30,
                               state="readonly",font=("Helvetica",16),
                               button_color=blue,border_color="blue",command=switch_term)
    term_label.place(x=20,y=20)
    term_combo.place(x=110,y=20)
    termly_pay_label=ctk.CTkLabel(set_term_win,text="Termly Pay",font=("Helvetica",16),
                                  )
    termly_pay_label.place(x=20, y=60)
    lnr_amount_entry=ctk.CTkEntry(set_term_win,width=180,height=30,
                               font=("Helvetica",16),border_color=blue
                               ,placeholder_text="Learner Termly pay")
    # grade_entry_combo.set("Select Grade")
    lnr_amount_entry.place(x=110,y=60)
    tr_week_label=ctk.CTkLabel(set_term_win,text="Weekday",font=("Helvetica",16))
    tr_week_label.place(x=20,y=100)
    tr_week_entry=ctk.CTkEntry(set_term_win,font=("Helvetica",16),width=180
                                  ,border_color=blue,placeholder_text="Teacher Weekly pay")
    tr_week_entry.place(x=110,y=100)
    tr_weekend_label=ctk.CTkLabel(set_term_win,text="Weekend",font=("Helvetica",16))
    tr_weekend_label.place(x=20,y=140)
    tr_weekend_entry=ctk.CTkEntry(set_term_win,font=("Helvetica",16),width=180
                                  ,border_color=blue,placeholder_text="Teacher Weekend pay"
                                  )
    tr_weekend_entry.place(x=110,y=140)
    promote_learners=ctk.CTkButton(set_term_win,text="move learners",
    font=("Helvetica",16),command=promote_learners_func,width=80) #should be disabled if its not term one
    promote_learners.place(x=20,y=180)
    undo_move_button=ctk.CTkButton(set_term_win,text="undo move",width=50,command=undo_promotion)
    undo_move_button.place(x=180,y=180)
    
    button=ctk.CTkButton(set_term_win,text="Save Changes",command=lambda:set_default_term(None)
                         ,width=60)
    button.place(x=110,y=230)
    
    
    set_term_label=ctk.CTkLabel(set_term_win,text="",
                                font=("helvetica",14))
    set_term_label.place(x=50,y=260)
    #setting the default term
    cur.execute("SELECT selected_term FROM term WHERE is_active=1")
    term=cur.fetchone()
    if term:
        selected_term=term[0]
        term_combo.set(selected_term)
    else:
        term_combo.set(term_combo.cget("values")[0])

#adding and deleting teachers and learners win func
def add_person_func():
    global person_type_combo,number_entry,reg_grade_combo,tr_title_combo,first_entry,second_entry,surname_entry,reg_person_label
    person_win=ctk.CTkToplevel(root)
    person_win.geometry("350x430+800+10")
    person_win.title("Learners Registration")
    person_win.resizable(width=False,height=False)
    person_win.transient(root)
    person_win.grab_set()
    person_win.iconbitmap(path)
    person_win.after(100, lambda: person_win.lift())  # Delay lifting the window
    person_win.after(200, lambda: person_win.focus_force())  # Delay forcing focus
    #add person widget
    person_type_label=ctk.CTkLabel(person_win,text="Person Type",font=("Helvetica",16))
    person_type_label.place(x=57,y=10)
    person_type_combo=ctk.CTkComboBox(person_win,height=30,width=155,
                                      border_color=blue,button_color=blue,font=("Helvetica",16),
                                      values=("Learner","Teacher"),state="readonly",command=disable_combo)
    person_type_combo.place(x=150,y=10)
    number_label=ctk.CTkLabel(person_win,text="Id No",font=("Helvetica",16))
    number_label.place(x=20,y=50)
    number_entry=ctk.CTkEntry(person_win,height=30,border_color=blue,width=180,
                                font=("helvetica",16))
    number_entry.place(x=125,y=50)
    reg_grade_label=ctk.CTkLabel(person_win,text="Grade",font=("helvetica",16),)
    reg_grade_label.place(x=20,y=90)
    #accessing values from the function
    grade=grades_list()
    reg_grade_combo=ctk.CTkComboBox(person_win,height=30,border_color=blue,width=180,
                                font=("helvetica",16),state="readonly",values=grade,
                                button_color=blue)
    reg_grade_combo.place(x=125,y=90)
    tr_title_label=ctk.CTkLabel(person_win,text="Title",font=("helvetica",16))
    tr_title_label.place(x=20,y=130)
    tr_title_combo=ctk.CTkComboBox(person_win,height=30,width=180,font=("Helvetica",16),
                                      border_color=blue,button_color=blue,
                                      values=("Tr","Mr","Mrs","Miss"),state="readonly")
    tr_title_combo.place(x=125,y=130)
    first_label=ctk.CTkLabel(person_win,text="First Name",font=("Helvetica",16))
    first_label.place(x=20,y=170)
    first_entry=ctk.CTkEntry(person_win,height=30,border_color=blue,width=180,
                                font=("helvetica",16))
    first_entry.place(x=125,y=170)
    second_label=ctk.CTkLabel(person_win,text="Second Name",font=("Helvetica",16))
    second_label.place(x=20,y=210)
    second_entry=ctk.CTkEntry(person_win,height=30,border_color=blue,width=180,
                                font=("helvetica",16))
    second_entry.place(x=125,y=210)
    
    surname_label=ctk.CTkLabel(person_win,text="Surname",font=("Helvetica",16))
    surname_label.place(x=20,y=250)
    surname_entry=ctk.CTkEntry(person_win,height=30,border_color=blue,width=180,
                                font=("helvetica",16))
    surname_entry.place(x=125,y=250)
     
    add_person_button=ctk.CTkButton(person_win,text="Add"
                         ,width=60,command=lambda:add_person(None))
    add_person_button.place(x=80,y=300)
    
    delete_person_button=ctk.CTkButton(person_win,text="Delete"
                         ,width=60,command=lambda:delete_person(None))
    delete_person_button.place(x=220,y=300)
    reg_person_label=ctk.CTkLabel(person_win,text="",
                                font=("helvetica",14))
    reg_person_label.place(x=80,y=340)

def switch_term(e=None):
    global term_combo
    selected_term = term_combo.get()

    # Resetting termly pay values: weekday, weekend, lnr_pay
    cur.execute("""
        SELECT weekday, weekend, lnr_pay FROM termly_pay
        WHERE term_id = (
            SELECT term_id FROM term WHERE is_active = 1
        )
    """)
    reset = cur.fetchone()

    # Handle cases where no active term exists
    if reset:
        weekday = reset[0]
        weekend = reset[1]
        lnr_pay = reset[2]
    else:
        # Default values if no active term exists
        weekday = 0.00
        weekend = 0.00
        lnr_pay = 0.00

    if not selected_term:
        set_term_label.configure(text="Please select a term.", text_color="red")
        return

    # Update the database to set the selected term as active
    cur.execute("UPDATE term SET is_active = 0")  # Deactivate any active terms
    cur.execute("UPDATE term SET is_active = 1 WHERE selected_term = %s", (selected_term,))
    my_db.commit()

    # Retrieve the ID of the term switched into
    cur.execute("SELECT term_id FROM term WHERE is_active = 1")
    term_id = cur.fetchone()[0]

    # Update or insert into `termly_pay`
    cur.execute("""
        INSERT INTO termly_pay (term_id, weekday, weekend, lnr_pay)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            weekday = VALUES(weekday),
            weekend = VALUES(weekend),
            lnr_pay = VALUES(lnr_pay)
    """, (term_id, weekday, weekend, lnr_pay))
    my_db.commit()

    # Update the label to indicate the active term
    set_term_label.configure(text=f"{selected_term}: Active")
    set_term_label.after(4000, lambda: set_term_label.configure(text=""))

    # Refresh the displayed learners
    display_learners()

def set_default_term(e):
    try:
        global term_combo, set_term_label, lnr_amount_entry, tr_weekend_entry, tr_week_entry
        # Get the selected term from the combo box
        selected = term_combo.get()
        lnr_pay = lnr_amount_entry.get()
        lnr_pay = float(lnr_pay)
        tr_weekly_pay = tr_week_entry.get()
        tr_weekly_pay = float(tr_weekly_pay)
        tr_weekend_pay = tr_weekend_entry.get()
        tr_weekend_pay = float(tr_weekend_pay)

        if all([lnr_pay, tr_weekly_pay, tr_weekend_pay]):
            # Deactivate all terms
            cur.execute("UPDATE term SET is_active = 0 WHERE is_active = 1")
            my_db.commit()

            # Activate the selected term
            cur.execute("UPDATE term SET is_active = 1 WHERE selected_term = %s", (selected,))
            my_db.commit()

            # Retrieve the current term id
            cur.execute("SELECT term_id, selected_term FROM term WHERE is_active = 1")
            term = cur.fetchone()

            if term:  # Ensure term is not None
                term_id = term[0]
                term_name = term[1]

                # Updating teacher pay
                cur.execute("""
                INSERT INTO termly_pay (term_id, weekday, weekend, lnr_pay)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                weekday = VALUES(weekday),
                weekend = VALUES(weekend),
                lnr_pay = VALUES(lnr_pay)
                """, (term_id, tr_weekly_pay, tr_weekend_pay, lnr_pay))
                my_db.commit()

                set_term_label.configure(text=f"{term_name} was set successfully")
                clear_term_win()
                display_learners()
                set_term_label.after(4000, lambda: set_term_label.configure(text=""))
            else:
                # If no active term is found
                root.bell()
                CTkMessagebox(title="Set Term", message="No active term found.", icon="warning")
        else:
            root.bell()
            CTkMessagebox(title="Set Term", message="Fill all fields to set term", icon="warning")
    except Exception as ex:
        # Catch any exceptions
        CTkMessagebox(title="Set Term", message=f"{ex}", icon="warning")
        my_db.rollback()

#placer
def placer(e):
    cord=f"{e.x} x {e.y}"
    disp_label.configure(text=cord)
    disp_label.after(3000,lambda:disp_label.configure(text=""))
    
#switching between light and dark modes
def toggle():
    #to work on how app can remember mode and to change path
        if toggle_switch.get()==1:
    # if toggle_switch.get()==1:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            # style 
            style=tb.Style()
            style.configure('Treeview',
                        rowheight=20,
                        font="times 13",
                        foreground="#FFFFFF",
                        background="#2A2A2A")
            style.configure("Treeview.Heading",foreground="#FFFFFF",font="Times 13",background="#2A2A2A")
            style.map('Treeview',background=[("selected","#1E90FF")])
            learner_tree_frame.configure(bg_color="#2A2A2A")
        else:
            ctk.set_appearance_mode("light")
            ctk.set_default_color_theme("blue")
            # style 
            style=tb.Style()
            style.configure('Treeview',
                        rowheight=20,
                        font="times 13",
                        background="#FFFFFF",
                        foreground="black")
            style.configure("Treeview.Heading",foreground="blue",font="Times 13",background="#FFFFFF")
            style.map('Treeview',background=[("selected",f"{blue}")])
           
#WIDGETS  
#adding treeview
learner_tree_frame=ctk.CTkFrame(root,fg_color="transparent")

#learner treeview
#style 
style=tb.Style()
style.configure('Treeview',
               rowheight=20,
               font="times 13",
               fieldbackground="pink")
            #    background=f"{blue}")
style.configure("Treeview.Heading",foreground="blue",font="Times 13")
style.map('Treeview',background=[("selected",f"{blue}")])

learner_tree_scroll=Scrollbar(learner_tree_frame,orient=VERTICAL)
learner_tree_scroll.pack(side=RIGHT,fill=Y)
learner_tree_frame.place(x=30,y=100)
learner_tree=ttk.Treeview(learner_tree_frame,yscrollcommand=learner_tree_scroll.set,height=12,
selectmode="extended")
learner_tree_scroll.configure(command=learner_tree.yview)
learner_tree["columns"]=("no","adm","grade","name","paid","balance")
learner_tree.column("#0",width=0,stretch=NO)
learner_tree.column("no",width=40,anchor="center",minwidth="35")
learner_tree.column("adm",width=100,minwidth=80,anchor=CENTER)
learner_tree.column("grade",width=70,anchor="center",minwidth=50)
learner_tree.column("name",width=250,minwidth=180,anchor=W)
learner_tree.column("paid",width=80,minwidth=75,anchor=CENTER)
learner_tree.column("balance",width=80,minwidth=75,anchor=CENTER)
#headings
learner_tree.heading("#0",text="")
learner_tree.heading("no",text="#",anchor=CENTER)
learner_tree.heading("adm",text="ADM",anchor=CENTER)
learner_tree.heading("grade",text="GRADE",anchor=CENTER)
learner_tree.heading("name",text="NAME",anchor=CENTER)
learner_tree.heading("paid",text="PAID",anchor=CENTER)
learner_tree.heading("balance",text="BAL",anchor=CENTER)
learner_tree.pack()

#setting menubutton
menubutton=tb.Menubutton(root,text="Menu")
menubutton.place(x=30,y=10) 
menu=tb.Menu(menubutton)
menubutton["menu"]=menu 

menu.add_command(label="Set Term",command=set_term_func)
menu.add_command(label="Register Persons",command=add_person_func)
menu.add_command(label="Learner Payment History",command=payment_history_func)
# menu.add_command(label=" Display Tr. Attnd. History") #on the monitor table
menu.add_command(label="Monitor Tr. Attendance",command=teacher_win_func)
#within the table display teachers, their total_sessions, and total(already paid)
#popup menu
#popup func

learner_menu=Menu(root,tearoff=0)
learner_menu=Menu(learner_menu,tearoff=0)
learner_menu.add_command(label="Delete learner",command=delete_learner)
learner_menu.add_separator()

learner_search_entry=ctk.CTkEntry(root,width=150,font=("helvetica",16),
placeholder_text="Search")
learner_search_entry.place(x=152,y=46)
search_button=ctk.CTkButton(root,text="Search",width=50,command=search_func)
search_button.place(x=311,y=46)
weeks=["One","Two","Three","Four","Five","Six","Seven",
       "Eight","Nine","Ten","Eleven","Twelve","Thirteen",
       "Fourteen"]
week_label=ctk.CTkLabel(root,text="Week",font=("Helvetica",16))
week_label.place(x=390,y=10)
week_combo=ctk.CTkComboBox(root,height=30,width=120,font=("Helvetica",16),
                                      border_color=blue,button_color=blue,
                                      values=(weeks),state="readonly")
week_combo.place(x=440,y=10)
search_label=ctk.CTkLabel(root,text="")
search_label.place(x=376,y=46)
search_by_label=ctk.CTkLabel(root,text="Search By")

search_by_combo=ctk.CTkComboBox(root,height=30,width=150,font=("Helvetica",16),
                                      border_color=blue,button_color=blue,
                                 values=("Search By","Adm No","Name"),state="readonly")
search_by_combo.place(x=152,y=10)
search_by_combo.set("Search by")
disp_label=ctk.CTkLabel(root,text="")
disp_label.place(x=286,y=545)
toggle_switch=ctk.CTkSwitch(root,text="Switch Mode",command=toggle)
toggle_switch.place(x=47,y=571)
#learner frame widgets frame
lnr_tree_w_frame=ctk.CTkFrame(root,fg_color="transparent")
lnr_tree_w_frame.place(x=40,y=416)

amount_label=ctk.CTkLabel(lnr_tree_w_frame,text="Amount",font=("helvetica",16))
amount_label.grid(row=0,column=0,sticky=W)
amount_entry=ctk.CTkEntry(lnr_tree_w_frame,width=150,font=("helvetica",16))
amount_entry.grid(row=0,column=1,padx=10)
From_label=ctk.CTkLabel(lnr_tree_w_frame,text="Received From",font=("helvetica",16))
From_label.grid(row=1,column=0,sticky=W,pady=10)
From_entry=ctk.CTkEntry(lnr_tree_w_frame,width=150,font=("helvetica",16))
From_entry.grid(row=1,column=1,padx=10,pady=10)
grade=grades_list()
disp_bal=ctk.CTkLabel(lnr_tree_w_frame,font=("Helvetica",16),text="Grade")
disp_bal.grid(row=0,column=3,padx=10)
disp_bal_combo=ctk.CTkComboBox(lnr_tree_w_frame,height=30,width=190,font=("Helvetica",16),
                                      border_color=blue,button_color=blue,
                                      values=(grade),state="readonly",command=display_learners)
disp_bal_combo.set(grade[0])

disp_bal_combo.grid(row=0,column=4)
delete_trans_button=ctk.CTkButton(lnr_tree_w_frame,text="Delete Transaction",width=100
                            ,command=delete_transaction)
delete_trans_button.grid(row=1,column=4)
# disp_bal_combo.set("Display Balances")
submit_button=ctk.CTkButton(lnr_tree_w_frame,text="Submit",width=80
                            ,command=make_payment)
submit_button.grid(row=1,columnspan=3,column=3)
submit_button.grid(row=2,column=1)
#calling functions
display_learners()
#bindings
root.bind("<Button-1>",placer)
root.bind("<Button-3>",binding)
root.mainloop()
