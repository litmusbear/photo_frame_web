import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import uuid
import os
import io

# 기존 모듈들 (환경에 맞게 파일이 존재해야 합니다)
from get_data import Picture
from font import *
from logo import logo
from border import *

st.set_page_config(page_title="폴라로이드 프레임 생성기", layout="centered")
st.title("📸 폴라로이드 스타일 사진 프레임 생성기")

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
            # 1. 데이터 및 기본 설정 불러오기
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

            # 3. 모델명/정보/로고/날짜 배치 함수 (높이 및 간격 최적화 버전)
            def place_model(canvas, pic, w, h, t, p, l_file):
                font_obj = set_font(p)       # Bold (모델명)
                font_reg = regular(p)        # Regular (촬영정보)
                font_dat = date_font(p)      # Light/Small (날짜)
                size, d_size = font_size(p)
                
                draw = ImageDraw.Draw(canvas)
                
                text_camera = pic.get_camera().upper()
                text_info = f"f/{pic.get_f_number()}  {pic.get_shutter()}  ISO{pic.get_iso()}"
                text_date = pic.get_datetime()

                # 수직 정렬 계산 (오른쪽 두 줄 높이 기준)
                line_spacing = int(size * 0.2)
                total_text_height = size + line_spacing + d_size
                start_y = h + (p - total_text_height) // 2
                
                # --- [왼쪽 그룹: 모델명 & 로고] ---
                camera_x = t 
                # 모델명을 먼저 쓰고 좌표를 추출합니다.
                draw.text((camera_x, start_y), text_camera, fill=(0, 0, 0), font=font_obj, anchor="la")
                
                # 모델명 텍스트의 실제 범위를 구함
                camera_bbox = draw.textbbox((camera_x, start_y), text_camera, font=font_obj, anchor="la")
                camera_end_x = camera_bbox[2]
                camera_center_y = (camera_bbox[1] + camera_bbox[3]) // 2  # 모델명의 수직 중앙선

                # 로고와 모델명 사이 간격을 좁게 설정
                tight_spacing = int(w * 0.008) 
                
                try:
                    if l_file and os.path.exists(l_file):
                        logo_img = Image.open(l_file).convert("RGBA")
                        logo_h = int(size * 0.9)  # 텍스트보다 살짝 작게 하여 정렬감 개선
                        logo_w = int(logo_img.width * (logo_h / logo_img.height))
                        logo_img = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                        
                        logo_x = camera_end_x + tight_spacing
                        # 로고의 중앙을 모델명의 수직 중앙에 맞춤
                        logo_y = int(camera_center_y - (logo_h // 2))
                        canvas.paste(logo_img, (logo_x, logo_y), logo_img)
                except:
                    pass

                # --- [오른쪽 그룹: 촬영정보 & 날짜] ---
                info_x = t + w 
                
                # 촬영 정보 (상단 라인 맞춤)
                draw.text((info_x, start_y), text_info, fill=(50, 50, 50), font=font_reg, anchor="ra")

                # 촬영 날짜 (촬영 정보 바로 아래)
                if text_date:
                    date_y = start_y + size + line_spacing
                    draw.text((info_x, date_y), text_date, fill=(140, 140, 140), font=font_dat, anchor="ra")

                return canvas

            # 실행 및 결과 출력
            base_canvas = add_border(image, width, height, thickness, padding)
            final_canvas = place_model(base_canvas, picture, width, height, thickness, padding, logo_file)

            st.image(final_canvas, caption=f"결과물: {uploaded_file.name}", use_container_width=True)

            # 다운로드 버튼
            buf = io.BytesIO()
            final_canvas.save(buf, format="JPEG", quality=95)
            st.download_button(
                label=f"💾 {uploaded_file.name} 다운로드",
                data=buf.getvalue(),
                file_name=f"polaroid_{uploaded_file.name}",
                key=unique_id
            )
            
        except Exception as e:
            st.error(f"⚠️ '{uploaded_file.name}' 처리 중 오류: {e}")
            
        st.divider()

    # 임시 파일 정리
    for path in temp_file_paths:
        if os.path.exists(path):
            os.remove(path)
