import easyocr
import re
import os
import numpy as np
from PIL import Image

reader = easyocr.Reader(['en'])

def extract_text_from_image(image_path):

    if not os.path.exists(image_path):
        print("❌ Path not found:", image_path)
        return ""

    try:
        img = Image.open(image_path).convert("RGB")
        img_np = np.array(img)
    except Exception as e:
        print("❌ Image open error:", e)
        return ""

    result = reader.readtext(img_np)

    if not result:
        print("❌ No text detected")
        return ""

    text = " ".join([res[1] for res in result])

    print("🔥 OCR OUTPUT:", text)

    text = text.lower()
    text = re.sub(r'[^a-zA-Z ]', ' ', text)

    return text