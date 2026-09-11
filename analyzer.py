import cv2
import math
import random
import numpy as np


# ============================================================
# SETTINGS
# ============================================================

MAX_DIMENSION = 1200

IDEAL_SAMOSA_ANGLE = 60.0

# A genuine corner must remain sharp even when examined
# at several different contour scales.
MAX_CORNER_ANGLE = 138.0

# Very weak/shallow turns are ignored.
MIN_CORNER_STRENGTH = 30.0

# Maximum corners we ever report.
MAX_CORNERS = 10


# ============================================================
# FUN MESSAGES
# ============================================================

SAMOSA_MESSAGES = [
    "Three genuine corners detected. Samosa geometry confirmed.",
    "Triangle detected. The snack has passed geometric inspection.",
    "Three corners reported for duty.",
    "Samosa-shaped geometry successfully identified."
]


NO_CORNER_MESSAGES = [
    "No genuine sharp corners detected.",
    "Smooth shape detected. No major corners found.",
    "This object prefers curves over corners.",
    "No significant geometric corners were found."
]


# ============================================================
# BASIC GEOMETRY
# ============================================================

def distance(a, b):
    return float(
        np.linalg.norm(
            a - b
        )
    )


def angle_between(a, center, b):
    """
    Return angle A-C-B in degrees.
    """

    vector1 = a - center
    vector2 = b - center

    length1 = np.linalg.norm(vector1)
    length2 = np.linalg.norm(vector2)

    if length1 < 1e-8 or length2 < 1e-8:
        return 180.0

    cosine = np.dot(
        vector1,
        vector2
    ) / (
        length1 *
        length2
    )

    cosine = np.clip(
        cosine,
        -1.0,
        1.0
    )

    return math.degrees(
        math.acos(cosine)
    )


def order_clockwise(points):
    """
    Order points around their center.
    The highest corner becomes A.
    """

    if len(points) == 0:
        return points

    center = np.mean(
        points,
        axis=0
    )

    directions = np.arctan2(
        points[:, 1] - center[1],
        points[:, 0] - center[0]
    )

    order = np.argsort(
        directions
    )

    ordered = points[
        order
    ]

    top_index = int(
        np.argmin(
            ordered[:, 1]
        )
    )

    return np.roll(
        ordered,
        -top_index,
        axis=0
    )


# ============================================================
# IMAGE MASKS
# ============================================================

def clean_mask(mask):
    """
    Remove small noise and close tiny gaps.
    """

    kernel_small = np.ones(
        (3, 3),
        np.uint8
    )

    kernel_large = np.ones(
        (7, 7),
        np.uint8
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel_small,
        iterations=1
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel_large,
        iterations=2
    )

    return mask


def generate_masks(image):
    """
    Try multiple ways to separate food from background.

    Using several masks makes the project work with more
    photographs instead of relying on one threshold method.
    """

    masks = []

    # --------------------------------------------------------
    # GRAYSCALE
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.GaussianBlur(
        gray,
        (7, 7),
        0
    )

    _, otsu = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY +
        cv2.THRESH_OTSU
    )

    masks.append(
        clean_mask(otsu)
    )

    masks.append(
        clean_mask(
            cv2.bitwise_not(
                otsu
            )
        )
    )

    # --------------------------------------------------------
    # HSV SATURATION
    #
    # Food is often more colourful than a white/gray
    # background or plate.
    # --------------------------------------------------------

    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV
    )

    saturation = hsv[:, :, 1]

    _, saturated = cv2.threshold(
        saturation,
        45,
        255,
        cv2.THRESH_BINARY
    )

    masks.append(
        clean_mask(
            saturated
        )
    )

    # --------------------------------------------------------
    # HSV SATURATION + VALUE
    # --------------------------------------------------------

    value = hsv[:, :, 2]

    sat_mask = (
        saturation > 35
    ).astype(
        np.uint8
    ) * 255

    value_mask = (
        value < 245
    ).astype(
        np.uint8
    ) * 255

    combined = cv2.bitwise_and(
        sat_mask,
        value_mask
    )

    masks.append(
        clean_mask(
            combined
        )
    )

    # --------------------------------------------------------
    # EDGES
    # --------------------------------------------------------

    edges = cv2.Canny(
        gray,
        45,
        140
    )

    edge_kernel = np.ones(
        (7, 7),
        np.uint8
    )

    edges = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        edge_kernel,
        iterations=2
    )

    masks.append(
        edges
    )

    return masks


# ============================================================
# SELECT MAIN FOOD OBJECT
# ============================================================

def contour_touches_frame(
    contour,
    width,
    height
):
    x, y, w, h = cv2.boundingRect(
        contour
    )

    touches = 0

    if x <= 2:
        touches += 1

    if y <= 2:
        touches += 1

    if x + w >= width - 2:
        touches += 1

    if y + h >= height - 2:
        touches += 1

    return touches >= 3


def contour_circularity(contour):
    """
    Circle ≈ 1.0
    Irregular / elongated shape = lower value
    """

    area = cv2.contourArea(
        contour
    )

    perimeter = cv2.arcLength(
        contour,
        True
    )

    if perimeter <= 0:
        return 0.0

    value = (
        4 *
        math.pi *
        area
        /
        (
            perimeter *
            perimeter
        )
    )

    return float(
        np.clip(
            value,
            0,
            1
        )
    )


def find_main_contour(image):

    height, width = (
        image.shape[:2]
    )

    image_area = float(
        width *
        height
    )

    candidates = []

    for mask in generate_masks(
        image
    ):

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_NONE
        )

        for contour in contours:

            area = cv2.contourArea(
                contour
            )

            if area < (
                image_area *
                0.006
            ):
                continue

            if area > (
                image_area *
                0.90
            ):
                continue

            if contour_touches_frame(
                contour,
                width,
                height
            ):
                continue

            perimeter = cv2.arcLength(
                contour,
                True
            )

            if perimeter < 80:
                continue

            x, y, w, h = cv2.boundingRect(
                contour
            )

            if w < 25 or h < 25:
                continue

            # ----------------------------------------------
            # Central objects are slightly preferred.
            # ----------------------------------------------

            moments = cv2.moments(
                contour
            )

            if moments["m00"] > 0:

                cx = (
                    moments["m10"] /
                    moments["m00"]
                )

                cy = (
                    moments["m01"] /
                    moments["m00"]
                )

            else:

                cx = x + w / 2
                cy = y + h / 2

            image_cx = width / 2
            image_cy = height / 2

            center_distance = math.sqrt(
                (
                    cx -
                    image_cx
                ) ** 2
                +
                (
                    cy -
                    image_cy
                ) ** 2
            )

            maximum_distance = math.sqrt(
                image_cx ** 2 +
                image_cy ** 2
            )

            centrality = max(
                0,
                1 -
                (
                    center_distance /
                    maximum_distance
                )
            )

            # Big coherent objects are preferred.
            score = (
                math.sqrt(area)
                *
                (
                    0.75 +
                    0.25 *
                    centrality
                )
            )

            candidates.append(
                (
                    score,
                    contour
                )
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item:
            item[0],
        reverse=True
    )

    return candidates[0][1]


# ============================================================
# CONTOUR RESAMPLING
# ============================================================

def resample_contour(
    contour,
    number_of_points=220
):
    """
    Convert an uneven OpenCV contour into evenly spaced points.
    """

    points = contour.reshape(
        -1,
        2
    ).astype(
        np.float64
    )

    if len(points) < 4:
        return points

    closed = np.vstack(
        [
            points,
            points[0]
        ]
    )

    segment_lengths = np.linalg.norm(
        np.diff(
            closed,
            axis=0
        ),
        axis=1
    )

    cumulative = np.concatenate(
        [
            [0.0],
            np.cumsum(
                segment_lengths
            )
        ]
    )

    perimeter = cumulative[-1]

    if perimeter <= 0:
        return points

    sample_locations = np.linspace(
        0,
        perimeter,
        number_of_points,
        endpoint=False
    )

    result = []

    for location in sample_locations:

        index = (
            np.searchsorted(
                cumulative,
                location,
                side="right"
            )
            -
            1
        )

        index = min(
            index,
            len(points) - 1
        )

        length = segment_lengths[
            index
        ]

        if length <= 1e-8:

            result.append(
                closed[index]
            )

            continue

        fraction = (
            location -
            cumulative[index]
        ) / length

        point = (
            closed[index]
            +
            fraction
            *
            (
                closed[index + 1]
                -
                closed[index]
            )
        )

        result.append(
            point
        )

    return np.array(
        result,
        dtype=np.float64
    )


def smooth_points(points):
    """
    Remove tiny fried-food texture bumps while preserving
    large geometric corners.
    """

    if len(points) < 10:
        return points

    radius = 3

    smoothed = []

    count = len(points)

    for i in range(count):

        nearby = []

        for offset in range(
            -radius,
            radius + 1
        ):

            nearby.append(
                points[
                    (
                        i +
                        offset
                    )
                    %
                    count
                ]
            )

        smoothed.append(
            np.mean(
                nearby,
                axis=0
            )
        )

    return np.array(
        smoothed,
        dtype=np.float64
    )


# ============================================================
# MULTI-SCALE CORNER DETECTION
# ============================================================

def corner_measurements(points):
    """
    Find corners that remain sharp at several measurement
    distances.

    A small crispy bump may look sharp at one tiny scale,
    but disappears when measured more broadly.

    A genuine samosa corner stays sharp at every scale.
    """

    count = len(points)

    if count < 20:
        return []

    scale_steps = [
        max(
            4,
            int(
                count *
                0.025
            )
        ),

        max(
            6,
            int(
                count *
                0.045
            )
        ),

        max(
            8,
            int(
                count *
                0.070
            )
        )
    ]

    candidates = []

    for i in range(count):

        angles = []

        for step in scale_steps:

            before = points[
                (
                    i -
                    step
                )
                %
                count
            ]

            center = points[i]

            after = points[
                (
                    i +
                    step
                )
                %
                count
            ]

            angle = angle_between(
                before,
                center,
                after
            )

            angles.append(
                angle
            )

        median_angle = float(
            np.median(
                angles
            )
        )

        maximum_angle = max(
            angles
        )

        strength = (
            180.0 -
            median_angle
        )

        # --------------------------------------------------
        # Genuine corners must remain reasonably sharp at
        # every measurement scale.
        # --------------------------------------------------

        if (
            median_angle <=
            MAX_CORNER_ANGLE
            and
            maximum_angle <=
            150.0
            and
            strength >=
            MIN_CORNER_STRENGTH
        ):

            candidates.append(
                {
                    "index": i,
                    "point": points[i],
                    "local_angle":
                        median_angle,
                    "strength":
                        strength
                }
            )

    return candidates


def suppress_nearby_corners(
    candidates,
    contour
):
    """
    Many neighboring contour points can represent the same
    physical corner. Keep only the strongest one.
    """

    if not candidates:
        return []

    perimeter = cv2.arcLength(
        contour,
        True
    )

    minimum_distance = max(
        18.0,
        perimeter *
        0.075
    )

    candidates = sorted(
        candidates,
        key=lambda item:
            item["strength"],
        reverse=True
    )

    accepted = []

    for candidate in candidates:

        candidate_point = candidate[
            "point"
        ]

        duplicate = False

        for existing in accepted:

            if distance(
                candidate_point,
                existing["point"]
            ) < minimum_distance:

                duplicate = True
                break

        if not duplicate:

            accepted.append(
                candidate
            )

        if (
            len(accepted)
            >=
            MAX_CORNERS
        ):
            break

    return accepted


# ============================================================
# ROUND / SMOOTH SHAPE CHECK
# ============================================================

def should_be_considered_smooth(
    contour,
    detected_corners
):
    """
    Important logic for cutlets, cookies and other rounded food.

    A rough circular edge can have tiny bumps, but those should
    not become six fake corners.
    """

    circularity = contour_circularity(
        contour
    )

    area = cv2.contourArea(
        contour
    )

    if area <= 0:
        return True

    x, y, w, h = cv2.boundingRect(
        contour
    )

    aspect_ratio = (
        min(
            w,
            h
        )
        /
        max(
            w,
            h
        )
    )

    # --------------------------------------------------------
    # A nearly round object should be treated as cornerless
    # unless there are a few VERY strong corners.
    # --------------------------------------------------------

    if (
        circularity >= 0.74
        and
        aspect_ratio >= 0.72
    ):

        strong = [
            corner
            for corner
            in detected_corners
            if corner[
                "local_angle"
            ] <= 105
        ]

        if len(
            strong
        ) < 3:

            return True

    return False


# ============================================================
# DETECT MAJOR CORNERS
# ============================================================

def detect_major_corners(contour):

    # Convex hull removes most crispy inward/outward texture.
    hull = cv2.convexHull(
        contour
    )

    sampled = resample_contour(
        hull,
        240
    )

    sampled = smooth_points(
        sampled
    )

    raw_candidates = (
        corner_measurements(
            sampled
        )
    )

    detected = (
        suppress_nearby_corners(
            raw_candidates,
            hull
        )
    )

    if should_be_considered_smooth(
        contour,
        detected
    ):

        return []

    return detected


# ============================================================
# POLYGON ANGLES
# ============================================================

def polygon_angles(points):

    count = len(points)

    if count < 3:

        return [
            0.0
            for _ in range(
                count
            )
        ]

    angles = []

    for i in range(count):

        previous = points[
            (
                i -
                1
            )
            %
            count
        ]

        current = points[i]

        following = points[
            (
                i +
                1
            )
            %
            count
        ]

        angle = angle_between(
            previous,
            current,
            following
        )

        angles.append(
            angle
        )

    return angles


# ============================================================
# CORNER QUALITY / PERFECTION
# ============================================================

def generic_corner_perfection(angle):
    """
    For non-samosa shapes we compare a real corner with the
    nearest common geometric corner angle.

    This is NOT used to turn smooth curves into corners.
    It only runs after the point has passed genuine-corner
    detection.
    """

    ideal_angles = [
        45.0,
        60.0,
        90.0,
        120.0,
        135.0
    ]

    nearest = min(
        ideal_angles,
        key=lambda ideal:
            abs(
                ideal -
                angle
            )
    )

    difference = abs(
        nearest -
        angle
    )

    score = (
        100.0 -
        (
            difference /
            30.0
        )
        *
        100.0
    )

    score = float(
        np.clip(
            score,
            0,
            100
        )
    )

    return (
        score,
        nearest
    )


def samosa_corner_perfection(
    angle
):
    """
    Samosa specifically wants 60 degrees.
    """

    difference = abs(
        angle -
        IDEAL_SAMOSA_ANGLE
    )

    score = (
        100.0 -
        (
            difference /
            60.0
        )
        *
        100.0
    )

    return float(
        np.clip(
            score,
            0,
            100
        )
    )


def samosa_score(angles):

    if len(angles) != 3:
        return None

    average_deviation = (
        sum(
            abs(
                angle -
                60.0
            )
            for angle
            in angles
        )
        /
        3.0
    )

    score = (
        100.0 -
        average_deviation *
        2.5
    )

    return float(
        np.clip(
            score,
            0,
            100
        )
    )


# ============================================================
# MAIN ANALYSIS
# ============================================================

def analyze(image):

    original_height, original_width = (
        image.shape[:2]
    )

    working = image.copy()

    scale = 1.0

    largest_dimension = max(
        original_width,
        original_height
    )

    # --------------------------------------------------------
    # RESIZE
    # --------------------------------------------------------

    if (
        largest_dimension >
        MAX_DIMENSION
    ):

        scale = (
            MAX_DIMENSION /
            float(
                largest_dimension
            )
        )

        new_width = int(
            original_width *
            scale
        )

        new_height = int(
            original_height *
            scale
        )

        working = cv2.resize(
            working,
            (
                new_width,
                new_height
            ),
            interpolation=cv2.INTER_AREA
        )

    # --------------------------------------------------------
    # FIND FOOD
    # --------------------------------------------------------

    contour = find_main_contour(
        working
    )

    if contour is None:

        return {
            "success": False,
            "error":
                "Could not isolate a clear food object. Try an image with a simpler background."
        }

    # --------------------------------------------------------
    # FIND REAL CORNERS
    # --------------------------------------------------------

    corner_information = (
        detect_major_corners(
            contour
        )
    )

    # --------------------------------------------------------
    # NO CORNERS
    # --------------------------------------------------------

    if not corner_information:

        return {
            "success": True,

            "image_width":
                original_width,

            "image_height":
                original_height,

            "corner_count":
                0,

            "is_triangle":
                False,

            "corners":
                [],

            "score":
                None,

            "band":
                "Smooth / Rounded Shape",

            "band_emoji":
                "⭕",

            "verdict":
                random.choice(
                    NO_CORNER_MESSAGES
                )
        }

    # --------------------------------------------------------
    # EXTRACT CORNER COORDINATES
    # --------------------------------------------------------

    points = np.array(
        [
            item["point"]
            for item
            in corner_information
        ],
        dtype=np.float64
    )

    points = order_clockwise(
        points
    )

    # restore original image coordinates
    points = (
        points /
        scale
    )

    corner_count = len(
        points
    )

    # --------------------------------------------------------
    # CALCULATE POLYGON ANGLES
    # --------------------------------------------------------

    angles = polygon_angles(
        points
    )

    corners = []

    for i in range(
        corner_count
    ):

        label = chr(
            65 + i
        )

        angle = float(
            angles[i]
        )

        corner = {
            "label":
                label,

            "x":
                round(
                    float(
                        points[i][0]
                    ),
                    2
                ),

            "y":
                round(
                    float(
                        points[i][1]
                    ),
                    2
                ),

            "angle":
                round(
                    angle,
                    1
                )
        }

        # ----------------------------------------------------
        # TRIANGLE / SAMOSA
        # ----------------------------------------------------

        if corner_count == 3:

            corner[
                "perfection"
            ] = round(
                samosa_corner_perfection(
                    angle
                ),
                1
            )

            corner[
                "nearest_ideal_angle"
            ] = 60

        # ----------------------------------------------------
        # OTHER GENUINE POLYGON
        # ----------------------------------------------------

        else:

            perfection, ideal = (
                generic_corner_perfection(
                    angle
                )
            )

            corner[
                "perfection"
            ] = round(
                perfection,
                1
            )

            corner[
                "nearest_ideal_angle"
            ] = int(
                ideal
            )

        corners.append(
            corner
        )

    # ========================================================
    # EXACTLY 3 CORNERS
    # ========================================================

    if corner_count == 3:

        score = samosa_score(
            angles
        )

        total_angle = sum(
            angles
        )

        sharpest_index = int(
            np.argmin(
                angles
            )
        )

        widest_index = int(
            np.argmax(
                angles
            )
        )

        spread = (
            max(
                angles
            )
            -
            min(
                angles
            )
        )

        symmetry = max(
            0.0,
            100.0 -
            (
                spread /
                120.0
            )
            *
            100.0
        )

        if score >= 95:

            band = (
                "Supreme Samosa"
            )

            emoji = "🏆"

        elif score >= 85:

            band = (
                "Respectable Triangle"
            )

            emoji = "✅"

        elif score >= 70:

            band = (
                "Samosa Shape Detected"
            )

            emoji = "🔺"

        else:

            band = (
                "Irregular Samosa Triangle"
            )

            emoji = "⚠️"

        return {
            "success":
                True,

            "image_width":
                original_width,

            "image_height":
                original_height,

            "corner_count":
                3,

            "is_triangle":
                True,

            "corners":
                corners,

            "score":
                round(
                    score,
                    1
                ),

            "band":
                band,

            "band_emoji":
                emoji,

            "verdict":
                random.choice(
                    SAMOSA_MESSAGES
                ),

            "stats": {

                "total_angle":
                    round(
                        total_angle,
                        1
                    ),

                "average_angle":
                    round(
                        total_angle /
                        3.0,
                        1
                    ),

                "sharpest": {

                    "label":
                        corners[
                            sharpest_index
                        ][
                            "label"
                        ],

                    "angle":
                        round(
                            angles[
                                sharpest_index
                            ],
                            1
                        )
                },

                "widest": {

                    "label":
                        corners[
                            widest_index
                        ][
                            "label"
                        ],

                    "angle":
                        round(
                            angles[
                                widest_index
                            ],
                            1
                        )
                },

                "symmetry":
                    round(
                        symmetry,
                        1
                    )
            }
        }

    # ========================================================
    # OTHER SHAPES
    # ========================================================

    return {
        "success":
            True,

        "image_width":
            original_width,

        "image_height":
            original_height,

        "corner_count":
            corner_count,

        "is_triangle":
            False,

        "corners":
            corners,

        "score":
            None,

        "band":
            f"{corner_count}-Corner Shape",

        "band_emoji":
            "🔍",

        "verdict":
            (
                f"{corner_count} genuine major "
                f"corner{'s' if corner_count != 1 else ''} detected."
            )
    }