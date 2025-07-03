from flask import Flask, render_template, request
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from detection import run_batch_tracker
from PIL import Image
import io

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def upload_file():
    result = None
    detection_complete = False

    if request.method == "POST":
        files = request.files.getlist("images")

        # List to hold PIL Images
        in_memory_images = []

        for file in files:
            if file.filename == "":
                continue

            # Read bytes into memory
            img_bytes = file.read()
            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            in_memory_images.append(image)

        # Process all images
        result = run_batch_tracker(in_memory_images)
        detection_complete = True

    return render_template(
        "index.html",
        result=result,
        detection_complete=detection_complete
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
