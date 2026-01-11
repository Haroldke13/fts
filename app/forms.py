from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField,SearchField,SelectField,DateTimeLocalField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")
    
    
class CheckoutFileForm(FlaskForm):
    file_number = StringField("File Number", validators=[DataRequired()])
    purpose = TextAreaField("Purpose of taking file", validators=[DataRequired()])
    checkout_signature = StringField("Checkout Signature")
    submit = SubmitField("Check Out File")
    
    
class ReturnFileForm(FlaskForm):
    file_number = StringField("File Number", validators=[DataRequired()])
    comments = TextAreaField("Comments on return")
    condition = SelectField("File Condition", choices=[("good", "Good"), ("fair", "Fair"), ("damaged", "Damaged"), ("lost", "Lost")], default="good")
    return_signature = StringField("Return Signature")
    submit = SubmitField("Return File")
    
    
class UploadFileForm(FlaskForm):
    file_number = StringField("File Number", validators=[DataRequired()])
    title = StringField("Title")
    department = StringField("Department")
    file = FileField("File (Optional)")
    submit = SubmitField("Upload File")
    
    
class CreateUserForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired()])
    designation = StringField("Designation", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    role = SelectField("Role", choices=[("staff", "Staff"), ("admin", "Admin")],default="staff")
    submit = SubmitField("Create User")
    
    
class CreateChatRoomForm(FlaskForm):
    name = StringField("Room Name", validators=[DataRequired()])
    submit = SubmitField("Create Chat Room")


class ChatMessageForm(FlaskForm):
    message = TextAreaField(
        "Message",
        validators=[Length(max=1000)]  # Made optional for media-only messages
    )
    image = FileField("Image")
    voice_note = FileField("Voice Note")
    video_note = FileField("Video Note")
    submit = SubmitField("Send")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm New Password", validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField("Change Password")
