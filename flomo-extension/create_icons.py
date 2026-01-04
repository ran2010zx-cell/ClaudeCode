#!/usr/bin/env python3
"""
简单的图标生成脚本
创建 Chrome 扩展所需的 PNG 图标文件
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """创建指定尺寸的图标"""
    # 创建圆角矩形背景
    img = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(img)

    # 绘制圆角矩形背景
    radius = int(size * 0.2)
    # 背景色 - flomo 蓝色
    bg_color = (52, 152, 219)  # #3498db

    # 绘制圆角矩形
    draw.rounded_rectangle(
        [(0, 0), (size, size)],
        radius=radius,
        fill=bg_color
    )

    # 添加文字 emoji
    # 计算 emoji 大小
    emoji_size = int(size * 0.6)

    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", emoji_size)
    except:
        # 如果找不到字体，使用默认字体
        font = ImageFont.load_default()

    # 绘制文字（使用简单的符号代替 emoji）
    text = "📝"

    # 计算文字位置（居中）
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    position = (
        (size - text_width) // 2,
        (size - text_height) // 2
    )

    # 绘制白色文字
    draw.text(position, text, fill='white', font=font)

    # 保存图片
    img.save(output_path, 'PNG')
    print(f"✓ 已创建: {output_path}")

def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(script_dir, 'icons')

    # 确保 icons 目录存在
    os.makedirs(icons_dir, exist_ok=True)

    print("🎨 开始生成 Chrome 扩展图标...")
    print()

    # 生成三种尺寸的图标
    sizes = {
        'icon16.png': 16,
        'icon48.png': 48,
        'icon128.png': 128
    }

    for filename, size in sizes.items():
        output_path = os.path.join(icons_dir, filename)
        create_icon(size, output_path)

    print()
    print("🎉 所有图标已生成完成！")
    print(f"📁 图标位置: {icons_dir}")

if __name__ == '__main__':
    main()
