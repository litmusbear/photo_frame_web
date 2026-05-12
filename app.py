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

if uploaded_files:
    temp_file_paths = []

    for uploaded_file in uploaded_files:
        unique_id = uuid.uuid4().hex
        # 파일명에 공백이나 특수문자가 있을 수 있으므로 안전하게 unique_id 위주로 생성
        temp_path = f"temp_{unique_id}.jpg"
        temp_file_paths.append(temp_path)

        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            # 1. 메타데이터 불러오기 예외 처리
            picture = Picture(temp_path)
            image = picture.get_image()
            if image is None:
                raise ValueError("이미지를 읽을 수 없습니다.")

            width, height = image.size
            thickness = get_thickness(height)
            padding = get_padding(height)
            logo_file = logo(picture)

            # 2. 테두리 추가 함수
            def add_border(img, w, h, t, p):
                border_width = w + (t * 2)
                border_height = h + t + p
                canvas = Image.new("RGB", (border_width, border_height), (255, 255, 255))
                canvas.paste(img, (t, t))
                return canvas

            # 3. 모델명/정보/로고/날짜 배치 함수
            def place_model(canvas, pic, w, h, t, p, l_file):
                font_obj = set_font(p)
                font_reg = regular(p)
                font_dat = date_font(p)
                size, d_size = font_size(p)
                
                draw = ImageDraw.Draw(canvas)
                
                # 메타데이터 가져오기
                text_camera = pic.get_camera()
                text_info = f"f/{pic.get_f_number()}  {pic.get_shutter()}  ISO{pic.get_iso()}"
                text_date = pic.get_datetime()

                canvas_width = canvas.size[0]
                center_y = h + (p // 2)
                info_x = canvas_width - (t * 2)
                
                line_spacing = int(size * 0.2)
                total_text_height = size + line_spacing + d_size
                start_y = h + (p - total_text_height) // 2
                visual_center_y = int(start_y + (size * 0.52))
                spacing = int(w * 0.012)
                
                # [날짜 그리기] - 로고 에러와 상관없이 항상 찍히도록 상단 배치
                if text_date:
                    date_y = start_y + size + line_spacing
                    draw.text((info_x, date_y), text_date, fill=(140, 140, 140), font=font_dat, anchor="ra")

                # 모델명 및 촬영정보 그리기
                draw.text((t * 2, center_y), text_camera, fill=(0, 0, 0), font=font_obj, anchor="lm")
                draw.text((info_x, start_y), text_info, fill=(50, 50, 50), font=font_reg, anchor="ra")

                # [로고 및 구분선 그리기] - 예외 처리 강화
                try:
                    if l_file and os.path.exists(l_file):
                        logo_img = Image.open(l_file).convert("RGBA")
                        logo_h = int(size * 0.95)
                        logo_w = int(logo_img.width * (logo_h / logo_img.height))
                        logo_img = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                        
                        info_bbox = draw.textbbox((info_x, start_y), text_info, font=font_reg, anchor="ra")
                        current_left_x = info_bbox[0] - spacing
                        
                        # 구분선
                        bar_h = int(size * 0.7)
                        draw.line([
                            (current_left_x, visual_center_y - bar_h // 2),
                            (current_left_x, visual_center_y + bar_h // 2)
                        ], fill=(220, 220, 220), width=2)

                        # 로고 붙이기
                        logo_x = int(current_left_x - spacing - logo_w)
                        logo_y = int(visual_center_y - (logo_h // 2))
                        canvas.paste(logo_img, (logo_x, logo_y), logo_img)
                except Exception as logo_err:
                    st.warning(f"로고를 불러오는 중 문제가 발생했습니다: {logo_err}")

                return canvas

            # 결과물 생성 실행
            base_canvas = add_border(image, width, height, thickness, padding)
            final_canvas = place_model(base_canvas, picture, width, height, thickness, padding, logo_file)

            # 화면 표시
            st.image(final_canvas, caption=f"결과물: {uploaded_file.name}", use_container_width=True)

            # 다운로드 버튼
            buf = io.BytesIO()
            final_canvas.save(buf, format="JPEG", quality=95)
            st.download_button(
                label=f"{uploaded_file.name} 저장",
                data=buf.getvalue(),
                file_name=f"result_{uploaded_file.name}",
                key=unique_id
            )
            
        except Exception as e:
            st.error(f"⚠️ '{uploaded_file.name}' 처리 중 오류 발생: {e}")
            continue
            
        st.divider()

    # 모든 처리가 끝난 후 임시 파일 일괄 삭제 (메모리 관리)
    for path in temp_file_paths:
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
