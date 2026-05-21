import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import uuid
import os
import io

from get_data import Picture
from font import *
from logo import logo
from border import *

st.set_page_config(page_title="폴라로이드 프레임 생성기", layout="centered")
st.title("📸 폴라로이드 스타일 사진 프레임 생성기")


# --- [함수 정의 영역] ---

def add_border(img, w, h, t, p):
    border_width = w + (t * 2)
    border_height = h + t + p
    canvas = Image.new("RGB", (border_width, border_height), (255, 255, 255))
    canvas.paste(img, (t, t))
    return canvas


def place_model(canvas, pic, w, h, t, p, l_file, chosen_utc=None, current_path=None):
    font_obj = set_font(p)
    font_reg = regular(p)
    font_dat = date_font(p)
    size, d_size = font_size(p)
    
    draw = ImageDraw.Draw(canvas)
    
    text_camera = pic.get_camera()
    text_info = f"f/{pic.get_f_number()}  {pic.get_shutter()}  ISO{pic.get_iso()}"
    
    # 사용자가 UI에서 최종 선택한 타임존을 기본값으로 지정
    utc_offset_str = chosen_utc if chosen_utc else "UTC+09:00"
    text_date = ""
    date_str = ""
    
    try:
        exif_data = pic.image._getexif() if hasattr(pic, 'image') else None
        if not exif_data and current_path:
            with Image.open(current_path) as img_exif:
                exif_data = img_exif._getexif()
        
        if exif_data:
            from PIL.ExifTags import TAGS
            readable_exif = {TAGS.get(tag, tag): val for tag, val in exif_data.items()}
            date_str = readable_exif.get("DateTimeOriginal", "")
            
            # GPS 데이터 알맹이 검증
            gps_info = readable_exif.get("GPSInfo", {})
            coords = None
            if gps_info and 2 in gps_info and 4 in gps_info and gps_info[2] and gps_info[4]:
                try:
                    def to_degrees(value):
                        return float(value[0]) + (float(value[1]) / 60.0) + (float(value[2]) / 3600.0)
                    lat = to_degrees(gps_info[2])
                    if readable_exif.get("GPSLatitudeRef", "N") == "S": lat = -lat
                    lon = to_degrees(gps_info[4])
                    if readable_exif.get("GPSLongitudeRef", "E") == "W": lon = -lon
                    
                    if lat != 0.0 or lon != 0.0:
                        coords = (lat, lon)
                except:
                    coords = None
            
            # 유효한 GPS가 있을 때만 동적 연산으로 수동 선택 무시
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
                except:
                    pass
    except:
        pass

    # 날짜 조립 및 null 예외 처리 강제 덮어쓰기
    from datetime import datetime
    
    if date_str:
        try:
            dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            text_date = dt.strftime(f"%Y-%b-%d %H:%M {utc_offset_str}")
        except:
            date_str = ""

    if not date_str:
        try:
            orig_date = pic.get_datetime() 
            if orig_date and "UTC" in orig_date:
                base_part = orig_date.split("UTC")[0].strip()
                text_date = f"{base_part} {utc_offset_str}"
            else:
                file_mtime = os.path.getmtime(current_path)
                dt = datetime.fromtimestamp(file_mtime)
                text_date = dt.strftime(f"%Y-%b-%d %H:%M {utc_offset_str}")
        except:
            dt = datetime.now()
            text_date = dt.strftime(f"%Y-%b-%d %H:%M {utc_offset_str}")

    # 레이아웃 정렬 및 이미지 합성
    line_spacing = int(size * 0.2)
    total_text_height = size + line_spacing + d_size
    start_y = h + (p - total_text_height) // 2
    visual_center_y = int(start_y + (size * 0.62)) 
    
    spacing = int(w * 0.01)
    current_x = t

    # 로고 그리기
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

    # 기기 모델명 그리기
    draw.text((int(current_x), int(start_y)), text_camera, fill=(0, 0, 0), font=font_obj, anchor="la")
    
    # 우측 정보 & 날짜 그리기
    info_x = t + w 
    draw.text((int(info_x), int(start_y)), text_info, fill=(50, 50, 50), font=font_reg, anchor="ra")

    if text_date:
        date_y = int(start_y + size + line_spacing)
        draw.text((int(info_x), date_y), text_date, fill=(140, 140, 140), font=font_dat, anchor="ra")

    return canvas


# --- [메인 구동 영역] ---

uploaded_files = st.file_uploader("사진들을 업로드하세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    temp_file_paths = []

    # 파일 업로드 시 파일명을 기반으로 session_state에 타임존 저장 공간 확보
    for uploaded_file in uploaded_files:
        file_id = uploaded_file.name
        if file_id not in st.session_state:
            st.session_state[file_id] = "UTC+09:00 (한국/일본)"

    for uploaded_file in uploaded_files:
        file_id = uploaded_file.name
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
            
            # [핵심 수정] 타임존 선택지 정의
            tz_options = ["UTC+09:00 (한국/일본)", "UTC+01:00 (유럽 서부)", "UTC+00:00 (런던/GMT)", "UTC-05:00 (뉴욕/동부)"]
            
            # session_state에 기억된 인덱스 계산
            current_index = tz_options.index(st.session_state[file_id])

            # selectbox 조작 시 session_state를 즉시 갱신하도록 콜백 함수 연결
            def update_tz(fid=file_id, uid=unique_id):
                st.session_state[fid] = st.session_state[f"selectbox_{uid}"]

            photo_timezone = st.selectbox(
                f"└ GPS 미검출 시 적용할 타임존 설정",
                tz_options,
                index=current_index,
                key=f"selectbox_{unique_id}",
                on_change=update_tz
            )
            
            # 최종 선택된 값에서 문자열 슬라이싱 ("UTC+01:00" 형태 추출)
            single_chosen_utc = st.session_state[file_id].split(" ")[0]

            # 이미지 프레임 합성
            base_canvas = add_border(image, width, height, thickness, padding)
            final_canvas = place_model(
                base_canvas, picture, width, height, thickness, padding, logo_file, 
                chosen_utc=single_chosen_utc, current_path=temp_path
            )

            st.image(final_canvas, caption=f"결과물: {uploaded_file.name}", use_container_width=True)

            # 다운로드 버튼
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
