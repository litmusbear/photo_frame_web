import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import uuid
import os
import io

# 기존 모듈 임포트 (파일들이 동일 경로에 있어야 합니다)
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
            picture = Picture(temp_path)
            image = picture.get_image()
            if image is None:
                raise ValueError("이미지를 읽을 수 없습니다.")

            width, height = image.size
            thickness = get_thickness(height)
            padding = get_padding(height)
            logo_file = logo(picture)

            # [추가] 사진 파일별 수동 타임존 선택 UI (key 중복 방지를 위해 unique_id 활용)
            st.subheader(f"🖼️ 파일: {uploaded_file.name}")
            photo_timezone = st.selectbox(
                f"└ GPS가 없을 경우 적용할 타임존 설정",
                ["UTC+09:00 (한국/일본)", "UTC+01:00 (유럽 서부)", "UTC+00:00 (런던/GMT)", "UTC-05:00 (뉴욕/동부)"],
                index=0,
                key=f"tz_{unique_id}"
            )
            single_chosen_utc = photo_timezone.split(" ")[0]

            def add_border(img, w, h, t, p):
                border_width = w + (t * 2)
                border_height = h + t + p
                canvas = Image.new("RGB", (border_width, border_height), (255, 255, 255))
                canvas.paste(img, (t, t))
                return canvas

            # [수정] 수동 선택된 fallback_utc 인자 추가
            def place_model(canvas, pic, w, h, t, p, l_file, fallback_utc):
                font_obj = set_font(p)       # Bold (모델명)
                font_reg = regular(p)        # Regular (촬영정보)
                font_dat = date_font(p)      # Light (날짜)
                size, d_size = font_size(p)
                
                draw = ImageDraw.Draw(canvas)
                
                text_camera = pic.get_camera() 
                text_info = f"f/{pic.get_f_number()}  {pic.get_shutter()}  ISO{pic.get_iso()}"
                
                # --- [수정 핵심: GPS 유무에 따른 날짜 및 타임존 처리] ---
                date_str = pic.get_exif_data().get("DateTimeOriginal", "")
                text_date = ""
                
                if date_str:
                    from datetime import datetime
                    from timezonefinder import TimezoneFinder
                    import pytz
                    
                    dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    
                    # Picture 객체 내부의 get_gps_info 혹은 기존 작성하셨던 방식으로 위경도 확인 시도
                    coords = pic.get_gps_info() if hasattr(pic, 'get_gps_info') else None
                    
                    # 1단계 기본값: 사용자가 UI에서 수동 선택한 타임존 설정
                    utc_offset_str = fallback_utc 

                    # 2단계 검증: 만약 사진에 진짜 GPS 데이터가 존재한다면 동적 계산하여 덮어쓰기
                    if coords:
                        try:
                            tf = TimezoneFinder()
                            tz_name = tf.timezone_at(lat=coords[0], lng=coords[1])
                            if tz_name:
                                timezone = pytz.timezone(tz_name)
                                aware_dt = timezone.localize(dt)
                                utc_offset = aware_dt.utcoffset()
                                hours = int(utc_offset.total_seconds() / 3600)
                                minutes = int((utc_offset.total_seconds() % 3600) / 60)
                                utc_offset_str = f"UTC{'+' if hours >= 0 else ''}{hours:02d}:{abs(minutes):02d}"
                        except:
                            pass # GPS 분석 실패 시 1단계에서 설정된 수동 세팅값 유지
                    
                    # 월 이름 약어 포맷 적용 (%B -> %b)
                    text_date = dt.strftime(f"%Y-%b-%d %H:%M {utc_offset_str}")
                # -------------------------------------------------------------

                line_spacing = int(size * 0.2)
                total_text_height = size + line_spacing + d_size
                start_y = h + (p - total_text_height) // 2
                
                visual_center_y = int(start_y + (size * 0.62)) 
                
                spacing = int(w * 0.01)
                current_x = t
                try:
                    if l_file and os.path.exists(l_file):
                        logo_img = Image.open(l_file).convert("RGBA")
                        logo_h = int(size * 0.95)
                        logo_w = int(logo_img.width * (logo_h / logo_img.height))
                        logo_img = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                        
                        logo_x = int(current_x)
                        logo_y = int(visual_center_y - (logo_h // 2))
                        canvas.paste(logo_img, (logo_x, logo_y), logo_img)
                        
                        current_x = logo_x + logo_w + int(spacing * 0.7)
                except:
                    pass
                draw.text((int(current_x), int(start_y)), text_camera, fill=(0, 0, 0), font=font_obj, anchor="la")

                info_x = t + w 
                
                draw.text((int(info_x), int(start_y)), text_info, fill=(50, 50, 50), font=font_reg, anchor="ra")

                if text_date:
                    date_y = int(start_y + size + line_spacing)
                    draw.text((int(info_x), date_y), text_date, fill=(140, 140, 140), font=font_dat, anchor="ra")

                return canvas

            # 이미지 합성 프로세스 실행 (수동 선택한 single_chosen_utc 인자 추가 전달)
            base_canvas = add_border(image, width, height, thickness, padding)
            final_canvas = place_model(base_canvas, picture, width, height,
