from flask import Flask, render_template, request
import os
from werkzeug.utils import secure_filename
from detection import run_batch_tracker

from supabase import create_client, Client

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

app = Flask(__name__)

# Temporary local folder for processing
UPLOAD_FOLDER = "temp_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Supabase
url: str = 'https://nrdknytydpyaodftavaa.supabase.co'
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5yZGtueXR5ZHB5YW9kZnRhdmFhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTYxMzkyMSwiZXhwIjoyMDY3MTg5OTIxfQ.a2jMHl0CkxGWvNjpA1ZYQ_-2izpnh6v6ZhnELRRuV5c"
supabase: Client = create_client(url, key)

@app.route("/", methods=["GET", "POST"])
def upload_file():
    result = None
    image_paths = []
    supabase_urls = []
    detection_complete = False

    if request.method == "POST":
        files = request.files.getlist("images")
        saved_files = []

        for file in files:
            if file.filename == "":
                continue

            filename = secure_filename(file.filename)
            local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save locally for YOLO processing
            file.save(local_path)
            saved_files.append(local_path)
            image_paths.append(local_path)

            # Upload to Supabase
            file.seek(0)  # Reset pointer before reading again
            data = file.read()
            supabase_path = f"uploads/{filename}"

            try:
                # Try uploading, fail if duplicate
                upload_res = supabase.storage.from_("uploads").upload(
                    supabase_path,
                    data,
                    {"content-type": file.content_type}
                )

                # This succeeded if no exception
                public_url = supabase.storage.from_("uploads").get_public_url(supabase_path)
                supabase_urls.append(public_url)

            except Exception as e:
                # If duplicate, you can overwrite instead
                if "The resource already exists" in str(e):
                    try:
                        # Overwrite using .update()
                        update_res = supabase.storage.from_("uploads").update(
                            supabase_path,
                            data,
                            {"content-type": file.content_type}
                        )
                        public_url = supabase.storage.from_("uploads").get_public_url(supabase_path)
                        supabase_urls.append(public_url)
                    except Exception as e2:
                        print("Update error:", e2)
                        supabase_urls.append("Error updating file")
                else:
                    print("Upload error:", e)
                    supabase_urls.append("Error uploading file")

        # Process all files at once
        result = run_batch_tracker(saved_files)
        detection_complete = True

    return render_template(
        "index.html",
        result=result,
        images=image_paths,
        supabase_urls=supabase_urls,
        detection_complete=detection_complete
    )
