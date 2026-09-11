"""Trimosa — a Flask server for the world's most unnecessary samosa scanner.

Serves the single-page frontend and exposes one API endpoint that runs the
OpenCV/NumPy analysis in ``analyzer.py``.
"""

import io

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, request

import analyzer

app = Flask(__name__)

# Send emoji verdicts as real UTF-8 instead of escaped \uXXXX pairs.
app.json.ensure_ascii = False

# 8 MB should be plenty for a jpeg of a samosa. And emotionally keep it 8 MB.
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/analyze")
def analyze():
    file = request.files.get("image")
    if file is None or file.filename == "":
        return jsonify(success=False, error="No image was uploaded."), 400

    extension = file.filename.rsplit(".", 1)[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return jsonify(
            success=False,
            error="We accept JPG, JPEG or PNG. Not existential dread as a file format.",
        ), 400

    raw = file.read()
    # Decode the uploaded bytes into an OpenCV BGR image.
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return jsonify(success=False, error="That file refused to be read."), 400

    return jsonify(analyzer.analyze(img))


@app.errorhandler(413)
def too_large(_error):
    return jsonify(success=False, error="That image is too large to judge."), 413


if __name__ == "__main__":
    app.run(debug=True)