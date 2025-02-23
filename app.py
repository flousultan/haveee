import os
from flask import Flask, render_template, request, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
from serverless_wsgi import handle_request
from extract import process_document

app = Flask(__name__)
app.config.from_object("config")

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            
            extracted_data = process_document(filepath)

            return render_template("results.html", tables=extracted_data)
    return render_template("index.html")

@app.route("/download")
def download_csv():
    file_path = "output.csv"
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
