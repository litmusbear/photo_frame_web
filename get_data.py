import re
from datetime import datetime 
from PIL import Image, ImageOps 
from PIL.ExifTags import TAGS 
import pytz
from timezonefinder import TimezoneFinder 

# 유명 번들렌즈(고정 렌즈) 카메라 DB
KNOWN_COMPACT_LENSES = { 
    # --- LEICA --- 
    "LEICA X1": "Elmarit 24mm f/2.8", 
    "LEICA X2": "Elmarit 24mm f/2.8", 
    "LEICA X VARIO": "Vario-Elmar 18-46mm f/3.5-6.4", 
    "LEICA X (TYP 113)": "Summilux 23mm f/1.7", 
    "LEICA X-U": "Summilux 23mm f/1.7", 
    "LEICA Q": "Summilux 28mm f/1.7", 
    "LEICA Q2": "Summilux 28mm f/1.7", 
    "LEICA Q3": "Summilux 28mm f/1.7", 
    "LEICA Q3 43": "APO-Summicron 43mm f/2", 
    "LEICA D-LUX 7": "Vario-Summilux 10.9-34mm f/1.7-2.8", 
    "LEICA D-LUX 8": "Vario-Summilux 10.9-34mm f/1.7-2.8", 
    "LEICA C-LUX": "Leica DC Vario-Elmarit 9-72mm f/3.3-6.4", 
    "LEICA V-LUX": "Leica DC Vario-Elmarit 9.1-146mm f/3.3-6.4", 
    "LEICA DIGILUX": "Vario-Summicron 7-22.5mm f/2-2.4",

    # --- SONY ---
    "RX100 VII": "24-200mm f/2.8-4.5",
    "RX100 M7": "24-200mm f/2.8-4.5",
    "RX100 VI": "24-200mm f/2.8-4.5",
    "RX100 M6": "24-200mm f/2.8-4.5",
    "RX100 V": "24-70mm f/1.8-2.8",
    "RX100 M5": "24-70mm f/1.8-2.8",
    "RX100 IV": "24-70mm f/1.8-2.8",
    "RX100 M4": "24-70mm f/1.8-2.8",
    "RX100 III": "24-70mm f/1.8-2.8",
    "RX100 M3": "24-70mm f/1.8-2.8",
    "RX100 II": "28-100mm f/1.8-4.9",
    "RX100 M2": "28-100mm f/1.8-4.9",
    "RX100": "28-100mm f/1.8-4.9",
    "RX1R II": "Sonnar 35mm f/2",
    "RX1R": "Sonnar 35mm f/2",
    "RX1": "Sonnar 35mm f/2",
    "RX10 IV": "24-600mm f/2.4-4",
    "RX10 III": "24-600mm f/2.4-4",
    "RX10 II": "24-200mm f/2.8",
    "RX10": "24-200mm f/2.8",
    "ZV-1": "24-70mm f/1.8-2.8",
    "DSC-WX": "Sony Compact Zoom",
    "CYBER-SHOT": "Sony Compact Zoom",

    # --- RICOH / PENTAX ---
    "GR III": "GR 28mm f/2.8",
    "GR IIIx": "GR 40mm f/2.8",
    "GR II": "GR 28mm f/2.8",
    "GR DIGITAL IV": "GR 28mm f/1.9",
    "GR DIGITAL III": "GR 28mm f/1.9",
    "GR DIGITAL": "GR 28mm f/2.8",
    "GXR": "Ricoh GXR Mount Unit",
    "WG-": "Ricoh Rugged Zoom",

    # --- FUJIFILM ---
    "X100V": "Fujinon 23mm f/2",
    "X100S": "Fujinon 23mm f/2",
    "X100F": "Fujinon 23mm f/2",
    "X100T": "Fujinon 23mm f/2",
    "X100VI": "Fujinon 23mm f/2",
    "X100": "Fujinon 23mm f/2",
    "FUJIFILM X70": "Fujinon 18.5mm f/2.8",
    "XF10": "Fujinon 18.5mm f/2.8",
    "X30": "Fujinon 7.1-28.4mm f/2-2.8",
    "X20": "Fujinon 7.1-28.4mm f/2-2.8",
    "XQ2": "Fujinon 4.4-13.2mm f/1.8-4.9",
    "XQ1": "Fujinon 4.4-13.2mm f/1.8-4.9",

    # --- CANON ---
    "G7 X MARK III": "24-100mm f/1.8-2.8",
    "G7 X MARK II": "24-100mm f/1.8-2.8",
    "G7 X": "24-100mm f/1.8-2.8",
    "G9 X MARK II": "28-84mm f/2-4.9",
    "G9 X": "28-84mm f/2-4.9",
    "G5 X MARK II": "24-120mm f/1.8-2.8",
    "G5 X": "24-100mm f/1.8-2.8",
    "G1 X MARK III": "24-72mm f/2.8-5.6",
    "G1 X MARK II": "24-120mm f/2-3.9",
    "G1 X": "28-112mm f/2.8-5.8",
    "POWERSHOT S120": "24-120mm f/1.8-5.7",
    "POWERSHOT S110": "24-120mm f/2-5.9",
    "POWERSHOT SX": "Canon Compact Zoom",

    # --- PANASONIC ---
    "LX100 II": "Vario-Summilux 10.9-34mm f/1.7-2.8",
    "LX100": "Vario-Summilux 10.9-34mm f/1.7-2.8",
    "LX10": "Leica DC Vario-Summilux 24-72mm f/1.4-2.8",
    "LX15": "Leica DC Vario-Summilux 24-72mm f/1.4-2.8",
    "TX2": "Leica DC Vario-Elmar 24-720mm f/3.3-6.4",
    "ZS200": "Leica DC Vario-Elmarit 24-360mm f/3.3-6.4",
    "TZ200": "Leica DC Vario-Elmarit 24-360mm f/3.3-6.4",

    # --- OLYMPUS ---
    "STYLUS 1": "6-72mm f/2.8",
    "XZ-2": "6-24mm f/1.8-2.5",
    "XZ-1": "6-24mm f/1.8-2.5",

    # --- 필름/토이카메라 ---
    "CONTAX T2": "Carl Zeiss Sonnar 38mm f/2.8",
    "CONTAX T3": "Carl Zeiss Sonnar 35mm f/2.8",
    "OLYMPUS MJU": "Olympus Zoom 35-70mm f/3.5-5.6",
    "OLYMPUS STYLUS EPIC": "35mm f/2.8",
}

def get_exif_data(image_path): 
    image = Image.open(image_path) 
    info = image._getexif() 
    exif_dict = {}
    if info:
        for tag, value in info.items():
            tag_name = TAGS.get(tag, tag)
            exif_dict[tag_name] = value
    return exif_dict

BRANDS_SAFE_TO_STRIP = {
    "CANON",       
    "PANASONIC",   
    "SONY",        
    "OLYMPUS",     
    "RICOH",       
}

def clean_camera_name(exif):
    make = exif.get("Make", "")
    model = exif.get("Model", "Unknown Camera")

    if make:
        make_keyword = make.split()[0] if make.split() else make
        if make_keyword.upper() in BRANDS_SAFE_TO_STRIP:
            pattern = re.compile(r"^\s*" + re.escape(make_keyword) + r"\s+", re.IGNORECASE)
            model = pattern.sub("", model).strip()

    return model

def get_shutter(exif): 
    shutter = exif.get("ExposureTime", "?") 
    if shutter: 
        if isinstance(shutter, tuple): 
            shutter = shutter[0] / shutter[1]
        if shutter < 1:
            denom = round(1 / shutter)
            shutter = f"1/{denom}"
        else:
            shutter = f"{shutter}\""
    else:
        shutter = "?"
    return shutter

def convert_to_degrees(value): 
    d = float(value[0]) 
    m = float(value[1]) 
    s = float(value[2]) 
    return d + (m / 60.0) + (s / 3600.0)

def get_gps(exif): 
    gps_info = exif.get("GPSInfo", {}) 
    if not gps_info: 
        return None
    try:
        lat = convert_to_degrees(gps_info[2])
        if gps_info[1] == 'S': lat = -lat
        lon = convert_to_degrees(gps_info[4])
        if gps_info[3] == 'W': lon = -lon
        return lat, lon
    except:
        return None

def get_datetime(exif): 
    date_str = exif.get("DateTimeOriginal", "") 
    if not date_str: return ""
    
    dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    coords = get_gps(exif)
    utc_offset_str = "UTC+00:00"

    if coords:
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=coords[0], lng=coords[1])
        if tz_name:
            timezone = pytz.timezone(tz_name)
            aware_dt = timezone.localize(dt)
            utc_offset = aware_dt.utcoffset()
            hours = int(utc_offset.total_seconds() / 3600)
            minutes = int((utc_offset.total_seconds() % 3600) / 60)
            utc_offset_str = f"UTC{'+' if hours >= 0 else ''}{hours:02d}:{abs(minutes):02d}"

    return dt.strftime(f"%Y-%b-%d %H:%M {utc_offset_str}")

def lookup_known_lens(camera_model): 
    if not camera_model: 
        return "" 
    model_upper = camera_model.upper() 
    for keyword, lens_spec in KNOWN_COMPACT_LENSES.items(): 
        if keyword.upper() in model_upper: 
            return lens_spec 
    return ""

def get_lens(exif, camera_model=""): 
    # 1. 고정 렌즈 카메라 DB 매칭
    known = lookup_known_lens(camera_model) 
    if known: 
        return known

    # 2. 메타데이터에서 렌즈 모델 가져오기
    lens = exif.get("LensModel", "")
    lens_str = str(lens).strip() if lens else ""

    # 3. 데이터가 비어있거나 올바르지 않으면 빈값 반환
    if not lens_str or lens_str.lower() in ["none", "unknown", "?", "built-in"]:
        return ""

    # 4. 카메라 기종명 중복 제거
    if camera_model:
        pattern = re.compile(re.escape(camera_model), re.IGNORECASE)
        lens_str = pattern.sub("", lens_str).strip()

    # 5. 스마트폰 특유의 TMI 설명조 텍스트 정제
    if "camera" in lens_str.lower():
        specs = re.findall(r'\d+(?:\.\d+)?\s*mm|\bf\/\d+(?:\.\d+)?', lens_str, re.IGNORECASE)
        if specs:
            lens_str = " ".join(specs).strip()
        else:
            lens_str = ""

    return lens_str.strip(" ,-_")


class Picture(): 
    def __init__(self, image_path): 
        img = Image.open(image_path) 
        self.image_path = image_path 
        self.exif = get_exif_data(image_path) 
        self.image = ImageOps.exif_transpose(img) 
        self.camera = clean_camera_name(self.exif) 
        self.iso = self.exif.get("ISOSpeedRatings", "?") 
        
        f_val = self.exif.get("FNumber", "?")
        if isinstance(f_val, tuple) and len(f_val) == 2 and f_val[1] != 0:
            f_val = f_val[0] / f_val[1]
        self.f_number = float(round(f_val, 1)) if isinstance(f_val, (int, float)) else f_val
        
        self.shutter = get_shutter(self.exif) 
        self.datetime = get_datetime(self.exif) 
        
        # 35mm 환산 화각 추출 (없으면 실제 FocalLength)
        eq_focal = self.exif.get("FocalLengthIn35mmFilm", "")
        if not eq_focal or str(eq_focal) == "?":
            eq_focal = self.exif.get("FocalLength", "")

        if isinstance(eq_focal, tuple) and len(eq_focal) == 2 and eq_focal[1] != 0:
            eq_focal = eq_focal[0] / eq_focal[1]

        # 화각 텍스트 추출 (0mm거나 없으면 빈값 처리)
        try:
            fval = int(float(eq_focal))
            self.focal_length = f"{fval}mm" if fval > 0 else ""
        except:
            self.focal_length = ""

        # 렌즈 이름 지정 (한글 대신 영문 사용으로 네모 깨짐 완전 방지)
        base_lens = get_lens(self.exif, self.camera)
        if base_lens:
            self.lens = base_lens
        else:
            self.lens = "Manual Lens"

    def get_image(self): return self.image
    def get_camera(self): return self.camera
    def get_iso(self): return self.iso
    def get_f_number(self): return self.f_number
    def get_shutter(self): return self.shutter
    def get_datetime(self): return self.datetime
    def get_lens(self): return self.lens
    def get_focal_length(self): return self.focal_length
