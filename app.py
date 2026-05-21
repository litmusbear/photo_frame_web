import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import uuid
import os
import io
from datetime import datetime

from get_data import Picture
from font import *
from logo import logo
from border import *

st.set_page_config(page_title="폴라로이드 프레임 생성기", layout="centered")
st.title("📸 폴라로이드 스타일 사진 프레임 생성기")


def add_border(img, w, h, t, p):
    border_width = w + (t * 2)
    border_height = h + t + p
    canvas = Image.new("RGB", (border_width, border_height), (255, 255, 255))
    canvas.paste(img, (t, t))
    return canvas


def place_model(canvas, pic, w, h, t, p, l_file, chosen_utc=None, current_path=None):
    font_obj = set_font(p)  # 이게 본래 볼드체 폰트 객체일 것입니다.
    font_reg = regular(p)
    font_dat = date_font(p)
    size, d_size = font_size(p)
    
    draw = ImageDraw.Draw(canvas)
    
    text_camera = pic.get_camera()
    text_info = f"f/{pic.get_f_number()}  {pic.get_shutter()}  ISO{pic.get_iso()}"
    
    # 1. 타임존 및 날짜 영역 (기존 유지)
    utc_offset_str = chosen_utc if chosen_utc else "UTC+09:00"
    text_date = ""
    date_str = ""
    has_valid_gps = False
    
    try:
        with Image.open(current_path) as img_exif:
            exif_data = img_exif._getexif()
        if exif_data:
            from PIL.ExifTags import TAGS
            readable_exif = {TAGS.get(tag, tag): val for tag, val in exif_data.items()}
            date_str = readable_exif.get("DateTimeOriginal", "")
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
                    if abs(lat) > 0.001 and abs(lon) > 0.001:
                        coords = (lat, lon)
                except: coords = None

            if coords:
                try:
                    from timezonefinder import TimezoneFinder
                    import pytz
                    tf = TimezoneFinder()
                    tz_name = tf.timezone_at(lat=coords[0], lng=coords[1])
                    if tz_name:
                        timezone = pytz.timezone(tz_name)
                        dt_obj = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                        aware_dt = timezone.localize(dt_obj)
                        utc_offset = aware_dt.utcoffset()
                        hours = int(utc_offset.total_seconds() / 3600)
                        minutes = int((utc_offset.total_seconds() % 3600) / 60)
                        utc_offset_str = f"UTC{'+' if hours >= 0 else ''}{hours:02d}:{abs(minutes):02d}"
                        has_valid_gps = True
                except: pass
    except: pass

    if has_valid_gps and date_str:
        try:
            dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            text_date = dt.strftime(f"%Y-%b-%d %H:%M {utc_offset_str}")
        except: pass

    if not text_date:
        if date_str:
            try:
                dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                text_date = dt.strftime(f"%Y-%b-%d %H:%M {chosen_utc}")
            except: date_str = ""
        if not date_str:
            try:
                file_mtime = os.path.getmtime(current_path)
                dt = datetime.fromtimestamp(file_mtime)
                text_date = dt.strftime(f"%Y-%b-%d %H:%M {chosen_utc}")
            except:
                text_date = datetime.now().strftime(f"%Y-%b-%d %H:%M {chosen_utc}")

    # 레이아웃 좌표 계산
    line_spacing = int(size * 0.2)
    start_y = h + (p - (size + line_spacing + d_size)) // 2
    visual_center_y = int(start_y + (size * 0.62)) 
    
    spacing = int(w * 0.01)
    current_x = t

    # 로고 계산
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
    except: pass

    # --- [🛠️ 굵기 보존형 실시간 스케일링 로직] ---
    info_x = t + w
    info_width = draw.textlength(text_info, font=font_reg)
    max_available_x = info_x - info_width - (spacing * 2)
    max_text_width = max_available_x - current_x
    current_text_width = draw.textlength(text_camera, font=font_obj)
    
    # 억지 굵기(스트로크) 기본값
    camera_stroke_width = 0
    
    if current_text_width > max_text_width:
        scale_factor = max(max_text_width / current_text_width, 0.4)
        new_size = int(size * scale_factor)
        
        # [처방 1] 기존 font_obj가 가지고 있던 볼드체 폰트 파일 경로를 정확히 유지하면서 크기만 분양
        font_path = font_obj.path if hasattr(font_obj, 'path') else "fonts/CustomFont.ttf" 
        try:
            font_obj = ImageFont.truetype(font_path, new_size)
        except:
            pass
        
        # [처방 2] 글자가 많이 작아졌을 경우(비율 85% 이하) 텍스트 외곽선 두께를 주어 강제로 볼드하게 만듦
        if scale_factor < 0.85:
            camera_stroke_width = max(1, int(new_size * 0.04))  # 폰트 크기에 비례하여 굵기 제어
    # --------------------------------------------

    # 최종 글자 그리기 (stroke 속성 추가)
    draw.text(
        (int(current_x), int(start_y)), 
        text_camera, 
        fill=(0, 0, 0), 
        font=font_obj, 
        anchor="la",
        stroke_width=camera_stroke_width,  # 👈 작아지면 작동하는 페이크 볼드 두께
        stroke_fill=(0, 0, 0)              # 👈 외곽선 색상도 검은색으로 통일
    )
    
    draw.text((int(info_x), int(start_y)), text_info, fill=(50, 50, 50), font=font_reg, anchor="ra")

    if text_date:
        date_y = int(start_y + size + line_spacing)
        draw.text((int(info_x), date_y), text_date, fill=(140, 140, 140), font=font_dat, anchor="ra")

    return canvas

uploaded_files = st.file_uploader("사진들을 업로드하세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    temp_file_paths = []

    if "tz_dict" not in st.session_state:
        st.session_state.tz_dict = {}

    for uploaded_file in uploaded_files:
        file_id = uploaded_file.name
        if file_id not in st.session_state.tz_dict:
            st.session_state.tz_dict[file_id] = "UTC+09:00 (한국/일본)"

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

            st.subheader(f"🖼️ 파일: {uploaded_file.name}")
            
            tz_options = ["UTC+09:00 (한국/일본)", "UTC+01:00 (유럽 서부)", "UTC+00:00 (런던/GMT)", "UTC-05:00 (뉴욕/동부)"]
            
            def make_callback(fid=file_id, uid=unique_id):
                return lambda: st.session_state.tz_dict.update({fid: st.session_state[f"selectbox_{uid}"]})

            current_index = tz_options.index(st.session_state.tz_dict[file_id])

            photo_timezone = st.selectbox(
                f"└ GPS 미검출 시 적용할 타임존 설정",
                tz_options,
                index=current_index,
                key=f"selectbox_{unique_id}",
                on_change=make_callback()
            )
            
            single_chosen_utc = st.session_state.tz_dict[file_id].split(" ")[0]

            base_canvas = add_border(image, width, height, thickness, padding)
            final_canvas = place_model(
                base_canvas, picture, width, height, thickness, padding, logo_file, 
                chosen_utc=single_chosen_utc, current_path=temp_path
            )

            st.image(final_canvas, caption=f"결과물: {uploaded_file.name}", width='stretch')

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
