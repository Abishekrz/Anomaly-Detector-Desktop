# utils/viz.py
from PIL import Image, ImageDraw, ImageFont

def draw_boxes(img_path, detections, save_path):
    try:
        img = Image.open(img_path).convert("RGB")
    except:
        print("ERROR: Failed to load image:", img_path)
        return

    draw = ImageDraw.Draw(img)

    # Default font
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    for det in detections:
        try:
            x1, y1, x2, y2 = det["bbox"]
            label = f"{det['label']} ({det['confidence']:.2f})"

            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline="red", width=3)

            # Text box
            text_w, text_h = draw.textbbox((0, 0), label, font=font)[2:]
            draw.rectangle([x1, y1 - text_h, x1 + text_w, y1], fill="red")
            draw.text((x1, y1 - text_h), label, fill="white", font=font)

        except Exception as e:
            print("Annotation error:", e)

    img.save(save_path)
    print("Annotation saved:", save_path)
