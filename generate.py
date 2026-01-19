import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

class EDDataGenerator:
    """Generate realistic Emergency Department data for Puurs Hospital"""
    
    def __init__(self, start_date='2020-01-01', end_date='2025-12-31'):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        
        # Reference data
        self.first_names = [
            'Emma', 'Lucas', 'Sophie', 'Thomas', 'Marie', 'Noah', 'Julie',
            'Arthur', 'Camille', 'Louis', 'Chloé', 'Victor', 'Nina', 'Alexander',
            'Sophia', 'Mohammed', 'Priya', 'Yuki', 'Zainab', 'Li', 'Ahmed',
            'Olga', 'Carlos', 'Kevin', 'Daniel'
        ]
        
        self.last_names = [
            'Janssen', 'Peeters', 'Maes', 'Jacobs', 'Willems', 'Dubois',
            'Lambert', 'Martin', 'Simon', 'Santos', 'Bailey', 'Rivera',
            'Kim', 'Hassan', 'Sharma', 'Tanaka', 'Omar', 'Wei', 'Farah',
            'Petrov', 'Garcia', 'Murphy', 'Cohen'
        ]
        
        self.diagnoses = [
            ('Intracranial Hemorrhage', 'Neurology', 1),
            ('Acute MI', 'Cardiology', 1),
            ('Sepsis', 'Infectious Disease', 1),
            ('Stroke', 'Neurology', 1),
            ('Respiratory Failure', 'Respiratory', 2),
            ('COPD Exacerbation', 'Respiratory', 2),
            ('Acute Gastroenteritis', 'Gastroenterology', 3),
            ('Acute Pancreatitis', 'Gastroenterology', 2),
            ('Electrolyte Disorder', 'General Practice', 3),
            ('Adrenal Crisis', 'Endocrinology', 2),
            ('Acute Arthritis', 'Orthopedics', 3),
            ('Fracture', 'Orthopedics', 3),
            ('Chest Pain', 'Cardiology', 3),
            ('Abdominal Pain', 'Gastroenterology', 3),
            ('Headache', 'Neurology', 3),
            ('Eye Trauma', 'Ophthalmology', 3),
            ('Laceration', 'General Practice', 4),
            ('UTI', 'Infectious Disease', 3),
            ('Pneumonia', 'Respiratory', 2),
            ('Asthma Exacerbation', 'Respiratory', 3),
            ('Cellulitis', 'Infectious Disease', 3),
            ('Minor Burn', 'General Practice', 4),
            ('Sprain', 'Orthopedics', 4),
            ('Viral Syndrome', 'General Practice', 4),
            ('Dehydration', 'General Practice', 3)
        ]
        
        self.races = [
            'White', 'African American', 'Two or More Races', 
            'Declined to Identify', 'Asian', 'Pacific Islander', 'Native American'
        ]
        
        self.insurance_types = ['Private', 'Public', 'None']
        
        # Staff roster
        self.staff = {
            'Consultants': [
                'Dr. Jan Vermeulen', 'Dr. Sophie Dubois', 'Dr. Marc Peeters',
                'Dr. Anna Claes', 'Dr. Peter Willems', 'Dr. Lisa Martens',
                'Dr. Erik Mertens', 'Dr. Sarah Wouters', 'Dr. Tom Jacobs',
                'Dr. Laura Hendrickx'
            ],
            'Registrars': [
                'Dr. Zainab Omar', 'Dr. Yuki Tanaka', 'Dr. Thomas Anderson',
                'Dr. Sofia Mendoza', 'Dr. Priya Sharma', 'Dr. Olga Petrov',
                'Dr. Nina Ivanova', 'Dr. Mohammed Hassan', 'Dr. Lucas Wright',
                'Dr. Li Wei', 'Dr. Kevin Murphy', 'Dr. Emma Thompson',
                'Dr. Daniel Cohen', 'Dr. Carlos Garcia', 'Dr. Ahmed Farah'
            ],
            'Medical Officers': [f'Dr. MO {i+1}' for i in range(20)],
            'Nurses': [f'Nurse {i+1}' for i in range(50)]
        }
        
        self.specialties = {
            'Acute Care': ['Dr. Zainab Omar', 'Dr. Thomas Anderson', 'Dr. Olga Petrov', 
                          'Dr. Nina Ivanova', 'Dr. Daniel Cohen', 'Dr. Carlos Garcia', 'Dr. Ahmed Farah'],
            'Emergency Medicine': ['Dr. Yuki Tanaka', 'Dr. Sofia Mendoza', 'Dr. Mohammed Hassan', 
                                  'Dr. Li Wei', 'Dr. Kevin Murphy'],
            'Pediatric Emergency': ['Dr. Priya Sharma', 'Dr. Lucas Wright', 'Dr. Emma Thompson']
        }
    
    def generate_patient_visits(self, n_visits=10000):
        """Generate patient visit records"""
        visits = []
        visit_id = 1
        
        current_date = self.start_date
        while current_date <= self.end_date:
            # Determine number of visits for this day (higher on weekdays, peaks at certain times)
            is_weekend = current_date.weekday() >= 5
            base_visits = np.random.poisson(8 if is_weekend else 12)
            
            for _ in range(base_visits):
                # Generate arrival time with realistic distribution
                hour_weights = [0.3]*7 + [0.8]*5 + [1.2]*5 + [1.5]*5 + [0.8]*2  # 24 hours
                arrival_hour = random.choices(range(24), weights=hour_weights)[0]
                arrival_minute = random.randint(0, 59)
                arrival_time = current_date.replace(hour=arrival_hour, minute=arrival_minute)
                
                # Patient demographics
                age = self._generate_age()
                gender = random.choice(['M', 'F', 'NC'])
                
                # Diagnosis and triage
                diagnosis, department, base_esi = random.choice(self.diagnoses)
                esi_level = max(1, min(5, base_esi + random.randint(-1, 1)))
                
                # Wait times based on ESI level
                door_to_doctor = self._generate_wait_time(esi_level)
                length_of_stay = self._generate_los(esi_level)
                
                # Outcomes
                lwbs = random.random() < 0.045  # 4.5% LWBS rate
                if lwbs:
                    outcome = 'LWBS'
                    satisfaction = random.randint(1, 3)
                else:
                    admit_prob = 0.7 if esi_level <= 2 else (0.4 if esi_level == 3 else 0.15)
                    outcome = 'Admitted' if random.random() < admit_prob else 'Discharged'
                    satisfaction = random.randint(3, 10) if outcome == 'Discharged' else random.randint(4, 9)
                
                # Other fields
                needs_labs = random.random() < 0.597
                needs_imaging = random.random() < 0.378
                needs_consult = random.random() < 0.284
                admin_flagged = random.random() < 0.497
                
                visit = {
                    'visit_id': f'V{visit_id:06d}',
                    'date': arrival_time.date(),
                    'arrival_time': arrival_time,
                    'patient_name': f"{random.choice(self.first_names)} {random.choice(self.last_names)}",
                    'age': age,
                    'gender': gender,
                    'race': random.choices(self.races, weights=[27, 20, 18, 12, 12, 6, 5])[0],
                    'diagnosis': diagnosis,
                    'department': department,
                    'esi_level': esi_level,
                    'door_to_doctor_mins': door_to_doctor,
                    'length_of_stay_mins': length_of_stay,
                    'satisfaction_score': satisfaction,
                    'outcome': outcome,
                    'insurance_type': random.choices(self.insurance_types, weights=[38.2, 51.6, 10.1])[0],
                    'needs_labs': needs_labs,
                    'needs_imaging': needs_imaging,
                    'needs_consult': needs_consult,
                    'admin_flagged': admin_flagged,
                    'lwbs': lwbs
                }
                
                visits.append(visit)
                visit_id += 1
            
            current_date += timedelta(days=1)
        
        return pd.DataFrame(visits)
    
    def generate_staff_hours(self, visits_df):
        """Generate staff hours worked based on visit data"""
        staff_records = []
        
        # Group visits by week
        visits_df['week'] = visits_df['date'].apply(lambda x: pd.Timestamp(x).isocalendar()[1])
        visits_df['year'] = visits_df['date'].apply(lambda x: pd.Timestamp(x).year)
        
        for specialty, doctors in self.specialties.items():
            for doctor in doctors:
                for year in visits_df['year'].unique():
                    for week in visits_df[visits_df['year'] == year]['week'].unique():
                        # Varying hours per week (some doctors work more)
                        base_hours = random.choice([6, 12, 18, 24, 30, 36])
                        hours = base_hours + random.randint(-2, 2)
                        
                        staff_records.append({
                            'staff_name': doctor,
                            'role': 'Registrar',
                            'specialty': specialty,
                            'year': year,
                            'week': week,
                            'hours_worked': max(0, hours)
                        })
        
        return pd.DataFrame(staff_records)
    
    def generate_referrals(self, visits_df):
        """Generate referral data"""
        referrals = []
        
        referral_depts = [
            'None', 'General Practice', 'Orthopedics', 'Physiotherapy',
            'Cardiology', 'Neurology', 'Gastroenterology', 'Renal',
            'Psychiatry', 'Infectious Disease'
        ]
        
        weights = [59, 20, 10, 3, 3, 2, 2, 1, 0.5, 0.5]
        
        for _, visit in visits_df.iterrows():
            if visit['outcome'] == 'Discharged':
                referral_dept = random.choices(referral_depts, weights=weights)[0]
                
                referrals.append({
                    'visit_id': visit['visit_id'],
                    'date': visit['date'],
                    'referral_department': referral_dept
                })
        
        return pd.DataFrame(referrals)
    
    def _generate_age(self):
        """Generate age with realistic distribution"""
        age_groups = [(0, 17), (18, 44), (45, 64), (65, 95)]
        weights = [49, 45, 43, 64]
        age_range = random.choices(age_groups, weights=weights)[0]
        return random.randint(age_range[0], age_range[1])
    
    def _generate_wait_time(self, esi_level):
        """Generate door-to-doctor time based on ESI level"""
        # ESI 1 should be fastest, ESI 5 slowest
        base_times = {1: 5, 2: 30, 3: 60, 4: 90, 5: 120}
        base = base_times.get(esi_level, 60)
        return max(1, int(np.random.exponential(base) + np.random.normal(40, 30)))
    
    def _generate_los(self, esi_level):
        """Generate length of stay based on ESI level"""
        # More critical cases stay longer
        base_los = {1: 600, 2: 500, 3: 400, 4: 300, 5: 200}
        base = base_los.get(esi_level, 400)
        return max(30, int(np.random.exponential(base/2) + np.random.normal(200, 150)))
    
    def generate_all_data(self, output_dir='data'):
        """Generate all datasets and save to CSV"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print("Generating patient visits...")
        visits_df = self.generate_patient_visits()
        visits_df.to_csv(f'{output_dir}/patient_visits.csv', index=False)
        print(f"Generated {len(visits_df)} patient visits")
        
        print("\nGenerating staff hours...")
        staff_df = self.generate_staff_hours(visits_df)
        staff_df.to_csv(f'{output_dir}/staff_hours.csv', index=False)
        print(f"Generated {len(staff_df)} staff records")
        
        print("\nGenerating referrals...")
        referrals_df = self.generate_referrals(visits_df)
        referrals_df.to_csv(f'{output_dir}/referrals.csv', index=False)
        print(f"Generated {len(referrals_df)} referrals")
        
        print("\n✓ All data generated successfully!")
        
        # summary statistics
        print("\n=== DATA SUMMARY ===")
        print(f"Date Range: {visits_df['date'].min()} to {visits_df['date'].max()}")
        print(f"Total Visits: {len(visits_df)}")
        print(f"Admission Rate: {(visits_df['outcome'] == 'Admitted').sum() / len(visits_df) * 100:.1f}%")
        print(f"LWBS Rate: {visits_df['lwbs'].sum() / len(visits_df) * 100:.2f}%")
        print(f"Avg Door-to-Doctor: {visits_df['door_to_doctor_mins'].mean():.1f} mins")
        print(f"Avg Length of Stay: {visits_df['length_of_stay_mins'].mean():.1f} mins")
        print(f"Avg Satisfaction: {visits_df['satisfaction_score'].mean():.1f}/10")
        
        return visits_df, staff_df, referrals_df


# Generate the data
if __name__ == "__main__":
    generator = EDDataGenerator(start_date='2020-01-01', end_date='2025-12-31')
    visits_df, staff_df, referrals_df = generator.generate_all_data()