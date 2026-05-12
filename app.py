import streamlit as st
from PIL import Image, ImageDraw
import uuid
import os
import io

from get_data import Picture
from font import *
from logo import logo
from border import *

st.title("📸 폴라로이드 스타일 사진 프레임 생성기")

uploaded_files = st.file_uploader("사진들을 업로드하세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files is not None:
    temp_file_paths = []

    for uploaded_file in uploaded_files:
        unique_id = uuid.uuid4().hex
        temp_path = f"temp_{unique_id}_{uploaded_file.name}"
        temp_file_paths.append(temp_path)

        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            picture = Picture(temp_path)
            image = picture.get_image()
            if image is None:
                raise ValueError("이미지가 손상되었거나 메타데이터가 없습니다.")

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

                return canvas

            base_canvas = add_border()
            final_canvas = place_model(base_canvas)

            st.image(final_canvas, caption="결과물 미리보기", use_container_width=True)

            buf = io.BytesIO()
            final_canvas.save(buf, format="JPEG", quality=95)
            st.download_button(
                label=f"{uploaded_file.name} 저장",
                data=buf.getvalue(),
                file_name=f"result_{uploaded_file.name}",
                key=unique_id
            )
        except Exception as e:
            # 메타데이터를 못 읽거나 처리 중 에러가 발생한 파일은 건너뛰고 경고 표시
            st.error(f"⚠️ '{uploaded_file.name}' 처리 중 오류 발생: 메타데이터를 읽을 수 없거나 지원하지 않는 형식입니다. (에러: {e})")
            continue
        st.divider()

        for path in temp_file_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass