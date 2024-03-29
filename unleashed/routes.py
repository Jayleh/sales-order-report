import os
import datetime as dt
from flask import render_template, jsonify, redirect, url_for, flash, request
from werkzeug.utils import secure_filename
import pandas as pd
from unleashed import app, db, mongo, bcrypt
from unleashed.forms import RegistrationForm, LoginForm, UploadForm
from unleashed.main import (get_bom_response, get_bom, get_soh_response,
                            get_soh, get_sales, get_purchases)
from unleashed.models import User
from flask_login import login_user, current_user, logout_user, login_required


def empty_folder(dir_name):
    # Delete any files existing in import folder
    files = os.listdir(dir_name)

    for file in files:
        os.remove(os.path.join(dir_name, file))


def check_reports():
    # See if any files in export folder
    dir_name = "unleashed/static/doc/export"

    files = os.listdir(dir_name)

    return files


def get_time_now():
    time_now = dt.datetime.today() - dt.timedelta(hours=7)
    time_now = time_now.strftime("%m/%d/%y %I:%M %p")

    return time_now


@app.route("/", methods=['GET', 'POST'])
@login_required
def home():
    form = UploadForm()

    # Grab bom from mongodb
    bills_of_materials = mongo.db.unleashed.find_one({"name": "bills_of_materials"})

    # Grab soh from mongodb
    stock_on_hand = mongo.db.unleashed.find_one({"name": "stock_on_hand"})

    # Import folder path
    import_dir_name = "unleashed/static/doc/import"

    if form.validate_on_submit():

        try:
            f = form.upload.data
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # List all components associated with initial product
            bom_df = get_bom(bills_of_materials)

            # List all quantities and descriptions
            product_df = get_soh(bom_df, stock_on_hand)

            # Grab quantity on sales
            product_df = get_sales(product_df)

            # Grab quantity on purchases
            product_df = get_purchases(product_df)

            # Grab datetime
            pst_today = dt.datetime.today() - dt.timedelta(hours=7)
            pst_today = pst_today.strftime(format="%Y%m%d%H%M%S")

            # Save report to export folder
            SAVING_PATH = f"unleashed/static/doc/export/{pst_today}_sales_order_report.xlsx"
            product_df.to_excel(SAVING_PATH, index=False, encoding='utf-8')

            # with open(SAVING_PATH, "rb") as fh:
            #     response = HttpResponse(fh.read(), content_type="text/csv")
            #     response["Content-Disposition"] = "inline; filename=" + os.path.basename(SAVING_PATH)
            #     return response

            empty_folder(import_dir_name)

            flash("Sales Order Report successfully generated.",
                  "background-color: #64b5f6;")

            return redirect(url_for('home'), code=302)

        except Exception as e:
            print(e)
            empty_folder(import_dir_name)
            flash("Sales Order Report generation was unsuccessful.",
                  "background-color: #e57373;")

    reports = check_reports()

    return render_template('index.html', form=form, bom_data=bills_of_materials, soh_data=stock_on_hand, reports=reports)


@app.route("/delete-reports")
@login_required
def delete_reports():
    export_dir_name = "unleashed/static/doc/export"

    try:
        # Empty export folder
        empty_folder(export_dir_name)

        flash("Sales reports successfully deleted.",
              "background-color: #64b5f6;")
    except Exception as e:
        print(e)
        flash("Uh oh. Something went wrong.",
              "background-color: #e57373;")

    return redirect(url_for('home'), code=302)


@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f"Account created for {form.username.data}! Please log in.",
              "background-color: #64b5f6;")
        return redirect(url_for("login"))
    return render_template("registration.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Login unsuccessful. Please check email and password.", "background-color: #e57373;")
    return render_template("login.html", title="Login", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/bom-data")
@login_required
def bom_data():
    # Find unleashed dictionary in mongodb
    bom_data = mongo.db.unleashed.find_one({"name": "bills_of_materials"})

    return jsonify(bom_data["Items"])


@app.route("/soh-data")
@login_required
def soh_data():
    # Find unleashed dictionary in mongodb
    soh_data = mongo.db.unleashed.find_one({"name": "stock_on_hand"})

    return jsonify(soh_data["Items"])


@app.route("/update-bom")
@login_required
def update_bom():
    try:
        # Create unleashed collection
        unleashed = mongo.db.unleashed

        # Call scrape function to return all reorder data
        bills_of_materials = get_bom_response()

        # Label collection
        bills_of_materials["name"] = "bills_of_materials"

        # Record time of update
        last_update = get_time_now()
        bills_of_materials["last_update"] = last_update

        # Replace specific document in collection with data, if not found insert new collection
        unleashed.replace_one(
            {"name": "bills_of_materials"},
            bills_of_materials,
            upsert=True
        )

        flash("Bills of Materials successfully updated.",
              "background-color: #64b5f6;")

    except Exception as e:
        print(e)
        raise
        flash("Bills of Materials update was unsuccessful.",
              "background-color: #e57373;")

    return redirect(url_for('home'), code=302)


@app.route("/update-soh")
@login_required
def update_soh():
    try:
        # Create unleashed collection
        unleashed = mongo.db.unleashed

        # Call scrape function to return all reorder data
        stock_on_hand = get_soh_response()

        # Label collection
        stock_on_hand["name"] = "stock_on_hand"

        # Record time of update
        last_update = get_time_now()
        stock_on_hand["last_update"] = last_update

        # Replace specific document in collection with data, if not found insert new collection
        unleashed.replace_one(
            {"name": "stock_on_hand"},
            stock_on_hand,
            upsert=True
        )

        flash("Stock on Hand successfully updated.",
              "background-color: #64b5f6;")

    except Exception as e:
        print(e)
        flash("Stock on Hand update was unsuccessful.",
              "background-color: #e57373;")

    return redirect(url_for('home'), code=302)
