INTEREST_RATES = {
    12: 10.5,   # 1 year
    24: 10.99,  # 2 years
    36: 11.49,  # 3 years
    48: 11.99,  # 4 years
    60: 12.49   # 5 years
}

PROCESSING_FEE_PERCENT = 2.0
MIN_LOAN_AMOUNT = 50000
MAX_LOAN_AMOUNT = 2000000

def calculate_emi(principal, rate_annual, tenure_months):
    """Calculate EMI using reducing balance method"""
    rate_monthly = rate_annual / (12 * 100)
    emi = principal * rate_monthly * ((1 + rate_monthly) ** tenure_months) / \
          (((1 + rate_monthly) ** tenure_months) - 1)
    return round(emi, 2)

def get_interest_rate(tenure_months):
    """Get interest rate based on tenure"""
    return INTEREST_RATES.get(tenure_months, 11.49)

def calculate_processing_fee(amount):
    """Calculate processing fee"""
    return round(amount * PROCESSING_FEE_PERCENT / 100, 2)