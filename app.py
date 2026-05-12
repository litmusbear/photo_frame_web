import streamlit as st
from PIL import Image, ImageDraw
import os

from get_data import Picture
from font import *
from logo import logo
from border import *

st.title("📸 필름 스타일 사진 보더 생성기")

uploaded_file = st.file_uploader("사진을 업로드하세요", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:

    original_file_name = uploaded_file.name
    temp_path = f"temp_{original_file_name}"

    with open("temp_image.jpg", "wb") as f:
        f.write(uploaded_file.getbuffer())

    picture = Picture("temp_image.jpg")
    image = picture.get_image()

    width, height = image.size
    thickness = get_thickness(height)
    padding = get_padding(height)
    logo_file = logo(picture)


    def add_border():
        border_width = width + (thickness * 2)
        border_height = height + thickness + padding

        canvas = Image.new("RGB", (border_width, border_height), (255, 255, 255))
        canvas.paste(image, (thickness, thickness))

        return canvas


    def place_model(canvas):
        font = set_font(padding)
        font_regular = regular(padding)
        font_date = date_font(padding)

        size, date_font_size = font_size(padding)
        text_camera = picture.get_camera()
        draw = ImageDraw.Draw(canvas)

        canvas_width = width + (thickness * 2)

        center_y = height + (padding // 2)
        right_margin = thickness * 2
        info_x = canvas_width - right_margin
        line_spacing = int(size * 0.2)
        total_text_height = size + line_spacing + date_font_size
        start_y = height + (padding - total_text_height) // 2
        visual_center_y = int(start_y + (size * 0.52))
        spacing = int(width * 0.012)
        text_info = f"f/{picture.get_f_number()}  {picture.get_shutter()}  ISO{picture.get_iso()}"
        text_date = picture.get_datetime()
        info_bbox = draw.textbbox((info_x, start_y), text_info, font=font_regular, anchor="ra")
        current_left_x = info_bbox[0] - spacing
        bar_h = int(size * 0.7)
        draw.line([
            (current_left_x, visual_center_y - bar_h // 2),
            (current_left_x, visual_center_y + bar_h // 2)
        ], fill=(220, 220, 220), width=2)

        current_left_x -= spacing

        draw.text((thickness * 2, center_y), text_camera, fill=(0, 0, 0), font=font, anchor="lm")
        draw.text((info_x, start_y), text_info, fill=(50, 50, 50), font=font_regular, anchor="ra")
        if text_date:
            date_y = start_y + size + line_spacing
            draw.text((info_x, date_y), text_date, fill=(140, 140, 140), font=font_date, anchor="ra")

        if logo_file and os.path.exists(logo_file):
            logo_img = Image.open(logo_file).convert("RGBA")
            logo_h = int(size * 0.95)
            logo_w = int(logo_img.width * (logo_h / logo_img.height))
            logo_img = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)

            logo_x = int(current_left_x - logo_w)
            logo_y = int(visual_center_y - (logo_h // 2))
            canvas.paste(logo_img, (logo_x, logo_y), logo_img)

        base = os.path.splitext(original_file_name) [0]
        output_path = f"{base}-watermarked.jpg"
        canvas.save(output_path, quality=95)
        print(f"저장 완료: {output_path}")
        return canvas

    canvas = place_model(add_border())

    st.image(canvas, caption="결과물 미리보기", use_container_width=True)

    import io

    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=95)
    st.download_button("사진 저장하기", buf.getvalue(), "result.jpg", "image/jpeg")