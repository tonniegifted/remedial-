from tkinter import*
from tkinter import ttk
from tkinter import messagebox
from CTkMessagebox import CTkMessagebox
import sqlite3
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Font
from decimal import Decimal
import customtkinter as ctk
import ttkbootstrap as tb
#creating connection for sqlite3    "C:/Users/Administrator/Documents"
#"C:/Users/Administrator/Documents/Remedial App/Remedial App.db"
import sqlite3
path="C:/Users/Administrator/Documents/Remedial App/Remedial App.db"
my_db = sqlite3.connect(path)
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
from tkinter import messagebox

def make_payment():
    try:
        # Validate amount entry
        try:
            amount_paid = float(amount_entry.get().strip())
            if amount_paid <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Remedial App", "Enter a valid amount greater than zero.")
            return

        # Get active term details
        cur.execute("SELECT term_id, term_number FROM term WHERE is_active = 1")
        active_term = cur.fetchone()
        if not active_term:
            messagebox.showinfo("Remedial App", "No active term found. Please check term setup.")
            return
        term_id, current_term_number = active_term

        # Validate learner selection
        pos = learner_tree.selection()
        if not pos:
            messagebox.showwarning("Remedial App", "Please select a learner.")
            return
        learner_id = learner_tree.item(pos[0], "values")[1]

        # Check if the learner's previous term is fully cleared
        if current_term_number > 1:
            # Fetch the previous term's ID and termly pay
            cur.execute("SELECT term_id FROM term WHERE term_number = ?", (current_term_number - 1,))
            prev_term = cur.fetchone()
            if prev_term:
                prev_term_id = prev_term[0]
                cur.execute("SELECT lnr_pay FROM termly_pay WHERE term_id = ?", (prev_term_id,))
                prev_term_fee = cur.fetchone()
                if prev_term_fee:
                    prev_term_fee = prev_term_fee[0]
                    # Fetch the previous term's payment details
                    cur.execute('''SELECT amount_paid, balance FROM transactions 
                                   WHERE learner_id = ? AND term_id = ?''', (learner_id, prev_term_id))
                    prev_record = cur.fetchone()

                    # Check if the previous term's payment is fully cleared
                    if prev_record:
                        prev_amount_paid, prev_balance = prev_record
                        if prev_balance != 0 or prev_amount_paid < prev_term_fee:
                            CTkMessagebox(
                                title="Remedial App",
                                message=f"Payment cannot be recorded\n clear Outstanding  balance: \n{prev_balance} KSH. before proceeding.",icon="warning"
                            )
                            return
                    else:
                        # If no record exists for the previous term, assume payment is unpaid
                        CTkMessagebox(
                            title="Remedial App",message=f"Payment cannot be recorded.\n Clear Outstanding balance: {prev_term_fee}KSH. before procced",icon="warning")
                        return

        # Retrieve current term fee
        cur.execute("SELECT lnr_pay FROM termly_pay WHERE term_id = ?", (term_id,))
        term_fee = cur.fetchone()[0]

        # Retrieve current term's transactions
        cur.execute('''SELECT amount_paid, balance FROM transactions
                       WHERE learner_id = ? AND term_id = ?''', (learner_id, term_id))
        record = cur.fetchone()

        # Calculate new amount and balance
        if record:
            new_amount = record[0] + amount_paid
            new_balance = record[1] - amount_paid
        else:
            new_amount = amount_paid
            new_balance = term_fee - amount_paid

        # Validate payment amount
        if new_amount > term_fee:
            CTkMessagebox(title="Remedial App", message="Amount Paid cannot exceed the termly payable amount.",icon="warning")
            return

        # Update or insert transaction
        if record:
            cur.execute('''UPDATE transactions SET amount_paid = ?, balance = ? 
                           WHERE learner_id = ? AND term_id = ?''', 
                        (new_amount, new_balance, learner_id, term_id))
        else:
            cur.execute('''INSERT INTO transactions(amount_paid, learner_id, term_id, balance)
                           VALUES (?, ?, ?, ?)''', (new_amount, learner_id, term_id, new_balance))

        my_db.commit()

        # Record transaction history
        comment = From_entry.get()
        cur.execute("SELECT transaction_id FROM transactions ORDER BY transaction_id DESC LIMIT 1")
        item = cur.fetchone()
        transaction_id = item[0] if item else None

        cur.execute("""INSERT INTO transaction_history(learner_id, amount, balance, term_id, comment, transaction_id)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                    (learner_id, amount_paid, new_balance, term_id, comment, transaction_id))
        my_db.commit()

        amount_entry.delete(0, END)
        From_entry.delete(0, END)
        disp_label.configure(text="Payment saved successfully")
        disp_label.after(4000, lambda: disp_label.configure(text=""))
        clear_learner_tree()
        display_learner()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

        

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
            teacher_tree.insert("",END,values=(index,teacher[0],f"{teacher[1].title() } {teacher[2].title()} {teacher[3].title()}"))
    else:
        messagebox.showinfo("Remedial App","No records for teachers")     
# def display_all_learners():
#     try:
#         #accessing the lnr_pay
#         cur.execute("""SELECT lnr_pay FROM termly_pay WHERE term_id=
#                     (SELECT  term_id FROM term WHERE is_active=1)""")
#         term_pay=cur.fetchone()[0]
#         # Query to retrieve all learners and their balances
#         cur.execute("""
#         SELECT 
#             learner.learner_id, 
#             learner.grade, 
#             learner.first, 
#             learner.second, 
#             learner.surname, 
#             IFNULL(transactions.amount_paid, 0) AS amount_paid, 
#             IFNULL(transactions.balance, 0) AS balance
#         FROM learner
#         LEFT JOIN transactions ON learner.learner_id = transactions.learner_id
#         WHERE term_id=(SELECT term_id FROM term WHERE is_active=1)"""  )
        
#         learners = cur.fetchall()
        
#         # Clear the treeview before inserting new data
#         learner_tree.delete(*learner_tree.get_children())
        
#         if learners:
#             for index, learner in enumerate(learners, start=1):
#                 # Insert the learner details into the treeview, including balances
#                 learner_tree.insert(
#                     "", 
#                     END, 
#                     values=(
#                         index, 
#                         learner[0],  # Learner ID
#                         learner[1],  # Grade
#                         f"{learner[2].title()} {learner[3].title()} {learner[4].title()}",  # Full Name
#                         learner[5],  # Amount Paid
#                         learner[6]   # Balance
#                     )
#                 )
#         else:
#             # Show a message if no learners are found
#             messagebox.showinfo("Remedial App", "No records found for any learners.")
#     except Exception as e:
#         # Catch and display any database errors
#         messagebox.showerror("Remedial App", f"An error occurred: {e}")

# def display_learner(e=None):
    
    
#     try:
#         cur.execute("""SELECT grade FROM learner WHERE learner_id=(SELECT learner_id
#                     FROM transactions ORDER BY transaction_id DESC)""")
#         g=cur.fetchone()[0]
#         # Get the selected grade from the dropdown combo box
#         grd = disp_bal_combo.get().strip()  # Remove any leading or trailing spaces
#         if grd=="Display Balances":
#             grd=g
#         # Check if a grade is selected
#         if not grd:
#             messagebox.showerror("Remedial App", "Please select a grade to filter learners.")
#             return
#         # Query to retrieve learners filtered by grade and their balances
#         cur.execute("""
#         SELECT 
#             learner.learner_id, 
#             learner.grade, 
#             learner.first, 
#             learner.second, 
#             learner.surname, 
#             IFNULL(transactions.amount_paid, 0) AS amount_paid, 
#             IFNULL(transactions.balance, 0) AS balance
#         FROM learner
#         LEFT JOIN transactions ON learner.learner_id = transactions.learner_id
#         WHERE learner.grade = ? AND term_id=(SELECT term_id FROM term WHERE is_active=1)
#         """, (grd,))
        
#         learners = cur.fetchall()
        
#         # Clear the treeview before inserting new data
#         learner_tree.delete(*learner_tree.get_children())
        
#         if learners:
#             for index, learner in enumerate(learners, start=1):
#                 # Insert the learner details into the treeview, including balances
#                 learner_tree.insert(
#                     "", 
#                     END, 
#                     values=(
#                         index, 
#                         learner[0],  # Learner ID
#                         learner[1],  # Grade
#                         f"{learner[2].title()} {learner[3].title()} {learner[4].title()}",  # Full Name
#                         learner[5],  # Amount Paid
#                         learner[6]   # Balance
#                     )
#                 )
#         else:
#             # Show a message if no learners are found for the selected grade
#             messagebox.showinfo("Remedial App", f"No records found for grade {grd}.")
#             #display all learners
#             display_all_learners()
#     except Exception as e:
#         # Catch and display database errors
#         messagebox.showerror("Remedial App", f"An error occurred: {e}")

# def display_learner(e=None):
#     try:
#         # Retrieve the grade of the most recent transaction if "Display Balances" is selected
#         cur.execute("""SELECT grade FROM learner WHERE learner_id=(SELECT learner_id
#                     FROM transactions ORDER BY transaction_id DESC)""")
#         g = cur.fetchone()[0]
        
#         # Get the selected grade from the dropdown combo box
#         grd = disp_bal_combo.get().strip()  # Remove any leading or trailing spaces
#         if grd == "Display Balances":
#             grd = g
        
#         # Check if a grade is selected
#         if not grd:
#             messagebox.showerror("Remedial App", "Please select a grade to filter learners.")
#             return
        
#         # Query to retrieve all learners of the selected grade and their balances
#         cur.execute("""
#         SELECT 
#             learner.learner_id, 
#             learner.grade, 
#             learner.first, 
#             learner.second, 
#             learner.surname, 
#             IFNULL(SUM(transactions.amount_paid), 0) AS amount_paid, 
#             (SELECT lnr_pay FROM termly_pay WHERE term_id=(SELECT term_id FROM term WHERE is_active=1)) - IFNULL(SUM(transactions.amount_paid), 0) AS balance
#         FROM learner
#         LEFT JOIN transactions ON learner.learner_id = transactions.learner_id AND term_id=(SELECT term_id FROM term WHERE is_active=1)
#         WHERE learner.grade = ?
#         GROUP BY learner.learner_id
#         """, (grd,))

#         learners = cur.fetchall()

#         # Clear the treeview before inserting new data
#         learner_tree.delete(*learner_tree.get_children())

#         if learners:
#             for index, learner in enumerate(learners, start=1):
#                 # Insert the learner details into the treeview, including balances
#                 learner_tree.insert(
#                     "", 
#                     END, 
#                     values=(
#                         index, 
#                         learner[0],  # Learner ID
#                         learner[1],  # Grade
#                         f"{learner[2].title()} {learner[3].title()} {learner[4].title()}",  # Full Name
#                         learner[5],  # Amount Paid
#                         learner[6]   # Balance
#                     )
#                 )
#         else:
#             # Check if the entire learners table is empty
#             cur.execute("SELECT COUNT(*) FROM learner")
#             total_learners = cur.fetchone()[0]
#             if total_learners == 0:
#                 messagebox.showinfo("Remedial App", "No records found for any learners.")
#             else:
#                 messagebox.showinfo("Remedial App", f"No records found for grade {grd}.")
#     except Exception as e:
#         # Catch and display database errors
#         messagebox.showerror("Remedial App", f"An error occurred: {e}")

def display_learner(e=None):
    try:
        # Retrieve the grade of the most recent transaction if "Display Balances" is selected
        cur.execute("""SELECT grade FROM learner WHERE learner_id=(SELECT learner_id
                    FROM transactions ORDER BY transaction_id DESC)""")
        result = cur.fetchone()
        
        # Check if a grade was retrieved
        if result:
            g = result[0]
        else:
            g = None  # No transactions found

        # Get the selected grade from the dropdown combo box
        grd = disp_bal_combo.get().strip()  # Remove any leading or trailing spaces
        if grd == "Display Balances":
            if g is None:
                messagebox.showinfo("Remedial App", "No recent transactions found to display balances.")
                return
            grd = g
        
        # Check if a grade is selected
        if not grd:
            messagebox.showerror("Remedial App", "Please select a grade to filter learners.")
            return
        
        # Query to retrieve all learners of the selected grade and their balances
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
        LEFT JOIN transactions ON learner.learner_id = transactions.learner_id AND term_id=(SELECT term_id FROM term WHERE is_active=1)
        WHERE learner.grade = ?
        GROUP BY learner.learner_id
        """, (grd,))

        learners = cur.fetchall()

        # Clear the treeview before inserting new data
        learner_tree.delete(*learner_tree.get_children())

        if learners:
            for index, learner in enumerate(learners, start=1):
                # Insert the learner details into the treeview, including balances
                learner_tree.insert(
                    "", 
                    END, 
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
            # Check if the entire learners table is empty
            cur.execute("SELECT COUNT(*) FROM learner")
            total_learners = cur.fetchone()[0]
            if total_learners == 0:
                messagebox.showinfo("Remedial App", "No records found for any learners.")
            else:
                messagebox.showinfo("Remedial App", f"No records found for grade {grd}.")
    except Exception as e:
        # Catch and display database errors
        messagebox.showerror("Remedial App", f"An error occurred: {e}")


def display_all_learners():
    try:
        # Accessing the lnr_pay for the active term
        cur.execute("""SELECT lnr_pay FROM termly_pay WHERE term_id=(SELECT term_id FROM term WHERE is_active=1)""")
        term_pay = cur.fetchone()[0]

        # Query to retrieve all learners and their balances
        cur.execute("""
        SELECT 
            learner.learner_id, 
            learner.grade, 
            learner.first, 
            learner.second, 
            learner.surname, 
            IFNULL(SUM(transactions.amount_paid), 0) AS amount_paid, 
            ? - IFNULL(SUM(transactions.amount_paid), 0) AS balance
        FROM learner
        LEFT JOIN transactions ON learner.learner_id = transactions.learner_id AND term_id=(SELECT term_id FROM term WHERE is_active=1)
        GROUP BY learner.learner_id
        """, (term_pay,))

        learners = cur.fetchall()

        # Clear the treeview before inserting new data
        learner_tree.delete(*learner_tree.get_children())

        if learners:
            for index, learner in enumerate(learners, start=1):
                # Insert the learner details into the treeview, including balances
                learner_tree.insert(
                    "", 
                    END, 
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
            # Show a message if no learners are found
            messagebox.showinfo("Remedial App", "No records found for any learners.")
    except Exception as e:
        # Catch and display any database errors
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
            messagebox.showwarning("Register Persons","Select person type to proceed")
            return
        #deleting learner
        if person=="Learner":
            #access learner before asking to delete
            cur.execute("""SELECT first,second,surname FROM learner WHERE learner_id=?
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
                    cur.execute("DELETE FROM learner WHERE learner_id=?",(id_number,))
                    my_db.commit()
                    clear_learner_tree()
                    display_learner()
                    reg_person_label.configure(text="Learner details deleted successfully")
                    reg_person_label.after(4000,lambda:reg_person_label.configure(text=""))
        else:
            person=="Teacher"
            #access learner before asking to delete
            cur.execute("""SELECT title,first,second,surname FROM teacher WHERE teacher_id=?
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
                    cur.execute("DELETE FROM teacher WHERE teacher_id=?",(id_number,))
                    my_db.commit()
                    reg_person_label.configure(text="Teacher details deleted successfully")
                    reg_person_label.after(4000,lambda:reg_person_label.configure(text=""))
    except Exception as ex:
        messagebox.showerror("Register Persons",f"{ex}")
#add person function
def add_person(person):
    try:
        global person_type_combo,number_entry,reg_grade_combo,tr_title_combo,first_entry,second_entry,surname_entry,reg_person_label
        person=person_type_combo.get()
        id_number=number_entry.get()
        id_number=int(id_number)
        grade=reg_grade_combo.get()
        title=tr_title_combo.get()
        first=first_entry.get().strip().title()
        second=second_entry.get().strip().title()
        surname=surname_entry.get().strip().title()
        if not person:
            root.bell()
            # messagebox.showwarning("Register Persons","Select Person type to proceed")
            CTkMessagebox(title="Register Persons",message="Select Person type to proceed",icon="warning")
            return
        if person=="Learner":
            if all([id_number,grade,first,second,grade]):
            #checking whether learner id exist
                cur.execute("SELECT learner_id FROM learner WHERE learner_id=?"
                            ,(id_number,))
                learner_id=cur.fetchone()
                learner_id= learner_id[0] if learner_id else None
                #inserting learner if id do not exists
                if not learner_id:
                    cur.execute("""INSERT INTO learner(learner_id,first,second,surname,grade)values(?,?,?,?,?)""",(id_number,first,second,surname,grade))
                    my_db.commit()
                    reg_person_label.configure(text="Learner details saved successfully")
                    reg_person_label.after(4000,lambda:reg_person_label.configure(text=""))
                    clear_person_win()
                    clear_learner_tree()
                    display_learner()
                #updating learner details if id exist
                else:
                    root.bell()
                    resp=messagebox.showwarning("Register Persons",f"Learner ID {id_number} exist do you want to\noverwrite?")
                    if resp:
                        cur.execute("""UPDATE learner SET first=?,second=?,surname=?,grade=? WHERE learner_id=?""",(first,second,surname,grade,learner_id))
                        reg_person_label.configure(text="Learner details updated successfully")
                        #adding learner added to the treeview
                        clear_learner_tree()
                        display_learner()
                        clear_person_win()
                        reg_person_label.after(4000,lambda:reg_person_label.configure(text=""))
                        my_db.commit()
                    else:
                        pass
            else:
                root.bell()
                messagebox.showwarning("Register Persons","Ensure that you have filled all the\nnecessary fields for person type:\nLearner")
        else:
            person=="Teacher"
            if all([id_number,title,first,second]):
                #checking whether teacher id exists
                cur.execute("""SELECT teacher_id FROM teacher WHERE teacher_id=
                            ?""",(id_number,))
                teacher_id=cur.fetchone()
                teacher_id=teacher_id[0] if teacher_id else None
                #inserting teacher record if id does not exist
                if not teacher_id:
                    cur.execute("""INSERT INTO teacher(teacher_id,title,first,second,surname)VALUES(?,?,?,?,?)""",(id_number,title,first,second,surname))
                    my_db.commit()
                    reg_person_label.configure(text="Teacher details saved successfully")
                    reg_person_label.after(4000,lambda:reg_person_label.configure(text=""))
                    clear_person_win()
                else:
                    root.bell()
                    resp=messagebox.showwarning("Register Persons",f"Teacher ID {id_number} exist do you want to\noverwrite?")
                    if resp:
                        cur.execute("""UPDATE teacher SET title=?,first=?,second=?,surname=? WHERE teacher_id=?""",(title,first,second,surname,teacher_id))
                        reg_person_label.configure(text="Teacher details updated successfully")
                        clear_person_win()
                        reg_person_label.after(4000,lambda:reg_person_label.configure(text=""))
                        my_db.commit()
                    else:
                        pass
            else:
                root.bell()
                messagebox.showwarning("Register Persons","Ensure that you have filled all the\nnecessary fields for person type:\nTeacher")
    except Exception as ex:
        messagebox.showerror("Register Persons",f"{ex}")
    
                
        
#accessing grades
def grades_list():
    grades=["Seven","Eight","Nine"]
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
#setting termly pay
#windows functions
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
    promote_learners=ctk.CTkCheckBox(set_term_win,text="Promote Learners",
    font=("Helvetica",16)) #should be disabled if its not term one
    promote_learners.place(x=20,y=180)
    
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
    #resetting termly pay weekday,weekend,lnr_pay
    cur.execute("""SELECT weekday,weekend,lnr_pay FROM termly_pay
                WHERE term_id= (SELECT term_id FROM term 
                WHERE is_active=1)""")
    reset=cur.fetchone()
    weekday=reset[0]
    weekend=reset[1]
    lnr_pay=reset[2]
    if not selected_term:
        set_term_label.configure(text="Please select a term.", text_color="red")
        return

    # Update the database to set the selected term as active
    cur.execute("UPDATE term SET is_active = 0")  # Deactivate any active terms
    cur.execute("UPDATE term SET is_active = 1 WHERE selected_term = ?", (selected_term,))
    my_db.commit()
    #retrieving id of the term switched into
    cur.execute("SELECT term_id FROM term WHERE is_active=1")
    term_id=cur.fetchone()[0]
    cur.execute("""
            INSERT OR REPLACE INTO termly_pay (term_id, weekday, weekend, lnr_pay)
            VALUES (?, ?, ?, ?)""", 
            (term_id, weekday, weekend, lnr_pay))
    my_db.commit()
    set_term_label.configure(text=f"{selected_term}: Active")
    set_term_label.after(4000,lambda:set_term_label.configure(text=""))
    display_all_learners()
def set_default_term(e):
    try:
        global term_combo,set_term_label,lnr_amount_entry,lnr_amount_entry,tr_weekend_entry,tr_week_entry
        # Get the selected term from the combo box
        selected = term_combo.get()
        lnr_pay=lnr_amount_entry.get()
        lnr_pay=float(lnr_pay)
        tr_weekly_pay=tr_week_entry.get()
        tr_weekly_pay=float(tr_weekly_pay)
        tr_weekend_pay=tr_weekend_entry.get()
        tr_weekend_pay=float(tr_weekend_pay)
        if all([lnr_pay,tr_weekly_pay,tr_weekend_pay,]):
            # Deactivate all terms
            cur.execute("UPDATE term SET is_active = 0 WHERE is_active = 1")
            my_db.commit()

            # Activate the selected term
            cur.execute("UPDATE term SET is_active = 1 WHERE selected_term = ?", (selected,))
            my_db.commit()
            #retrieving current term id
            cur.execute("SELECT term_id,selected_term FROM term WHERE is_active=1")
            term=cur.fetchone()
            term_id=term[0]
            term_name=term[1]
            #updating teacher pay
            cur.execute("""
            INSERT OR REPLACE INTO termly_pay (term_id, weekday, weekend, lnr_pay)
            VALUES (?, ?, ?, ?)""", 
            (term_id, tr_weekly_pay, tr_weekend_pay, lnr_pay))
            my_db.commit()
            set_term_label.configure(text=f"{term_name} was set successfully")
            clear_term_win()
            display_all_learners()
            set_term_label.after(4000,lambda: set_term_label.configure(text=""))
        else:
            root.bell()
            messagebox.showwarning("Set Term","Fill all fields to set term")
    except Exception as ex:
            messagebox.showerror("Set Term",f"{ex}")
            my_db.rollback()
            
#placer
def placer(e):
    ...
#     cord=f"{e.x} x {e.y}"
#     disp_label.configure(text=cord)
#     disp_label.after(3000,lambda:disp_label.configure(text=""))
    
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
learner_tree_frame.place(x=30,y=80)
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
# menu.add_command(label=" Display Tr. Attnd. History") #on the monitor table
menu.add_command(label="Monitor Tr. Attendance",command=teacher_win_func)
#within the table display teachers, their total_sessions, and total(already paid)


main_win_search=ctk.CTkEntry(root,width=150,font=("helvetica",16),
placeholder_text="Search")
main_win_search.place(x=152,y=10)
search_button=ctk.CTkButton(root,text="Search",width=50)
search_button.place(x=310,y=10)
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
search_label.place(x=157,y=40)

disp_label=ctk.CTkLabel(root,text="")
disp_label.place(x=286,y=516)
toggle_switch=ctk.CTkSwitch(root,text="Switch Mode",command=toggle)
toggle_switch.place(x=47,y=530)
#learner frame widgets frame
lnr_tree_w_frame=ctk.CTkFrame(root,fg_color="transparent")
lnr_tree_w_frame.place(x=40,y=370)

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
disp_bal_combo=ctk.CTkComboBox(lnr_tree_w_frame,height=30,width=180,font=("Helvetica",16),
                                      border_color=blue,button_color=blue,
                                      values=(grade),state="readonly",command=display_learner)
disp_bal_combo.grid(row=0,column=4)
disp_bal_combo.set("Display Balances")
submit_button=ctk.CTkButton(lnr_tree_w_frame,text="Submit",width=80
                            ,command=make_payment)
submit_button.grid(row=1,columnspan=3,column=3)
submit_button.grid(row=2,column=1)
#calling functions
display_all_learners()

root.bind("<Button-1>",placer)
root.mainloop()
