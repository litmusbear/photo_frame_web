import streamlit as st
from PIL import Image, ImageDraw, ImageFont
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

            # [수동 선택 UI 덧붙임] 사진마다 독립된 선택창 제공
            st.subheader(f"🖼️ 파일: {uploaded_file.name}")
            photo_timezone = st.selectbox(
                f"└ GPS 미검출 시 적용할 타임존 설정",
                ["UTC+09:00 (한국/일본)", "UTC+01:00 (유럽 서부)", "UTC+00:00 (런던/GMT)", "UTC-05:00 (뉴욕/동부)"],
                index=0,
                key=f"tz_{unique_id}"
            )
            single_chosen_utc = photo_timezone.split(" ")[0]

            # 2. 테두리 추가 함수 (기존 유지)
            def add_border(img, w, h, t, p):
                border_width = w + (t * 2)
                border_height = h + t + p
                canvas = Image.new("RGB", (border_width, border_height), (255, 255, 255))
                canvas.paste(img, (t, t))
                return canvas

            # 3. 배치 함수 (기존 인자 유지 + 내부에 예외 처리 로직만 덧붙임)
            def place_model(canvas, pic, w, h, t, p, l_file):
                font_obj = set_font(p)
                font_reg = regular(p)
                font_dat = date_font(p)
                size, d_size = font_size(p)
                
                draw = ImageDraw.Draw(canvas)
                
                text_camera = pic.get_camera()
                text_info = f"f/{pic.get_f_number()}  {pic.get_shutter()}  ISO{pic.get_iso()}"
                
                # --- [기존 변수명 유지 및 예외 처리 로직 덧붙임] ---
                text_date = ""
                try:
                    # 기존 Picture 객체의 _getexif()나 내부 딕셔너리 안전하게 접근
                    exif_data = pic.image._getexif() if hasattr(pic, 'image') else None
                    if not exif_data:
                        # 대안으로 임시 이미지에서 직접 로드
                        with Image.open(temp_path) as img_exif:
                            exif_data = img_exif._getexif()
                    
                    if exif_data:
                        from PIL.ExifTags import TAGS
                        readable_exif = {TAGS.get(tag, tag): val for tag, val in exif_data.items()}
                        date_str = readable_exif.get("DateTimeOriginal", "")
                        
                        if date_str:
                            from datetime import datetime
                            from timezonefinder import TimezoneFinder
                            import pytz
                            
                            dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                            
                            # 기본 세팅은 UI에서 선택한 타임존 (single_chosen_utc 가 주입됨)
                            utc_offset_str = single_chosen_utc
                            
                            # GPS 정보 파싱 시도
                            gps_info = readable_exif.get("GPSInfo", {})
                            coords = None
                            if gps_info and 2 in gps_info and 4 in gps_info:
                                try:
                                    def to_degrees(value):
                                        return float(value[0]) + (float(value[1]) / 60.0) + (float(value[2]) / 3600.0)
                                    lat = to_degrees(gps_info[2])
                                    if readable_exif.get("GPSLatitudeRef", "N") == "S": lat = -lat
                                    lon = to_degrees(gps_info[4])
                                    if readable_exif.get("GPSLongitudeRef", "E") == "W": lon = -lon
                                    coords = (lat, lon)
                                except:
                                    pass
                            
                            # GPS 정보가 확실히 있을 때만 타임존 덮어쓰기
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
                                    pass
                            
                            # 약어 달 포맷 적용 (%Y-%b-%d)
                            text_date = dt.strftime(f"%Y-%b-%d %H:%M {utc_offset_str}")
                except:
                    # 에러 시 기존 원본 메서드로 백업 처리
                    text_date = pic.get_datetime()
                # -----------------------------------------------------------------

                line_spacing = int(size * 0.2)
                total_text_height = size + line_spacing + d_size
                
                start_y = h + (p - total_text_height) // 2
                visual_center_y = int(start_y + (size * 0.62)) 
                
                spacing = int(w * 0.01)
                current_x = t

                # [로고 처리]
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
                except Exception:
                    pass

                # [텍스트 그리기]
                draw.text((int(current_x), int(start_y)), text_camera, fill=(0, 0, 0), font=font_obj, anchor="la")
                info_x = t + w 
                draw.text((int(info_x), int(start_y)), text_info, fill=(50, 50, 50), font=font_reg, anchor="ra")

                if text_date:
                    date_y = int(start_y + size + line_spacing)
                    draw.text((int(info_x), date_y), text_date, fill=(140, 140, 140), font=font_dat, anchor="ra")

                return canvas

            # 실행 및 출력
            base_canvas = add_border(image, width, height, thickness, padding)
            final_canvas = place_model(base_canvas, picture, width, height, thickness, padding, logo_file)

            st.image(final_canvas, caption=f"결과물: {uploaded_file.name}", use_container_width=True)

            buf = io.BytesIO()
            final_canvas.save(buf, format="JPEG", quality=95)
            st.download_button(
                label=f"{uploaded_file.name} 저장",
                data=buf.getvalue(),
                file_name=f"result_{uploaded_file.name}",
                key=f"btn_{unique_id}"
            )
            
        except Exception as e:
            st.error(f"⚠️ '{uploaded_file.name}' 처리 중 오류 발생: {e}")
            continue
            
        st.divider()

    for path in temp_file_paths:
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
