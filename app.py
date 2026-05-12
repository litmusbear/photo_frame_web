import streamlit as st
from PIL import Image, ImageDraw
import uuid
import os
import io

from get_data import Picture
from font import *
from logo import logo
from border import *

st.title("📸 필름 스타일 사진 프레임 생성기")

uploaded_files = st.file_uploader("사진들을 업로드하세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    temp_file_paths = []

    for uploaded_file in uploaded_files:
        unique_id = uuid.uuid4().hex
        temp_path = f"temp_{unique_id}.jpg"
        temp_file_paths.append(temp_path)

        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            # 1. 데이터 불러오기
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
                
                text_camera = pic.get_camera()
                text_info = f"f/{pic.get_f_number()}  {pic.get_shutter()}  ISO{pic.get_iso()}"
                text_date = pic.get_datetime()

                # --- 중요: 사진 라인에 맞추기 위한 좌표 설정 ---
                # 사진이 시작되는 왼쪽 끝은 t(thickness)입니다.
                camera_x = t 
                # 사진이 끝나는 오른쪽 끝은 t + w 입니다.
                info_x = t + w 
                # ------------------------------------------

                line_spacing = int(size * 0.2)
                total_text_height = size + line_spacing + d_size
                start_y = h + (p - total_text_height) // 2
                center_y = h + (p // 2)
                visual_center_y = int(start_y + (size * 0.52))
                spacing = int(w * 0.012)
                
                # [로고 처리] 기기명 왼쪽에 배치
                try:
                    if l_file and os.path.exists(l_file):
                        logo_img = Image.open(l_file).convert("RGBA")
                        logo_h = int(size * 1.1) 
                        logo_w = int(logo_img.width * (logo_h / logo_img.height))
                        logo_img = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                        
                        logo_x = camera_x
                        logo_y = int(center_y - (logo_h // 2))
                        canvas.paste(logo_img, (logo_x, logo_y), logo_img)
                        
                        # 로고 너비만큼 기기명 좌표 이동
                        camera_x = logo_x + logo_w + spacing
                except Exception as logo_err:
                    pass # 로고 실패 시 원래 camera_x(t) 유지

                # [텍스트 그리기]
                # 날짜 (사진 오른쪽 라인에 맞춤)
                if text_date:
                    date_y = start_y + size + line_spacing
                    draw.text((info_x, date_y), text_date, fill=(140, 140, 140), font=font_dat, anchor="ra")

                # 기기명 (사진 왼쪽 라인 혹은 로고 옆)
                draw.text((camera_x, center_y), text_camera, fill=(0, 0, 0), font=font_obj, anchor="lm")
                
                # 촬영 정보 (사진 오른쪽 라인에 맞춤)
                draw.text((info_x, start_y), text_info, fill=(50, 50, 50), font=font_reg, anchor="ra")

                return canvas


            # 결과물 생성 및 표시
            base_canvas = add_border(image, width, height, thickness, padding)
            final_canvas = place_model(base_canvas, picture, width, height, thickness, padding, logo_file)

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

    # 임시 파일 삭제
    for path in temp_file_paths:
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
