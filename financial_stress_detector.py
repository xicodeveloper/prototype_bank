"""
Financial Stress Detector - Identifies risky financial patterns.
Detects: late payments, overdrafts, cash flow issues, declining balances
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from collections import defaultdict


class FinancialStressDetector:
    """Detect financial stress indicators from transaction patterns."""
    
    def __init__(self, sensitivity='medium'):
        """
        Initialize detector.
        
        Args:
            sensitivity: 'low', 'medium', or 'high' - affects detection thresholds
        """
        self.sensitivity = sensitivity
        self.thresholds = self._set_thresholds(sensitivity)
        self.stress_indicators = []
        
    def _set_thresholds(self, sensitivity):
        """Set detection thresholds based on sensitivity."""
        base = {
            'small_withdrawal_threshold': 60,
            'small_withdrawal_count': 6,
            'small_withdrawal_days': 14,
            'declining_balance_months': 2,
            'balance_decline_pct': 20,
            'high_fee_threshold': 50
        }
        
        if sensitivity == 'high':
            base['small_withdrawal_count'] = 4
            base['balance_decline_pct'] = 15
        elif sensitivity == 'low':
            base['small_withdrawal_count'] = 8
            base['balance_decline_pct'] = 30
            
        return base
    
    def detect_late_payment_fees(self, df):
        """Detect late payment and overdraft fees."""
        indicators = []
        
        # Look for fee transactions
        fee_keywords = ['late payment', 'late fee', 'overdraft', 'nsf', 
                       'insufficient funds', 'returned payment']
        
        fee_txns = df[
            (df['type'] == 'fee') |
            df['description'].str.lower().str.contains('|'.join(fee_keywords), na=False)
        ]
        
        if len(fee_txns) > 0:
            total_fees = abs(fee_txns['amount'].sum())
            
            # Group fees by type
            overdraft_fees = fee_txns[
                fee_txns['description'].str.contains('overdraft', case=False, na=False)
            ]
            late_payment_fees = fee_txns[
                fee_txns['description'].str.contains('late', case=False, na=False)
            ]
            
            severity = 'low'
            if total_fees > self.thresholds['high_fee_threshold']:
                severity = 'medium'
            if len(fee_txns) >= 3:
                severity = 'high'
            
            indicators.append({
                'indicator_type': 'late_payment_fees',
                'severity': severity,
                'date_range': (fee_txns['date'].min(), fee_txns['date'].max()),
                'details': {
                    'total_fees': round(total_fees, 2),
                    'num_fees': len(fee_txns),
                    'overdraft_fees': len(overdraft_fees),
                    'late_payment_fees': len(late_payment_fees),
                    'fee_list': fee_txns[['date', 'description', 'amount']].to_dict('records')
                },
                'message': f'  {len(fee_txns)} late payment/overdraft fee(s) detected (${total_fees:.2f} total)',
                'recommendation': 'Consider setting up automatic payments to avoid late fees.'
            })
        
        return indicators
    
    def detect_frequent_small_withdrawals(self, df):
        """Detect patterns of frequent small ATM withdrawals (cash flow issues)."""
        indicators = []
        
        # Look for ATM withdrawals
        atm_txns = df[
            (df['type'] == 'withdrawal') |
            df['description'].str.contains('ATM', case=False, na=False)
        ].copy()
        
        if len(atm_txns) > 0:
            # Focus on small withdrawals
            small_withdrawals = atm_txns[
                abs(atm_txns['amount']) < self.thresholds['small_withdrawal_threshold']
            ]
            
            if len(small_withdrawals) > 0:
                # Look for clusters
                small_withdrawals = small_withdrawals.sort_values('date')
                
                # Check for frequent withdrawals in short time periods
                for i in range(len(small_withdrawals)):
                    window_start = small_withdrawals.iloc[i]['date']
                    window_end = window_start + timedelta(days=self.thresholds['small_withdrawal_days'])
                    
                    window_txns = small_withdrawals[
                        (small_withdrawals['date'] >= window_start) &
                        (small_withdrawals['date'] <= window_end)
                    ]
                    
                    if len(window_txns) >= self.thresholds['small_withdrawal_count']:
                        total_withdrawn = abs(window_txns['amount'].sum())
                        avg_withdrawal = abs(window_txns['amount'].mean())
                        
                        severity = 'medium'
                        if len(window_txns) >= 10:
                            severity = 'high'
                        
                        indicators.append({
                            'indicator_type': 'frequent_small_withdrawals',
                            'severity': severity,
                            'date_range': (window_start, window_end),
                            'details': {
                                'num_withdrawals': len(window_txns),
                                'total_amount': round(total_withdrawn, 2),
                                'avg_withdrawal': round(avg_withdrawal, 2),
                                'days': self.thresholds['small_withdrawal_days']
                            },
                            'message': f' {len(window_txns)} small ATM withdrawals in {self.thresholds["small_withdrawal_days"]} days (potential cash flow issue)',
                            'recommendation': 'Multiple small withdrawals may indicate cash flow difficulties. Consider reviewing your budget.'
                        })
                        break  # Only report the first cluster
        
        return indicators
    
    def detect_payday_loans(self, df):
        """Detect potential payday loans or cash advances."""
        indicators = []
        
        payday_keywords = ['cash advance', 'payday', 'quickcash', 'fastcash', 
                          'advance america', 'check into cash']
        
        loan_txns = df[
            df['description'].str.lower().str.contains('|'.join(payday_keywords), na=False) |
            (df['category'] == 'Loan')
        ]
        
        if len(loan_txns) > 0:
            for _, txn in loan_txns.iterrows():
                indicators.append({
                    'indicator_type': 'payday_loan',
                    'severity': 'high',
                    'date_range': (txn['date'], txn['date']),
                    'details': {
                        'merchant': txn['merchant'],
                        'amount': txn['amount'],
                        'date': txn['date']
                    },
                    'message': f' Potential payday loan detected: ${abs(txn["amount"]):.2f}',
                    'recommendation': 'Payday loans often have very high interest rates. Explore alternatives like credit union loans or payment plans.'
                })
        
        return indicators
    
    def calculate_running_balance(self, df):
        """Calculate running balance from transactions."""
        df_sorted = df.sort_values('date').copy()
        df_sorted['balance'] = df_sorted['amount'].cumsum()
        # Assume starting balance of $5000 for demo
        df_sorted['balance'] += 5000
        return df_sorted
    
    def detect_declining_balance(self, df):
        """Detect declining account balance trends."""
        indicators = []
        
        # Calculate running balance
        df_with_balance = self.calculate_running_balance(df)
        
        # Check balance trend over time
        if len(df_with_balance) > 30:
            # Compare first month vs last month average
            days_total = (df_with_balance['date'].max() - df_with_balance['date'].min()).days
            
            if days_total >= 60:
                mid_point = df_with_balance['date'].min() + timedelta(days=days_total//2)
                
                early_balance = df_with_balance[
                    df_with_balance['date'] <= mid_point
                ]['balance'].mean()
                
                late_balance = df_with_balance[
                    df_with_balance['date'] > mid_point
                ]['balance'].mean()
                
                if early_balance > 0:
                    decline_pct = ((early_balance - late_balance) / early_balance) * 100
                    
                    if decline_pct > self.thresholds['balance_decline_pct']:
                        severity = 'medium'
                        if decline_pct > 40:
                            severity = 'high'
                        elif decline_pct < 25:
                            severity = 'low'
                        
                        indicators.append({
                            'indicator_type': 'declining_balance',
                            'severity': severity,
                            'date_range': (df_with_balance['date'].min(), df_with_balance['date'].max()),
                            'details': {
                                'early_avg_balance': round(early_balance, 2),
                                'recent_avg_balance': round(late_balance, 2),
                                'decline_percentage': round(decline_pct, 2),
                                'current_balance': round(df_with_balance['balance'].iloc[-1], 2)
                            },
                            'message': f' Account balance declining by {decline_pct:.1f}% over time',
                            'recommendation': 'Your account balance is declining. Review your spending and consider ways to increase income or reduce expenses.'
                        })
        
        return indicators
    
    def analyze(self, transactions_df):
        """
        Analyze transactions for financial stress indicators.
        
        Args:
            transactions_df: DataFrame with transaction data
            
        Returns:
            List of stress indicators
        """
        df = transactions_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        all_indicators = []
        
        # Run all detectors
        all_indicators.extend(self.detect_late_payment_fees(df))
        all_indicators.extend(self.detect_frequent_small_withdrawals(df))
        all_indicators.extend(self.detect_payday_loans(df))
        all_indicators.extend(self.detect_declining_balance(df))
        
        # Sort by severity
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        all_indicators.sort(key=lambda x: severity_order.get(x['severity'], 3))
        
        self.stress_indicators = all_indicators
        return all_indicators
    
    def get_summary(self):
        """Get empathetic summary of financial stress indicators."""
        if not self.stress_indicators:
            return "\nNo significant financial stress indicators detected. Keep up the good work!"
        
        summary = f"\n{'='*60}\nFINANCIAL HEALTH INSIGHTS\n{'='*60}\n"
        summary += f"We've identified {len(self.stress_indicators)} area(s) that may need attention.\n"
        
        
        high_severity = [i for i in self.stress_indicators if i['severity'] == 'high']
        medium_severity = [i for i in self.stress_indicators if i['severity'] == 'medium']
        low_severity = [i for i in self.stress_indicators if i['severity'] == 'low']
        
        if high_severity:
            summary += f"HIGH PRIORITY ({len(high_severity)} item(s)):\n"
            for indicator in high_severity:
                summary += f"\n   {indicator['message']}\n"
                summary += f"    {indicator['recommendation']}\n"
        
        if medium_severity:
            summary += f"\nMEDIUM PRIORITY ({len(medium_severity)} item(s)):\n"
            for indicator in medium_severity:
                summary += f"\n   {indicator['message']}\n"
                summary += f"    {indicator['recommendation']}\n"
        
        if low_severity:
            summary += f"\nLOW PRIORITY ({len(low_severity)} item(s)):\n"
            for indicator in low_severity:
                summary += f"\n   {indicator['message']}\n"
                summary += f"    {indicator['recommendation']}\n"
        
        summary += f"\n{'='*60}\n"
        return summary
    
    def get_risk_score(self):
        """Calculate overall financial stress risk score (0-100)."""
        if not self.stress_indicators:
            return 0
        
        score = 0
        for indicator in self.stress_indicators:
            if indicator['severity'] == 'high':
                score += 30
            elif indicator['severity'] == 'medium':
                score += 15
            else:
                score += 5
        
        return min(score, 100)


if __name__ == "__main__":
    from transaction_generator import TransactionGenerator
    
    generator = TransactionGenerator()
    df = generator.generate_dataset(include_life_events=False, include_stress=True)
    
    detector = FinancialStressDetector(sensitivity='medium')
    indicators = detector.analyze(df)
    
    print(detector.get_summary())
    print(f"\nOverall Risk Score: {detector.get_risk_score()}/100")
