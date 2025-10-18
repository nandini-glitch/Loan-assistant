from data.customers import get_customer_by_phone

class VerificationAgent:
    """Worker Agent: Handles KYC verification"""
    
    def __init__(self):
        self.name = "Verification Agent"
    
    def verify_customer(self, phone_number):
        """
        Verify customer KYC details from CRM
        Returns customer data if found, None otherwise
        """
        phone = phone_number.strip().replace(' ', '').replace('-', '')
        
        # Simulate CRM lookup
        customer_data = get_customer_by_phone(phone)
        
        if customer_data:
            return {
                'verified': True,
                'customer': customer_data,
                'message': f"Customer verified successfully. Welcome back, {customer_data['name']}!"
            }
        else:
            return {
                'verified': False,
                'customer': None,
                'message': "We couldn't find your details in our system. Please check the phone number."
            }
    
    def verify_address(self, customer_data, provided_address):
        """Verify address matches records"""
        # In real scenario, this would do fuzzy matching
        return customer_data['address'].lower() in provided_address.lower() or \
               provided_address.lower() in customer_data['address'].lower()
    
    def verify_pan(self, customer_data, provided_pan):
        """Verify PAN matches records"""
        return customer_data['pan'].upper() == provided_pan.upper().strip()