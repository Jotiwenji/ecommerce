CITY_AREA_ID_MAP: dict[str, int] = {
    "北京": 2,
    "上海": 786,
    "天津": 20,
    "重庆": 2238,
    "石家庄": 38,
    "秦皇岛": 76,
    "太原": 217,
    "呼和浩特": 347,
    "沈阳": 463,
    "大连": 477,
    "长春": 578,
    "哈尔滨": 648,
    "南京": 804,
    "苏州": 842,
    "杭州": 915,
    "宁波": 929,
    "合肥": 1019,
    "福州": 1140,
    "厦门": 1154,
    "南昌": 1223,
    "济南": 1335,
    "青岛": 1348,
    "郑州": 1491,
    "洛阳": 1514,
    "武汉": 1668,
    "长沙": 1785,
    "广州": 1922,
    "深圳": 1945,
    "南宁": 2068,
    "桂林": 2092,
    "海口": 2192,
    "三亚": 2197,
    "成都": 2278,
    "贵阳": 2476,
    "昆明": 2574,
    "拉萨": 2720,
    "西安": 2802,
    "兰州": 2921,
    "西宁": 3025,
    "银川": 3079,
    "乌鲁木齐": 3107,
}


def resolve_area_id(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    s = str(value).strip()
    if s.isdigit():
        return int(s)
    name = s.rstrip("市区县")
    if name in CITY_AREA_ID_MAP:
        return CITY_AREA_ID_MAP[name]
    for city_name, area_id in CITY_AREA_ID_MAP.items():
        if city_name in s or s in city_name:
            return area_id
    return None
