from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class IciciStatement(db.Model):
    __tablename__ = 'icici_statements'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(60), nullable=True)
    transaction_date = db.Column(db.DateTime, nullable=True)
    Ref_or_Cheque_number = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    credit_or_debit  = db.Column(db.String(60), nullable=True)
    transaction_amount = db.Column(db.Numeric(12, 2), nullable=True)
    available_amount = db.Column(db.Numeric(12, 2), nullable=True)
    upload_admin_id = db.Column(db.String(50), nullable=True)
    upload_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Boolean, nullable=False, default=False)


class HdfcStatement(db.Model):
    __tablename__ = 'hdfc_statements'

    id = db.Column(db.Integer, primary_key=True)
    transaction_date = db.Column(db.DateTime, nullable=True)
    narration = db.Column(db.String(255), nullable=True)
    Ref_or_Cheque_number = db.Column(db.String(255), nullable=True)
    withdrawal_amount = db.Column(db.Numeric(12, 2), nullable=True)
    deposit_amount = db.Column(db.Numeric(12, 2), nullable=True)
    closing_amount = db.Column(db.Numeric(12, 2), nullable=True)
    upload_admin_id = db.Column(db.String(50), nullable=True)
    upload_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Boolean, nullable=False, default=False)


class SbiStatement(db.Model):
    __tablename__ = 'sbi_statements'

    id = db.Column(db.Integer, primary_key=True)
    transaction_date = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    Ref_or_Cheque_number = db.Column(db.String(255), nullable=True)
    branch_code = db.Column(db.String, nullable=True)
    withdrawal_amount = db.Column(db.Float, nullable=True)
    deposit_amount = db.Column(db.Float, nullable=True)
    closing_amount = db.Column(db.Float, nullable=True)
    upload_admin_id = db.Column(db.String(50), nullable=True)
    upload_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Boolean, nullable=False, default=False)

