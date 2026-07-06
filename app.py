import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import uuid
import os
import io
from datetime import datetime

try:
    import piexif
    HAS_PIEXIF = True
except ImportError:
    HAS_PIEXIF = False

from get_data import Picture
from font import *
from logo import logo
from border import *

# 1. 페이지 설정 및 감성 테마 CSS 적용
st.set_page_config(page_title="폴라로이드 프레임 생성기", layout="centered")

st.markdown("""
    <style>
    /* 따뜻하고 감성적인 스튜디오 톤 배경 */
    .stApp {
        background-color: #FBF9F6;
    }
    /* 업로드 박스 디자인 고급화 */
    .stFileUploader {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0px 8px 24px rgba(149, 157, 165, 0.06);
        border: 1px dashed #E2DFD9;
    }
    /* 안내 문구 스타일 */
    .info-text {
        color: #6E6E6E;
        font-size: 0.95rem;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📸 폴라로이드 스타일 사진 프레임 생성기")
st.markdown('<p class="info-text">디지털 사진에 카메라 기종, 촬영 정보(EXIF), 그리고 감성적인 폴라로이드 테두리를 입혀줍니다.</p>', unsafe_allow_html=True)


def add_border(img, w, h, t, p):
    border_width = w + (t * 2)
    border_height = h + t + p
    canvas = Image.new("RGB", (border_width, border_height), (255, 255, 255))
    canvas.paste(img, (t, t))
    return canvas


def extract_exif_bytes(source_path):
    """
    원본 이미지 파일에서 EXIF 메타데이터를 추출.
    piexif가 있으면 Orientation을 1로 정규화해서 캔버스 크기 변경으로 인한
    이중 회전 문제를 방지. 없으면 PIL의 기본 EXIF 파싱 결과로 폴백.
    """
    if HAS_PIEXIF:
        try:
            exif_dict = piexif.load(source_path)
            exif_dict["0th"][piexif.ImageIFD.Orientation] = 1
            return piexif.dump(exif_dict)
        except Exception:
            pass

    try:
        with Image.open(source_path) as img:
            exif_data = img.info.get("exif")
        if exif_data:
            return exif_data
    except Exception:
        pass

    return None


def place_model(canvas, pic, w, h, t, p, l_file, chosen_utc=None, current_path=None):
    # 기본 외부 폰트 설정 가져오기
    font_obj = set_font(p)  
    font_reg = regular(p)
    font_dat = date_font(p)
    size, d_size = font_size(p)
    
    # 💡 [글자 크기 상향] 가로형 사진(w > h)일 때 글자 크기 배율을 1.3배로 키웠습니다.
    if w > h:
        scale_up_factor = 1.30  
        size = int(size * scale_up_factor)
        d_size = int(d_size * scale_up_factor)
    
    draw = ImageDraw.Draw(canvas)
    
    text_camera = pic.get_camera()
    text_info = f"f/{pic.get_f_number()}  {pic.get_shutter()}  ISO{pic.get_iso()}"
    text_lens = pic.get_lens() if hasattr(pic, "get_lens") else ""
        if not text_lens:
            text_lens = "Lens Unspecified"   # 👈 여기 문구를 취향껏 교체

    
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

    line_spacing = int(size * 0.2)
    
    # 💡 [오리지널 패딩 보존 + 글자 크기 비례 간격 튜닝]
    # 전체 패딩(p) 내에서 커진 폰트 크기에 어울리도록 여백 시작점을 잡아줍니다.
    if w > h:
        gap = int(p * 0.12)  
        start_y = h + t + gap
    else:
        start_y = h + (p - (size + line_spacing + d_size)) // 2  
        
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
    except: pass

    info_x = t + w
    info_width = draw.textlength(text_info, font=font_reg)
    max_available_x = info_x - info_width - (spacing * 2)
    max_text_width = max_available_x - current_x
    current_text_width = draw.textlength(text_camera, font=font_obj)
    
    camera_stroke_width = 0
    
    if current_text_width > max_text_width:
        scale_factor = max(max_text_width / current_text_width, 0.4)
        new_size = int(size * scale_factor)
        font_obj = create_custom_font(new_size, is_bold=True)
        if scale_factor < 0.8:
            camera_stroke_width = max(1, int(new_size * 0.03))
    elif w > h:
        # 커진 size 밸런스에 맞춰 최종 폰트 객체 매핑
        font_obj = create_custom_font(size, is_bold=True)
        font_reg = create_custom_font(int(size * 0.85), is_bold=False)
        font_dat = create_custom_font(int(size * 0.65), is_bold=False)

    draw.text(
        (int(current_x), int(start_y)), 
        text_camera, 
        fill=(0, 0, 0), 
        font=font_obj, 
        anchor="la",
        stroke_width=camera_stroke_width,  
        stroke_fill=(0, 0, 0)              
    )

    # 💡 카메라명 아래에 렌즈 정보 추가 (날짜와 동일 스타일)
    if text_lens:
        lens_y = int(start_y + size + int(size * 0.15))
        draw.text(
            (int(current_x), lens_y),
            text_lens,
            fill=(140, 140, 140),
            font=font_dat,
            anchor="la"
        )
    
    draw.text((int(info_x), int(start_y)), text_info, fill=(50, 50, 50), font=font_reg, anchor="ra")

    if text_date:
        date_y = int(start_y + size + line_spacing)
        draw.text((int(info_x), date_y), text_date, fill=(140, 140, 140), font=font_dat, anchor="ra")

    return canvas



# 파일 업로더 컴포넌트
uploaded_files = st.file_uploader("사진들을 업로드하세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    temp_file_paths = []

    if "tz_dict" not in st.session_state:
        st.session_state.tz_dict = {}

    for uploaded_file in uploaded_files:
        file_id = uploaded_file.name
        if file_id not in st.session_state.tz_dict:
            st.session_state.tz_dict[file_id] = "UTC+09:00 (한국/일본/인도네시아 동부)"

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

            # 🔍 디버그: 렌즈 EXIF 값 확인용 (확인 끝나면 이 블록 삭제하세요)
            with st.expander(f"🔍 디버그 정보 - {uploaded_file.name}"):
                st.write("LensModel (원본 EXIF):", repr(picture.exif.get("LensModel")))
                st.write("LensSpecification (원본 EXIF):", repr(picture.exif.get("LensSpecification")))
                st.write("get_lens() 결과:", repr(picture.get_lens()))
                st.write("전체 EXIF 키 목록:", list(picture.exif.keys()))

            width, height = image.size
            
            # 💡 [오리지널 패딩 연산 100% 보존]
            thickness = get_thickness(height)
            padding = get_padding(height)
                
            logo_file = logo(picture)

            st.subheader(f"🖼️ 파일: {uploaded_files.name if hasattr(uploaded_files, 'name') else uploaded_file.name}")
            
            show_timezone_selector = True 
            
            try:
                with Image.open(temp_path) as img_exif:
                    exif_data = img_exif._getexif()
                if exif_data:
                    from PIL.ExifTags import TAGS
                    readable_exif = {TAGS.get(tag, tag): val for tag, val in exif_data.items()}
                    gps_info = readable_exif.get("GPSInfo", {})
                    if gps_info and 2 in gps_info and 4 in gps_info:
                        show_timezone_selector = False 
            except:
                pass 

            tz_options = [
                "UTC+09:00 (한국/일본/인도네시아 동부)",
                "UTC+08:00 (중국/대만/홍콩/싱가포르/필리핀)",
                "UTC+07:00 (베트남/태국/인도네시아 서부)",
                "UTC+05:30 (인도/스리랑카)",
                "UTC+04:00 (두바이/아랍에미리트/오만)",
                "UTC+03:00 (사우디/터키/동유럽/모스크바)",
                "UTC+02:00 (그리스/이집트/남아공/중유럽 서머타임)",
                "UTC+01:00 (프랑스/독일/이탈리아/스페인/서유럽)",
                "UTC+00:00 (런던/영국/아일랜드/GMT 표준시)",
                "UTC-04:00 (미국 동부 서머타임/캐나다)",
                "UTC-05:00 (뉴욕/워싱턴/미국 동부 표준시)",
                "UTC-06:00 (시카고/미국 중부 표준시)",
                "UTC-08:00 (로스앤젤레스/샌프란시스코/미국 태평양 표준시)",
                "UTC-10:00 (하와이)",
                "UTC+10:00 (시드니/멜버른/호주 동부)",
                "UTC+12:00 (뉴질랜드/피지)"
            ]
            
            if show_timezone_selector:
                def make_callback(fid=file_id, uid=unique_id):
                    return lambda: st.session_state.tz_dict.update({fid: st.session_state[f"selectbox_{uid}"]})

                if st.session_state.tz_dict[file_id] in tz_options:
                    current_index = tz_options.index(st.session_state.tz_dict[file_id])
                else:
                    current_index = 0

                photo_timezone = st.selectbox(
                    f"⚠️ GPS 정보가 없습니다. 적용할 타임존을 선택하세요.",
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

            st.image(final_canvas, caption=f"결과물: {uploaded_file.name}", use_container_width=True)

            # 원본 EXIF 메타데이터 추출 및 저장
            exif_bytes = extract_exif_bytes(temp_path)

            buf = io.BytesIO()
            if exif_bytes:
                final_canvas.save(buf, format="JPEG", quality=95, exif=exif_bytes)
            else:
                final_canvas.save(buf, format="JPEG", quality=95)

            st.download_button(
                label=f"📥 {uploaded_file.name} 저장",
                data=buf.getvalue(),
                file_name=f"result_{uploaded_file.name}",
                key=f"btn_{unique_id}",
                use_container_width=True 
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
else:
    st.info("💡 위 박스에 사진을 업로드하면 촬영 정보가 담긴 폴라로이드 프레임이 실시간으로 생성됩니다.")
