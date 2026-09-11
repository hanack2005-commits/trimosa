"""Trimosa — the ridiculously serious samosa-geometry analyzer.

This is the computer-vision heart of the project. It uses OpenCV and NumPy
to take a photo of a samosa and extract an absurd amount of geometry:

    1. Separate the samosa from the background.
    2. Outline the samosa using contour detection.
    3. Approximate the outline with a triangle (three corners).
    4. Measure the interior angle at each corner.
    5. Compare the result to the "perfect samosa" (three 60 degree corners)
       and produce a Trimosa Score from 0 to 100.

The comments walk through each step so the file also doubles as a gentle
introduction to basic computer vision.
"""

import math
import random

import cv2
import numpy as np

# The ideal samosa is an equilateral triangle: every corner must be 60 degrees.
IDEAL_ANGLE = 60.0
TRIANGLE_TOTAL = 180.0

# Photos whose longest side exceeds this are downscaled before analysis.
MAX_DIM = 1200

# Funny messages the frontend rotates through while the analysis "grinds".
LOADING_MESSAGES = [
    "Locating suspicious corners...",
    "Consulting the laws of geometry...",
    "Questioning the chef's decisions...",
    "Calculating unnecessary mathematics...",
    "Inspecting triangular integrity...",
    "Cross-examining the pastry for corner-related crimes...",
]

# Friendlier, funnier errors for when the triangle cannot be found.
ERROR_MESSAGES = [
    "Samosa not found. Please stop uploading random objects.",
    "Triangle detection failed. The samosa may be geometrically confused.",
    "No corners detected. This is an outrage against geometry.",
    "We searched high and low. All we found is carbs.",
]

# Funny verdicts, chosen by how close the score is to perfection.
VERDICTS = {
    "supreme": [
        "Mathematically delicious.",
        "The chef clearly studied geometry.",
        "This samosa is 96% geometry and 100% unnecessary analysis.",
        "Behold: peak triangle. Pythagoras is weeping with joy.",
        "The laws of triangles would approve. Maybe even applaud.",
    ],
    "respectable": [
        "Triangle detected. Purpose still not detected.",
        "Almost perfect. Almost. The corners sense the spotlight.",
        "Solid geometry with minor feelings of inadequacy at corner B.",
        "A professional-grade triangle. Extremely edible mathematics.",
    ],
    "average": [
        "Average samosa. Average triangle. Average everything.",
        "Corner B is showing signs of rebellion.",
        "Technically triangular. Emotionally unstable.",
        "Physically a triangle. Spiritually a circle.",
    ],
    "violation": [
        "This samosa has committed crimes against geometry.",
        "Carpenters are whispering about this triangle.",
        "Corner C has clearly had a long day.",
        "The angles are fighting each other. Nobody is winning.",
    ],
    "revoked": [
        "Triangle license revoked. Please exit the triangle.",
        "We are legally required to report this to Isaac Newton.",
        "This is not a triangle. This is a 'what happened'.",
        "Geometry has been notified. Legal team now involved.",
    ],
}


def interior_angles(tri):
    """Return the interior angle (degrees) at each of the three corners.

    For corner ``v`` we take the two side vectors that leave ``v`` and use
    the dot-product rule for the angle between two vectors:

        A . B = |A| * |B| * cos(theta)   =>   theta = acos(A . B / |A||B|)

    The three angles of any triangle add up to 180 degrees, which powers most
    of the "scientific" claims on the frontend.
    """
    angles = []
    for i in range(3):
        v = tri[i]
        side_a = tri[(i + 1) % 3] - v
        side_b = tri[(i + 2) % 3] - v
        cosine = float(np.dot(side_a, side_b))
        cosine /= (np.linalg.norm(side_a) * np.linalg.norm(side_b)) + 1e-9
        angles.append(math.degrees(math.acos(max(-1.0, min(1.0, cosine)))))
    return angles


def label_triangle(tri):
    """Give the triangle's corners deterministic labels: A, B, C.

    The three corners are walked clockwise around the centroid, starting at
    the top-most corner. It is just a convention, but it lets the user track
    which measured angle belongs to which visual marker.
    """
    centroid = tri.mean(axis=0)

    # Angle of each corner measured "from the top" going clockwise. Image y
    # grows downward, so a point straight above the centroid has angle 0.
    phi = np.arctan2(tri[:, 0] - centroid[0], centroid[1] - tri[:, 1])
    order = np.argsort(phi)  # clockwise around the centroid

    ordered = tri[order].copy()
    top = int(np.argmin(ordered[:, 1]))  # start the walk at the top corner
    ordered = np.roll(ordered, -top, axis=0)
    return np.array(["A", "B", "C"]), ordered


def fit_triangle(contour):
    """Simplify a contour until it snaps into exactly three corners.

    ``approxPolyDP`` reduces a contour to fewer points; the ``epsilon``
    controls how aggressive the simplification is. We scan from tight (2% of
    the perimeter, keeps the outline realistic) to loose, and return the first
    polygon that collapses into a triangle.
    """
    arc_length = cv2.arcLength(contour, True)
    if arc_length <= 0:
        return None
    for ratio in (0.012, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.13):
        approx = cv2.approxPolyDP(contour, ratio * arc_length, True)
        if len(approx) == 3:
            return approx.reshape(3, 2).astype(np.float64)
    return None


def border_hugging(contour, width, height, image_area):
    """True when a blob basically touches the image edges.

    A contour hugging 3+ edges of the frame is usually the background, the
    table, or the photo border — not the samosa, which is the whole point.
    """
    x, y, w, h = cv2.boundingRect(contour)
    touches = 0
    touches += 1 if x <= 1 else 0
    touches += 1 if y <= 1 else 0
    touches += 1 if (x + w) >= width - 1 else 0
    touches += 1 if (y + h) >= height - 1 else 0
    return touches >= 3 and cv2.contourArea(contour) > 0.4 * image_area


def triangle_fill(contour, tri):
    """How snugly our triangle sits inside the blob (0..1).

    A samosa roughly fills the triangle its corners define. If the object is
    clearly not triangular (a circle, a square, a banana) the fitted triangle
    leaves big empty gaps and this ratio drops — our "is this even a triangle?"
    sanity check.
    """
    blob_area = max(cv2.contourArea(contour), 1e-6)
    # Shoelace formula: signed area of a polygon from its vertices.
    x0, y0 = tri[0]
    x1, y1 = tri[1]
    x2, y2 = tri[2]
    triangle_area = abs((x0 * (y1 - y2) + x1 * (y2 - y0) + x2 * (y0 - y1)) / 2.0)
    return triangle_area / blob_area


def valid_angles(angles):
    """Reject degenerate "triangles" where two corners are nearly on top."""
    return all(10.0 < angle < 170.0 for angle in angles)


def _candidate_contours(gray):
    """Outline hunting with two complementary strategies:

    Strategy A — Otsu thresholding turns the photo into black & white and
                 lets contours fall out of the binary image. We check both
                 polarities because a samosa may be lighter *and* darker
                 than its plate, depending on the day.

    Strategy B — Canny edge detection finds outlines even when plain
                 thresholding struggles (samosa sitting on a samosa-coloured
                 plate, dramatic lighting, etc.).
    """
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    contours = []

    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    for binary in (thresh, cv2.bitwise_not(thresh)):
        found, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours.extend(found)

    edges = cv2.Canny(blurred, 50, 150)
    # Close the little gaps between edge fragments so the outline is one blob.
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    found, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours.extend(found)

    return contours


def classify(score):
    """Map a score to a funny rank with the required band emoji."""
    if score >= 95:
        return "supreme", "Supreme Samosa", "🏆"
    if score >= 85:
        return "respectable", "Respectable Triangle", "🔺"
    if score >= 70:
        return "average", "Average Samosa", "😐"
    if score >= 50:
        return "violation", "Geometry Violation", "⚠️"
    return "revoked", "Triangle License Revoked", "💀"


def random_verdict(score):
    """Pick a funny verdict appropriate to the score band."""
    key, _, _ = classify(score)
    return random.choice(VERDICTS[key])


def analyze(img_bgr):
    """Run the full Trimosa pipeline. Returns a JSON-friendly result dict."""
    orig_h, orig_w = img_bgr.shape[:2]

    # Downscale very large photos so the analysis stays fast.
    scale = 1.0
    working = img_bgr
    if max(orig_w, orig_h) > MAX_DIM:
        scale = MAX_DIM / float(max(orig_w, orig_h))
        working = cv2.resize(
            img_bgr,
            (int(orig_w * scale), int(orig_h * scale)),
            interpolation=cv2.INTER_AREA,
        )

    h, w = working.shape[:2]
    image_area = float(h * w)
    gray = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY)

    # Find the biggest outline that will behave like a triangle. The samosa is
    # usually the largest coherent object in a photo, so biggest-first works.
    best_tri = None
    best_area = -1.0
    for contour in _candidate_contours(gray):
        blob_area = cv2.contourArea(contour)
        if blob_area < 0.004 * image_area or blob_area > 0.98 * image_area:
            continue
        if border_hugging(contour, w, h, image_area):
            continue
        tri = fit_triangle(contour)
        if tri is None:
            continue
        angles = interior_angles(tri)
        if not valid_angles(angles):
            continue
        if triangle_fill(contour, tri) < 0.45:
            continue
        if blob_area > best_area:
            best_area = blob_area
            best_tri = tri

    if best_tri is None:
        return {
            "success": False,
            "error": random.choice(ERROR_MESSAGES),
            "image_width": orig_w,
            "image_height": orig_h,
        }

    # Scale the triangle coordinates back to the original image coordinates,
    # then label the corners A, B and C.
    tri = best_tri / scale
    labels, tri = label_triangle(tri)
    angles = interior_angles(tri)

    total = sum(angles)
    average = total / 3.0
    deviations = [abs(a - IDEAL_ANGLE) for a in angles]
    average_deviation = sum(deviations) / 3.0

    sharpest_i = int(np.argmin(angles))
    widest_i = int(np.argmax(angles))

    # Symmetry: perfect (all equal) is 100%, utterly lopsided is 0%.
    symmetry = max(0.0, 100.0 * (1.0 - (max(angles) - min(angles)) / TRIANGLE_TOTAL))

    # The score is angle-driven: every degree of average deviation from the
    # ideal 60 degrees costs 2.5 points (100 * 1/40).
    score = max(0.0, min(100.0, 100.0 * (1.0 - average_deviation / 40.0)))

    corners = [
        {
            "label": labels[i],
            "x": round(float(tri[i][0]), 2),
            "y": round(float(tri[i][1]), 2),
            "angle": round(angles[i], 1),
        }
        for i in range(3)
    ]

    stats = {
        "total_angle": round(total, 1),
        "sharpest": {"label": labels[sharpest_i], "angle": round(angles[sharpest_i], 1)},
        "widest": {"label": labels[widest_i], "angle": round(angles[widest_i], 1)},
        "average_angle": round(average, 1),
        "deviation": round(average_deviation, 2),
        "deviation_per_corner": [
            {"label": labels[i], "deviation": round(deviations[i], 2)} for i in range(3)
        ],
        "symmetry": round(symmetry, 1),
    }

    key, band, emoji = classify(score)

    return {
        "success": True,
        "image_width": orig_w,
        "image_height": orig_h,
        "corners": corners,
        "stats": stats,
        "score": round(score, 1),
        "band": band,
        "band_emoji": emoji,
        "verdict": random.choice(VERDICTS[key]),
    }