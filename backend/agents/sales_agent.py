from data.offers import get_interest_rate, calculate_emi, calculate_processing_fee

class SalesAgent:
    """Worker Agent: Handles sales negotiation and loan terms discussion"""
    
    def __init__(self):
        self.name = "Sales Agent"
    
    def discuss_loan_terms(self, customer_data, requested_amount, tenure_months):
        """
        Discuss loan terms with customer
        Returns loan offer details
        """
        interest_rate = get_interest_rate(tenure_months)
        emi = calculate_emi(requested_amount, interest_rate, tenure_months)
        processing_fee = calculate_processing_fee(requested_amount)
        total_interest = (emi * tenure_months) - requested_amount
        total_payable = emi * tenure_months
        
        return {
            'loan_amount': requested_amount,
            'tenure_months': tenure_months,
            'tenure_years': tenure_months // 12,
            'interest_rate': interest_rate,
            'emi': round(emi, 2),
            'processing_fee': processing_fee,
            'total_interest': round(total_interest, 2),
            'total_payable': round(total_payable, 2)
        }
    
    def suggest_optimal_tenure(self, customer_data, loan_amount):
        """
        Suggest optimal tenure based on customer's salary
        Keep EMI at comfortable 30-35% of salary
        """
        monthly_salary = customer_data['monthly_salary']
        comfortable_emi = monthly_salary * 0.35
        
        # Try different tenures to find optimal
        tenures = [12, 24, 36, 48, 60]
        suggestions = []
        
        for tenure in tenures:
            rate = get_interest_rate(tenure)
            emi = calculate_emi(loan_amount, rate, tenure)
            emi_ratio = (emi / monthly_salary) * 100
            
            suggestions.append({
                'tenure_months': tenure,
                'emi': round(emi, 2),
                'emi_ratio': round(emi_ratio, 2),
                'comfortable': emi_ratio <= 35
            })
        
        # Find the shortest comfortable tenure
        optimal = None
        for sug in suggestions:
            if sug['comfortable']:
                if optimal is None or sug['tenure_months'] < optimal['tenure_months']:
                    optimal = sug
        
        return {
            'all_options': suggestions,
            'recommended': optimal if optimal else suggestions[-1]  # Default to longest if none comfortable
        }
    
    def handle_negotiation(self, customer_data, current_offer, negotiation_point):
        """
        Handle customer negotiation on loan terms
        Can adjust tenure, suggest lower amount, etc.
        """
        loan_amount = current_offer['loan_amount']
        
        if negotiation_point == 'emi_too_high':
            # Suggest longer tenure or lower amount
            longer_tenure_options = self.suggest_optimal_tenure(customer_data, loan_amount)
            return {
                'type': 'tenure_adjustment',
                'message': "I understand. Let me show you options with longer tenure for lower EMIs.",
                'options': longer_tenure_options['all_options']
            }
        
        elif negotiation_point == 'rate_too_high':
            # Explain rate is competitive, show benefits
            return {
                'type': 'rate_justification',
                'message': f"Our rate of {current_offer['interest_rate']}% is highly competitive for personal loans. Plus, you get benefits like no prepayment charges and quick disbursal.",
                'benefits': [
                    "Zero prepayment charges",
                    "Instant approval for eligible customers",
                    "Flexible repayment options",
                    "Top-up loan facility available"
                ]
            }
        
        elif negotiation_point == 'amount_too_low':
            max_eligible = customer_data['pre_approved_limit'] * 2
            if loan_amount < max_eligible:
                return {
                    'type': 'amount_increase',
                    'message': f"You can borrow up to ₹{max_eligible:,}. Would you like to increase your loan amount?",
                    'max_amount': max_eligible
                }
            else:
                return {
                    'type': 'max_reached',
                    'message': f"You're already at the maximum eligible amount based on your profile. We'd be happy to review this again after 6 months!"
                }
        
        return {
            'type': 'general',
            'message': "I'm here to help! What specifically would you like to adjust?"
        }