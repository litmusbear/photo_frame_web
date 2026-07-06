from PIL import Image, ImageOps
from PIL.ExifTags import TAGS
from datetime import datetime
from timezonefinder import TimezoneFinder
import pytz

# 💡 유명 번들렌즈(고정 렌즈) 카메라 DB
# 카메라 모델명에 아래 키워드가 포함되면 렌즈 스펙을 자동으로 채워줍니다.
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

    # --- 필름/토이카메라 (똑딱이 감성 강한 것들) ---
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

def get_shutter(exif):
    shutter = exif.get("ExposureTime", "?")
    if shutter:
        # 만약 데이터가 (분자, 분모) 형태의 튜플로 들어올 경우를 대비
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
        tz_name = tf.timezone_at(lat=coords[0], lng=coords[1])  # 위경도로 타임존 이름 찾기
        if tz_name:
            timezone = pytz.timezone(tz_name)
            aware_dt = timezone.localize(dt)
            utc_offset = aware_dt.utcoffset()

            hours = int(utc_offset.total_seconds() / 3600)
            minutes = int((utc_offset.total_seconds() % 3600) / 60)
            utc_offset_str = f"UTC{'+' if hours >= 0 else ''}{hours:02d}:{abs(minutes):02d}"

    return dt.strftime(f"%Y-%b-%d %H:%M {utc_offset_str}")


def lookup_known_lens(camera_model):
    """카메라 모델명으로 유명 번들렌즈 DB에서 매칭"""
    if not camera_model:
        return ""
    model_upper = camera_model.upper()
    for keyword, lens_spec in KNOWN_COMPACT_LENSES.items():
        if keyword.upper() in model_upper:
            return lens_spec
    return ""


def get_lens(exif, camera_model=""):
    # 1순위: 유명 번들렌즈 카메라 DB 매칭
    known = lookup_known_lens(camera_model)
    if known:
        return known

    # 2순위: EXIF LensModel (교환렌즈 카메라 등 DB에 없는 경우의 fallback)
    lens = exif.get("LensModel", "")
    if lens:
        lens_str = lens.strip()
        
        # 💡 [핵심 수정] 렌즈명 맨 앞에 카메라 기종명(Model)이 중복으로 붙어있으면 제거합니다.
        # 예: "iPhone 11 Pro back triple camera..." -> "back triple camera..."
        if camera_model and lens_str.startswith(camera_model):
            lens_str = lens_str[len(camera_model):].strip()
            
        return lens_str

    # 여기까지 왔으면 렌즈 정보를 알아낼 방법이 없음
    return ""


class Picture():
    def __init__(self, image_path):
        img = Image.open(image_path)
        self.image_path = image_path
        self.exif = get_exif_data(image_path)
        self.image = ImageOps.exif_transpose(img)
        self.camera = self.exif.get("Model", "Unknown Camera")
        self.iso = self.exif.get("ISOSpeedRatings", "?")
        
        # 안전한 float 변환을 위해 처리
        f_val = self.exif.get("FNumber", "?")
        self.f_number = float(round(f_val, 1)) if isinstance(f_val, (int, float)) else f_val
        
        self.shutter = get_shutter(self.exif)
        self.datetime = get_datetime(self.exif)
        # 💡 주입할 때 camera_model(self.camera)을 함께 넘겨주어 내부에서 필터링하게 합니다.
        self.lens = get_lens(self.exif, self.camera)

    def get_image(self): return self.image
    def get_camera(self): return self.camera
    def get_iso(self): return self.iso
    def get_f_number(self): return self.f_number
    def get_shutter(self): return self.shutter
    def get_datetime(self): return self.datetime
    def get_lens(self): return self.lens



class Picture():
    def __init__(self, image_path):
        img = Image.open(image_path)
        self.image_path = image_path
        self.exif = get_exif_data(image_path)
        self.image = self.image = ImageOps.exif_transpose(img)
        self.camera = self.exif.get("Model", "Unknown Camera")
        self.iso = self.exif.get("ISOSpeedRatings", "?")
        self.f_number = float(round(self.exif.get("FNumber", "?"),1))
        self.shutter = get_shutter(self.exif)
        self.datetime = get_datetime(self.exif)
        self.lens = get_lens(self.exif, self.camera)

    def get_image(self):
        return self.image

    def get_camera(self):
        return self.camera

    def get_iso(self):
        return self.iso

    def get_f_number(self):
        return self.f_number

    def get_shutter(self):
        return self.shutter

    def get_datetime(self):
        return self.datetime

    def get_lens(self):
        return self.lens
