import random
from datetime import datetime, timedelta, time
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, Admin, Doctor, Patient, Department, Appointment, DoctorAvailability, Treatment

# --- DATA POOLS ---
DEPT_NAMES = [
    ("Cardiology", "Heart & Vascular care"),
    ("Neurology", "Brain & Nervous system"),
    ("Orthopedics", "Bone & Joint specialists"),
    ("Pediatrics", "Child healthcare"),
    ("Dermatology", "Skin, Hair & Nails"),
    ("General Medicine", "Primary care & Checkups")
]

DOC_NAMES = [
    "Dr. Gregory House", "Dr. Stephen Strange", "Dr. Meredith Grey", "Dr. Derek Shepherd",
    "Dr. Cristina Yang", "Dr. John Watson", "Dr. Leonard McCoy", "Dr. Dana Scully",
    "Dr. Doogie Howser", "Dr. Michaela Quinn", "Dr. Frasier Crane", "Dr. Hannibal Lecter"
]

PATIENT_NAMES = [
    "John Doe", "Jane Smith", "Alice Johnson", "Bob Brown", "Charlie Davis",
    "Diana Prince", "Evan Wright", "Fiona Shrek", "George Martin", "Hannah Abbott",
    "Ian Malcolm", "Julia Roberts", "Kevin Bacon", "Laura Croft", "Michael Scott",
    "Nancy Wheeler", "Oscar Martinez", "Pam Beesly", "Quentin Tarantino", "Rachel Green",
    "Steve Rogers", "Tony Stark", "Bruce Wayne", "Clark Kent", "Peter Parker",
    "Natasha Romanoff", "Wanda Maximoff", "Vision", "Sam Wilson", "Bucky Barnes",
    "Loki Laufeyson", "Thor Odinson", "Clint Barton", "Kate Bishop", "Yelena Belova",
    "Matt Murdock", "Jessica Jones", "Luke Cage", "Danny Rand", "Frank Castle"
]

DIAGNOSES = [
    ("Migraine", "Sumatriptan 50mg", "Avoid bright lights.", "Neurology"),
    ("Hypertension", "Lisinopril 10mg", "Reduce salt intake.", "Cardiology"),
    ("Acne Vulgaris", "Benzoyl Peroxide", "Apply nightly.", "Dermatology"),
    ("Fractured Radius", "Cast application", "Keep dry for 6 weeks.", "Orthopedics"),
    ("Common Cold", "Rest & Fluids", "Isolate for 3 days.", "General Medicine"),
    ("Chickenpox", "Calamine Lotion", "Avoid scratching.", "Pediatrics"),
    ("Anxiety", "Therapy sessions", "Practice mindfulness.", "Neurology"),
    ("Arrhythmia", "Beta Blockers", "Monitor heart rate.", "Cardiology")
]

def seed_data():
    with app.app_context():
        print("--- WAPING OLD DATA & CREATING TABLES ---")
        db.drop_all()
        db.create_all()

        # 1. Create Admin
        print("Creating Admin...")
        pw = generate_password_hash('12345', method='pbkdf2:sha256')
        admin_user = User(username='admin', password=pw, role='admin')
        db.session.add(admin_user)
        db.session.commit()
        
        admin_profile = Admin(user_id=admin_user.id, full_name="Super Administrator")
        db.session.add(admin_profile)
        db.session.commit()

        # 2. Create Departments
        print("Creating Departments...")
        depts = []
        for name, desc in DEPT_NAMES:
            d = Department(name=name, description=desc)
            db.session.add(d)
            depts.append(d)
        db.session.commit()

        # 3. Create Doctors
        print("Creating Doctors...")
        doctors = []
        for i, name in enumerate(DOC_NAMES):
            # Assign to departments in round-robin fashion
            dept = depts[i % len(depts)]
            username = name.split()[1].lower() + str(i) # e.g. house0, strange1
            
            u = User(username=username, password=pw, role='doctor')
            db.session.add(u)
            db.session.commit()
            
            doc = Doctor(
                user_id=u.id, 
                full_name=name, 
                department_id=dept.id, 
                qualification=f"MD {dept.name}"
            )
            db.session.add(doc)
            db.session.commit() # <--- FIXED: Commit here to generate doc.id
            doctors.append(doc)
            
            # Add Availability (M/W/F or T/T/S)
            is_mwf = i % 2 == 0
            days = ["Monday", "Wednesday", "Friday"] if is_mwf else ["Tuesday", "Thursday", "Saturday"]
            start_h = 9 if is_mwf else 14
            
            for day in days:
                slot = DoctorAvailability(
                    doctor_id=doc.id,
                    day_of_week=day,
                    start_time=time(start_h, 0),
                    end_time=time(start_h + 4, 0) # 4 hour shift
                )
                db.session.add(slot)
        
        db.session.commit()

        # 4. Create Patients
        print("Creating Patients...")
        patients = []
        for i, name in enumerate(PATIENT_NAMES):
            username = f"patient{i}"
            u = User(username=username, password=pw, role='patient')
            db.session.add(u)
            db.session.commit()
            
            pat = Patient(
                user_id=u.id, 
                full_name=name, 
                phone=f"98765{i:05d}", 
                age=random.randint(18, 80),
                address=f"Apartment {i}, City Center"
            )
            db.session.add(pat)
            patients.append(pat)
        
        db.session.commit()

        # 5. Create Appointments & Treatments
        print("Generating Appointments (This may take a second)...")
        today = datetime.now().date()
        
        # A. Past Appointments (Completed)
        for _ in range(200): # Create 200 past records
            pat = random.choice(patients)
            doc = random.choice(doctors)
            days_ago = random.randint(1, 90)
            appt_date = today - timedelta(days=days_ago)
            
            appt = Appointment(
                patient_id=pat.id,
                doctor_id=doc.id,
                date_scheduled=appt_date,
                time_scheduled=time(random.randint(9, 17), 0),
                status='Completed'
            )
            db.session.add(appt)
            db.session.commit() # Commit to get ID
            
            # Add Treatment
            relevant_diag = [d for d in DIAGNOSES if d[3] == doc.department.name]
            if not relevant_diag: relevant_diag = DIAGNOSES
            
            diag_data = random.choice(relevant_diag)
            
            treat = Treatment(
                appointment_id=appt.id,
                diagnosis=diag_data[0],
                prescription=diag_data[1],
                notes=diag_data[2],
                visit_type=random.choice(["In-person", "Online"]),
                tests_done=random.choice(["None", "Blood Pressure", "X-Ray", "MRI"]) if random.random() > 0.7 else "None"
            )
            db.session.add(treat)

        # B. Future Appointments (Scheduled)
        for _ in range(50): # Create 50 upcoming
            pat = random.choice(patients)
            doc = random.choice(doctors)
            days_future = random.randint(1, 14)
            appt_date = today + timedelta(days=days_future)
            
            appt = Appointment(
                patient_id=pat.id,
                doctor_id=doc.id,
                date_scheduled=appt_date,
                time_scheduled=time(random.randint(9, 17), 0),
                status='Scheduled'
            )
            db.session.add(appt)

        db.session.commit()
        print("--- BIG DATA SEEDED SUCCESSFULLY! ---")
        print(f"Stats: {len(depts)} Depts, {len(doctors)} Docs, {len(patients)} Patients, ~250 Appts")

if __name__ == "__main__":
    seed_data()