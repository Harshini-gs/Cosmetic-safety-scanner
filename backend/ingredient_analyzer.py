import pandas as pd
from fuzzywuzzy import process

data = pd.read_csv("dataset/ingredient_info_large.csv")

ingredient_list = data["ingredient"].str.lower().tolist()


def get_best_match(word):
    result = process.extractOne(word, ingredient_list)

    if result:
        match, score = result

        if score >= 85:
            return match

    return None


# =========================
# CATEGORY DETECTION
# =========================
def detect_category(ingredient):
    ing = ingredient.lower()

    categories = {
        "Preservative": [
            "paraben", "phenoxyethanol", "formaldehyde",
            "dmdm", "triclosan"
        ],

        "Alcohol": [
            "alcohol", "ethanol", "isopropyl"
        ],

        "Fragrance": [
            "fragrance", "parfum", "essential oil"
        ],

        "Humectant": [
            "glycerin", "glycol", "hyaluronic",
            "sorbitol", "propylene glycol"
        ],

        "Oil / Emollient": [
            "oil", "petrolatum", "lanolin",
            "butter"
        ],

        "Acid / Exfoliant": [
            "acid", "bha", "aha", "salicylic",
            "glycolic", "lactic"
        ],

        "Surfactant / Cleanser": [
            "sulfate", "sodium lauryl sulfate",
            "cocamidopropyl"
        ],

        "Colorant / Pigment": [
            "color", "caramel", "dye",
            "pigment"
        ],

        "Thickener / Stabilizer": [
            "gum", "cellulose",
            "carrageenan", "starch"
        ]
    }

    for category, keywords in categories.items():

        for keyword in keywords:

            if keyword in ing:
                return category

    return "General"


# =========================
# SAFER ALTERNATIVES
# =========================
def get_safe_alternative(ingredient, risk):
    ing = ingredient.lower()

    if risk == "High":

        if "paraben" in ing:
            return "Choose paraben-free products."

        elif "fragrance" in ing or "parfum" in ing:
            return "Choose fragrance-free products."

        elif "sulfate" in ing:
            return "Use sulfate-free cleansers."

        elif "formaldehyde" in ing:
            return "Avoid formaldehyde-releasing preservatives."

        else:
            return "Consider avoiding this ingredient."

    elif risk == "Moderate":

        if "alcohol" in ing:
            return "Use alcohol-free products if possible."

        elif "acid" in ing:
            return "Use slowly and apply sunscreen."

        elif "glycol" in ing:
            return "Patch test before use."

        else:
            return "Use with caution."

    return "Generally safe for most users."


# =========================
# SKIN TYPE WARNINGS
# =========================
def get_skin_type_warning(ingredient, risk, skin_type):

    ing = ingredient.lower()
    skin_type = skin_type.lower()

    if skin_type == "sensitive":

        if any(x in ing for x in [
            "fragrance", "parfum",
            "alcohol", "acid", "oil"
        ]):
            return "⚠ May irritate sensitive skin."

    elif skin_type == "dry":

        if any(x in ing for x in [
            "alcohol", "sulfate", "acid"
        ]):
            return "⚠ May cause dryness."

    elif skin_type == "oily":

        if any(x in ing for x in [
            "coconut oil",
            "mineral oil",
            "lanolin"
        ]):
            return "⚠ May clog pores."

    return "No specific skin-type warning."


# =========================
# PREGNANCY WARNINGS
# =========================
def check_pregnancy_safety(ingredient):

    ing = ingredient.lower()

    pregnancy_avoid = {
        "retinol":
            "Retinol is generally avoided during pregnancy.",

        "salicylic acid":
            "High concentrations may not be suitable during pregnancy.",

        "hydroquinone":
            "Hydroquinone is usually avoided during pregnancy.",

        "oxybenzone":
            "Oxybenzone may raise pregnancy concerns.",

        "formaldehyde":
            "Formaldehyde-releasing preservatives should be avoided."
    }

    for key, warning in pregnancy_avoid.items():

        if key in ing:
            return warning

    return None


# =========================
# MAIN ANALYSIS
# =========================
def analyze_ingredients(
        ingredients_text,
        skin_type="normal",
        pregnancy_check=False
):

    ingredients = list(set([
        i.strip().lower()
        for i in ingredients_text.split(",")
        if i.strip()
    ]))

    results = []

    total_score = 0

    pregnancy_alerts = []

    for ing in ingredients:

        best_match = get_best_match(ing)

        if best_match:

            row = data[
                data["ingredient"].str.lower() == best_match
            ].iloc[0]

            risk = row["risk"]

            function = row["function"]

            side_effects = row["side_effects"]

            category = detect_category(best_match)

            # RISK SCORE
            if risk.lower() == "high":
                score = 3

            elif risk.lower() == "moderate":
                score = 2

            else:
                score = 1

            total_score += score

            alternative = get_safe_alternative(
                best_match,
                risk
            )

            personal_warning = get_skin_type_warning(
                best_match,
                risk,
                skin_type
            )

            pregnancy_warning = None

            if pregnancy_check:

                pregnancy_warning = check_pregnancy_safety(
                    best_match
                )

                if pregnancy_warning:

                    pregnancy_alerts.append({
                        "ingredient": best_match,
                        "warning": pregnancy_warning
                    })

            results.append({

                "ingredient": best_match,

                "category": category,

                "risk": risk,

                "function": function,

                "side_effects": side_effects,

                "alternative": alternative,

                "personal_warning": personal_warning,

                "pregnancy_warning": pregnancy_warning
            })

    total = len(results)

    if total == 0:

        avg_score = 0

        safety_percent = 0

        verdict = "NO DATA ❌"

        recommendation = "No recommendation available"

    else:

        avg_score = total_score / total

        safe_count = sum(
            1 for item in results
            if item["risk"] == "Safe"
        )

        moderate_count = sum(
            1 for item in results
            if item["risk"] == "Moderate"
        )

        high_count = sum(
            1 for item in results
            if item["risk"] == "High"
        )

        safety_percent = (
            (
                safe_count * 100
            ) + (
                moderate_count * 50
            )
        ) / total

        if avg_score >= 2.5:

            verdict = "UNSAFE ❌"

            recommendation = "❌ Avoid this product"

        elif avg_score >= 1.5:

            verdict = "MODERATE ⚠️"

            recommendation = "⚠ Use with caution"

        else:

            verdict = "SAFE ✅"

            recommendation = "✅ Safe to use"

    priority = {
        "High": 3,
        "Moderate": 2,
        "Safe": 1
    }

    results.sort(
        key=lambda item:
        priority.get(item["risk"], 0),
        reverse=True
    )

    risk_summary = {

        "High": sum(
            1 for item in results
            if item["risk"] == "High"
        ),

        "Moderate": sum(
            1 for item in results
            if item["risk"] == "Moderate"
        ),

        "Safe": sum(
            1 for item in results
            if item["risk"] == "Safe"
        )
    }

    return (
        results,
        round(avg_score, 2),
        verdict,
        round(safety_percent, 2),
        recommendation,
        risk_summary,
        pregnancy_alerts
    )