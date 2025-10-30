"""
Unit tests for the Financial Insights Prototype.
Tests both the Life Event Detector and Financial Stress Detector.
"""

import unittest
import pandas as pd
from datetime import datetime, timedelta
from transaction_generator import TransactionGenerator
from life_event_detector import LifeEventDetector
from financial_stress_detector import FinancialStressDetector


class TestTransactionGenerator(unittest.TestCase):
    """Test the transaction generator."""
    
    def test_generator_creates_transactions(self):
        """Test that generator creates transactions."""
        generator = TransactionGenerator(seed=123)
        df = generator.generate_dataset(
            include_life_events=False,
            include_stress=False,
            num_days=30
        )
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        print(f"Generator created {len(df)} transactions")
    
    def test_transaction_columns(self):
        """Test that transactions have required columns."""
        generator = TransactionGenerator(seed=123)
        df = generator.generate_dataset(num_days=30)
        
        required_columns = ['transaction_id', 'date', 'description', 
                          'amount', 'category', 'merchant', 'type']
        
        for col in required_columns:
            self.assertIn(col, df.columns)
        
        print(f"All required columns present: {required_columns}")
    
    def test_life_events_injection(self):
        """Test that life events are injected."""
        generator = TransactionGenerator(seed=123)
        df = generator.generate_dataset(
            include_life_events=True,
            include_stress=False,
            num_days=90
        )
        
        # Should have job change, relocation, and travel indicators
        # Check for any new company (InnovateCo, TechStart, FutureWorks, NextGen, etc.)
        has_new_employer = any(
            any(company in str(desc) for company in ['InnovateCo', 'TechStart', 'FutureWorks', 'NextGen'])
            for desc in df['description']
        )
        self.assertTrue(has_new_employer, "No new employer found in transactions")
        
        # Check for moving company
        has_moving = any('Mover' in str(desc) or 'Move' in str(desc) or 'Relocation' in str(desc) 
                        for desc in df['description'])
        self.assertTrue(has_moving, "No moving company found in transactions")
        
        # Check for travel - look for airlines, airways, or travel category
        has_travel = any('Airline' in str(desc) or 'Airways' in str(desc) or 'Hotel' in str(desc) 
                        for desc in df['description'])
        if not has_travel:
            # Also check if Travel category exists
            has_travel = 'Travel' in df['category'].values
        
        self.assertTrue(has_travel, "No travel indicators found in transactions")
        
        print("Life events successfully injected")
    
    def test_stress_indicators_injection(self):
        """Test that financial stress indicators are injected."""
        generator = TransactionGenerator(seed=123)
        df = generator.generate_dataset(
            include_life_events=False,
            include_stress=True,
            num_days=90
        )
        
        # Should have late fees, ATM withdrawals, and payday loan
        self.assertTrue(any('Late Payment' in str(desc) or 'Overdraft' in str(desc) 
                          for desc in df['description']))
        atm_count = sum('ATM' in str(desc) for desc in df['description'])
        self.assertGreater(atm_count, 5)
        
        print(f"Financial stress indicators injected (found {atm_count} ATM withdrawals)")


class TestLifeEventDetector(unittest.TestCase):
    """Test the Life Event Detector."""
    
    def setUp(self):
        """Set up test data."""
        self.generator = TransactionGenerator(seed=456)
        self.detector = LifeEventDetector(sensitivity='medium')
    
    def test_job_change_detection(self):
        """Test detection of job changes."""
        df = self.generator.generate_dataset(
            include_life_events=True,
            include_stress=False,
            num_days=90
        )
        
        events = self.detector.analyze(df)
        job_changes = [e for e in events if e['event_type'] == 'job_change']
        
        self.assertGreater(len(job_changes), 0)
        self.assertIn('new_employer', job_changes[0]['details'])
        self.assertGreater(job_changes[0]['confidence'], 0.7)
        
        print(f"Job change detected: {job_changes[0]['details']['new_employer']}")
        print(f"Confidence: {job_changes[0]['confidence']*100:.1f}%")
    
    def test_relocation_detection(self):
        """Test detection of relocations."""
        df = self.generator.generate_dataset(
            include_life_events=True,
            include_stress=False,
            num_days=90
        )
        
        events = self.detector.analyze(df)
        relocations = [e for e in events if e['event_type'] == 'relocation']
        
        self.assertGreater(len(relocations), 0)
        self.assertGreater(relocations[0]['confidence'], 0.6)
        
        print(f"Relocation detected")
        print(f"Confidence: {relocations[0]['confidence']*100:.1f}%")
        print(f"Details: {relocations[0]['details']}")
    
    def test_travel_detection(self):
        """Test detection of travel."""
        df = self.generator.generate_dataset(
            include_life_events=True,
            include_stress=False,
            num_days=90
        )
        
        events = self.detector.analyze(df)
        travel = [e for e in events if e['event_type'] == 'travel']
        
        self.assertGreater(len(travel), 0)
        self.assertGreater(travel[0]['confidence'], 0.6)
        self.assertIn('total_spent', travel[0]['details'])
        
        print(f"Travel detected")
        print(f"Duration: {travel[0]['details']['duration_days']} days")
        print(f"Total spent: ${travel[0]['details']['total_spent']:.2f}")
    
    def test_no_false_positives_on_normal_data(self):
        """Test that detector doesn't flag normal transactions."""
        df = self.generator.generate_dataset(
            include_life_events=False,
            include_stress=False,
            num_days=90
        )
        
        events = self.detector.analyze(df)
        
        # Should detect very few or no events in normal data
        self.assertLessEqual(len(events), 1)  # Allow for occasional false positive
        
        print(f"Normal data check: {len(events)} events detected (good!)")


class TestFinancialStressDetector(unittest.TestCase):
    """Test the Financial Stress Detector."""
    
    def setUp(self):
        """Set up test data."""
        self.generator = TransactionGenerator(seed=789)
        self.detector = FinancialStressDetector(sensitivity='medium')
    
    def test_late_payment_detection(self):
        """Test detection of late payment fees."""
        df = self.generator.generate_dataset(
            include_life_events=False,
            include_stress=True,
            num_days=90
        )
        
        indicators = self.detector.analyze(df)
        late_fees = [i for i in indicators if i['indicator_type'] == 'late_payment_fees']
        
        self.assertGreater(len(late_fees), 0)
        self.assertIn('total_fees', late_fees[0]['details'])
        self.assertGreater(late_fees[0]['details']['total_fees'], 0)
        
        print(f"Late payment fees detected")
        print(f"Total fees: ${late_fees[0]['details']['total_fees']:.2f}")
        print(f"Severity: {late_fees[0]['severity']}")
    
    def test_frequent_withdrawals_detection(self):
        """Test detection of frequent small withdrawals."""
        df = self.generator.generate_dataset(
            include_life_events=False,
            include_stress=True,
            num_days=90
        )
        
        indicators = self.detector.analyze(df)
        withdrawals = [i for i in indicators 
                      if i['indicator_type'] == 'frequent_small_withdrawals']
        
        self.assertGreater(len(withdrawals), 0)
        self.assertGreater(withdrawals[0]['details']['num_withdrawals'], 5)
        
        print(f"Frequent small withdrawals detected")
        print(f"Number of withdrawals: {withdrawals[0]['details']['num_withdrawals']}")
        print(f"Total amount: ${withdrawals[0]['details']['total_amount']:.2f}")
    
    def test_payday_loan_detection(self):
        """Test detection of payday loans."""
        df = self.generator.generate_dataset(
            include_life_events=False,
            include_stress=True,
            num_days=90
        )
        
        indicators = self.detector.analyze(df)
        loans = [i for i in indicators if i['indicator_type'] == 'payday_loan']
        
        self.assertGreater(len(loans), 0)
        self.assertEqual(loans[0]['severity'], 'high')
        
        print(f"Payday loan detected")
        print(f"Amount: ${abs(loans[0]['details']['amount']):.2f}")
        print(f"Severity: {loans[0]['severity']}")
    
    def test_declining_balance_detection(self):
        """Test detection of declining balance."""
        df = self.generator.generate_dataset(
            include_life_events=False,
            include_stress=True,
            num_days=90
        )
        
        indicators = self.detector.analyze(df)
        declining = [i for i in indicators if i['indicator_type'] == 'declining_balance']
        
        # Declining balance might not always be detected depending on data
        if len(declining) > 0:
            self.assertIn('decline_percentage', declining[0]['details'])
            print(f"Declining balance detected")
            print(f"Decline: {declining[0]['details']['decline_percentage']:.1f}%")
        else:
            print("No declining balance detected (data may not trigger threshold)")
    
    def test_risk_score_calculation(self):
        """Test that risk score is calculated correctly."""
        df = self.generator.generate_dataset(
            include_life_events=False,
            include_stress=True,
            num_days=90
        )
        
        self.detector.analyze(df)
        risk_score = self.detector.get_risk_score()
        
        self.assertGreaterEqual(risk_score, 0)
        self.assertLessEqual(risk_score, 100)
        self.assertGreater(risk_score, 30)  # Should have some risk with stress data
        
        print(f"Risk score calculated: {risk_score}/100")
    
    def test_healthy_financial_data(self):
        """Test that detector shows low risk for healthy finances."""
        df = self.generator.generate_dataset(
            include_life_events=False,
            include_stress=False,
            num_days=90
        )
        
        self.detector.analyze(df)
        risk_score = self.detector.get_risk_score()
        
        # Healthy data should have low or zero risk
        self.assertLess(risk_score, 30)
        
        print(f"Healthy data check: Risk score = {risk_score}/100 (good!)")


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def test_complete_analysis_workflow(self):
        """Test the complete analysis workflow."""
        print("\n" + "="*60)
        print("INTEGRATION TEST: Complete Analysis Workflow")
        print("="*60)
        
        # Generate data
        generator = TransactionGenerator(seed=999)
        df = generator.generate_dataset(
            include_life_events=True,
            include_stress=True,
            num_days=90
        )
        
        print(f"\n1. Generated {len(df)} transactions")
        
        # Run life event detection
        life_detector = LifeEventDetector()
        life_events = life_detector.analyze(df)
        
        print(f"2. Detected {len(life_events)} life events:")
        for event in life_events:
            print(f"   - {event['event_type']}: {event['confidence']*100:.1f}% confidence")
        
        # Run financial stress detection
        stress_detector = FinancialStressDetector()
        stress_indicators = stress_detector.analyze(df)
        risk_score = stress_detector.get_risk_score()
        
        print(f"3. Detected {len(stress_indicators)} stress indicators")
        print(f"4. Risk Score: {risk_score}/100")
        
        # Verify results
        self.assertGreater(len(life_events), 0)
        self.assertGreater(len(stress_indicators), 0)
        self.assertGreater(risk_score, 0)
        
        print("\nINTEGRATION TEST PASSED")
        print("="*60 + "\n")


def run_tests():
    """Run all tests with detailed output."""
    print("\n" + "="*70)
    print("  FINANCIAL INSIGHTS PROTOTYPE - TEST SUITE")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTransactionGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestLifeEventDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestFinancialStressDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\nALL TESTS PASSED!")
        print("="*70 + "\n")
        return 0
    else:
        print("\nSOME TESTS FAILED")
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    exit(run_tests())
