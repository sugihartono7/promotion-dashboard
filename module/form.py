from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from wtforms.fields.html5 import DateField
from flask_wtf.file import FileField, FileRequired, FileAllowed

class CustomerForm(FlaskForm):
    code = StringField('Code', validators=[DataRequired()])

class DropshipperForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])

class TypeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    # password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])

class RoleForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])

class PromotionForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    info = StringField('Info', validators=[DataRequired()])
    start_date = DateField('Start Date')
    end_date = DateField('End Date')

class RewardForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])

class ProductForm(FlaskForm):
    sku = StringField('SKU', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])

class SearchForm(FlaskForm):
    s = StringField()

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class SplashScreenForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])

class BannerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])

class CustomerVoucerForm(FlaskForm):
    start_date = DateField('Start Date')
    end_date = DateField('End Date')

class CustomerClassForm(FlaskForm):
    code = StringField('Code', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])

class VoucerMemberForm(FlaskForm):
    voucer_code = StringField('Voucer Code', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    start_date = DateField('Start Date')
    end_date = DateField('End Date')

class AccountForm(FlaskForm):
    name = StringField('Nama', validators=[DataRequired()])
    address = StringField('Alamat', validators=[DataRequired()])
    phone1 = StringField('Phone 1', validators=[DataRequired()])
    bank_number = StringField('Bank Number', validators=[DataRequired()])
    bank_name = StringField('Bank Name', validators=[DataRequired()])
    postal_code = StringField('Kode Pos', validators=[DataRequired()])
    pass1 = PasswordField('Ganti Password')
    pass2 = PasswordField('Repeat Password', validators=[EqualTo('pass1')])

class DropshipperForm(FlaskForm):
    name = StringField('Nama', validators=[DataRequired()])
    address = StringField('Alamat', validators=[DataRequired()])
    phone = StringField('No Hp', validators=[DataRequired()])
    postal_code = StringField('Kode Pos', validators=[DataRequired()])

class ReportSalesForm(FlaskForm):
    start_date = DateField('Start Date')
    end_date = DateField('End Date')

class ReportProductForm(FlaskForm):
    start_date = DateField('Start Date')
    end_date = DateField('End Date')    
