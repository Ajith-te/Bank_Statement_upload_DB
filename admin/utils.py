from flask import jsonify, request
import pandas as pd
import requests
from datetime import datetime

from functools import wraps

from config import HDFC_REQUIRED_COLUMNS, ICICI_REQUIRED_COLUMNS, SBI_REQUIRED_COLUMNS
from config import REQUIRED_BANK_DATA_HDFC, REQUIRED_BANK_DATA_ICICI, REQUIRED_BANK_DATA_SBI

def current_time():
    return datetime.now().strftime('%Y-%m-%d %I:%M %p')

# < ------------------------------bank's columns check ------------------------------------------>

def validate_column_hdfc(df):
    required_columns = HDFC_REQUIRED_COLUMNS
    if not required_columns.issubset(df.columns):
        missing_columns = required_columns - set(df.columns)
        return False, f"Missing required columns for Bank HDFC: {', '.join(missing_columns)}"
    return True, "Validation successful for Bank HDFC"


def validate_column_icici(df):
    required_columns = ICICI_REQUIRED_COLUMNS
    if not required_columns.issubset(df.columns):
        missing_columns = required_columns - set(df.columns)
        return False, f"Missing required columns for Bank ICICI: {', '.join(missing_columns)}"
    return True, "Validation successful for Bank ICICI"


def validate_column_sbi(df):
    required_columns = SBI_REQUIRED_COLUMNS
    if not required_columns.issubset(df.columns):
        missing_columns = required_columns - set(df.columns)
        return False, f"Missing required columns for Bank SBI: {', '.join(missing_columns)}"
    return True, "Validation successful for Bank SBI"


# < ------------------------------bank's credentials check ------------------------------------------>

def validate_account_hdfc(file, engine):
    df = pd.read_excel(file, engine=engine, header=None)
    required_details = REQUIRED_BANK_DATA_HDFC
    details_df = df.head(19)
    all_text = ' '.join(details_df.astype(str).stack().unique())
    missing_details = [detail for detail in required_details if detail not in all_text]
    if missing_details:
        return False, f"Missing required bank detail(s): {', '.join(missing_details)}"
    return True, "Bank details validation successful"


def validate_account_icici(file, engine):
    df = pd.read_excel(file, engine=engine, header=None)
    required_details = REQUIRED_BANK_DATA_ICICI
    details_df = df.head(19)
    all_text = ' '.join(details_df.astype(str).stack().unique())
    missing_details = [detail for detail in required_details if detail not in all_text]
    if missing_details:
        return False, f"Missing required bank detail(s): {', '.join(missing_details)}"
    return True, "Bank details validation successful"


def validate_account_sbi(file, engine):
    df = pd.read_excel(file, engine=engine, header=None)
    required_details = REQUIRED_BANK_DATA_SBI
    details_df = df.head(19)
    all_text = ' '.join(details_df.astype(str).stack().unique())
    missing_details = [detail for detail in required_details if detail not in all_text]
    if missing_details:
        return False, f"Missing required bank detail(s): {', '.join(missing_details)}"
    return True, "Bank details validation successful"


# token check with other user micro service
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        headers = {'Authorization': token}
        try:
            user_info_response = requests.post("http://127.0.0.1:5001/token_check", headers=headers)
            
            if user_info_response.status_code != 200:
                return jsonify({'message': 'Token is invalid'}), 401
            
            user_info = user_info_response.json()
            logged_user_id = user_info.get("_id")
            logged_user_code = user_info.get("user_code")
            logged_user_name = user_info.get("user_name")
        except Exception as e:
            return jsonify({'message': 'Token is invalid', 'error': str(e)}), 401
 
        return f(logged_user_id, logged_user_code, logged_user_name, *args, **kwargs)
 
    return decorated
