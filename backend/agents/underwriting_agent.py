import random
import re
from data.offers import calculate_emi

class UnderwritingAgent:
    """Worker Agent: Handles credit evaluation and eligibility"""
    
    def __init__(self):
        self.name = "Underwriting Agent"
        self.min_credit_score = 700
    
    def fetch_credit_score(self, customer_data):
        """
        Fetch credit score from mock credit bureau API
        Simulates real-time API call to CIBIL/Experian
        """
        print(f"[Underwriting Agent] Fetching credit score for {customer_data['name']}...")
        
        base_score = customer_data['credit_score']
        
        # Simulate API delay and variation
        import time
        time.sleep(0.5)  # Simulate network delay
        
        variation = random.randint(-5, 5)
        final_score = max(300, min(900, base_score + variation))
        
        print(f"[Underwriting Agent] Credit score retrieved: {final_score}/900")
        
        return {
            'credit_score': final_score,
            'score_band': self._get_score_band(final_score),
            'bureau': 'CIBIL',
            'fetched_at': 'Mock API Call'
        }
    
    def _get_score_band(self, score):
        """Categorize credit score into bands"""
        if score >= 800:
            return 'Excellent'
        elif score >= 750:
            return 'Very Good'
        elif score >= 700:
            return 'Good'
        elif score >= 650:
            return 'Fair'
        else:
            return 'Poor'
    
    def extract_salary_from_slip(self, salary_slip_path):
        """
        Extract salary from uploaded slip
        In real scenario, use OCR (Tesseract/AWS Textract)
        For demo, we extract from filename or use customer's stored salary
        """
        print(f"[Underwriting Agent] Analyzing salary slip: {salary_slip_path}")
        
        # Simulate OCR processing
        import time
        time.sleep(1)
        
        # Try to extract salary from filename (for demo)
        # Example: salary_slip_85000.pdf
        match = re.search(r'(\d{5,})', salary_slip_path)
        if match:
            extracted_salary = int(match.group(1))
            print(f"[Underwriting Agent] Extracted salary: ₹{extracted_salary}")
            return extracted_salary
        
        # If no salary in filename, return None (will use customer data)
        return None
    
    def evaluate_eligibility(self, customer_data, loan_amount, tenure_months, interest_rate, uploaded_salary_slip=None):
        """
        Evaluate loan eligibility based on business rules
        
        Rules:
        1. Credit score must be >= 700
        2. If amount <= pre-approved limit: Instant approval
        3. If amount <= 2x pre-approved limit: Need salary slip, EMI <= 50% salary
        4. If amount > 2x pre-approved limit: Reject
        """
        print(f"\n[Underwriting Agent] Starting eligibility evaluation...")
        print(f"[Underwriting Agent] Loan Amount: ₹{loan_amount:,}")
        print(f"[Underwriting Agent] Tenure: {tenure_months} months")
        
        credit_info = self.fetch_credit_score(customer_data)
        credit_score = credit_info['credit_score']
        pre_approved = customer_data['pre_approved_limit']
        monthly_salary = customer_data['monthly_salary']
        
        print(f"[Underwriting Agent] Pre-approved limit: ₹{pre_approved:,}")
        print(f"[Underwriting Agent] Monthly salary: ₹{monthly_salary:,}")
        
        # Rule 1: Check credit score
        if credit_score < self.min_credit_score:
            print(f"[Underwriting Agent] ❌ Rejected - Credit score {credit_score} < {self.min_credit_score}")
            return {
                'approved': False,
                'reason': 'credit_score_low',
                'message': f"Unfortunately, your credit score ({credit_score}) is below our minimum requirement of {self.min_credit_score}. Please improve your credit score and reapply after 3 months.",
                'credit_info': credit_info,
                'needs_salary_slip': False
            }
        
        # Calculate EMI for eligibility check
        emi_amount = calculate_emi(loan_amount, interest_rate, tenure_months)
        print(f"[Underwriting Agent] Calculated EMI: ₹{emi_amount:,.2f}")
        
        # Rule 2: Within pre-approved limit
        if loan_amount <= pre_approved:
            print(f"[Underwriting Agent] ✅ Approved - Within pre-approved limit")
            return {
                'approved': True,
                'reason': 'within_pre_approved',
                'message': f"Great news! Your loan is instantly approved as it's within your pre-approved limit of ₹{pre_approved:,}.",
                'credit_info': credit_info,
                'emi_amount': emi_amount,
                'needs_salary_slip': False
            }
        
        # Rule 3: Between 1x and 2x pre-approved limit
        elif loan_amount <= (2 * pre_approved):
            print(f"[Underwriting Agent] ⚠️ Requires salary verification (amount > pre-approved)")
            
            # Check if salary slip is needed
            if not uploaded_salary_slip:
                print(f"[Underwriting Agent] 📄 Requesting salary slip...")
                return {
                    'approved': False,
                    'reason': 'salary_slip_required',
                    'message': f"Since you're requesting ₹{loan_amount:,}, which is above your pre-approved limit of ₹{pre_approved:,}, we need your latest salary slip to verify your repayment capacity.",
                    'credit_info': credit_info,
                    'needs_salary_slip': True
                }
            
            # Salary slip uploaded - verify EMI
            print(f"[Underwriting Agent] 📄 Salary slip received, verifying...")
            
            # Try to extract salary from slip
            extracted_salary = self.extract_salary_from_slip(uploaded_salary_slip)
            if extracted_salary:
                monthly_salary = extracted_salary
                print(f"[Underwriting Agent] Using extracted salary: ₹{monthly_salary:,}")
            else:
                print(f"[Underwriting Agent] Using stored salary: ₹{monthly_salary:,}")
            
            emi_to_salary_ratio = (emi_amount / monthly_salary) * 100
            print(f"[Underwriting Agent] EMI to Salary Ratio: {emi_to_salary_ratio:.2f}%")
            
            if emi_to_salary_ratio <= 50:
                print(f"[Underwriting Agent] ✅ Approved - EMI within 50% of salary")
                return {
                    'approved': True,
                    'reason': 'salary_verified',
                    'message': f"Excellent! Your EMI (₹{emi_amount:,.0f}) is {emi_to_salary_ratio:.1f}% of your monthly salary, which is within our comfortable limit of 50%.",
                    'credit_info': credit_info,
                    'emi_amount': emi_amount,
                    'emi_to_salary_ratio': round(emi_to_salary_ratio, 2),
                    'verified_salary': monthly_salary,
                    'needs_salary_slip': False
                }
            else:
                print(f"[Underwriting Agent] ❌ Rejected - EMI ratio {emi_to_salary_ratio:.1f}% > 50%")
                return {
                    'approved': False,
                    'reason': 'high_emi_ratio',
                    'message': f"Unfortunately, the EMI (₹{emi_amount:,.0f}) would be {emi_to_salary_ratio:.1f}% of your monthly salary (₹{monthly_salary:,}), which exceeds our maximum limit of 50%. You can apply for a lower amount or longer tenure.",
                    'credit_info': credit_info,
                    'emi_amount': emi_amount,
                    'max_affordable_emi': monthly_salary * 0.5,
                    'needs_salary_slip': False
                }
        
        # Rule 4: More than 2x pre-approved limit
        else:
            max_eligible = pre_approved * 2
            print(f"[Underwriting Agent] ❌ Rejected - Amount exceeds 2x pre-approved limit")
            return {
                'approved': False,
                'reason': 'exceeds_limit',
                'message': f"The requested amount of ₹{loan_amount:,} exceeds twice your pre-approved limit. Based on your profile, we can offer up to ₹{max_eligible:,}. Would you like to apply for this amount instead?",
                'credit_info': credit_info,
                'max_eligible_amount': max_eligible,
                'needs_salary_slip': False
            }