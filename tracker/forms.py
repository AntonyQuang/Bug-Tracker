# Importing wtforms and flask-wtf modules
from wtforms import StringField, EmailField, PasswordField, SubmitField, SelectField, validators
from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm

# Importing variables for SelectFields
from tracker.models import User
from tracker import app

# User dropdown creation
with app.app_context():
    users = User.query.with_entities(User.username).all()
    username_list = [(name[0], name[0]) for name in users]


class UserForm(FlaskForm):
    username = StringField("Username", [validators.Length(min=4, max=30), validators.DataRequired()])
    first_name = StringField("First Name", [validators.Length(min=3, max=50), validators.DataRequired()])
    surname = StringField("Surname", [validators.Length(min=3, max=50), validators.DataRequired()])
    email = EmailField("Email Address", [validators.Length(min=6, max=180), validators.Email()])
    password = PasswordField("Password", [validators.Length(min=3, max=180), validators.DataRequired(),
                                          validators.EqualTo("confirm_password", message="Passwords must match")])
    confirm_password = PasswordField("Repeat Password")
    submit = SubmitField("Register")


class AdminEditUserForm(FlaskForm):
    username = StringField("Username", [validators.Length(min=4, max=30), validators.DataRequired()])
    first_name = StringField("First Name", [validators.Length(min=3, max=50), validators.DataRequired()])
    surname = StringField("Surname", [validators.Length(min=3, max=50), validators.DataRequired()])
    email = EmailField("Email Address", [validators.Length(min=6, max=180), validators.Email()])
    user_type = SelectField("Status",
                            choices=[("Pending Verification", "Pending Verification"), ("Verified", "Verified"),
                                     ("Admin", "Admin"), ("Retired", "Retired")])
    update = SubmitField("Update")


class EditUserForm(FlaskForm):
    username = StringField("Username", [validators.Length(min=4, max=30), validators.DataRequired()])
    first_name = StringField("First Name", [validators.Length(min=3, max=50), validators.DataRequired()])
    surname = StringField("Surname", [validators.Length(min=3, max=50), validators.DataRequired()])
    email = EmailField("Email Address", [validators.Length(min=6, max=180), validators.Email()])
    update = SubmitField("Update")


class AdminPasswordForm(FlaskForm):
    new_password = PasswordField("New Password", [validators.Length(min=3, max=180), validators.DataRequired(),
                                                  validators.EqualTo("confirm_password",
                                                                     message="Passwords must match")])
    confirm_password = PasswordField("Confirm Password", [validators.DataRequired()])
    update = SubmitField("Update Password")


class UserPasswordForm(FlaskForm):
    old_password = PasswordField("Old Password", [validators.DataRequired()])
    new_password = PasswordField("New Password", [validators.Length(min=3, max=180), validators.DataRequired(),
                                                  validators.EqualTo("confirm_password",
                                                                     message="Passwords must match")])
    confirm_password = PasswordField("Confirm Password")
    update = SubmitField("Update Password")


class LoginForm(FlaskForm):
    email = EmailField("Email Address", [validators.Length(min=6, max=180), validators.Email()])
    password = PasswordField("New password", [validators.DataRequired()])
    submit = SubmitField("Log in")


class BugForm(FlaskForm):
    bug = StringField("Bug", [validators.Length(max=140), validators.DataRequired()])
    description = CKEditorField("Description", [validators.DataRequired()])
    urgency = SelectField("Urgency Level", choices=[("Low", "Low"), ("Medium", "Medium"), ("High", "High")])
    status = SelectField("Status", choices=[("Pending Assignment", "Pending Assignment"), ("Ongoing", "Ongoing"),
                                            ("Complete", "Complete")])
    task = StringField("Task", [validators.Length(max=140)])
    project = StringField("Project", [validators.Length(max=140)])
    user = SelectField("Assigned User", choices=username_list, validate_choice=False)
    submit = SubmitField("Submit Bug")


class CommentForm(FlaskForm):
    text = CKEditorField("Comment", [validators.DataRequired()])
    submit = SubmitField("Submit Comment")
