from datetime import datetime, timedelta
from utils.pdf_generator import generate_sanction_letter_pdf

class SanctionAgent:
    """Worker Agent: Generates sanction letter once loan is approved"""
    
    def __init__(self):
        self.name = "Sanction Agent"
    
    def generate_sanction_letter(self, customer_data, loan_terms, credit_info):
        """
        Generate PDF sanction letter with all loan details
        """
        print(f"\n[Sanction Agent] Generating sanction letter for {customer_data['name']}...")
        
        # Generate loan reference number
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        loan_ref_number = f"TCPL{timestamp[-10:]}"
        
        # Calculate validity and disbursal dates
        sanction_date = datetime.now()
        validity_date = sanction_date + timedelta(days=30)
        expected_disbursal = sanction_date + timedelta(days=3)
        
        sanction_details = {
            'loan_reference_number': loan_ref_number,
            'sanction_date': sanction_date.strftime("%d %B %Y"),
            'validity_date': validity_date.strftime("%d %B %Y"),
            'expected_disbursal_date': expected_disbursal.strftime("%d %B %Y"),
            
            # Customer details
            'customer_name': customer_data['name'],
            'customer_address': customer_data['address'],
            'customer_pan': customer_data['pan'],
            'customer_email': customer_data['email'],
            
            # Loan details
            'loan_amount': loan_terms['loan_amount'],
            'tenure_months': loan_terms['tenure_months'],
            'interest_rate': loan_terms['interest_rate'],
            'emi_amount': loan_terms['emi'],
            'processing_fee': loan_terms['processing_fee'],
            'total_interest': loan_terms['total_interest'],
            'total_payable': loan_terms['total_payable'],
            
            # Credit details
            'credit_score': credit_info['credit_score'],
            'credit_bureau': credit_info['bureau'],
            
            # Terms and conditions
            'terms': self._generate_terms_and_conditions(),
            
            # Documents required
            'documents_required': self._get_required_documents()
        }
        
        # Generate PDF
        pdf_path = generate_sanction_letter_pdf(sanction_details)
        
        # Get just the filename for frontend
        import os
        pdf_filename = os.path.basename(pdf_path)
        
        print(f"[Sanction Agent] PDF generated: {pdf_path}")
        print(f"[Sanction Agent] Filename: {pdf_filename}")
        
        return {
            'success': True,
            'loan_reference_number': loan_ref_number,
            'pdf_path': pdf_path,
            'pdf_filename': pdf_filename,
            'sanction_details': sanction_details,
            'message': f"Congratulations! Your loan of ₹{loan_terms['loan_amount']:,} has been sanctioned."
        }
    
    def _generate_terms_and_conditions(self):
        """Standard terms and conditions"""
        return [
            "This sanction is valid for 30 days from the date of issue.",
            "Loan disbursal is subject to verification of submitted documents.",
            "Interest will be charged on a reducing balance basis.",
            "No prepayment charges for foreclosure after 6 months.",
            "EMI will be auto-debited from your registered bank account.",
            "Delayed payments will attract penalty charges of 2% per month.",
            "Insurance charges may be applicable as per policy norms.",
            "The company reserves the right to modify terms as per regulatory requirements."
        ]
    
    def _get_required_documents(self):
        """List of documents needed for disbursal"""
        return [
            "PAN Card (verified copy)",
            "Aadhaar Card (verified copy)",
            "Latest 3 months' salary slips",
            "Bank statements for last 6 months",
            "Passport size photographs (2 nos.)",
            "Cancelled cheque / Bank account proof"
        ]
    
    def get_sanction_summary(self, sanction_result):
        """
        Create a friendly summary message for the customer
        """
        details = sanction_result['sanction_details']
        
        summary = f"""🎉 Loan Sanctioned Successfully!

Loan Reference: {sanction_result['loan_reference_number']}
Amount: ₹{details['loan_amount']:,}
EMI: ₹{details['emi_amount']:,} for {details['tenure_months']} months
Interest Rate: {details['interest_rate']}% p.a.

Expected Disbursal: {details['expected_disbursal_date']}
Valid Until: {details['validity_date']}

Next Steps:
1. Download your sanction letter
2. Submit required documents
3. Funds will be disbursed within 48 hours of document verification

Thank you for choosing Tata Capital!"""
        
        return summary