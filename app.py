import os
from flask import Flask, render_template, request, send_file, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
import pandas as pd
from serverless_wsgi import handle_request
from extract import process_document, parse_api_response
from services.supabase import supabase_service
import io

app = Flask(__name__)
app.config.from_object("config")
app.secret_key = os.urandom(24)  # Add secret key for session management

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
            
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            try:
                # Save file temporarily
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                
                # Upload to Supabase
                file_id, file_url = supabase_service.upload_file(filepath)
                
                # Store file info in session
                session['file_id'] = file_id
                session['file_url'] = file_url
                
                # Process the document
                extracted_data, csv_data = process_document(filepath)
                
                # Store results in session
                session['analysis_results'] = extracted_data
                session['csv_data'] = csv_data
                
                # Clean up temporary file
                os.remove(filepath)
                
                # Parse the extracted data for display
                parsed_data = parse_api_response(extracted_data)
                return render_template(
                    "results.html",
                    key_info=parsed_data['key_info'],
                    charges=parsed_data['charges'],
                    options=parsed_data['options'],
                    clauses=parsed_data['clauses']
                )
            except Exception as e:
                print(f"Error processing document: {e}")
                flash(f"Error processing document: {str(e)}")
                return redirect(url_for('index'))
                
    return render_template("index.html")

@app.route('/download_csv')
def download_csv():
    if 'analysis_results' not in session:
        flash('No analysis results available. Please upload a document first.')
        return redirect(url_for('index'))
    
    try:
        # Get the CSV data from the session
        csv_data = session.get('csv_data', '')
        
        # Check if we have actual data
        if not csv_data or csv_data.strip() == "":
            flash('No CSV data available. Please try processing the document again.')
            return redirect(url_for('index'))
        
        # Create a buffer
        buffer = io.StringIO()
        buffer.write(csv_data)
        buffer.seek(0)
        
        return send_file(
            io.BytesIO(buffer.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='lease_analysis.csv'
        )
    except Exception as e:
        print(f"Error in download_csv: {str(e)}")
        flash(f"Error downloading CSV: {str(e)}")
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
