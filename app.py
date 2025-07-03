from flask import Flask, render_template, request
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from detection import run_batch_tracker  # NEW
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def upload_file():
    result = None
    image_paths = []
    detection_complete = False

    if request.method == "POST":
        files = request.files.getlist("images")
        saved_files = []

        for file in files:
            if file.filename == "":
                continue

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            saved_files.append(filepath)
            image_paths.append(filepath)

        # Process all files at once
        result = run_batch_tracker(saved_files)
        detection_complete = True

    return render_template(
        "index.html",
        result=result,
        images=image_paths,
        detection_complete=detection_complete
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)