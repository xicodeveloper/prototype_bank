"""
Life Event Detector - Identifies major life changes from transaction patterns.
Detects: job changes, relocations, travel events
"""

import pandas as pd
from datetime import timedelta
from collections import defaultdict


class LifeEventDetector:
    """Detect significant life events from transaction patterns."""
    
    def __init__(self, sensitivity='medium'):
        """
        Initialize detector.
        
        Args:
            sensitivity: 'low', 'medium', or 'high' - affects detection thresholds
        """
        self.sensitivity = sensitivity
        self.events = []
        
    def detect_job_change(self, df):
        """Detect potential job changes from income patterns."""
        events = []
        
        # Look for income sources
        income_df = df[df['type'] == 'deposit'].copy()
        income_df = income_df[income_df['category'] == 'Income']
        
        # Group by merchant (employer)
        employer_changes = []
        employers = income_df['merchant'].unique()
        
        if len(employers) > 1:
            for i, employer in enumerate(employers):
                employer_txns = income_df[income_df['merchant'] == employer]
                first_payment = employer_txns['date'].min()
                last_payment = employer_txns['date'].max()
                
                if i > 0:
                    events.append({
                        'event_type': 'job_change',
                        'date': first_payment,
                        'confidence': 0.85,
                        'details': {
                            'new_employer': employer,
                            'previous_employer': employers[i-1],
                            'first_payment_date': first_payment,
                            'income_change': self._calculate_income_change(
                                income_df, employers[i-1], employer
                            )
                        },
                        'message': f'Potential job change detected: New income source from {employer}'
                    })
        
        return events
    
    def _calculate_income_change(self, income_df, old_employer, new_employer):
        """Calculate income change between employers."""
        old_avg = income_df[income_df['merchant'] == old_employer]['amount'].mean()
        new_avg = income_df[income_df['merchant'] == new_employer]['amount'].mean()
        
        if old_avg and new_avg:
            change_pct = ((new_avg - old_avg) / old_avg) * 100
            return round(change_pct, 2)
        return None
    
    def detect_relocation(self, df):
        """Detect potential relocations from transaction patterns."""
        events = []
        
        # Look for moving-related keywords
        moving_keywords = ['mover', 'moving', 'relocation', 'truck rental', 'u-haul', 'pods']
        utility_setup_keywords = ['setup', 'activation', 'new service', 'installation']
        
        moving_txns = df[
            df['description'].str.lower().str.contains('|'.join(moving_keywords), na=False)
        ]
        
        for _, txn in moving_txns.iterrows():
            # Look for corroborating evidence within 30 days
            window_start = txn['date'] - timedelta(days=7)
            window_end = txn['date'] + timedelta(days=30)
            window_df = df[(df['date'] >= window_start) & (df['date'] <= window_end)]
            
            # Check for security deposits
            security_deposits = window_df[
                (window_df['description'].str.contains('deposit', case=False, na=False)) &
                (window_df['amount'] < -1000)
            ]
            
            # Check for utility setups
            utility_setups = window_df[
                window_df['description'].str.lower().str.contains('|'.join(utility_setup_keywords), na=False)
            ]
            
            confidence = 0.6
            if len(security_deposits) > 0:
                confidence += 0.2
            if len(utility_setups) > 0:
                confidence += 0.15
            
            events.append({
                'event_type': 'relocation',
                'date': txn['date'],
                'confidence': min(confidence, 0.95),
                'details': {
                    'moving_charge': txn['amount'],
                    'moving_company': txn['merchant'],
                    'security_deposits_found': len(security_deposits),
                    'utility_setups_found': len(utility_setups)
                },
                'message': f'Potential relocation detected on {txn["date"].strftime("%Y-%m-%d")}'
            })
        
        return events
    
    def detect_travel(self, df):
        """Detect travel events from transaction patterns."""
        events = []
        
        # Travel-related keywords
        travel_keywords = ['airline', 'flight', 'hotel', 'resort', 'hostel', 
                          'airbnb', 'booking.com', 'expedia', 'travel insurance']
        
        # Look for foreign transactions (check if location column exists and has data)
        has_location = 'location' in df.columns
        
        # Look for travel merchant patterns
        travel_txns = df[
            df['description'].str.lower().str.contains('|'.join(travel_keywords), na=False) |
            (df['category'] == 'Travel')
        ]
        
        # Group nearby travel transactions
        if len(travel_txns) > 0:
            travel_txns = travel_txns.sort_values('date')
            
            # Simple clustering by date proximity
            trips = []
            current_trip = []
            
            for idx, txn in travel_txns.iterrows():
                if not current_trip:
                    current_trip.append(txn)
                else:
                    last_date = current_trip[-1]['date']
                    if (txn['date'] - last_date).days <= 30:
                        current_trip.append(txn)
                    else:
                        if len(current_trip) >= 1:
                            trips.append(current_trip)
                        current_trip = [txn]
            
            if current_trip:
                trips.append(current_trip)
            
            # Create events for each trip
            for trip in trips:
                trip_df = pd.DataFrame(trip)
                total_spent = abs(trip_df['amount'].sum())
                start_date = trip_df['date'].min()
                end_date = trip_df['date'].max()
                
                # Check for foreign location
                destination = None
                if 'location' in trip_df.columns:
                    locations = trip_df['location'].dropna()
                    if len(locations) > 0:
                        destination = locations.iloc[0]
                
                confidence = 0.7
                if destination:
                    confidence += 0.2
                if total_spent > 500:
                    confidence += 0.1
                
                # Extract merchant names for better context
                merchants = trip_df['merchant'].unique().tolist() if 'merchant' in trip_df.columns else []
                
                # Create descriptive message
                if destination:
                    message = f'Travel to {destination}: {start_date.strftime("%Y-%m-%d")} - {end_date.strftime("%Y-%m-%d")}'
                else:
                    message = f'Travel detected: {start_date.strftime("%Y-%m-%d")} - {end_date.strftime("%Y-%m-%d")}'
                
                events.append({
                    'event_type': 'travel',
                    'date': start_date,
                    'confidence': min(confidence, 0.95),
                    'details': {
                        'start_date': start_date,
                        'end_date': end_date,
                        'duration_days': (end_date - start_date).days,
                        'total_spent': round(total_spent, 2),
                        'num_transactions': len(trip),
                        'destination': destination,
                        'merchants': merchants[:3] if len(merchants) > 0 else None  # Top 3 merchants
                    },
                    'message': message
                })
        
        return events
    
    def analyze(self, transactions_df):
        """
        Analyze transactions for all life events.
        
        Args:
            transactions_df: DataFrame with transaction data
            
        Returns:
            List of detected events
        """
        df = transactions_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        all_events = []
        
        # Detect each type of life event
        all_events.extend(self.detect_job_change(df))
        all_events.extend(self.detect_relocation(df))
        all_events.extend(self.detect_travel(df))
        
        # Sort by date
        all_events.sort(key=lambda x: x['date'])
        
        self.events = all_events
        return all_events
    
    def get_summary(self):
        """Get summary of detected events."""
        if not self.events:
            return "No life events detected."
        
        summary = f"\n{'='*60}\nLIFE EVENT DETECTION SUMMARY\n{'='*60}\n"
        summary += f"Total events detected: {len(self.events)}\n\n"
        
        for i, event in enumerate(self.events, 1):
            summary += f"{i}. {event['event_type'].upper().replace('_', ' ')}\n"
            summary += f"   Date: {event['date'].strftime('%Y-%m-%d')}\n"
            summary += f"   Confidence: {event['confidence']*100:.1f}%\n"
            summary += f"   {event['message']}\n"
            
            if event['details']:
                summary += "   Details:\n"
                for key, value in event['details'].items():
                    if value is not None:
                        summary += f"   - {key.replace('_', ' ').title()}: {value}\n"
            summary += "\n"
        
        return summary


if __name__ == "__main__":
    from transaction_generator import TransactionGenerator
    
    generator = TransactionGenerator()
    df = generator.generate_dataset(include_life_events=True, include_stress=False)
    
    detector = LifeEventDetector()
    events = detector.analyze(df)
    
    print(detector.get_summary())
