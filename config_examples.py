#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置示例 - Android 开关机动画制作工具
"""

# 常用的 Android 设备分辨率配置
RESOLUTION_PRESETS = {
    "720p": (720, 1280),
    "1080p": (1080, 1920),
    "1440p": (1440, 2560),
    "4K": (2160, 3840),
    "小米": (1080, 2340),
    "华为": (1080, 2244),
    "三星": (1440, 3040),
    "OnePlus": (1080, 2400),
}

# 常用帧率配置
FPS_PRESETS = {
    "流畅": 60,
    "标准": 30,
    "省电": 24,
    "慢动作": 15,
    "超慢": 10,
}

# 动画类型配置
ANIMATION_TYPES = {
    "开机动画": {
        "description": "设备启动时播放的动画",
        "recommended_fps": 30,
        "recommended_loop": 1,
        "max_duration": 10,  # 秒
    },
    "关机动画": {
        "description": "设备关机时播放的动画",
        "recommended_fps": 24,
        "recommended_loop": 1,
        "max_duration": 5,  # 秒
    },
    "充电动画": {
        "description": "设备充电时播放的动画",
        "recommended_fps": 15,
        "recommended_loop": 0,  # 无限循环
        "max_duration": 3,  # 秒
    },
}

# 图片质量配置
IMAGE_QUALITY = {
    "高质量": 95,
    "标准": 85,
    "压缩": 75,
    "高压缩": 60,
}

# desc.txt 模板
DESC_TEMPLATES = {
    "标准模板": "{width} {height} {fps}\np {loop} 0 part0\n",
    "多部分模板": "{width} {height} {fps}\np 1 0 part0\np 0 0 part1\n",
    "带暂停模板": "{width} {height} {fps}\np {loop} 1000 part0\n",
}

# 文件命名规则
FILE_NAMING = {
    "数字序列": "{index:05d}.jpg",  # 00000.jpg, 00001.jpg, ...
    "带前缀": "frame_{index:04d}.jpg",  # frame_0000.jpg, frame_0001.jpg, ...
    "时间戳": "{timestamp}_{index:03d}.jpg",  # 用于调试
}

# 优化建议
OPTIMIZATION_TIPS = {
    "文件大小": [
        "使用适当的图片质量设置",
        "避免过多的图片帧数",
        "选择合适的分辨率",
        "使用 JPEG 格式而非 PNG",
    ],
    "播放流畅度": [
        "保持一致的图片尺寸",
        "使用稳定的帧率",
        "避免过高的分辨率",
        "测试在目标设备上的表现",
    ],
    "兼容性": [
        "使用标准的 ZIP 压缩",
        "确保 desc.txt 格式正确",
        "使用 JPEG 图片格式",
        "避免特殊字符在文件名中",
    ],
}

# 设备特定配置
DEVICE_CONFIGS = {
    "小米设备": {
        "path": "/system/media/bootanimation.zip",
        "resolution": (1080, 2340),
        "fps": 30,
        "notes": "MIUI 系统可能需要额外的权限设置",
    },
    "华为设备": {
        "path": "/system/media/bootanimation.zip",
        "resolution": (1080, 2244),
        "fps": 24,
        "notes": "EMUI 系统支持自定义开机动画",
    },
    "三星设备": {
        "path": "/system/media/bootanimation.zip",
        "resolution": (1440, 3040),
        "fps": 30,
        "notes": "One UI 可能需要特殊的签名",
    },
    "原生Android": {
        "path": "/system/media/bootanimation.zip",
        "resolution": (1080, 1920),
        "fps": 30,
        "notes": "标准 AOSP 配置",
    },
}

def get_recommended_settings(animation_type, device_type=None):
    """获取推荐设置"""
    settings = {
        "fps": 30,
        "loop": 1,
        "resolution": (720, 1280),
        "quality": 85,
    }
    
    # 根据动画类型调整
    if animation_type in ANIMATION_TYPES:
        anim_config = ANIMATION_TYPES[animation_type]
        settings["fps"] = anim_config["recommended_fps"]
        settings["loop"] = anim_config["recommended_loop"]
    
    # 根据设备类型调整
    if device_type and device_type in DEVICE_CONFIGS:
        device_config = DEVICE_CONFIGS[device_type]
        settings["resolution"] = device_config["resolution"]
        settings["fps"] = device_config["fps"]
    
    return settings

def validate_settings(fps, loop, image_count, resolution):
    """验证设置的合理性"""
    warnings = []
    errors = []
    
    # 检查帧率
    if fps > 60:
        warnings.append("帧率过高可能导致设备性能问题")
    elif fps < 10:
        warnings.append("帧率过低可能导致动画不流畅")
    
    # 检查图片数量
    if image_count > 100:
        warnings.append("图片数量过多可能导致文件过大")
    elif image_count < 5:
        warnings.append("图片数量过少可能导致动画过短")
    
    # 检查分辨率
    width, height = resolution
    if width * height > 4096 * 4096:
        errors.append("分辨率过高，可能导致内存不足")
    
    # 估算文件大小
    estimated_size = image_count * (width * height * 3) // 10  # 粗略估算
    if estimated_size > 50 * 1024 * 1024:  # 50MB
        warnings.append(f"预估文件大小约 {estimated_size // (1024*1024)}MB，可能过大")
    
    return warnings, errors

if __name__ == "__main__":
    # 示例用法
    print("=== Android 开关机动画配置示例 ===")
    
    # 获取开机动画的推荐设置
    settings = get_recommended_settings("开机动画", "小米设备")
    print(f"\n开机动画推荐设置: {settings}")
    
    # 验证设置
    warnings, errors = validate_settings(
        fps=settings["fps"],
        loop=settings["loop"],
        image_count=30,
        resolution=settings["resolution"]
    )
    
    if warnings:
        print("\n⚠️  警告:")
        for warning in warnings:
            print(f"   - {warning}")
    
    if errors:
        print("\n❌ 错误:")
        for error in errors:
            print(f"   - {error}")
    
    print("\n📱 支持的设备类型:")
    for device, config in DEVICE_CONFIGS.items():
        print(f"   - {device}: {config['resolution']} @ {config['fps']}fps")
