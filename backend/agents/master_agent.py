from agents.verification_agent import VerificationAgent
from agents.sales_agent import SalesAgent
from agents.underwriting_agent import UnderwritingAgent
from agents.sanction_agent import SanctionAgent
from utils.nlp_processor import NLPProcessor

class MasterAgent:
    """
    Main Orchestrator: Manages conversation flow and coordinates worker agents
    """

    def __init__(self):
        self.name = "Master Agent"

        # Initialize worker agents
        self.verification_agent = VerificationAgent()
        self.sales_agent = SalesAgent()
        self.underwriting_agent = UnderwritingAgent()
        self.sanction_agent = SanctionAgent()
        self.nlp = NLPProcessor()

        # Conversation state
        self.conversation_state = {
            'stage': 'initial',
            'customer_data': None,
            'loan_amount': None,
            'tenure_months': None,
            'loan_terms': None,
            'uploaded_salary_slip': None,
            'underwriting_result': None,
            'sanction_result': None
        }

    def process_message(self, user_message, context=None):
        """
        Main orchestration logic
        Determines which agent to invoke based on conversation stage
        """
        stage = self.conversation_state['stage']
        
        print(f"\n[Master Agent] Processing message at stage: {stage}")
        print(f"[Master Agent] User message: {user_message}")
        print(f"[Master Agent] Context: {context}")

        if stage == 'initial':
            return self._handle_initial_greeting()

        elif stage == 'awaiting_phone':
            return self._handle_phone_verification(user_message)

        elif stage == 'awaiting_loan_amount':
            return self._handle_loan_amount(user_message)

        elif stage == 'awaiting_tenure':
            return self._handle_tenure_selection(user_message)

        elif stage == 'reviewing_terms':
            return self._handle_terms_review(user_message)

        elif stage == 'awaiting_salary_slip':
            return self._handle_salary_slip_upload(context)

        elif stage == 'processing_underwriting':
            return self._handle_underwriting()

        elif stage == 'generating_sanction':
            return self._handle_sanction_generation()

        elif stage == 'completed':
            return {
                'response': "Your loan has been processed! Is there anything else I can help you with?",
                'stage': 'completed',
                'action': None
            }

        # fallback
        return {
            'response': "I'm not sure what to do next. Let me connect you with our support team.",
            'stage': stage,
            'action': 'error'
        }

    def _handle_initial_greeting(self):
        """Initial greeting and lead capture"""
        self.conversation_state['stage'] = 'awaiting_phone'
        return {
            'response': "Hi! 👋 Welcome to Tata Capital. I'm here to help you get a personal loan approved quickly. May I have your mobile number to get started?",
            'stage': 'awaiting_phone',
            'action': 'request_phone'
        }

    def _handle_phone_verification(self, phone_number):
        """Delegate to Verification Agent with NLP processing"""
        # Use NLP to clean phone number
        cleaned_phone = self.nlp.clean_phone_number(phone_number)

        print(f"[Master Agent] Processing phone: {phone_number} -> {cleaned_phone}")

        result = self.verification_agent.verify_customer(cleaned_phone)

        if result.get('verified'):
            customer = result.get('customer')
            self.conversation_state['customer_data'] = customer
            self.conversation_state['stage'] = 'awaiting_loan_amount'

            pre_approved = customer.get('pre_approved_limit', 0)

            return {
                'response': f"Welcome back, {customer.get('name')}! 🎉\n\nGreat news — you're pre-approved for a personal loan up to ₹{pre_approved:,}.\n\nHow much would you like to borrow today?",
                'stage': 'awaiting_loan_amount',
                'action': 'request_amount',
                'customer_data': customer
            }
        else:
            # In case verification failed
            return {
                'response': result.get('message', "Verification failed.") +
                            "\n\nPlease try again or use one of these test numbers:\n• 9876543210\n• 9123456789\n• 8765432109",
                'stage': 'awaiting_phone',
                'action': 'retry_phone'
            }

    def _handle_loan_amount(self, amount_text):
        """Parse and validate loan amount using NLP"""
        try:
            amount = self.nlp.extract_loan_amount(amount_text)
        except ValueError:
            amount = None

        print(f"[Master Agent] Extracted amount from '{amount_text}': {amount}")

        if amount is None:
            return {
                'response': "I couldn't understand the amount. Could you please specify how much you need? For example: '250000' or '2.5 lakh'",
                'stage': 'awaiting_loan_amount',
                'action': 'amount_unclear'
            }

        # Business limits
        if amount < 50000:
            return {
                'response': "The minimum loan amount is ₹50,000. Would you like to apply for at least ₹50,000?",
                'stage': 'awaiting_loan_amount',
                'action': 'amount_too_low'
            }
        if amount > 2000000:
            return {
                'response': "The maximum loan amount is ₹20,00,000. Would you like to apply for a lower amount?",
                'stage': 'awaiting_loan_amount',
                'action': 'amount_too_high'
            }

        self.conversation_state['loan_amount'] = amount
        self.conversation_state['stage'] = 'awaiting_tenure'

        # Get tenure suggestions from Sales Agent
        customer = self.conversation_state['customer_data']
        suggestions = self.sales_agent.suggest_optimal_tenure(customer, amount)
        recommended = suggestions.get('recommended')

        return {
            'response': (
                f"Perfect! ₹{amount:,} it is.\n\n"
                f"For this amount, I'd recommend a {recommended['tenure_months']}-month tenure. "
                f"Your EMI would be around ₹{recommended['emi']:,.0f}/month.\n\n"
                "Would you like to go with "
                f"{recommended['tenure_months']} months, or would you prefer a different tenure? "
                
            ),
            'stage': 'awaiting_tenure',
            'action': 'request_tenure',
            'loan_amount': amount,
            'suggestions': suggestions.get('all_options')
        }

    def _handle_tenure_selection(self, tenure_text):
        """Parse tenure and show loan terms using NLP"""
        try:
            tenure = self.nlp.extract_tenure(tenure_text)
        except ValueError:
            tenure = None

        print(f"[Master Agent] Extracted tenure from '{tenure_text}': {tenure}")

        if tenure is None:
            return {
                'response': "I couldn't understand the tenure. Please specify like: '36 months' or '3 years'",
                'stage': 'awaiting_tenure',
                'action': 'tenure_unclear'
            }

        if tenure not in [12, 24, 36, 48, 60]:
            return {
                'response': "Please choose from: 12, 24, 36, 48, or 60 months",
                'stage': 'awaiting_tenure',
                'action': 'invalid_tenure'
            }

        self.conversation_state['tenure_months'] = tenure

        # Get detailed terms from Sales Agent
        customer = self.conversation_state['customer_data']
        amount = self.conversation_state['loan_amount']
        loan_terms = self.sales_agent.discuss_loan_terms(customer, amount, tenure)
        self.conversation_state['loan_terms'] = loan_terms
        self.conversation_state['stage'] = 'reviewing_terms'

        response = (
            f"Excellent choice! Here's your loan summary:\n\n"
            f"💰 Loan Amount: ₹{loan_terms['loan_amount']:,}\n"
            f"⏱️ Tenure: {loan_terms['tenure_months']} months ({loan_terms['tenure_years']} years)\n"
            f"📊 Interest Rate: {loan_terms['interest_rate']}% p.a.\n"
            f"💳 Monthly EMI: ₹{loan_terms['emi']:,.2f}\n"
            f"💵 Processing Fee: ₹{loan_terms['processing_fee']:,.2f}\n\n"
            f"📈 Total Interest: ₹{loan_terms['total_interest']:,.2f}\n"
            f"📌 Total Payable: ₹{loan_terms['total_payable']:,.2f}\n\n"
            "Shall we proceed with these terms? (Yes/No)"
        )

        return {
            'response': response,
            'stage': 'reviewing_terms',
            'action': 'show_terms',
            'loan_terms': loan_terms
        }

    def _handle_terms_review(self, user_response):
        """Handle customer's acceptance or negotiation using NLP"""
        if self.nlp.is_affirmative(user_response):
            # Move to underwriting
            self.conversation_state['stage'] = 'processing_underwriting'
            return self._handle_underwriting()

        elif self.nlp.is_negative(user_response):
            return {
                'response': "No problem! What would you like to adjust? The amount or the tenure?",
                'stage': 'awaiting_loan_amount',
                'action': 'restart_terms'
            }

        else:
            return {
                'response': "I didn't quite catch that. Shall we proceed with these loan terms? Please reply with Yes or No.",
                'stage': 'reviewing_terms',
                'action': 'clarify_acceptance'
            }

    def _handle_underwriting(self):
        """Delegate to Underwriting Agent"""
        customer = self.conversation_state['customer_data']
        amount = self.conversation_state['loan_amount']
        tenure = self.conversation_state['tenure_months']
        loan_terms = self.conversation_state.get('loan_terms')
        salary_slip = self.conversation_state.get('uploaded_salary_slip')

        print(f"[Master Agent] Calling underwriting with salary_slip: {salary_slip}")

        result = self.underwriting_agent.evaluate_eligibility(
            customer, amount, tenure, loan_terms.get('interest_rate'), salary_slip
        )

        print(f"[Master Agent] Underwriting result: {result}")

        self.conversation_state['underwriting_result'] = result

        if result.get('approved'):
            print(f"[Master Agent] ✅ Loan APPROVED by underwriting!")
            # Proceed to sanction
            self.conversation_state['stage'] = 'generating_sanction'
            return self._handle_sanction_generation()

        elif result.get('needs_salary_slip'):
            print(f"[Master Agent] 📄 Salary slip needed")
            self.conversation_state['stage'] = 'awaiting_salary_slip'
            return {
                'response': result.get('message', "We need additional documents.") + "\n\nPlease upload your latest salary slip to continue.",
                'stage': 'awaiting_salary_slip',
                'action': 'request_document',
                'credit_info': result.get('credit_info')
            }

        else:
            print(f"[Master Agent] ❌ Loan REJECTED by underwriting")
            # Loan rejected
            self.conversation_state['stage'] = 'completed'
            rejection_msg = result.get('message', "We are unable to approve your loan at this time.") + "\n\n"
            if result.get('reason') == 'exceeds_limit':
                rejection_msg += f"However, you can apply for up to ₹{result.get('max_eligible_amount', 0):,}. Would you like to revise your application?"
            else:
                rejection_msg += "Don't worry! You can reapply after 3 months or try improving your credit score."

            return {
                'response': rejection_msg,
                'stage': 'completed',
                'action': 'loan_rejected',
                'rejection_reason': result.get('reason')
            }

    def _handle_salary_slip_upload(self, context):
        """Handle salary slip upload"""
        print(f"[Master Agent] _handle_salary_slip_upload called with context: {context}")
        
        if context and context.get('file_uploaded'):
            file_path = context.get('file_path') or context.get('file_name')
            self.conversation_state['uploaded_salary_slip'] = file_path

            print(f"[Master Agent] ✅ Salary slip uploaded: {file_path}")
            print(f"[Master Agent] Triggering underwriting process...")

            self.conversation_state['stage'] = 'processing_underwriting'
            
            # Call underwriting directly
            return self._handle_underwriting()
        else:
            print(f"[Master Agent] ❌ No file in context")
            return {
                'response': "I haven't received the document yet. Please upload your salary slip (PDF, JPG, or PNG).",
                'stage': 'awaiting_salary_slip',
                'action': 'awaiting_upload'
            }

    def _handle_sanction_generation(self):
        """Delegate to Sanction Agent to generate letter"""
        customer = self.conversation_state['customer_data']
        loan_terms = self.conversation_state['loan_terms']
        underwriting_result = self.conversation_state['underwriting_result']

        print(f"[Master Agent] Generating sanction letter...")

        sanction_result = self.sanction_agent.generate_sanction_letter(
            customer, loan_terms, underwriting_result.get('credit_info')
        )

        print(f"[Master Agent] Sanction result: {sanction_result}")

        self.conversation_state['sanction_result'] = sanction_result
        self.conversation_state['stage'] = 'completed'

        summary = self.sanction_agent.get_sanction_summary(sanction_result)

        return {
            'response': summary,
            'stage': 'completed',
            'action': 'loan_approved',
            'sanction_result': sanction_result,
            'pdf_available': True,
            'pdf_path': sanction_result.get('pdf_filename', sanction_result.get('pdf_path'))
        }

    def reset_conversation(self):
        """Reset conversation state for new session"""
        self.conversation_state = {
            'stage': 'initial',
            'customer_data': None,
            'loan_amount': None,
            'tenure_months': None,
            'loan_terms': None,
            'uploaded_salary_slip': None,
            'underwriting_result': None,
            'sanction_result': None
        }