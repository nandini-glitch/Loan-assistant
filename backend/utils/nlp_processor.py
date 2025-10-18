import re

class NLPProcessor:
    """
    NLP utility for processing natural language inputs
    Handles intent detection and entity extraction
    """
    
    def __init__(self):
        self.name = "NLP Processor"
        
        # Intent patterns
        self.intents = {
            'loan_amount': [
                r'(\d+)\s*(?:thousand|k|lac|lakh|lacs|lakhs)?',
                r'(?:loan|borrow|need)\s+(?:of\s+)?(?:rs\.?|₹)?\s*(\d+)',
                r'(?:rs\.?|₹)\s*(\d+)',
            ],
            'tenure': [
                r'(\d+)\s*(?:months?|mon|mo)',
                r'(\d+)\s*(?:years?|yr)',
                r'for\s+(\d+)\s+(?:months?|years?)',
            ],
            'affirmative': [
                r'\b(?:yes|yeah|yep|sure|ok|okay|correct|right|proceed|continue|go ahead|fine|alright)\b',
            ],
            'negative': [
                r'\b(?:no|nope|nah|not|cancel|stop|dont|don\'t)\b',
            ],
            'help': [
                r'\b(?:help|assist|support|guide|confused|what|how)\b',
            ],
            'restart': [
                r'\b(?:restart|reset|start over|new|begin again)\b',
            ]
        }
    
    def extract_loan_amount(self, text):
        """
        Extract loan amount from natural language
        Examples:
        - "I need 5 lakh" -> 500000
        - "250000" -> 250000
        - "2.5 lac" -> 250000
        - "50k" -> 50000
        """
        text = text.lower().strip()
        
        # Remove commas
        text = text.replace(',', '')
        
        # Check for crores
        crore_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:crore|crores|cr)', text)
        if crore_match:
            amount = float(crore_match.group(1)) * 10000000
            return int(amount)
        
        # Check for lakhs/lacs
        lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lac|lakh|lacs|lakhs|l)', text)
        if lakh_match:
            amount = float(lakh_match.group(1)) * 100000
            return int(amount)
        
        # Check for thousands
        thousand_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:thousand|k)', text)
        if thousand_match:
            amount = float(thousand_match.group(1)) * 1000
            return int(amount)
        
        # Check for plain numbers
        number_match = re.search(r'\d+', text)
        if number_match:
            return int(number_match.group(0))
        
        return None
    
    def extract_tenure(self, text):
        """
        Extract tenure from natural language
        Examples:
        - "36 months" -> 36
        - "3 years" -> 36
        - "2 year" -> 24
        """
        text = text.lower().strip()
        
        # Check for years
        year_match = re.search(r'(\d+)\s*(?:years?|yrs?|yr)', text)
        if year_match:
            years = int(year_match.group(1))
            return years * 12
        
        # Check for months
        month_match = re.search(r'(\d+)\s*(?:months?|mon|mo|m)', text)
        if month_match:
            return int(month_match.group(1))
        
        # Check for plain numbers (assume months if 12-60, years if 1-5)
        number_match = re.search(r'\b(\d+)\b', text)
        if number_match:
            num = int(number_match.group(1))
            # If number is between 1-5, likely years
            if 1 <= num <= 5:
                return num * 12
            # If number is between 12-60, likely months
            elif 12 <= num <= 60:
                return num
        
        return None
    
    def detect_intent(self, text):
        """
        Detect user intent from text
        Returns: intent name or None
        """
        text = text.lower()
        
        for intent, patterns in self.intents.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent
        
        return None
    
    def is_affirmative(self, text):
        """Check if response is yes/affirmative"""
        return self.detect_intent(text) == 'affirmative'
    
    def is_negative(self, text):
        """Check if response is no/negative"""
        return self.detect_intent(text) == 'negative'
    
    def clean_phone_number(self, text):
        """Extract and clean phone number"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', text)
        
        # Indian mobile numbers are 10 digits
        if len(digits) == 10:
            return digits
        elif len(digits) > 10:
            # Take last 10 digits
            return digits[-10:]
        
        return digits
    
    def extract_entities(self, text, entity_type):
        """
        Generic entity extraction
        """
        if entity_type == 'amount':
            return self.extract_loan_amount(text)
        elif entity_type == 'tenure':
            return self.extract_tenure(text)
        elif entity_type == 'phone':
            return self.clean_phone_number(text)
        
        return None
    
    def generate_contextual_response(self, intent, context):
        """
        Generate contextual responses based on intent
        """
        responses = {
            'help': "I'm here to help you get a personal loan! Just tell me how much you need and for how long.",
            'restart': "Sure! Let's start fresh. What's your mobile number?",
            'confused': "No worries! Let me guide you step by step.",
        }
        
        return responses.get(intent, None)
    
    def humanize_number(self, num):
        """Convert number to human readable format"""
        if num >= 10000000:
            return f"₹{num/10000000:.2f} Crore"
        elif num >= 100000:
            return f"₹{num/100000:.2f} Lakh"
        elif num >= 1000:
            return f"₹{num/1000:.2f}K"
        else:
            return f"₹{num:,}"