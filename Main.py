from tkinter import *
from tkinter import ttk
import os
import mysql.connector
import base64
from tkinter import messagebox
from datetime import datetime
import threading
import time
import datetime
from functools import cmp_to_key

connection = False
if os.path.exists('saved_credentials.txt'):
    with open('saved_credentials.txt', 'r') as file:
        encoded_data = file.read().strip()
    encoded_host, encoded_user, encoded_password = encoded_data.split(';')
    host = base64.b64decode(encoded_host.encode()).decode()
    user = base64.b64decode(encoded_user.encode()).decode()
    password = base64.b64decode(encoded_password.encode()).decode()
else:
    def save_credentials():
        global host; global user; global password
        host = host_entry.get()
        user = user_entry.get()
        password = password_entry.get()
        with open('saved_credentials.txt', 'w') as file:
            encoded_host = base64.b64encode(host.encode()).decode()
            encoded_user = base64.b64encode(user.encode()).decode()
            encoded_password = base64.b64encode(password.encode()).decode()
            file.write(f"{encoded_host};{encoded_user};{encoded_password}")
        window.destroy()
    window = Tk()
    window.iconbitmap('./hospital.ico')
    window.title("Credentials Input")
    window.geometry("300x200")
    window.resizable(False, False)
    host_label = Label(window, text="Host:")
    host_label.pack()
    host_entry = Entry(window)
    host_entry.pack()
    user_label = Label(window, text="User:")
    user_label.pack()
    user_entry = Entry(window)
    user_entry.pack()
    password_label = Label(window, text="Password:")
    password_label.pack()
    password_entry = Entry(window, show="*")  # Use 'show' to hide password characters
    password_entry.pack()
    save_button = Button(window, text="Connect", command=save_credentials)
    save_button.pack()
    window.mainloop()
    
database = "hospital_db"
try:
    conn = mysql.connector.connect(host=host, user=user, password=password)
    if conn.is_connected():
        cursor = conn.cursor()

        # Create the hospital_db if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        conn.database = database

        # Create Patients table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Patients (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                specialization VARCHAR(100),
                fees DECIMAL(10, 2),
                slot VARCHAR(100)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Doctors (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                specialization VARCHAR(255),
                slot VARCHAR(100),
                patients_per_slot INT  
            )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Staffs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            Name VARCHAR(100),
            Profession VARCHAR(100),
            Working_Day VARCHAR(50),
            Working_hour INT
        )
    """)
        conn.commit()
        cursor.close()
        conn.close()
        messagebox.showinfo("Connected", "You are connected!")
        connection = True
    else:
        messagebox.showerror("Connection failed")
except mysql.connector.Error as e:
    messagebox.showerror("Error", f"Invalid Credentials\n{e}")
    if os.path.exists('saved_credentials.txt'):
        os.remove('saved_credentials.txt')
if connection:
    conn = mysql.connector.connect(host=host, user=user, password=password, database=database)
    cursor = conn.cursor()
    root = Tk()
    root.iconbitmap('./hospital.ico')
    root.title("Hospital Manager")
    running_thread = True
    notebook = ttk.Notebook(root)

    tab1 = ttk.Frame(notebook)
    tab2 = ttk.Frame(notebook)
    tab3 = ttk.Frame(notebook)
    tab4 = ttk.Frame(notebook)
    notebook.add(tab1, text="Patients")
    notebook.add(tab2, text="Doctors")
    notebook.add(tab3, text="Appointments")
    notebook.add(tab4, text= "Staff") 

    specializations = [
    "Cardiology", "Dermatology", "Endocrinology", "Gastroenterology",
    "Neurology", "Orthopedics", "Pediatrics", "Psychiatry", "Radiology", "Urology"]
    # Tab1 Patients:
    # "Name", "Specialization", "Fees", "Deadline"
    def add_patient():
        name = e1_tab1.get()
        specialization = e2_tab1.get()
        fees = e3_tab1.get()
        slot = e4_tab1.get()  # Replace 'deadline' with 'slot'

        if name != '' and specialization != '' and fees != '' and slot != '':
            insert_query = "INSERT INTO Patients (name, specialization, fees, slot) VALUES (%s, %s, %s, %s)"  # Adjusted the query
            data = (name, specialization, fees, slot)  # Adjusted the data
            cursor.execute(insert_query, data)
            conn.commit()

        e1_tab1.delete(0, END)
        e2_tab1.set("Select Specialization") 
        e3_tab1.delete(0, END)
        e4_tab1.delete(0, END)
        populate_patient_tree(tree_tab1)
        
    def delete_patient():
        patient_id = e5_tab1.get()

        if patient_id != '':
            # Delete the patient
            delete_query = "DELETE FROM Patients WHERE id = %s"
            data = (patient_id,)
            cursor.execute(delete_query, data)
            conn.commit()

            # Update the IDs to be sequential
            update_query = "SET @counter = 0;"
            cursor.execute(update_query)
            conn.commit()

            update_query = "UPDATE Patients SET id = @counter := @counter + 1;"
            cursor.execute(update_query)
            conn.commit()

            update_query = "ALTER TABLE Patients AUTO_INCREMENT = 1;"
            cursor.execute(update_query)
            conn.commit()

            # Fetch the data again after updating IDs
            populate_patient_tree(tree_tab1)

        e5_tab1.delete(0, END)
    def remove_patient(patient_id):

        if patient_id != '':
            # Delete the patient
            delete_query = "DELETE FROM Patients WHERE id = %s"
            data = (patient_id,)
            cursor.execute(delete_query, data)
            conn.commit()

            # Update the IDs to be sequential
            update_query = "SET @counter = 0;"
            cursor.execute(update_query)
            conn.commit()

            update_query = "UPDATE Patients SET id = @counter := @counter + 1;"
            cursor.execute(update_query)
            conn.commit()

            update_query = "ALTER TABLE Patients AUTO_INCREMENT = 1;"
            cursor.execute(update_query)
            conn.commit()

            # Fetch the data again after updating IDs
            populate_patient_tree(tree_tab1)

    def delete_past_deadline_records():
        global running_thread
        while running_thread:
            current_datetime = datetime.datetime.now()

            # Select all patient data from the Patients table
            select_query = "SELECT id, slot FROM Patients"
            cursor.execute(select_query)
            patients = cursor.fetchall()

            for patient in patients:
                slot_string = str(patient[1])  # Assuming the slot is at index 1
                slot_parts = slot_string.split('-')  # Split slot by '-'

                slot_day_time = slot_parts[0].split()  # Split day and time (e.g., ['Mon', '17:30'])
                slot_time = slot_parts[1]  # Extract the end time (e.g., '15:00')

                # Extract day and time from the slot
                slot_day = slot_day_time[0]  # Get the day from the slot

                # Compare current day and time with the slot day and end time
                current_day = current_datetime.strftime('%a')
                current_time = current_datetime.strftime('%H:%M')

                # Get the numerical representation of the current and slot days
                days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                current_day_index = days_of_week.index(current_day)
                slot_day_index = days_of_week.index(slot_day)

                if current_day_index > slot_day_index or (current_day_index == slot_day_index and current_time > slot_time):
                    remove_patient(patient[0])  # Invoke delete_patient with the ID to delete

            # Wait for a certain time period before checking again
            time.sleep(1) 
    def on_closing():
        global running_thread
        running_thread = False  # Set the flag to stop the background thread
        root.destroy()   # Close the main window
        delete_thread.join()
    def populate_patient_tree(tree):
        # Select all patient data from the Patients table
        select_query = "SELECT * FROM Patients"

        cursor.execute(select_query)
        patients = cursor.fetchall()

        for item in tree.get_children():
            tree.delete(item)
        for patient in patients:
            tree.insert("", "end", values=patient)

    def suggest_slots(event):
        selected_specialization = e2_tab1.get()

        if selected_specialization != 'Select Specialization':
            # Fetch available slots for the selected specialization from the Doctors table
            select_query = "SELECT slot FROM Doctors WHERE specialization = %s"
            cursor.execute(select_query, (selected_specialization,))
            slots = cursor.fetchall()
            available_slots = [slot[0].strip('{}') for slot in slots]
            # Display available slots in the slot entry Combobox
            e4_tab1['values'] = available_slots

    shift = 250
    Label(tab1, text="Name").place(x=10 + shift, y=10)
    e1_tab1 = Entry(tab1, width=30, bg="#FFFFFF")
    e1_tab1.place(x=120 + shift, y=10)

    Label(tab1, text="Specialization").place(x=10 + shift, y=40)
    e2_tab1 = ttk.Combobox(tab1, values=specializations, width=27)
    e2_tab1.place(x=120 + shift, y=40)
    e2_tab1.set("Select Specialization")  # Set a default value for the Combobox
    e2_tab1.bind("<<ComboboxSelected>>", suggest_slots)

    Label(tab1, text="Fees").place(x=10 + shift, y=70)
    e3_tab1 = Entry(tab1, width=30, bg="#FFFFFF")
    e3_tab1.place(x=120 + shift, y=70)

    Label(tab1, text="Slot").place(x=10 + shift, y=100)
    e4_tab1 = ttk.Combobox(tab1, width=27)  # Use ttk.Combobox for slot entry
    e4_tab1.place(x=120 + shift, y=100)

    Button(tab1, text="Add Patient", command=add_patient).place(x=10 + shift, y=130, width=300)

    Label(tab1,text="Delete Patient ID").place(x = 10 + shift, y = 160)
    e5_tab1 = Entry(tab1,width=30, bg="#FFFFFF")
    e5_tab1.place(x = 120 + shift,y = 160 )

    Button(tab1,text="Delete",command=delete_patient).place(x=10+shift,y=190,width=300)

    # Create a Treeview widget to display patient data
    tree_tab1 = ttk.Treeview(tab1, columns=("ID", "Name", "Specialization", "Fees", "Slot"), show="headings", height=10)
    tree_tab1.heading("ID", text="ID")
    tree_tab1.heading("Name", text="Name")
    tree_tab1.heading("Specialization", text="Specialization")
    tree_tab1.heading("Fees", text="Fees")
    tree_tab1.heading("Slot", text="Slot")

    # Set column widths
    tree_tab1.column("ID", width=50)
    tree_tab1.column("Name", width=160)
    tree_tab1.column("Specialization", width=160)
    tree_tab1.column("Fees", width=160)
    tree_tab1.column("Slot", width=170)

    # Set a specific height for the Treeview
    tree_tab1_height = 500
    tree_tab1.place(x=10, y=220, relwidth=1, height=tree_tab1_height)

    # Create a vertical scrollbar
    tree_scroll_y = ttk.Scrollbar(tab1, orient="vertical", command=tree_tab1.yview)
    tree_tab1.configure(yscroll=tree_scroll_y.set)
    tree_scroll_y.place(x= 780, y=220, height=tree_tab1_height)

    # Configure the Treeview to expand vertically
    tree_tab1.grid_propagate(False)

    # Populate the treeview initially
    populate_patient_tree(tree_tab1)
    delete_thread = threading.Thread(target=delete_past_deadline_records)
    delete_thread.daemon = True  # Daemonize the thread to terminate it when the main program exits
    delete_thread.start()

    # Tab 2 Doctors:
    def add_doctor():
        name = e1_tab2.get()
        specialization = e2_tab2.get()
        slot = e3_tab2.get()
        patients_per_slot = e4_tab2.get()  # Added field for Patients per Slot

        if name != '' and specialization != '' and slot != '' and patients_per_slot != '':
            insert_query = "INSERT INTO Doctors (name, specialization, slot, patients_per_slot) VALUES (%s, %s, %s, %s)"
            data = (name, specialization, slot, patients_per_slot)
            cursor.execute(insert_query, data)
            conn.commit()

        e1_tab2.delete(0, END)
        e2_tab2.set("Select Specialization")  # Reset Combobox to default
        e3_tab2.delete(0, END)
        e4_tab2.delete(0, END)
        populate_doctor_tree(tree_tab2)

    def delete_doctor():
        doctor_id = e5_tab2.get()  # Changed the entry number for deleting doctor

        if doctor_id != '':
            # Delete the doctor
            delete_query = "DELETE FROM Doctors WHERE id = %s"
            data = (doctor_id,)
            cursor.execute(delete_query, data)
            conn.commit()

            # Update the IDs to be sequential
            update_query = "SET @counter = 0;"
            cursor.execute(update_query)
            conn.commit()

            update_query = "UPDATE Doctors SET id = @counter := @counter + 1;"
            cursor.execute(update_query)
            conn.commit()

            update_query = "ALTER TABLE Doctors AUTO_INCREMENT = 1;"
            cursor.execute(update_query)
            conn.commit()

            # Fetch the data again after deletion
            populate_doctor_tree(tree_tab2)

        e5_tab2.delete(0, END)

    def populate_doctor_tree(tree):
        # Select all doctor data from the Doctors table
        select_query = "SELECT * FROM Doctors"

        cursor.execute(select_query)
        doctors = cursor.fetchall()

        for item in tree.get_children():
            tree.delete(item)
        for doctor in doctors:
            tree.insert("", "end", values=doctor)

    shift_tab2 = 250
    Label(tab2, text="Name").place(x=10 + shift_tab2, y=10)
    e1_tab2 = Entry(tab2, width=30, bg="#FFFFFF")
    e1_tab2.place(x=120 + shift_tab2, y=10)

    Label(tab2, text="Specialization").place(x=10 + shift_tab2, y=40)
    e2_tab2 = ttk.Combobox(tab2, values=specializations, width=27)
    e2_tab2.place(x=120 + shift_tab2, y=40)
    e2_tab2.set("Select Specialization")  # Set a default value for the Combobox

    Label(tab2, text="Slot").place(x=10 + shift_tab2, y=70)  # Updated label text
    e3_tab2 = Entry(tab2, width=30, bg="#FFFFFF")
    e3_tab2.place(x=120 + shift_tab2, y=70)

    Label(tab2, text="Patients per Slot").place(x=10 + shift_tab2, y=100)  # Added Patients per Slot label
    e4_tab2 = Entry(tab2, width=30, bg="#FFFFFF")
    e4_tab2.place(x=120 + shift_tab2, y=100)  # Adjusted position of Patients per Slot entry

    Button(tab2, text="Add Doctor", command=add_doctor).place(x=10 + shift_tab2, y=130, width=300)  # Adjusted position

    Label(tab2, text="Delete Doctor ID").place(x=10 + shift_tab2, y=160)  # Adjusted position
    e5_tab2 = Entry(tab2, width=30, bg="#FFFFFF")
    e5_tab2.place(x=150 + shift_tab2, y=160)  # Adjusted position

    Button(tab2, text="Delete", command=delete_doctor).place(x=10 + shift_tab2, y=190, width=300)  # Adjusted position

    # Create a Treeview widget to display doctor data
    tree_tab2 = ttk.Treeview(tab2, columns=("ID", "Name", "Specialization", "Slot", "Patients per Slot"), show="headings", height=10)
    tree_tab2.heading("ID", text="ID")
    tree_tab2.heading("Name", text="Name")
    tree_tab2.heading("Specialization", text="Specialization")
    tree_tab2.heading("Slot", text="Slot")  # Updated heading text
    tree_tab2.heading("Patients per Slot", text="Patients per Slot")  # Added Patients per Slot heading text

    # Set column widths
    tree_tab2.column("ID", width=50)
    tree_tab2.column("Name", width=75)
    tree_tab2.column("Specialization", width=75)
    tree_tab2.column("Slot", width=75)  # Adjusted width
    tree_tab2.column("Patients per Slot", width=75)  # Adjusted width

    # Set a specific height for the Treeview
    tree_tab2_height = 500
    tree_tab2.place(x=10, y=220, relwidth=1, height=tree_tab2_height)

    # Create a vertical scrollbar
    tree_scroll_y_tab2 = ttk.Scrollbar(tab2, orient="vertical", command=tree_tab2.yview)
    tree_tab2.configure(yscroll=tree_scroll_y_tab2.set)
    tree_scroll_y_tab2.place(x= 780, y=220, height=tree_tab2_height)

    # Configure the Treeview to expand vertically
    tree_tab2.grid_propagate(False)
    populate_doctor_tree(tree_tab2)

    # tab Appointments

    def get_appointment_data_by_specialization(specialization):
        appointment_data = []
        days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        if specialization:
            select_doctors_query = "SELECT name, slot, patients_per_slot FROM Doctors WHERE specialization = %s"
            cursor.execute(select_doctors_query, (specialization,))
            doctors = cursor.fetchall()
            doctors = [list(doctor) for doctor in doctors]
            doctors.sort(key=lambda x: (days_of_week.index(x[1].split()[0]),x[1].split()[1].split('-')[1]))

            select_patient_query = "SELECT id, name, specialization, fees, slot FROM Patients WHERE specialization = %s"
            cursor.execute(select_patient_query, (specialization,))
            patients = cursor.fetchall()
            patients.sort(reverse=True,key= lambda x:x[3])

            current_datetime = datetime.datetime.now()
            current_day = current_datetime.strftime("%a") 
            current_time = current_datetime.strftime("%H:%M")  
            current_day_index = days_of_week.index(current_day)
            for patient in patients:
                for i in range(len(doctors)):
                    if doctors[i][1] == patient[4]:
                        if doctors[i][2]:
                            appointment_data.append([patient[1],doctors[i][0],patient[3],doctors[i][1]])                            
                            doctors[i][2] -= 1
                            break
                        else:
                            l = i - 1; r = i + 1
                            while l >= 0:
                                slot_day_index, slot_end_time = days_of_week.index(doctors[l][1].split()[0]), doctors[l][1].split('-')[1]
                                if doctors[l][2] and (slot_day_index > current_day_index or (slot_day_index == current_day_index and slot_end_time > current_time)) :
                                    appointment_data.append([patient[1],doctors[l][0],patient[3],doctors[l][1]])
                                    doctors[l][2] -= 1
                                    r = len(doctors) + 1
                                l -= 1
                            while r < len(doctors):
                                if doctors[r][2]:
                                    appointment_data.append([patient[1],doctors[r][0],patient[3],doctors[r][1]])
                                    doctors[r][2] -= 1
                                    break
                                r += 1          
                        break

        appointment_data.sort(key=lambda x: (days_of_week.index(x[3].split()[0]),x[3].split()[1].split('-')[1]))
        return appointment_data


    def show_appointments_by_specialization():
        specialization = e_specialization.get()

        if specialization != '':
            # Clear the existing entries in the Treeview
            for item in tree_specialization.get_children():
                tree_specialization.delete(item)
            appointments_data = get_appointment_data_by_specialization(specialization)

            # Insert the filtered appointments into the Treeview
            for appointment in appointments_data:
                tree_specialization.insert("", "end", values=appointment)

    # Create a Combobox widget for specialization selection in Tab3
    Label(tab3, text="Specialization").place(x=10+250, y=10)
    e_specialization = ttk.Combobox(tab3, values=specializations, width=27)
    e_specialization.place(x=120+250, y=10)
    e_specialization.set("Select Specialization")  
    Button(tab3, text="Show Appointments", command=show_appointments_by_specialization).place(x=10+250, y=40, width=300)

    # Create a Treeview to display search results
    tree_specialization = ttk.Treeview(tab3, columns=("Name","Doctor","Fees", "Slot"), show="headings", height=10)
    tree_specialization.heading("Name", text="Name")
    tree_specialization.heading("Doctor", text="Doctor")
    tree_specialization.heading("Fees", text="Fees")
    tree_specialization.heading("Slot", text="Slot")

    # Set column widths
    tree_specialization.column("Name", width=160)
    tree_specialization.column("Doctor", width=160)
    tree_specialization.column("Fees", width=160)
    tree_specialization.column("Slot", width=170)

    # Set a specific height for the Treeview
    tree_specialization_height = 620
    tree_specialization.place(x=10, y=80, relwidth=1, height=tree_specialization_height)

    # Create a vertical scrollbar
    tree_scroll_y_specialization = ttk.Scrollbar(tab3, orient="vertical", command=tree_specialization.yview)
    tree_specialization.configure(yscroll=tree_scroll_y_specialization.set)
    tree_scroll_y_specialization.place(x=780, y=80, height=tree_specialization_height)

    # Configure the Treeview to expand vertically
    tree_specialization.grid_propagate(False)

    # tab4 Staffs
    def add_staff():
        name = e_name_staff.get()
        profession = e_profession_staff.get()
        working_day = e_working_day_staff.get()
        working_hour = e_hour_per_day.get()

        if name and profession and working_day and working_hour:
            insert_query = "INSERT INTO Staffs (Name, Profession, Working_Day, Working_hour) VALUES (%s, %s, %s, %s)"
            data = (name, profession, working_day, working_hour)
            cursor.execute(insert_query, data)
            conn.commit()

            
        e_name_staff.delete(0,END)
        e_profession_staff.set("Select Profession")
        e_working_day_staff.delete(0,END)
        e_hour_per_day.delete(0,END)
        populate_staff_tree(tree_staff)

    def delete_staff():
        staff_id = e_delete_staff.get()  # Changed the entry number for deleting doctor

        if staff_id:
            # Delete the doctor
            delete_query = "DELETE FROM Staffs WHERE id = %s"
            data = (staff_id,)
            cursor.execute(delete_query, data)
            conn.commit()

            # Update the IDs to be sequential
            update_query = "SET @counter = 0;"
            cursor.execute(update_query)
            conn.commit()

            update_query = "UPDATE Staffs SET id = @counter := @counter + 1;"
            cursor.execute(update_query)
            conn.commit()

            update_query = "ALTER TABLE Staffs AUTO_INCREMENT = 1;"
            cursor.execute(update_query)
            conn.commit()
            # Fetch the data again after deletion
            populate_staff_tree(tree_staff)

        e_delete_staff.delete(0, END)

    def populate_staff_tree(tree):
        select_query = "SELECT * FROM Staffs"
        cursor.execute(select_query)
        staffs = cursor.fetchall()

        for item in tree.get_children():
            tree.delete(item)
        for staff in staffs:
            tree.insert("", "end", values=staff)

    profession_options = [
    "Nurse",
    "Pharmacist",
    "Lab Technician",
    "Radiologist",
    "Physiotherapist",
    "Occupational Therapist",
    "Medical Technologist",
    "Medical Social Worker",
    "Dietitian",
    "Respiratory Therapist"]

    Label(tab4, text="Name").place(x=10 + shift, y=10)
    e_name_staff = Entry(tab4, width=30, bg="#FFFFFF")
    e_name_staff.place(x=120+ shift, y=10)

    Label(tab4,text="Profession").place(x=10+shift,y=40)
    e_profession_staff = ttk.Combobox(tab4, values=profession_options, width=27)
    e_profession_staff.place(x=120+ shift, y=40)
    e_profession_staff.set("Select Profession")

    Label(tab4, text="Working Day").place(x=10 + shift, y=70)
    e_working_day_staff = Entry(tab4, width=30, bg="#FFFFFF")
    e_working_day_staff.place(x=120+shift, y=70)

    Label(tab4,text="Hour Per Day").place(x=10+shift,y=100)
    e_hour_per_day = Entry(tab4, width=30, bg= "#FFFFFF")
    e_hour_per_day.place(x=120+shift, y = 100)

    Button(tab4, text="Add Staff", command=add_staff).place(x=10+shift, y=130, width=300)

    Label(tab4, text="Delete Staff ID").place(x=10 + shift, y=160)  # Adjusted position
    e_delete_staff = Entry(tab4, width=30, bg="#FFFFFF")
    e_delete_staff.place(x=120 + shift, y=160)  # Adjusted position

    Button(tab4, text="Delete", command=delete_staff).place(x=10 + shift, y=190, width=300)  # Adjusted position

    tree_staff = ttk.Treeview(tab4, columns=("ID", "Name", "Profession", "Working Day", "Working hour"), show="headings", height=10)
    tree_staff.heading("ID", text="ID")
    tree_staff.heading("Name", text="Name")
    tree_staff.heading("Profession", text="Profession")
    tree_staff.heading("Working Day", text="Working Day")
    tree_staff.heading("Working hour", text="Hours Per Day")

    # Set column widths
    tree_staff.column("ID", width=50)
    tree_staff.column("Name", width=160)
    tree_staff.column("Profession", width=160)
    tree_staff.column("Working Day", width=160)
    tree_staff.column("Working hour", width=160)


    tree_staff_height = 450
    tree_staff.place(x=10, y=250, relwidth=1, height=tree_staff_height)

    # Create a vertical scrollbar
    tree_scroll_y_staff = ttk.Scrollbar(tab4, orient="vertical", command=tree_staff.yview)
    tree_staff.configure(yscroll=tree_scroll_y_staff.set)
    tree_scroll_y_staff.place(x=780, y=250, height=tree_staff_height)
    tree_staff.grid_propagate(False)

    populate_staff_tree(tree=tree_staff)
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    notebook.pack(expand=True, fill="both")
    root.geometry("800x750")
    root.resizable(0, 0)
    root.mainloop()

    # Close the cursor and connection when done
    cursor.close()
    conn.close()