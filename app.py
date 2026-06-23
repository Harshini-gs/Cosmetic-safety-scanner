from flask import Flask, render_template, request
import os
import pandas as pd
import re
from backend.image_scanner import extract_text_from_image
from backend.ingredient_analyzer import analyze_ingredients

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/scan", methods=["POST"])
def scan():
    if "image" not in request.files:
        return "No file uploaded ❌"

    file = request.files["image"]

    if file.filename == "":
        return "No selected file ❌"

    skin_type = request.form.get("skin_type", "normal")
    pregnancy_check = request.form.get("pregnancy_check") == "yes"

    filename = "uploaded.jpg"
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(image_path)

    text = extract_text_from_image(image_path)

    if not text.strip():
        return render_template(
            "result.html",
            extracted_text="No text detected ❌",
            filtered_text="",
            results=[],
            score=0,
            verdict="No Data",
            safety_percent=0,
            recommendation="No recommendation available",
            risk_summary={"High": 0, "Moderate": 0, "Safe": 0},
            skin_type=skin_type,
            pregnancy_check=pregnancy_check,
            pregnancy_alerts=[],
            image_path=image_path
        )

    print("OCR TEXT:", text)

    data = pd.read_csv("dataset/ingredients.csv")
    valid_ingredients = set(data["name"].dropna().str.lower().str.strip())

    clean_text = re.sub(r"[^a-zA-Z0-9\s\-]", " ", text.lower())
    clean_text = re.sub(r"\s+", " ", clean_text).strip()

    filtered_set = set()

    aliases = {
        "water": "water",
        "aqua": "water",

        "glycerin": "glycerin",
        "glycerine": "glycerin",
        "glycerol": "glycerin",

        "propylene glycol": "propylene glycol",

        "sodium lactate": "sodium lactate",

        "glycyrrhiza glabra": "glycyrrhiza glabra",
        "licorice": "glycyrrhiza glabra",
        "liquorice": "glycyrrhiza glabra",

        "salvia rosmarinus": "salvia rosmarinus",
        "rosemary": "salvia rosmarinus",
        "rose hydrosol": "rose hydrosol",

        "rhaphiolepis indica": "rhaphiolepis indica",
        "snow white": "rhaphiolepis indica",

        "germall ii": "germall ii",
        "germall": "germall ii",

        "ethyl alcohol": "alcohol",
        "ethanol": "alcohol",
        "alcohol": "alcohol",

        "heparin sodium": "heparin sodium",
        "sodium heparin": "heparin sodium",

        "hydrolysed gelatin": "gelatin",
        "hydrolyzed gelatin": "gelatin",
        "gelatin": "gelatin",

        "microcrystalline cellulose": "microcrystalline cellulose",
        "cellulose": "cellulose",

        "maltodextrin": "maltodextrin",
        "carrageenan": "carrageenan",
        "caramel coloring": "caramel",
        "liquid caramel coloring": "caramel",
        "caramel": "caramel",

        "xanthan": "xanthan gum",
        "xanthan gum": "xanthan gum",

        "locust bean gum": "locust bean gum",
        "orange oil": "orange oil",
        "duck oil": "duck oil",
        "textra starch": "starch",
        "starch": "starch"
    }

    # 1. Alias matching
    for alias, canonical in aliases.items():
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, clean_text):
            filtered_set.add(canonical)

    # 2. Exact phrase matching from dataset
    for ingredient in valid_ingredients:
        ingredient_clean = ingredient.lower().strip()

        if len(ingredient_clean) > 3:
            pattern = r"\b" + re.escape(ingredient_clean) + r"\b"

            if re.search(pattern, clean_text):
                filtered_set.add(ingredient_clean)

    filtered = sorted(list(filtered_set))
    filtered_text = ", ".join(filtered)

    print("FILTERED INGREDIENTS:", filtered_text)

    results, score, verdict, safety_percent, recommendation, risk_summary, pregnancy_alerts = analyze_ingredients(
        filtered_text,
        skin_type,
        pregnancy_check
    )

    return render_template(
        "result.html",
        extracted_text=text,
        filtered_text=filtered_text,
        results=results,
        score=score,
        verdict=verdict,
        safety_percent=safety_percent,
        recommendation=recommendation,
        risk_summary=risk_summary,
        skin_type=skin_type,
        pregnancy_check=pregnancy_check,
        pregnancy_alerts=pregnancy_alerts,
        image_path=image_path
    )


if __name__ == "__main__":
    app.run(debug=True)