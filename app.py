import io
import traceback

import cv2
import numpy as np
from PIL import Image
from flask import Flask, jsonify, render_template, request

import analyzer


app = Flask(__name__)

app.json.ensure_ascii = False
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024


@app.route("/")
def index():
    return render_template("index.html")


def decode_image(raw_bytes):
    """
    Try OpenCV first.
    If that fails, try Pillow.
    """

    # Try OpenCV
    array = np.frombuffer(raw_bytes, dtype=np.uint8)

    image = cv2.imdecode(
        array,
        cv2.IMREAD_COLOR
    )

    if image is not None:
        return image

    # Pillow fallback
    try:
        pil_image = Image.open(
            io.BytesIO(raw_bytes)
        )

        pil_image = pil_image.convert("RGB")

        rgb = np.array(pil_image)

        image = cv2.cvtColor(
            rgb,
            cv2.COLOR_RGB2BGR
        )

        return image

    except Exception:
        return None


@app.route("/api/analyze", methods=["POST"])
def analyze():

    file = request.files.get("image")

    if file is None or file.filename == "":
        return jsonify({
            "success": False,
            "error": "No image was uploaded."
        }), 400

    raw = file.read()

    if len(raw) == 0:
        return jsonify({
            "success": False,
            "error": "The uploaded image is empty."
        }), 400

    image = decode_image(raw)

    if image is None:
        return jsonify({
            "success": False,
            "error": "Could not read this image. Try JPG, PNG or WebP."
        }), 400

    try:

        result = analyzer.analyze(image)

        return jsonify(result)

    except Exception as error:

        print("\nTRIMOSA ERROR")
        print(error)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "error": "The geometry department suffered an internal crisis."
        }), 500


@app.errorhandler(413)
def image_too_large(error):

    return jsonify({
        "success": False,
        "error": "Image too large. Maximum size is 8 MB."
    }), 413


if __name__ == "__main__":

    print("")
    print("🥟 TRIMOSA IS RUNNING")
    print("Open:")
    print("http://127.0.0.1:5000")
    print("")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )