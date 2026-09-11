const LOADING_MESSAGES = [
    "Scanning Shape",
    "Detecting outline",
    "Searching for corners",
    "Measuring corner angles",
    "Comparing geometry",
    "Consulting unnecessary mathematics"
];


const COLORS = [
    "#e11d48",
    "#d97706",
    "#0f9b8e",
    "#2563eb",
    "#7c3aed",
    "#db2777",
    "#0891b2",
    "#65a30d",
    "#9333ea",
    "#ea580c"
];


// ======================================================
// ELEMENTS
// ======================================================


const fileInput =
    document.getElementById("fileInput");


const dropzone =
    document.getElementById("dropzone");


const uploadBtn =
    document.getElementById("uploadBtn");


const analyzeBtn =
    document.getElementById("analyzeBtn");


const removeBtn =
    document.getElementById("removeBtn");


const previewImg =
    document.getElementById("previewImg");


const dzIdle =
    document.getElementById("dzIdle");


const dzPreview =
    document.getElementById("dzPreview");


const errorCard =
    document.getElementById("errorCard");


const errorMessage =
    document.getElementById("errorMessage");


const dismissErrorBtn =
    document.getElementById("dismissErrorBtn");


const results =
    document.getElementById("results");


const cornerCount =
    document.getElementById("cornerCount");


const bandEmoji =
    document.getElementById("bandEmoji");


const bandName =
    document.getElementById("bandName");


const verdictLine =
    document.getElementById("verdictLine");


const triangleScoreCard =
    document.getElementById("triangleScoreCard");


const scoreValue =
    document.getElementById("scoreValue");


const resultCanvas =
    document.getElementById("resultCanvas");


const legend =
    document.getElementById("legend");


const triangleStats =
    document.getElementById("triangleStats");


const nonTriangleStats =
    document.getElementById("nonTriangleStats");


const statsList =
    document.getElementById("statsList");


const detectedCornerText =
    document.getElementById("detectedCornerText");


const againBtn =
    document.getElementById("againBtn");


const loadingOverlay =
    document.getElementById("loadingOverlay");


const loadingMsg =
    document.getElementById("loadingMsg");


// ======================================================
// VARIABLES
// ======================================================


let selectedFile = null;

let loadingTimer = null;

let scanOverlay = null;


const ACCEPTED_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp"
];


const MAX_SIZE =
    8 * 1024 * 1024;


// ======================================================
// FILE INPUT
// ======================================================


dropzone.addEventListener(
    "click",
    () => {

        fileInput.click();

    }
);


uploadBtn.addEventListener(
    "click",
    () => {

        fileInput.click();

    }
);


fileInput.addEventListener(
    "change",
    event => {

        if (
            event.target.files.length
        ) {

            setFile(
                event.target.files[0]
            );

        }

    }
);


// ======================================================
// DRAG + DROP
// ======================================================


dropzone.addEventListener(
    "dragover",
    event => {

        event.preventDefault();

        dropzone.classList.add(
            "dragover"
        );

    }
);


dropzone.addEventListener(
    "dragleave",
    event => {

        event.preventDefault();

        dropzone.classList.remove(
            "dragover"
        );

    }
);


dropzone.addEventListener(
    "drop",
    event => {

        event.preventDefault();

        dropzone.classList.remove(
            "dragover"
        );


        const file =
            event.dataTransfer.files[0];


        if (file) {

            setFile(file);

        }

    }
);


// ======================================================
// BUTTONS
// ======================================================


removeBtn.addEventListener(
    "click",
    event => {

        event.stopPropagation();

        clearFile();

    }
);


analyzeBtn.addEventListener(
    "click",
    () => {

        if (selectedFile) {

            analyzeImage();

        }

    }
);


againBtn.addEventListener(
    "click",
    () => {

        clearFile();

        results.hidden = true;

        errorCard.hidden = true;


        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });

    }
);


dismissErrorBtn.addEventListener(
    "click",
    () => {

        errorCard.hidden = true;

    }
);


// ======================================================
// SET FILE
// ======================================================


function setFile(file) {

    if (
        !ACCEPTED_TYPES.includes(
            file.type
        )
    ) {

        showError(
            "Please use JPG, PNG or WebP."
        );

        return;

    }


    if (
        file.size > MAX_SIZE
    ) {

        showError(
            "Maximum image size is 8 MB."
        );

        return;

    }


    selectedFile = file;


    previewImg.src =
        URL.createObjectURL(
            file
        );


    dzIdle.hidden = true;

    dzPreview.hidden = false;


    analyzeBtn.disabled = false;


    errorCard.hidden = true;

    results.hidden = true;

}


// ======================================================
// CLEAR FILE
// ======================================================


function clearFile() {

    selectedFile = null;


    fileInput.value = "";


    previewImg.src = "";


    dzIdle.hidden = false;

    dzPreview.hidden = true;


    analyzeBtn.disabled = true;


    removeScanAnimation();

}


// ======================================================
// SCAN OVERLAY
// ======================================================


function startScanAnimation() {

    removeScanAnimation();


    dzPreview.classList.add(
        "scanning"
    );


    scanOverlay =
        document.createElement(
            "div"
        );


    scanOverlay.className =
        "scan-overlay";


    scanOverlay.innerHTML = `

        <div class="scan-line"></div>

        <div class="scan-label">
            Scanning Shape
        </div>

    `;


    dzPreview.appendChild(
        scanOverlay
    );

}


function removeScanAnimation() {

    dzPreview.classList.remove(
        "scanning"
    );


    if (scanOverlay) {

        scanOverlay.remove();

        scanOverlay = null;

    }

}


// ======================================================
// ANALYZE
// ======================================================


async function analyzeImage() {

    if (!selectedFile) {

        return;

    }


    startScanAnimation();

    showLoading();


    const formData =
        new FormData();


    formData.append(
        "image",
        selectedFile,
        selectedFile.name
    );


    /*
       Small delay so the user can actually
       see the scanning animation.
    */

    await wait(1200);


    try {

        const response =
            await fetch(
                "/api/analyze",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            showError(
                data.error ||
                `Server error ${response.status}`
            );

            return;

        }


        if (!data.success) {

            showError(
                data.error ||
                "Shape detection failed."
            );

            return;

        }


        /*
          Let the scanner finish visually.
        */

        await wait(700);


        renderResults(
            data
        );

    }

    catch (error) {

        console.error(
            "TRIMOSA ERROR:",
            error
        );


        showError(
            "Could not reach Trimosa. Make sure python app.py is running."
        );

    }

    finally {

        removeScanAnimation();

        hideLoading();

    }

}


// ======================================================
// WAIT HELPER
// ======================================================


function wait(milliseconds) {

    return new Promise(
        resolve =>
            setTimeout(
                resolve,
                milliseconds
            )
    );

}


// ======================================================
// LOADING
// ======================================================


function showLoading() {

    let index = 0;


    loadingMsg.textContent =
        LOADING_MESSAGES[index];


    loadingTimer =
        setInterval(
            () => {

                index =
                    (
                        index + 1
                    )
                    %
                    LOADING_MESSAGES.length;


                loadingMsg.textContent =
                    LOADING_MESSAGES[index];

            },
            850
        );


    loadingOverlay.hidden =
        false;

}


function hideLoading() {

    clearInterval(
        loadingTimer
    );


    loadingOverlay.hidden =
        true;

}


// ======================================================
// ERROR
// ======================================================


function showError(message) {

    errorMessage.textContent =
        message;


    errorCard.hidden =
        false;


    errorCard.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });

}


// ======================================================
// RESULT
// ======================================================


function renderResults(data) {

    const resultHeader =
        document.querySelector(
            ".result-header"
        );


    resultHeader.classList.remove(
        "matched",
        "not-matched"
    );


    /*
       For Trimosa:
       exactly 3 detected corners = shape matched.
    */

    if (
        data.corner_count === 3
    ) {

        resultHeader.classList.add(
            "matched"
        );

    }

    else {

        resultHeader.classList.add(
            "not-matched"
        );

    }


    cornerCount.textContent =
        data.corner_count;


    /*
       MATCHED / NOT MATCHED heading
    */

    if (
        data.corner_count === 3
    ) {

        bandEmoji.textContent =
            "✅";


        bandName.textContent =
            "MATCHED";


        verdictLine.textContent =
            "Shape matches the required 3-corner samosa geometry.";

    }

    else {

        bandEmoji.textContent =
            "✕";


        bandName.textContent =
            "NOT MATCHED";


        verdictLine.textContent =
            `${data.corner_count} significant corner${data.corner_count === 1 ? "" : "s"} detected. Required samosa shape: 3 corners.`;

    }


    // ==================================================
    // CORNER LEGEND
    // ==================================================


    legend.innerHTML =
        data.corners

        .map(
            (corner, index) => {

                const color =
                    COLORS[
                        index %
                        COLORS.length
                    ];


                let angleText = "";


                if (
                    corner.angle !== undefined &&
                    Number(corner.angle) > 0
                ) {

                    angleText =
                        ` · ${Number(corner.angle).toFixed(1)}°`;

                }


                let perfectionText = "";


                if (
                    corner.perfection !== undefined
                ) {

                    perfectionText =
                        ` · ${Number(corner.perfection).toFixed(1)}%`;

                }


                return `

                    <span
                        class="legend-item"
                        style="animation-delay:${index * 0.12}s"
                    >

                        <span
                            class="legend-dot"
                            style="
                                background:${color};
                                color:${color};
                            "
                        ></span>

                        Corner ${corner.label}
                        ${angleText}
                        ${perfectionText}

                    </span>

                `;

            }
        )

        .join("");


    // ==================================================
    // TRIANGLE / SAMOSA
    // ==================================================


    if (
        data.is_triangle &&
        data.score !== null &&
        data.score !== undefined &&
        data.stats
    ) {

        triangleScoreCard.hidden =
            false;


        triangleStats.hidden =
            false;


        nonTriangleStats.hidden =
            true;


        /*
           Count score from zero.
        */

        animateScore(
            Number(
                data.score
            )
        );


        statsList.innerHTML = `

            <li>

                <span>
                    Shape comparison
                </span>

                <strong>
                    MATCHED ✓
                </strong>

            </li>


            <li>

                <span>
                    Corners detected
                </span>

                <strong>
                    3
                </strong>

            </li>


            <li>

                <span>
                    Ideal samosa angles
                </span>

                <strong>
                    60° · 60° · 60°
                </strong>

            </li>


            <li>

                <span>
                    Total angle
                </span>

                <strong>
                    ${Number(data.stats.total_angle).toFixed(1)}°
                </strong>

            </li>


            <li>

                <span>
                    Average angle
                </span>

                <strong>
                    ${Number(data.stats.average_angle).toFixed(1)}°
                </strong>

            </li>


            <li>

                <span>
                    Sharpest corner
                </span>

                <strong>

                    ${data.stats.sharpest.label}

                    ·

                    ${Number(data.stats.sharpest.angle).toFixed(1)}°

                </strong>

            </li>


            <li>

                <span>
                    Widest corner
                </span>

                <strong>

                    ${data.stats.widest.label}

                    ·

                    ${Number(data.stats.widest.angle).toFixed(1)}°

                </strong>

            </li>


            <li>

                <span>
                    Symmetry
                </span>

                <strong>
                    ${Number(data.stats.symmetry).toFixed(1)}%
                </strong>

            </li>

        `;

    }


    // ==================================================
    // NON TRIANGLE
    // ==================================================


    else {

        triangleScoreCard.hidden =
            true;


        triangleStats.hidden =
            true;


        nonTriangleStats.hidden =
            false;


        detectedCornerText.textContent =
            data.corner_count;


        const details =
            data.corners

            .map(
                corner => {

                    const angle =
                        Number(corner.angle) > 0
                        ?
                        `${Number(corner.angle).toFixed(1)}°`
                        :
                        "—";


                    const perfection =
                        corner.perfection !== undefined
                        ?
                        `${Number(corner.perfection).toFixed(1)}%`
                        :
                        "—";


                    return `

                        <li>

                            <span>
                                Corner ${corner.label}
                            </span>

                            <strong>
                                ${angle}
                            </strong>

                        </li>


                        <li>

                            <span>
                                Corner ${corner.label} perfection
                            </span>

                            <strong>
                                ${perfection}
                            </strong>

                        </li>

                    `;

                }
            )

            .join("");


        nonTriangleStats.innerHTML = `

            <p class="non-triangle-message">

                <strong>
                    NOT MATCHED ✕
                </strong>

                <br><br>

                Required samosa shape:
                <strong>
                    3 significant corners.
                </strong>

            </p>


            <p>

                Detected:

                <strong>
                    ${data.corner_count}
                </strong>

                corner${data.corner_count === 1 ? "" : "s"}.

            </p>


            ${
                data.corners.length
                ?
                `

                    <ul class="stats-list">

                        ${details}

                    </ul>

                `
                :
                ""
            }

        `;

    }


    // ==================================================
    // DRAW ANIMATED OVERLAY
    // ==================================================


    drawOverlayAnimated(
        data
    );


    results.hidden =
        false;


    results.classList.remove(
        "result-enter"
    );


    void results.offsetWidth;


    results.classList.add(
        "result-enter"
    );


    results.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


// ======================================================
// SCORE COUNT UP
// ======================================================


function animateScore(finalScore) {

    const duration =
        1000;


    const start =
        performance.now();


    const scoreContainer =
        scoreValue.parentElement;


    scoreContainer.classList.remove(
        "score-pop"
    );


    void scoreContainer.offsetWidth;


    scoreContainer.classList.add(
        "score-pop"
    );


    function update(now) {

        const elapsed =
            now - start;


        const progress =
            Math.min(
                elapsed / duration,
                1
            );


        /*
           Ease-out animation
        */

        const eased =
            1 -
            Math.pow(
                1 - progress,
                3
            );


        const value =
            finalScore *
            eased;


        scoreValue.textContent =
            value.toFixed(1);


        if (
            progress < 1
        ) {

            requestAnimationFrame(
                update
            );

        }

    }


    requestAnimationFrame(
        update
    );

}


// ======================================================
// ANIMATED CANVAS
// ======================================================


function drawOverlayAnimated(data) {

    const canvas =
        resultCanvas;


    const ctx =
        canvas.getContext(
            "2d"
        );


    const image =
        previewImg;


    function startDrawing() {

        const parent =
            canvas.parentElement;


        const maxWidth =
            parent.clientWidth - 20;


        const originalWidth =
            Number(
                data.image_width
            );


        const originalHeight =
            Number(
                data.image_height
            );


        const displayWidth =
            Math.min(
                maxWidth,
                originalWidth
            );


        const scale =
            displayWidth /
            originalWidth;


        canvas.width =
            Math.round(
                originalWidth *
                scale
            );


        canvas.height =
            Math.round(
                originalHeight *
                scale
            );


        const points =
            data.corners.map(
                corner => ({
                    x:
                        Number(corner.x) *
                        scale,

                    y:
                        Number(corner.y) *
                        scale
                })
            );


        let progress =
            0;


        const duration =
            1100;


        let startTime =
            null;


        function animate(time) {

            if (!startTime) {

                startTime =
                    time;

            }


            progress =
                Math.min(
                    (
                        time -
                        startTime
                    )
                    /
                    duration,
                    1
                );


            ctx.clearRect(
                0,
                0,
                canvas.width,
                canvas.height
            );


            ctx.drawImage(
                image,
                0,
                0,
                canvas.width,
                canvas.height
            );


            /*
               Dark computer vision tint
            */

            ctx.fillStyle =
                "rgba(0,20,30,0.09)";


            ctx.fillRect(
                0,
                0,
                canvas.width,
                canvas.height
            );


            if (
                points.length >= 2
            ) {

                drawProgressivePolygon(
                    ctx,
                    points,
                    progress,
                    data.corner_count === 3
                );

            }


            drawProgressiveCorners(
                ctx,
                data,
                points,
                progress
            );


            if (
                progress < 1
            ) {

                requestAnimationFrame(
                    animate
                );

            }

        }


        requestAnimationFrame(
            animate
        );

    }


    if (
        image.complete &&
        image.naturalWidth
    ) {

        startDrawing();

    }

    else {

        image.onload =
            startDrawing;

    }

}


// ======================================================
// POLYGON DRAWING
// ======================================================


function drawProgressivePolygon(
    ctx,
    points,
    progress,
    matched
) {

    const totalSegments =
        points.length;


    const amount =
        progress *
        totalSegments;


    ctx.beginPath();


    ctx.moveTo(
        points[0].x,
        points[0].y
    );


    for (
        let i = 0;
        i < totalSegments;
        i++
    ) {

        const segmentProgress =
            Math.max(
                0,
                Math.min(
                    1,
                    amount - i
                )
            );


        if (
            segmentProgress <= 0
        ) {

            break;

        }


        const start =
            points[i];


        const end =
            points[
                (i + 1)
                %
                points.length
            ];


        const x =
            start.x +
            (
                end.x -
                start.x
            )
            *
            segmentProgress;


        const y =
            start.y +
            (
                end.y -
                start.y
            )
            *
            segmentProgress;


        ctx.lineTo(
            x,
            y
        );

    }


    ctx.strokeStyle =
        matched
        ?
        "#22c55e"
        :
        "#ef4444";


    ctx.lineWidth =
        4;


    ctx.lineJoin =
        "round";


    ctx.shadowColor =
        matched
        ?
        "#22c55e"
        :
        "#ef4444";


    ctx.shadowBlur =
        16;


    ctx.stroke();


    ctx.shadowBlur =
        0;


    /*
       Fill only when finished
    */

    if (
        progress > 0.95 &&
        points.length >= 3
    ) {

        ctx.beginPath();


        ctx.moveTo(
            points[0].x,
            points[0].y
        );


        for (
            let i = 1;
            i < points.length;
            i++
        ) {

            ctx.lineTo(
                points[i].x,
                points[i].y
            );

        }


        ctx.closePath();


        ctx.fillStyle =
            matched
            ?
            "rgba(34,197,94,0.12)"
            :
            "rgba(239,68,68,0.10)";


        ctx.fill();

    }

}


// ======================================================
// CORNER MARKERS
// ======================================================


function drawProgressiveCorners(
    ctx,
    data,
    points,
    progress
) {

    data.corners.forEach(
        (corner, index) => {

            const revealPoint =
                (
                    index + 1
                )
                /
                (
                    data.corners.length + 1
                );


            if (
                progress <
                revealPoint
            ) {

                return;

            }


            const localProgress =
                Math.min(
                    (
                        progress -
                        revealPoint
                    )
                    *
                    8,
                    1
                );


            const point =
                points[index];


            const color =
                data.corner_count === 3
                ?
                "#22c55e"
                :
                COLORS[
                    index %
                    COLORS.length
                ];


            const radius =
                10 *
                localProgress;


            /*
               Glow
            */

            ctx.beginPath();


            ctx.arc(
                point.x,
                point.y,
                radius + 6,
                0,
                Math.PI * 2
            );


            ctx.fillStyle =
                hexToRGBA(
                    color,
                    0.18
                );


            ctx.fill();


            /*
               Actual marker
            */

            ctx.beginPath();


            ctx.arc(
                point.x,
                point.y,
                radius,
                0,
                Math.PI * 2
            );


            ctx.fillStyle =
                color;


            ctx.shadowColor =
                color;


            ctx.shadowBlur =
                18;


            ctx.fill();


            ctx.shadowBlur =
                0;


            ctx.strokeStyle =
                "#ffffff";


            ctx.lineWidth =
                3;


            ctx.stroke();


            if (
                localProgress <
                0.8
            ) {

                return;

            }


            let label =
                `Corner ${corner.label}`;


            if (
                Number(corner.angle) > 0
            ) {

                label +=
                    ` · ${Number(corner.angle).toFixed(1)}°`;

            }


            ctx.font =
                "800 15px Nunito, sans-serif";


            ctx.textAlign =
                "center";


            ctx.textBaseline =
                "middle";


            const width =
                ctx.measureText(
                    label
                ).width +
                16;


            const height =
                26;


            let labelX =
                point.x;


            let labelY =
                point.y - 32;


            if (
                labelY <
                25
            ) {

                labelY =
                    point.y + 34;

            }


            labelX =
                Math.max(
                    width / 2,
                    Math.min(
                        canvas.width -
                        width / 2,
                        labelX
                    )
                );


            ctx.fillStyle =
                "rgba(8,25,32,0.88)";


            ctx.fillRect(
                labelX -
                width / 2,
                labelY -
                height / 2,
                width,
                height
            );


            ctx.fillStyle =
                "#ffffff";


            ctx.fillText(
                label,
                labelX,
                labelY
            );

        }
    );

}


// ======================================================
// COLOR HELPER
// ======================================================


function hexToRGBA(
    hex,
    alpha
) {

    const value =
        hex.replace(
            "#",
            ""
        );


    const r =
        parseInt(
            value.substring(
                0,
                2
            ),
            16
        );


    const g =
        parseInt(
            value.substring(
                2,
                4
            ),
            16
        );


    const b =
        parseInt(
            value.substring(
                4,
                6
            ),
            16
        );


    return `rgba(${r},${g},${b},${alpha})`;

}