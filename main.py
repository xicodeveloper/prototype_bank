"""
Financial Insights Prototype - Main Demo
Demonstrates life-event detection and financial stress detection
"""

from transaction_generator import TransactionGenerator
from life_event_detector import LifeEventDetector
from financial_stress_detector import FinancialStressDetector
import pandas as pd


def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def main():
    """Run the complete demo."""
    print_header("FINANCIAL INSIGHTS PROTOTYPE")
    print("Analyzing transaction patterns for life events and financial stress...\n")
    
    # Generate synthetic transaction data
    print("Generating synthetic transaction data...")
    generator = TransactionGenerator() 
    transactions_df = generator.generate_dataset(
        include_life_events=True,
        include_stress=True,
        num_days=90
    )
    
    print(f"Generated {len(transactions_df)} transactions over 90 days\n")
    
    # Display sample transactions
    print_header("SAMPLE TRANSACTIONS")
    print(transactions_df.head(10).to_string(index=False))
    print(f"\n... and {len(transactions_df) - 10} more transactions")

    # LIFE EVENT DETECTION
    print_header("LIFE EVENT DETECTION")
    print("Analyzing transaction patterns for major life changes...\n")
    
    life_detector = LifeEventDetector(sensitivity='medium')
    life_events = life_detector.analyze(transactions_df)
    
    print(life_detector.get_summary())

    # FINANCIAL STRESS DETECTION 
    print_header("FINANCIAL STRESS ANALYSIS")
    print("Checking for financial stress indicators...\n")
    
    stress_detector = FinancialStressDetector(sensitivity='medium')
    stress_indicators = stress_detector.analyze(transactions_df)
    
    print(stress_detector.get_summary())
    
    #  OVERALL SUMMARY 
    print_header("OVERALL SUMMARY")
    
    risk_score = stress_detector.get_risk_score()
    
    print(f"Analysis Complete")
    print(f"\nLife Events Detected: {len(life_events)}")
    print(f"Financial Stress Indicators: {len(stress_indicators)}")
    print(f"Financial Stress Risk Score: {risk_score}/100")
    
    if risk_score < 30:
        print(f"\nFinancial health looks good!")
    elif risk_score < 60:
        print(f"\nSome areas need attention")
    else:
        print(f"\nSignificant financial stress detected - support recommended")
    
    print(f"\n{'='*70}\n")
    
    # Save detailed report
    print("Saving detailed transaction report...")
    transactions_df.to_csv('transaction_report.csv', index=False)
    print("Report saved to: transaction_report.csv\n") 
    print(f"\n{'='*70}")
    print("Prototype complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
