<img width="1280" height="640" alt="git (1)" src="https://github.com/user-attachments/assets/8920b256-2ba8-4988-b824-5351134eb4bd" />



# [Trimosa] 🎯


## Basic Details
### Team Name: [Hana Dhaniya]


### Team Members
- Team Lead: [Hana CK] - [KAHM Unity Womens College (Autonomous),Manjeri]
- Member 2: [Dhaniya KM] - [KAHM Unity Womens College (Autonomous),Manjeri]

### Project Description
[Trimosa is a fun AI/computer-vision-based food shape analysis project that detects an object's significant corners using OpenCV. It analyzes samosa geometry, measures corner angles, and calculates how closely a three-corner shape matches the ideal triangular samosa.]

### The Problem (that doesn't exist)
[Samosas are everywhere, but nobody is asking the important question: Are their corners geometrically perfect? Humanity has survived far too long without scientifically judging samosa triangles.]

### The Solution (that nobody asked for)
[Trimosa uses computer vision to detect an uploaded food's shape, count its significant corners, and measure their angles. If it finds three corners, it compares them with the ideal 60°–60°–60° samosa and awards a completely unnecessary Trimosa Perfection Score.]

## Technical Details
### Technologies/Components Used
For Software:
- [Python, HTML, CSS, JavaScript]
- [Flask]
- [OpenCV (opencv-python), NumPy, Pillow]
- [Visual Studio Code, Git, GitHub, Render, Web Browser]

For Hardware:
- [Laptop/Desktop computer]
- [Minimum 4 GB RAM, dual-core processor, and sufficient storage to run Python and OpenCV]
- [Tools required: Smartphone/camera for capturing food images and an internet connection for accessing the deployed web application]

### Implementation
For Software:
# Installation
[pip install -r requirements.txt]

# Run
[python app.py]

### Project Documentation
For Software:

# Screenshots (Add at least 3)
(<img src="img4.png">)
*Trimosa home page showing the image upload interface where users can upload a food image for shape and corner analysis.*

![Screenshot2](<img src="img3.png">)
*AImage preview and scanning stage, where Trimosa prepares the uploaded food image for computer vision analysis.*

![Screenshot3](<img src="img2.png">)
**Shape analysis result showing the detected significant corners and geometric information identified using OpenCV.*

![Screenshot3](<img src="img1.png">)
*Final Trimosa result displaying the detected corner count, shape classification, and analysis verdict.*

# Diagrams
![Workflow](
┌─────────────────────┐
│     User / Browser  │
│  Upload Food Image  │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│   HTML / CSS / JS   │
│    Web Interface    │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│    Flask Backend    │
│     Python API      │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ OpenCV Image        │
│ Preprocessing       │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Contour & Shape     │
│ Detection           │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Significant Corner  │
│ Detection           │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Corner Count &      │
│ Angle Calculation   │
└──────────┬──────────┘
           ↓
      ┌────┴─────┐
      │3 Corners?│
      └──┬────┬──┘
       YES    NO
        ↓      ↓
  Trimosa    Display
   Score     Detected
 + Verdict    Shape
        └──┬───┘
           ↓
┌─────────────────────┐
│ Results Displayed   │
│     to User         │
└─────────────────────┘)
*Trimosa workflow: The uploaded food image is processed using Flask and OpenCV to detect the food's shape and significant corners. If three corners are detected, their angles are analyzed to generate the Trimosa Score and verdict.*

For Hardware:

# Schematic & Circuit
![Circuit](Add your circuit diagram here)
*Add caption explaining connections*

![Schematic](Add your schematic diagram here)
*Add caption explaining the schematic*

# Build Photos
![Components](Add photo of your components here)
*List out all components shown*

![Build](Add photos of build process here)
*Explain the build steps*

![Final](Add photo of final product here)
*Explain the final build*

### Project Demo
# Video
[(https://drive.google.com/file/d/1tZsVkTSZ6CENNhpf8S8V25zECZ7BJHGU/view?usp=drive_link)]
*The demo video shows the complete working of Trimosa — uploading a food image, scanning and processing the image, detecting significant corners, analyzing the shape and corner angles, and displaying the final Trimosa score and verdict for a three-corner samosa.*

# Additional Demos
[Add any extra demo materials/links]

## Team Contributions
- [Hana CK]: [Developed the frontend interface, UI/UX design, animations, testing, documentation, and project presentation.]
- [Dhaniya KM]: [Developed the OpenCV-based image processing, shape and corner detection, angle calculations, and integration of the analysis system with the frontend.]

---
Made with ❤️ at TinkerHub Useless Projects 

![Static Badge](https://img.shields.io/badge/TinkerHub-24?color=%23000000&link=https%3A%2F%2Fwww.tinkerhub.org%2F)
![Static Badge](https://img.shields.io/badge/UselessProjects--26-26?link=https%3A%2F%2Ftinkerhub.org%2Fevents%2F1M8ORET9A1%2Fuseless-projects-3.0)



