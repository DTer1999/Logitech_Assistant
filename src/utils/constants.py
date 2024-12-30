from typing import Dict, List
from enum import Enum, auto

class WeaponType(Enum):
    """武器类型枚举"""
    RIFLE = auto()      # 步枪
    SNIPER = auto()     # 狙击枪
    SMG = auto()        # 冲锋枪
    LMG = auto()        # 轻机枪
    DMR = auto()        # 精确射手步枪
    UNKNOWN = auto()    # 未知类型

class PoseType(Enum):
    """姿势类型枚举"""
    STAND = auto()      # 站立
    CROUCH = auto()     # 蹲下
    UNKNOWN = auto()    # 未知姿势

# 武器名称映射
WEAPON_NAME_MAP: Dict[str, str] = {
    "AKM": "AKM",
    "Berry": "Berry",
    "AUG": "AUG",
    "M416": "M416",
    "ACE32": "ACE32",
    "G36C": "G36C",
    "GROZA": "GROZA",
    "FAMAS": "FAMAS",
    "M16": "M16",
    "K2": "K2",
    "SCAR": "SCAR",
    "M249": "M249",
    "DP28": "DP28",
    "MG3": "MG3",
    "P90": "P90",
    "QBZ": "QBZ",
    "MK47": "MK47",
    "DLG": "DLG",
    "SKS": "SKS",
    "SLR": "SLR",
    "MINI": "MINI",
    "MK12": "MK12",
    "QBU": "QBU",
    "VSS": "VSS",
    "MK14": "MK14",
    "JS9": "JS9",
    "MP5": "MP5",
    "MP9": "MP9",
    "UMP": "UMP",
    "TOM": "TOM",
    "UZI": "UZI",
    "VECTOR": "VECTOR",
    "PP19": "PP19",
}

# 配件名称映射
ATTACHMENT_NAME_MAP: Dict[str, str] = {
    # 倍镜
    "reddot": "红点",
    "quanxi": "全息",
    "x2": "2倍",
    "x3": "3倍",
    "x4": "4倍",
    "x6": "6倍",
    "x8": "8倍",
    # 枪口
    "bc1": "补偿1",
    "bc2": "补偿2",
    "bc3": "补偿3",
    "xy1": "消焰1",
    "xy2": "消焰2",
    "xy3": "消焰3",
    "xx": "消声1",
    "xx1": "消声2",
    "zt": "抑制",
    # 握把
    "angle": "三角",
    "light": "轻型",
    "line": "垂直",
    "thumb": "拇指",
    "red": "红握",
    # 枪托
    "normal": "枪托",
    "heavy": "重型",
    "pg": "屁股",
}

# 姿势名称映射
POSE_NAME_MAP: Dict[str, str] = {
    "stand": "站立",
    "down": "蹲下",
}

# 属性键名列表
ATTRIBUTE_KEYS: Dict[str, List[str]] = {
    "poses": ["stand", "down"],
    "weapons": list(WEAPON_NAME_MAP.keys()),
    "scopes": ["reddot", "quanxi", "x2", "x3", "x4", "x6", "x8"],
    "muzzles": ["bc1", "bc2", "bc3", "xy1", "xy2", "xy3", "xx", "xx1", "zt"],
    "grips": ["angle", "light", "line", "thumb", "red"],
    "stocks": ["normal", "heavy", "pg"],
}

def get_weapon_type(weapon_name: str) -> WeaponType:
    """获取武器类型"""
    rifle_weapons = ["AKM", "Berry", "AUG", "M416", "ACE32", "G36C", "GROZA", "FAMAS", "M16", "K2", "SCAR", "QBZ"]
    dmr_weapons = ["SKS", "SLR", "MINI", "MK12", "QBU", "VSS", "MK14"]
    smg_weapons = ["JS9", "MP5", "MP9", "UMP", "TOM", "UZI", "VECTOR", "PP19", "P90"]
    lmg_weapons = ["M249", "DP28", "MG3"]
    
    if weapon_name in rifle_weapons:
        return WeaponType.RIFLE
    elif weapon_name in dmr_weapons:
        return WeaponType.DMR
    elif weapon_name in smg_weapons:
        return WeaponType.SMG
    elif weapon_name in lmg_weapons:
        return WeaponType.LMG
    return WeaponType.UNKNOWN

def translate_name(key: str) -> str:
    """
    翻译键名为显示名称
    
    Args:
        key: 原始键名
        
    Returns:
        str: 翻译后的名称
    """
    # 检查各个映射表
    for name_map in [WEAPON_NAME_MAP, ATTACHMENT_NAME_MAP, POSE_NAME_MAP]:
        if key in name_map:
            return name_map[key]
    return key

def get_attribute_keys(category: str) -> List[str]:
    """
    获取指定类别的属性键名列表
    
    Args:
        category: 类别名称
        
    Returns:
        List[str]: 属性键名列表
    """
    return ATTRIBUTE_KEYS.get(category, [category])

def get_pose_type(pose_name: str) -> PoseType:
    """
    获取姿势类型
    
    Args:
        pose_name: 姿势名称
        
    Returns:
        PoseType: 姿势类型枚举值
    """
    pose_map = {
        "stand": PoseType.STAND,
        "crouch": PoseType.CROUCH,
        "prone": PoseType.PRONE
    }
    return pose_map.get(pose_name, PoseType.UNKNOWN)