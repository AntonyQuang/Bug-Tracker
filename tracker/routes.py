from tracker import app, db, bcrypt
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, login_required, current_user, logout_user
from tracker.forms import UserForm, LoginForm, BugForm, CommentForm, AdminPasswordForm, AdminEditUserForm, \
    UserPasswordForm
from tracker.models import User, Bug, Comments
from datetime import datetime
import pandas as pd
import plotly
import plotly.graph_objs as go
import json


# ------------------------------ Home and Index ------------------------------ #

# Homepage
@app.route("/")
def home():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    bugs = Bug.query.filter_by(parent_user_id=current_user.id)
    sql_bugs_query = f"SELECT * FROM bugs WHERE parent_user_id={current_user.id} AND NOT status='Complete';"
    df = pd.read_sql_query(sql_bugs_query, con=db.engine)
    status_counts = df["status"].value_counts()
    urgent_counts = df["urgency"].value_counts()
    project_counts = df["project"].value_counts()

    # Setting up a dictionary of statistics

    data = {}
    urgency_colors_dict = {"High": "#C5564B", "Medium": "#E9C773", "Low": "#64D367"}
    urgency_colors = [urgency_colors_dict[label] for label in urgent_counts.index]

    data["status"] = [
        go.Pie(
            values=status_counts.values,
            labels=status_counts.index,
            hole=0.5,
            textinfo='label+value',

        )
    ]
    data["urgent"] = [
        go.Pie(
            values=urgent_counts.values,
            labels=urgent_counts.index,
            hole=0.5,
            textinfo='label+value',
            marker={"colors": urgency_colors}
        )
    ]

    data["project"] = [
        go.Pie(
            values=project_counts.values,
            labels=project_counts.index,
            hole=0.5,
            textinfo='label+value',
        )
    ]

    bug_qty = status_counts.sum()
    graphjson = {key: json.dumps(item, cls=plotly.utils.PlotlyJSONEncoder) for key, item in data.items()}
    return render_template("home.html", plot_data=graphjson, bug_qty=bug_qty)


# See index of all bugs
@app.route("/index")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    bugs = Bug.query.all()
    return render_template("index.html", bugs=bugs)


# See index of bugs related to user
@app.route("/index/user/<int:user_id>", methods=["GET", "POST"])
@login_required
def user_index(user_id):
    bugs = Bug.query.filter_by(parent_user_id=user_id)
    return render_template("index.html", bugs=bugs)


# ------------------------------ Logins and Register ------------------------------ #

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    register_form = UserForm()
    if register_form.validate_on_submit():
        username_check = User.query.filter_by(username=register_form.username.data).first()
        if username_check:
            flash("Username has already been taken", category="warning")
            return redirect(url_for("register"))
        email_check = User.query.filter_by(email=register_form.email.data.lower()).first()
        if email_check:
            flash("Email is already associated with another account", category="warning")
            return redirect(url_for("register"))
        hash_password = bcrypt.generate_password_hash(register_form.password.data)
        user = User(username=register_form.username.data,
                    first_name=register_form.first_name.data.title(),
                    surname=register_form.surname.data.title(),
                    email=register_form.email.data.lower(),
                    password=hash_password,
                    start_datetime=datetime.now(),
                    user_type="Pending Verification")
        with app.app_context():
            db.session.add(user)
            db.session.commit()
        registered_user = User.query.filter_by(username=register_form.username.data).first()
        if registered_user.id == 1:
            registered_user.user_type = "Admin"
            db.session.commit()
        flash(f"Welcome {register_form.first_name.data}, thank you for registering", "success")
        return redirect(url_for("home"))
    return render_template("register.html", register_form=register_form)


# Log user in
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in", category="warning")
        return redirect(url_for("home"))
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data.lower()).first()
        if user and bcrypt.check_password_hash(user.password, login_form.password.data):
            login_user(user)
            flash("You have logged in", category="success")
            print("Log in success")
            return redirect(url_for("home"))
        else:
            flash("Log in details are incorrect", category="danger")
            return redirect(url_for("login"))
    return render_template("login.html", login_form=login_form)


# Log user out
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


# ------------------------------ User Profile ------------------------------ #

# User profile
@app.route("/user/<int:user_id>")
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("user_profile.html", user_details=user, current_user=current_user)


# ------------------------------ Admin Functions ------------------------------ #

# Access user database (Admin)
@app.route("/admin/users")
@login_required
def users():
    if current_user.user_type != "Admin":
        return "Admin privileges needed"
    users_data = User.query.all()
    return render_template("users.html", users=users_data)


# Edit User (Admin)
@app.route("/admin/user/<int:user_id>", methods=["GET", "POST"])
@login_required
def admin_edit_user(user_id):
    if current_user.user_type != "Admin":
        return "Admin privileges needed"
    update_form = AdminEditUserForm()
    existing_details = User.query.get_or_404(user_id)
    if update_form.validate_on_submit():
        print(update_form.username.data)
        existing_details.username = update_form.username.data
        existing_details.first_name = update_form.first_name.data.title()
        existing_details.surname = update_form.surname.data.title()
        existing_details.email = update_form.email.data.lower()
        existing_details.user_type = update_form.user_type.data
        db.session.commit()
        flash(f"{existing_details.username}'s details updated", category="success")
        return redirect(url_for("users"))
    update_form.user_type.default = existing_details.user_type
    update_form.process()
    return render_template("admin_edit_user.html", existing_details=existing_details, update_form=update_form,
                           admin=current_user.user_type)


# Edit password (Admin)
@app.route("/admin/user/<int:user_id>/password", methods=["GET", "POST"])
@login_required
def admin_edit_password(user_id):
    if current_user.user_type != "Admin":
        flash("Admin privileges required", category="danger")
        return redirect(url_for("index"))
    password_form = AdminPasswordForm()
    existing_details = User.query.get_or_404(user_id)
    password_form.validate()
    if password_form.validate_on_submit():
        hash_password = bcrypt.generate_password_hash(password_form.new_password.data)
        existing_details.password = hash_password
        db.session.commit()
        flash(f"Password for {existing_details.username} successfully updated", category="success")
        return redirect(url_for("admin_edit_user", user_id=existing_details.id))
    elif password_form.errors["new_password"][0] == "Passwords must match":
        flash(f"Passwords did not match", category="danger")
        return render_template("admin_edit_password.html",
                               password_form=password_form, admin=current_user.user_type)
    return render_template("admin_edit_password.html", existing_details=existing_details,
                           password_form=password_form)


# Delete user
@app.route("/admin/user/<int:user_id>/delete", methods=["GET", "POST"])
@login_required
def admin_delete_user(user_id):
    if current_user.user_type != "Admin":
        flash("Admin privileges required", category="danger")
        return redirect(url_for("home"))
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.user_type == "Admin":
        flash("Cannot delete Admin", category="danger")
        return redirect(url_for("users"))
    else:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f"User {user_to_delete.username} successfully deleted.")
        return redirect(url_for("users"))


# Admin statistics
@app.route("/admin/statistics", methods=["GET"])
@login_required
def admin_statistics():
    if current_user.user_type != "Admin":
        flash("Admin privileges required", category="danger")
        return redirect(url_for("home"))
    bugs = Bug.query.all()
    sql_bugs_query = f"SELECT * FROM bugs;"
    df = pd.read_sql_query(sql_bugs_query, con=db.engine)
    status_counts = df["status"].value_counts()
    urgent_counts = df["urgency"].value_counts()
    project_counts = df["project"].value_counts()

    # Setting up a dictionary of statistics
    data = {}
    urgency_colors_dict = {"High": "#C5564B", "Medium": "#E9C773", "Low": "#64D367"}
    urgency_colors = [urgency_colors_dict[label] for label in urgent_counts.index]

    data["status"] = [
        go.Pie(
            values=status_counts.values,
            labels=status_counts.index,
            hole=0.5,
            textinfo='label+value',

        )
    ]
    data["urgent"] = [
        go.Pie(
            values=urgent_counts.values,
            labels=urgent_counts.index,
            hole=0.5,
            textinfo='label+value',
            marker={"colors": urgency_colors}
        )
    ]

    data["project"] = [
        go.Pie(
            values=project_counts.values,
            labels=project_counts.index,
            hole=0.5,
            textinfo='label+value',
        )
    ]

    graphjson = {key: json.dumps(item, cls=plotly.utils.PlotlyJSONEncoder) for key, item in data.items()}

    return render_template("statistics.html", plot_data=graphjson)


# ------------------------------ Changing User Information ------------------------------ #

# Edit Password (Users)
@app.route("/user/<int:user_id>/password", methods=["GET", "POST"])
@login_required
def user_edit_password(user_id):
    if current_user.id != user_id:
        flash("Please log into your account to change your password", category="danger")
        return redirect(url_for("index"))
    else:
        password_form = UserPasswordForm()
        existing_details = User.query.get_or_404(user_id)
        password_form.validate()
        if password_form.validate_on_submit():
            if bcrypt.check_password_hash(existing_details.password, password_form.old_password.data):
                hash_password = bcrypt.generate_password_hash(password_form.new_password.data)
                existing_details.password = hash_password
                db.session.commit()
                flash(f"Password for {existing_details.username} successfully updated", category="success")
                return redirect(url_for("user_profile", user_id=existing_details.id))
            else:
                flash(f"Incorrect password", category="danger")
                return render_template("user_edit_password.html", existing_details=existing_details,
                                       password_form=password_form)
        elif password_form.errors["new_password"][0] == "Passwords must match":
            flash(f"Passwords did not match", category="danger")
            return render_template("user_edit_password.html", existing_details=existing_details,
                                   password_form=password_form)
        return render_template("user_edit_password.html", existing_details=existing_details,
                               password_form=password_form)


# ------------------------------ Bugs ------------------------------ #

# Add bug
@app.route("/add-bug", methods=["GET", "POST"])
@login_required
def add_bug():
    bug_form = BugForm()
    user = db.session.query(User).filter_by(username=current_user.username).first()

    if bug_form.validate_on_submit():
        bug = Bug(
            bug=bug_form.bug.data,
            description=bug_form.description.data,
            urgency=bug_form.urgency.data,
            status=bug_form.status.data,
            task=bug_form.task.data,
            project=bug_form.project.data,
            start_datetime=datetime.now(),
            update_datetime=datetime.now(),
            parent_user=user,
        )
        db.session.add(bug)
        db.session.commit()
        flash("Bug successfully added", category="success")
        return redirect(url_for("home"))
    print(bug_form.errors)
    return render_template("add_bug.html", bug_form=bug_form)


# Bug Profile
@app.route("/bug/<int:bug_id>", methods=["GET", "POST"])
@login_required
def bug_profile(bug_id):
    bug = Bug.query.get_or_404(bug_id)
    comment_form = CommentForm()
    user = db.session.query(User).filter_by(username=current_user.username).first()
    comments = Comments.query.filter_by(parent_bug=bug).order_by(Comments.id.desc()).all()
    if comment_form.validate_on_submit():
        comment = Comments(
            text=comment_form.text.data,
            parent_bug=bug,
            parent_user=user,
            start_datetime=datetime.now(),
            update_datetime=datetime.now()

        )
        db.session.add(comment)
        db.session.commit()
        flash("Comment successfully added", category="success")
        return redirect(url_for('bug_profile', bug_id=bug.id, bug=bug, comment_form=comment_form, comments=comments))
    return render_template("bug_profile.html", bug=bug, comment_form=comment_form, comments=comments)


# Edit bug
@app.route("/edit/bug/<int:bug_id>", methods=["GET", "POST"])
@login_required
def edit_bug(bug_id):
    bug = Bug.query.get_or_404(bug_id)
    all_users = User.query.all()
    user_list = [user.username for user in all_users]
    bug_edit_form = BugForm()
    bug_edit_form.description.default = bug.description
    bug_edit_form.user.choices = user_list
    bug_edit_form.user.default = bug.parent_user.username
    bug_edit_form.status.default = bug.status
    bug_edit_form.urgency.default = bug.urgency
    users_table = User
    if bug_edit_form.validate_on_submit():
        print(bug_edit_form.description.data)
        assigned_user = users_table.query.filter_by(username=bug_edit_form.user.data).first()
        if assigned_user:
            bug.bug = bug_edit_form.bug.data
            bug.description = bug_edit_form.description.data
            bug.urgency = bug_edit_form.urgency.data
            bug.status = bug_edit_form.status.data
            bug.task = bug_edit_form.task.data
            bug.project = bug_edit_form.project.data
            bug.update_datetime = datetime.now()
            bug.parent_user_id = assigned_user.id
            db.session.commit()
            flash(f"Bug {bug_id} successfully updated", category="success")
            return redirect(url_for("bug_profile", bug_id=bug.id))
        else:
            flash(f"User {bug_edit_form.user.data} does not exist", category="danger")
            return render_template("edit_bug.html", bug=bug, bug_edit_form=bug_edit_form)
    if bug_edit_form.errors:
        render_template("edit_bug.html", bug=bug, bug_edit_form=bug_edit_form)
    bug_edit_form.process()
    return render_template("edit_bug.html", bug=bug, bug_edit_form=bug_edit_form)


# ------------------------------ Comments ------------------------------ #


# Comments
@app.route("/delete/comment/<int:comment_id>", methods=["GET", "POST"])
@login_required
def delete_comment(comment_id):
    comment = Comments.query.get_or_404(comment_id)
    bug = comment.parent_bug
    user = comment.parent_user
    if current_user.id != user.id:
        flash("You do not have permission to delete this comment", category="danger")
        return redirect(url_for("bug_profile", bug_id=bug.id))
    else:
        db.session.delete(comment)
        db.session.commit()
        flash("Comment successfully deleted", category="success")
        return redirect(url_for("bug_profile", bug_id=bug.id))


@app.route("/edit/comment/<int:comment_id>", methods=["GET", "POST"])
@login_required
def edit_comment(comment_id):
    comment_form = CommentForm()
    comment = Comments.query.get_or_404(comment_id)
    bug = comment.parent_bug
    user = comment.parent_user
    comment_form.text.default = comment.text
    if comment_form.validate_on_submit():
        if current_user.id != user.id:
            flash("You do not have permission to edit this comment", category="danger")
            return redirect(url_for("bug_profile", bug_id=bug.id))
        else:
            comment.text = comment_form.text.data
            comment.update_datetime = datetime.now()
            db.session.commit()
            flash("Your comment has been updated", category="success")
            return redirect(url_for("bug_profile", bug_id=bug.id))
    comment_form.process()
    return render_template("edit_comment.html", comment=comment, comment_form=comment_form)


@app.route("/comments/<int:user_id>", methods=["GET", "POST"])
@login_required
def user_comments(user_id):
    comments = Comments.query.filter_by(parent_user_id=user_id).order_by(Comments.id.desc()).all()
    return render_template("user_comments.html", comments=comments)
