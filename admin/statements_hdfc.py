import logging

import pandas as pd
from flask import Blueprint, jsonify, request
from admin.utils import current_time, validate_column_hdfc, validate_account_hdfc
from config import HDFC_ROW
from logs.log import log_data
from admin.database import HdfcStatement, db

# Create a Blueprint instance
hdfc_bp = Blueprint('hdfc', __name__)


# Bank statement of HDFC
@hdfc_bp.route('/statement/hdfc', methods=['POST'])
def upload_file_hdfc():
    """
    HDFC Bank Settlement upload.
    ---
    tags:
      - HDFC Bank
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
        description: HDFC Settlement updated successfully 
      400:
        description: Bad Request - Missing or invalid parameters
      500:
        description: Internal Server Error - Error updating details

    """
    user_id = request.headers.get('User-id')
    if not user_id:
        return jsonify({'error': 'Admin ID Missing'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    if not file.filename.endswith(('.xls', '.xlsx')):
        return jsonify({'error': 'Allowed file types are .xls and .xlsx'}), 400
    
    try:
        if file.filename.endswith('.xls'):
            engine = 'xlrd'
        elif file.filename.endswith('.xlsx'):
            engine = 'openpyxl'
            
        valid, message = validate_account_hdfc(file, engine)
        if not valid:
            return jsonify({'error': message}), 400 
        
        df = pd.read_excel(file, engine=engine, header = HDFC_ROW)

        valid, message = validate_column_hdfc(df)
        if not valid:
            return jsonify({'error': message}), 400
        
        start_index = df.apply(lambda row: row.astype(str).str.contains(r'\*').all(), axis=1).idxmax() + 1
        end_index = df.iloc[::-1].apply(lambda row: row.astype(str).str.contains(r'\*').all(), axis=1).idxmax() - 1
        df = df.iloc[start_index:end_index]

        
        df_date = pd.to_datetime(df['Date'])
        existing_data = HdfcStatement.query.filter(HdfcStatement.transaction_date.in_(df_date.unique())).all()
        
        if existing_data:
            transaction_data_df = pd.DataFrame({
                'transaction_date': pd.to_datetime(df['Date']),
                'narration': df['Narration'],
                'Ref_or_Cheque_number': df['Chq./Ref.No.'],
                'withdrawal_amount': pd.to_numeric(df['Withdrawal Amt.']),
                'deposit_amount': pd.to_numeric(df['Deposit Amt.']),
                'closing_amount': pd.to_numeric(df['Closing Balance'])
            })
            
            # Convert existing data to a pandas DataFrame
            existing_data_df = pd.DataFrame([{
                'transaction_date': row.transaction_date,
                'narration': row.narration,
                'Ref_or_Cheque_number': row.Ref_or_Cheque_number,
                'withdrawal_amount': pd.to_numeric(row.withdrawal_amount),
                'deposit_amount': pd.to_numeric(row.deposit_amount),
                'closing_amount': pd.to_numeric(row.closing_amount)
            } for row in existing_data])
           
            # Step 3: Find the difference between the DataFrames
            merged_df = pd.merge(transaction_data_df, existing_data_df, 
                                on=['transaction_date', 'narration', 'Ref_or_Cheque_number', 
                                    'withdrawal_amount', 'deposit_amount', 'closing_amount'], 
                                how='left', indicator=True)
                 
            # Select rows that are only in transaction_data_df
            new_unique_data_df = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge'])
            
            # Ensure there are new unique rows to process
            if not new_unique_data_df.empty:
                for index, row in new_unique_data_df.iterrows():
                    transaction_data = row.to_dict()
                    bank_statement = HdfcStatement(
                        transaction_date = transaction_data.get('transaction_date'),
                        narration = transaction_data.get('narration'),
                        Ref_or_Cheque_number = transaction_data.get('Ref_or_Cheque_number'),
                        withdrawal_amount = transaction_data.get('withdrawal_amount'),
                        deposit_amount = transaction_data.get('deposit_amount'),
                        closing_amount = transaction_data.get('closing_amount'),
                        upload_admin_id = user_id,
                        upload_time = current_time(),
                    )
                    db.session.add(bank_statement)
                db.session.commit()

                log_data(message = 'HDFC File data successfully stored', event_type="/statement/hdfc", log_level=logging.INFO)
                return jsonify({'message': 'HDFC file data successfully stored in the database'}), 201
            
            else:
                log_data(message='No new unique transactions to store', event_type="/statement/icici", log_level=logging.INFO)
                return jsonify({'message': 'No new unique transactions to store'}), 200
                
        # IF empty data in DB stroe the data all no check    
        for index, row in df.iterrows():
            transaction_data = row.to_dict()
            bank_statement = HdfcStatement(
                transaction_date = transaction_data.get('Date', ''),
                narration = transaction_data.get('Narration', ''),
                Ref_or_Cheque_number = transaction_data.get('Chq./Ref.No.', ''),
                withdrawal_amount = transaction_data.get('Withdrawal Amt.', ''),
                deposit_amount = transaction_data.get('Deposit Amt.', ''),
                closing_amount = transaction_data.get('Closing Balance', ''),
                upload_admin_id = user_id,
                upload_time = current_time(),
            )
            db.session.add(bank_statement)
        db.session.commit()

        log_data(message = 'HDFC File data successfully stored', event_type="/statement/hdfc", log_level=logging.INFO)
        return jsonify({'message': 'HDFC file data successfully stored in the database'}), 201
        

    except Exception as e:
        db.session.rollback()
        error_message = f"Error processing file upload for bank {str(e)}"
        log_data(message = error_message, event_type="/statement/hdfc", log_level=logging.ERROR)
        return jsonify({'error': error_message}), 500
