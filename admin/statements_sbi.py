import logging
import traceback

import pandas as pd
from flask import Blueprint, jsonify, request
from admin.utils import current_time, validate_account_sbi, validate_column_sbi
from config import SBI_ROW
from logs.log import log_data
from admin.database import SbiStatement, db

# Create a Blueprint instance
sbi_bp = Blueprint('sbi', __name__)


# Bank statement of SBI
@sbi_bp.route('/statement/sbi', methods=['POST'])
def upload_file_sbi():
    """
    SBI Bank Settlement upload.
    ---
    tags:
      - SBI Bank
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
        description: SBI Settlement updated successfully 
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
        valid, message = validate_account_sbi(file, engine)
        if not valid:
            return jsonify({'error': message}), 400
        
        df = pd.read_excel(file, engine=engine, header = SBI_ROW)
        df = df.rename(columns=lambda x: x.strip() if isinstance(x, str) else x)
       
        # Convert 'Debit' column to float
        df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce')
        df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce')
        
        last_nan_row_index = df.index[df.isna().all(axis=1)].max()
        if pd.isna(last_nan_row_index):
            valid_df = df
        else:
            valid_df = df.iloc[:last_nan_row_index]
        
        valid_df = valid_df.where(pd.notnull(valid_df), None)
        valid_df = valid_df.astype(str)
        
        valid, message = validate_column_sbi(valid_df)
        if not valid:
            return jsonify({'error': message}), 400
        
        # Replace 'nan' string with actual NaN values
        valid_df.replace('nan', pd.NA, inplace=True)
                

        df_date = valid_df['Txn Date'].unique()
        existing_data = SbiStatement.query.filter(SbiStatement.transaction_date.in_(df_date)).all()
        
        if existing_data:
            transaction_data_df = pd.DataFrame({
                'transaction_date': pd.to_datetime(valid_df['Txn Date']),
                'description': valid_df['Description'],
                'Ref_or_Cheque_number': valid_df['Ref No./Cheque No.'],
                'branch_code' : valid_df['Branch Code'],
                'withdrawal_amount': pd.to_numeric(valid_df['Debit']),
                'deposit_amount': pd.to_numeric(valid_df['Credit']),
                'closing_amount': pd.to_numeric(valid_df['Balance']),
            })
            
            # Convert existing data to a pandas DataFrame
            existing_data_df = pd.DataFrame([{
                'transaction_date': row.transaction_date,
                'description': row.description,
                'Ref_or_Cheque_number': row.Ref_or_Cheque_number,
                'branch_code' : row.branch_code,
                'withdrawal_amount': pd.to_numeric(row.withdrawal_amount),
                'deposit_amount': pd.to_numeric(row.deposit_amount),
                'closing_amount': pd.to_numeric(row.closing_amount),
            } for row in existing_data])
          
            # Step 3: Find the difference between the DataFrames
            merged_df = pd.merge(transaction_data_df, existing_data_df, 
                                on=['transaction_date', 'description', 'Ref_or_Cheque_number', 'branch_code',
                                    'withdrawal_amount', 'deposit_amount', 'closing_amount'], 
                                how='left', indicator=True)
                 
            # Select rows that are only in transaction_data_df
            new_unique_data_df = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge'])
            
            # Ensure there are new unique rows to process
            if not new_unique_data_df.empty:
                for index, row in new_unique_data_df.iterrows():
                    transaction_data = row.to_dict()
                    bank_statement = SbiStatement(
                        transaction_date = transaction_data.get('transaction_date'),
                        description = transaction_data.get('description'),
                        Ref_or_Cheque_number = transaction_data.get('Ref_or_Cheque_number'),
                        branch_code = transaction_data.get('branch_code'),
                        withdrawal_amount = transaction_data.get('withdrawal_amount'),
                        deposit_amount = transaction_data.get('deposit_amount'),
                        closing_amount = transaction_data.get('closing_amount'),
                        upload_admin_id = user_id,
                        upload_time = current_time()
                    )
                    db.session.add(bank_statement)
                db.session.commit()

                log_data(message = 'SBI File data successfully stored', event_type="/statement/hdfc", log_level=logging.INFO)
                return jsonify({'message': 'SBI File data successfully stored in the database'}), 201
            
            else:
                log_data(message='No new unique transactions to store', event_type="/statement/hdfc", log_level=logging.INFO)
                return jsonify({'message': 'No new unique transactions to store'}), 200
    
        # IF empty data in DB stroe the data all no check
        for index, row in valid_df.iterrows():
            transaction_data = row.to_dict()
            bank_statement = SbiStatement(
                transaction_date=transaction_data.get('Txn Date', ''),
                description=transaction_data.get('Description', ''),
                Ref_or_Cheque_number=transaction_data.get('Ref No./Cheque No.', ''),
                branch_code = transaction_data.get('Branch Code', ''),
                withdrawal_amount = transaction_data.get('Debit', ''),
                deposit_amount=transaction_data.get('Credit', ''),
                closing_amount=transaction_data.get('Balance', ''),
                upload_admin_id=user_id,
                upload_time=current_time(),
            )
            db.session.add(bank_statement)

        db.session.commit()
        log_data(message = 'SBI File data successfully stored', event_type="/statement/sbi", log_level=logging.INFO)
        return jsonify({'message': 'SBI File data successfully stored in the database'}), 201


    except Exception as e:
        db.session.rollback()
        error_message = f"Error processing file upload for bank {str(e)}"
        log_data(message = error_message, event_type="/statement/sbi", log_level=logging.ERROR)
        return jsonify({'error': error_message}), 500

