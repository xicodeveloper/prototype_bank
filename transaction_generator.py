"""
Synthetic transaction data generator for testing detectors.
Simulates realistic banking transactions with various patterns.
"""

import random
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd

fake = Faker()


class TransactionGenerator:
    """Generate realistic synthetic transaction data."""
    
    def __init__(self, seed=None):
        if seed is not None:
            random.seed(seed)
            Faker.seed(seed)
        
    def generate_normal_transactions(self, start_date, num_days=90):
        """Generate normal day-to-day transactions."""
        transactions = []
        current_date = start_date
        
        for day in range(num_days):
            # Salary deposit (bi-weekly)
            if day % 14 == 0:
                transactions.append({
                    'date': current_date,
                    'description': 'ACME Corp Payroll Deposit',
                    'amount': 2500.00,
                    'category': 'Income',
                    'merchant': 'ACME Corp',
                    'type': 'deposit'
                })
            
            # Regular expenses (60% of days)
            if random.random() < 0.6:
                # Groceries
                if random.random() < 0.4:
                    transactions.append({
                        'date': current_date,
                        'description': f'{fake.company()} Supermarket',
                        'amount': -round(random.uniform(30, 120), 2),
                        'category': 'Groceries',
                        'merchant': fake.company(),
                        'type': 'purchase'
                    })
                
                # Utilities (monthly)
                if day % 30 == 15:
                    for utility in ['Electric Company', 'Water Utility', 'Internet Provider']:
                        transactions.append({
                            'date': current_date,
                            'description': f'{utility} Payment',
                            'amount': -round(random.uniform(50, 150), 2),
                            'category': 'Utilities',
                            'merchant': utility,
                            'type': 'bill_payment'
                        })
                
                # Rent (monthly)
                if day % 30 == 1:
                    transactions.append({
                        'date': current_date,
                        'description': 'Rent Payment',
                        'amount': -1200.00,
                        'category': 'Housing',
                        'merchant': 'Property Management',
                        'type': 'bill_payment'
                    })
                
                # Coffee/restaurants
                if random.random() < 0.5:
                    transactions.append({
                        'date': current_date,
                        'description': f'{fake.company()} Cafe',
                        'amount': -round(random.uniform(5, 45), 2),
                        'category': 'Dining',
                        'merchant': fake.company(),
                        'type': 'purchase'
                    })
            
            current_date += timedelta(days=1)
        
        return transactions
    
    def inject_life_events(self, transactions, start_date):
        """Inject life event indicators into transactions."""
        life_events = []
        
        # Random companies and amounts for more variety
        old_company = random.choice(['ACME Corp', 'GlobalTech Inc', 'TechCorp', 'DataSystems LLC'])
        new_company = random.choice(['TechStart Inc', 'InnovateCo', 'FutureWorks', 'NextGen Solutions'])
        old_salary = round(random.uniform(2200, 2800), 2)
        new_salary = round(random.uniform(2800, 3500), 2)
        
        # Job change (random day between 40-50)
        job_change_day = random.randint(40, 50)
        job_change_date = start_date + timedelta(days=job_change_day)
        life_events.extend([
            {
                'date': job_change_date - timedelta(days=2),
                'description': f'Final paycheck - {old_company}',
                'amount': old_salary,
                'category': 'Income',
                'merchant': old_company,
                'type': 'deposit'
            },
            {
                'date': job_change_date + timedelta(days=random.randint(5, 10)),
                'description': f'{new_company} Payroll Deposit',
                'amount': new_salary,
                'category': 'Income',
                'merchant': new_company,
                'type': 'deposit'
            }
        ])
        
        # Relocation (random day between 45-55)
        move_day = random.randint(45, 55)
        move_date = start_date + timedelta(days=move_day)
        moving_company = random.choice(['Swift Movers LLC', 'Quick Move Services', 'City Movers', 'RelocationPro'])
        apartment_name = random.choice(['New Apartments', 'Riverside Complex', 'Oak Street Residences', 'Metro Living'])
        moving_cost = round(random.uniform(350, 650), 2)
        deposit_amount = round(random.uniform(1800, 2600), 2)
        
        life_events.extend([
            {
                'date': move_date - timedelta(days=random.randint(2, 5)),
                'description': moving_company,
                'amount': -moving_cost,
                'category': 'Moving',
                'merchant': moving_company,
                'type': 'purchase'
            },
            {
                'date': move_date,
                'description': f'{apartment_name} - Security Deposit',
                'amount': -deposit_amount,
                'category': 'Housing',
                'merchant': apartment_name,
                'type': 'purchase'
            },
            {
                'date': move_date + timedelta(days=random.randint(1, 3)),
                'description': f'{random.choice(["City", "Metro", "Regional"])} Electric - New Service Setup',
                'amount': -round(random.uniform(50, 100), 2),
                'category': 'Utilities',
                'merchant': 'City Electric',
                'type': 'bill_payment'
            }
        ])
        
        # Travel (random day between 65-75)
        travel_day = random.randint(65, 75)
        travel_date = start_date + timedelta(days=travel_day)
        
        # Random destinations
        destinations = [
            ('Barcelona, Spain', 'Cafe Barcelona', 'SkyHigh Airlines', 'Coastal Resort Hotel'),
            ('Paris, France', 'Le Bistro Paris', 'Air France', 'Paris Grand Hotel'),
            ('Tokyo, Japan', 'Sushi House Tokyo', 'Japan Airlines', 'Tokyo Palace Hotel'),
            ('London, UK', 'The London Pub', 'British Airways', 'Westminster Hotel'),
            ('Rome, Italy', 'Trattoria Roma', 'Italian Airways', 'Roman Empire Hotel'),
            ('Cancun, Mexico', 'Beach Bar Cancun', 'AeroMexico', 'Paradise Resort'),
        ]
        
        destination = random.choice(destinations)
        city_location = destination[0]
        restaurant = destination[1]
        airline = destination[2]
        hotel = destination[3]
        
        flight_cost = round(random.uniform(450, 850), 2)
        hotel_cost = round(random.uniform(600, 1200), 2)
        
        life_events.extend([
            {
                'date': travel_date - timedelta(days=random.randint(10, 20)),
                'description': airline,
                'amount': -flight_cost,
                'category': 'Travel',
                'merchant': airline,
                'type': 'purchase',
                'location': None
            },
            {
                'date': travel_date - timedelta(days=random.randint(5, 12)),
                'description': hotel,
                'amount': -hotel_cost,
                'category': 'Travel',
                'merchant': hotel,
                'type': 'purchase',
                'location': city_location
            },
            {
                'date': travel_date,
                'description': f'Foreign Transaction - {restaurant}',
                'amount': -round(random.uniform(25, 65), 2),
                'category': 'Dining',
                'merchant': restaurant,
                'type': 'purchase',
                'location': city_location
            },
            {
                'date': travel_date + timedelta(days=random.randint(1, 3)),
                'description': f'{restaurant.split()[0]} Souvenir Shop',
                'amount': -round(random.uniform(40, 120), 2),
                'category': 'Shopping',
                'merchant': 'Local Shop',
                'type': 'purchase',
                'location': city_location
            }
        ])
        
        return transactions + life_events
    
    def inject_financial_stress(self, transactions, start_date):
        """Inject financial stress indicators into transactions."""
        stress_indicators = []
        
        # Late payment fees (random timing and amounts)
        stress_day = random.randint(55, 70)
        stress_date = start_date + timedelta(days=stress_day)
        bank_name = random.choice(['MegaBank', 'FirstBank', 'CityBank', 'National Trust'])
        
        late_fee = round(random.uniform(25, 40), 2)
        overdraft_fee = round(random.uniform(25, 35), 2)
        
        stress_indicators.extend([
            {
                'date': stress_date,
                'description': f'Late Payment Fee - Credit Card',
                'amount': -late_fee,
                'category': 'Fees',
                'merchant': bank_name,
                'type': 'fee'
            },
            {
                'date': stress_date + timedelta(days=random.randint(3, 7)),
                'description': 'Overdraft Fee',
                'amount': -overdraft_fee,
                'category': 'Fees',
                'merchant': bank_name,
                'type': 'fee'
            }
        ])
        
        # Multiple small ATM withdrawals (cash flow issues) - random count
        num_withdrawals = random.randint(6, 10)
        for i in range(num_withdrawals):
            stress_indicators.append({
                'date': stress_date + timedelta(days=i),
                'description': f'ATM Withdrawal #{random.randint(1000, 9999)}',
                'amount': -round(random.uniform(20, 60), 2),
                'category': 'ATM',
                'merchant': 'ATM',
                'type': 'withdrawal'
            })
        
        # Payday loan indicator (random company and amount)
        loan_company = random.choice(['QuickCash', 'FastMoney', 'CashAdvance Plus', 'PaydayNow'])
        loan_amount = round(random.uniform(300, 600), 2)
        
        stress_indicators.append({
            'date': stress_date + timedelta(days=random.randint(8, 14)),
            'description': f'{loan_company} Advance',
            'amount': loan_amount,
            'category': 'Loan',
            'merchant': loan_company,
            'type': 'deposit'
        })
        
        return transactions + stress_indicators
    
    def generate_dataset(self, include_life_events=True, include_stress=True, num_days=90):
        """Generate complete dataset with optional life events and stress indicators."""
        start_date = datetime.now() - timedelta(days=num_days)
        
        # Base transactions
        transactions = self.generate_normal_transactions(start_date, num_days)
        
        # Add life events
        if include_life_events:
            transactions = self.inject_life_events(transactions, start_date)
        
        # Add financial stress
        if include_stress:
            transactions = self.inject_financial_stress(transactions, start_date)
        
        # Convert to DataFrame and sort by date
        df = pd.DataFrame(transactions)
        df = df.sort_values('date').reset_index(drop=True)
        
        # Add transaction ID
        df.insert(0, 'transaction_id', range(1, len(df) + 1))
        
        return df


if __name__ == "__main__":
    # Demo
    generator = TransactionGenerator()
    df = generator.generate_dataset()
    print(f"Generated {len(df)} transactions")
    print(df.head(10))
