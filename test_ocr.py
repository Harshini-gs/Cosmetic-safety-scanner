from backend.image_scanner import extract_text_from_image

text = extract_text_from_image("static/uploads/uploaded.jpg")

print("OCR OUTPUT:\n", text)