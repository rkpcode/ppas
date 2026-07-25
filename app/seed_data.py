import os
from datetime import date, timedelta
from app.core.database import SessionLocal, engine, Base
from app.models.medicine import Medicine, Batch
from app.models.customer import Customer
from app.models.supplier import Supplier
from app.models.staff import Staff
import app.models  # Ensure all models are registered
from app.services.auth_service import get_password_hash

def seed_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        if db.query(Staff).first():
            print("Database already seeded.")
            return

        print("Seeding staff...")
        staff1 = Staff(name="Rahul Pradhan", username="rahul.owner", hashed_password=get_password_hash("password123"), role="owner")
        staff2 = Staff(name="Sneha Das", username="sneha.pharm", hashed_password=get_password_hash("password123"), role="pharmacist")
        staff3 = Staff(name="Amit Kumar", username="amit.staff", hashed_password=get_password_hash("password123"), role="staff")
        db.add_all([staff1, staff2, staff3])
        
        print("Seeding suppliers...")
        sup1 = Supplier(name="Odisha Pharma Distributors", contact_phone="+919876543210")
        sup2 = Supplier(name="Kalinga Medical Supply", contact_phone="+918765432109")
        db.add_all([sup1, sup2])
        
        print("Seeding customers...")
        customers = [
            Customer(name="Priyanka Mohanty", phone="+919012345678", address="Bhubaneswar"),
            Customer(name="Rakesh Jena", phone="+919012345679", address="Cuttack"),
            Customer(name="Subrat Sahoo", phone="+919012345680", address="Puri"),
            Customer(name="Archana Nayak", phone="+919012345681", address="Balasore"),
            Customer(name="Sandeep Mishra", phone="+919012345682", address="Berhampur")
        ]
        db.add_all(customers)
        
        print("Seeding medicines...")
        medicines_data = [
            ("Crocin 500mg", "Paracetamol", "GSK", "Pain Relief", 15.50, False),
            ("Dolo 650mg", "Paracetamol", "Micro Labs", "Pain Relief", 30.00, False),
            ("Pan-D", "Pantoprazole + Domperidone", "Alkem", "Antacid", 120.00, False),
            ("Augmentin 625 Duo", "Amoxicillin + Clavulanic Acid", "GSK", "Antibiotic", 200.00, True),
            ("Azithral 500", "Azithromycin", "Alembic", "Antibiotic", 119.50, True),
            ("Allegra 120mg", "Fexofenadine", "Sanofi", "Antiallergic", 215.00, False),
            ("Amlokind-AT", "Amlodipine + Atenolol", "Mankind", "Anti-Hypertensive", 45.00, True),
            ("Calpol 500mg", "Paracetamol", "GSK", "Pain Relief", 14.50, False),
            ("Combiflam", "Ibuprofen + Paracetamol", "Sanofi", "Pain Relief", 35.00, False),
            ("Thyronorm 50mcg", "Thyroxine", "Abbott", "Hormone", 140.00, False),
            ("Shelcal 500", "Calcium + Vitamin D3", "Torrent", "Supplement", 115.00, False),
            ("Telma 40", "Telmisartan", "Glenmark", "Anti-Hypertensive", 220.00, True),
            ("Ecosprin 75", "Aspirin", "USV", "Blood Thinner", 5.50, False),
            ("Becosules", "Multivitamin", "Pfizer", "Supplement", 45.00, False),
            ("Cheston Cold", "Cetirizine + Paracetamol", "Cipla", "Cold", 45.00, False),
            ("Aciloc 150", "Ranitidine", "Cadila", "Antacid", 40.00, False),
            ("Levocet M", "Levocetirizine + Montelukast", "Hetero", "Antiallergic", 180.00, False),
            ("Okacet", "Cetirizine", "Cipla", "Antiallergic", 20.00, False),
            ("Voveran SR 100", "Diclofenac", "Novartis", "Pain Relief", 110.00, False),
            ("Gelusil MPS", "Antacid", "Pfizer", "Antacid", 125.00, False),
            ("O2", "Ofloxacin + Ornidazole", "Medley", "Antibiotic", 150.00, True),
            ("Taxim-O 200", "Cefixime", "Alkem", "Antibiotic", 160.00, True),
            ("Montek LC", "Montelukast + Levocetirizine", "Sun Pharma", "Antiallergic", 195.00, False),
            ("Deriphyllin", "Etofylline + Theophylline", "Zydus", "Asthma", 25.00, False),
            ("Ascoril LS", "Ambroxol + Levosalbutamol", "Glenmark", "Cough Syrup", 110.00, False),
            ("Corex DX", "Dextromethorphan + Chlorpheniramine", "Pfizer", "Cough Syrup", 130.00, False),
            ("Evion 400", "Vitamin E", "Merck", "Supplement", 35.00, False),
            ("Zinetac 150", "Ranitidine", "GSK", "Antacid", 30.00, False),
            ("Omez 20", "Omeprazole", "Dr Reddy", "Antacid", 55.00, False),
            ("Pudin Hara", "Mentha Piperita", "Dabur", "Digestion", 45.00, False)
        ]
        
        for name, gen, mfr, cat, price, is_sch in medicines_data:
            med = Medicine(name=name, generic_name=gen, manufacturer=mfr, category=cat, unit_price=price, is_schedule_h=is_sch)
            b1 = Batch(batch_number=f"B_{name[:3].upper()}1", quantity=50, expiry_date=date.today() + timedelta(days=365))
            b2 = Batch(batch_number=f"B_{name[:3].upper()}2", quantity=20, expiry_date=date.today() + timedelta(days=20))
            med.batches.extend([b1, b2])
            db.add(med)
            
        db.commit()
        print("Database seeded successfully.")
    except Exception as e:
        print(f"Error seeding db: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
