import logging

import pandas as pd
from flask import Blueprint, jsonify, request
from config import ICICI_ROW
from admin.utils import current_time, validate_column_icici, validate_account_icici
from logs.log import log_data
from admin.database import IciciStatement, db

# Create a Blueprint instance
icici_bp = Blueprint('icici', __name__)

# Bank statement of ICICI
@icici_bp.route('/statement/icici', methods=['POST'])
def upload_file_icici():
    """
    ICICI Bank Settlement upload.
    ---
    tags:
      - ICICI Bank
    parameters:
      - in: header
        name: User-id
        type: string
        required: true
        description: User ID
      - name: file
        in: formData
        type: file
        description: statement file

    responses:
      201:
        description: ICICI Settlement updated successfully 
      400:
        description: Bad Request - Missing or invalid parameters
      500:
        description: Internal Server Error - Error updating details
    """

    user_id = request.headers.get('User-id')
    if not user_id:
        return jsonify({'error': 'Admin ID Missing'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400
    if not file.filename.endswith(('.xls', '.xlsx')):
        return jsonify({'error': 'Allowed file types are .xls and .xlsx'}), 400

    try:
        # Determine the correct engine to use based on file extension and read from appropriate header row
        engine = 'xlrd' if file.filename.endswith('.xls') else 'openpyxl'

        # Validate the file with bank details account and name
        valid, message = validate_account_icici(file, engine)
        if not valid:
            return jsonify({'error': message}), 400
        
        df = pd.read_excel(file, engine=engine, header= ICICI_ROW)
        valid, message = validate_column_icici(df)
        if not valid:
            return jsonify({'error': message}), 400
        
        df_date = df['Txn Posted Date']
        existing_data = IciciStatement.query.filter(IciciStatement.transaction_date.in_(df_date.unique())).all()

        if existing_data:
            from dateutil.parser import parse

            def parse_date(date):
                if isinstance(date, str):
                    try:
                        return parse(date)
                    except ValueError:
                        return pd.NaT  # Return a NaT (Not a Time) for invalid dates
                return date  # Return the original date if it's already a datetime object

               
            transaction_data_df = pd.DataFrame({
                'transaction_date': df['Txn Posted Date'].apply(parse_date),
                'transaction_id' : df['Transaction ID'],
                'Ref_or_Cheque_number': df['ChequeNo.'],
                'description': df['Description'],
                'credit_or_debit': df['Cr/Dr'],
                'transaction_amount': pd.to_numeric(df['Transaction Amount(INR)']),
                'available_amount': pd.to_numeric(df['Available Balance(INR)'])
            })
                                  
            # Convert existing data to a pandas DataFrame
            existing_data_df = pd.DataFrame([{
                'transaction_date': parse_date(row.transaction_date),
                'transaction_id': row.transaction_id,
                'Ref_or_Cheque_number': row.Ref_or_Cheque_number,
                'description': row.description,
                'credit_or_debit': row.credit_or_debit,
                'transaction_amount': pd.to_numeric(row.transaction_amount),
                'available_amount': pd.to_numeric(row.available_amount)
            } for row in existing_data])
           
            # Step 3: Find the difference between the DataFrames
            merged_df = pd.merge(transaction_data_df, existing_data_df, 
                                on=['transaction_date', 'transaction_id', 'Ref_or_Cheque_number', 'description',
                                    'credit_or_debit', 'transaction_amount', 'available_amount'], 
                                how='left', indicator=True)
            # Select rows that are only in transaction_data_df
            new_unique_data_df = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge'])

            # Ensure there are new unique rows to process
            if not new_unique_data_df.empty:
                # Insert new unique rows into the database
                for index, row in new_unique_data_df.iterrows():
                    transaction_data = row.to_dict()
                    bank_statement = IciciStatement(
                        transaction_date=transaction_data.get('transaction_date'),
                        transaction_id=transaction_data.get('transaction_id'),
                        description=transaction_data.get('description'),
                        Ref_or_Cheque_number=transaction_data.get('Ref_or_Cheque_number'),
                        credit_or_debit=transaction_data.get('credit_or_debit'),
                        transaction_amount=transaction_data.get('transaction_amount'),
                        available_amount=transaction_data.get('available_amount'),
                        upload_admin_id=user_id,
                        upload_time=current_time(),
                    )
                    db.session.add(bank_statement)
                db.session.commit()

                log_data(message='ICICI File data successfully stored', event_type="/statement/icici", log_level=logging.INFO)
                return jsonify({'message': 'ICICI file data successfully stored in the database'}), 201
            
            else:
                log_data(message='No new unique transactions to store', event_type="/statement/icici", log_level=logging.INFO)
                return jsonify({'message': 'No new unique transactions to store'}), 200
            
        # IF empty data in DB stroe the data all no check
        for index, row in df.iterrows():
            transaction_data = row.to_dict() 
            icici_statement = IciciStatement(
                transaction_id = transaction_data.get('Transaction ID', ''),
                transaction_date = transaction_data.get('Txn Posted Date', ''),
                Ref_or_Cheque_number = transaction_data.get('ChequeNo.', ''),
                description = transaction_data.get('Description', ''),
                credit_or_debit = transaction_data.get('Cr/Dr', ''),
                transaction_amount = transaction_data.get('Transaction Amount(INR)', ''),
                available_amount = transaction_data.get('Available Balance(INR)', ''),
                upload_admin_id = user_id,
                upload_time = current_time(),
            )
            db.session.add(icici_statement)
        db.session.commit()

        log_data(message = 'ICICI File data successfully stored', event_type="/statement/icici", log_level=logging.INFO)
        return jsonify({'message': 'ICICI File data successfully stored in the database'}), 201
        
        
    except Exception as e:
        db.session.rollback()
        error_message = f"Error processing file upload for bank {str(e)}"
        log_data(message = error_message, event_type="/statement/icici", log_level=logging.ERROR)
        return jsonify({'error': error_message}), 500

