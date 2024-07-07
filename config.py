import os
from dotenv import load_dotenv

load_dotenv()

# DataBase URL
BANK_DATABASE_URI = os.getenv('BANK_DATABASE_URI')

# Admin upload the bank statements start the data row 
HDFC_ROW = 20
ICICI_ROW = 6
SBI_ROW = 21


# Required column check with excel sheet's 
HDFC_REQUIRED_COLUMNS = {'Date', 'Narration', 'Deposit Amt.', 'Chq./Ref.No.'}
ICICI_REQUIRED_COLUMNS = {'Transaction ID', 'Txn Posted Date', 'Description', 'Cr/Dr', 'Transaction Amount(INR)'}
SBI_REQUIRED_COLUMNS = {'Txn Date', 'Description', 'Ref No./Cheque No.', 'Branch Code', 'Credit'}


HDFC_HEAD_ROW = 19
REQUIRED_BANK_DATA_HDFC = {
        'HDFC BANK Ltd.', 
        'M/S.    FIA TECHNOLOGY SERVICES PVT LTD', 
        'Account Branch :BADSHAHPUR',
        'Address :HDFC BANK', 
        'State :HARYANA',
        'City :GURGAON 122018', 
        'Cust ID :52888590', 
        'Account No :50200006689170     Imperia', 
        'RTGS/NEFT IFSC :HDFC0001098   MICR :110240138'
    }

ICICI_HEAD_ROW = 19
REQUIRED_BANK_DATA_ICICI = {
        'Transactions List -   -FIA TECHNOLOGY SERVICES PVT LTD (INR) - 002105016912'
    }

SBI_HEAD_ROW = 19
REQUIRED_BANK_DATA_SBI = {
        '_00000033925608549', 
        'FIA TECHNOLOGY SERVICES P. LTD                              ', 
        '840, 8TH FLOOR, JMD MEGAPOLIS,SOHNA ROAD , SEC-48, GURGAON',
        'SBIN0002300', 
        'GURGAON',
        'HARYANA-122001', 
        'BADSHAPUR(02300)'
    }

