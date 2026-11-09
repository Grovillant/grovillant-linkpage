import qrcode
from PIL import Image, ImageDraw
import os

# 脚本所在目录（相对路径，不再写死 ~/grovillant-linkpage）
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = script_dir
logo_path = os.path.join(script_dir, "logo.jpg")

# 主域名
main_url = "https://grovillant.com"

# 5 个渠道：文件名 → 跳转 URL
channels = {
    "pkg":    "https://grovillant.com/q/pkg",
    "manual": "https://grovillant.com/q/manual",
    "card":   "https://grovillant.com/q/card",
    "fair":   "https://grovillant.com/q/fair",
    "ad":     "https://grovillant.com/q/ad",
}


def make_qr(url):
    """生成一个带 logo 的高清二维码 PIL 图（300dpi）。"""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=40,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a2e", back_color="white").convert('RGB')

    # 中间放 logo
    if os.path.exists(logo_path):
        logo = Image.open(logo_path)
        logo_size = int(img.size[0] * 0.22)
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

        pos = ((img.size[0] - logo_size) // 2, (img.size[1] - logo_size) // 2)

        # 白色圆形背景
        bg_size = logo_size + 40
        bg_pos = ((img.size[0] - bg_size) // 2, (img.size[1] - bg_size) // 2)
        draw_img = ImageDraw.Draw(img)
        draw_img.ellipse(
            (bg_pos[0], bg_pos[1], bg_pos[0] + bg_size, bg_pos[1] + bg_size),
            fill="white",
        )
        img.paste(logo, pos)

    return img, qr


def save_png(img, path, dpi=(300, 300)):
    """保存屏幕版 PNG（300dpi）。"""
    img.save(path, "PNG", dpi=dpi)
    print(f"PNG saved: {path} ({img.size[0]}x{img.size[1]} px)")


def save_print_png(img, path, padding=200, dpi=(300, 300)):
    """保存印刷版 PNG（四周加白边）。"""
    new_size = (img.size[0] + padding * 2, img.size[1] + padding * 2)
    padded_img = Image.new('RGB', new_size, 'white')
    padded_img.paste(img, (padding, padding))
    padded_img.save(path, "PNG", dpi=dpi)
    print(f"Print PNG saved: {path} ({padded_img.size[0]}x{padded_img.size[1]} px)")


# ========== 1. 主域名二维码 ==========
print("=== 主域名 QR 码 ===")
main_img, main_qr = make_qr(main_url)

main_png = os.path.join(output_dir, "grovillant-qr-code.png")
save_png(main_img, main_png)

main_print = os.path.join(output_dir, "grovillant-qr-code-print.png")
save_print_png(main_img, main_print)

# 主域名 SVG
import qrcode.image.svg
factory = qrcode.image.svg.SvgImage
qr_svg = qrcode.QRCode(
    version=main_qr.version,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
qr_svg.add_data(main_url)
qr_svg.make(fit=True)
svg_img = qr_svg.make_image(image_factory=factory, fill_color="#1a1a2e", back_color="white")
svg_path = os.path.join(output_dir, "grovillant-qr-code.svg")
svg_img.save(svg_path)
print(f"SVG saved: {svg_path}")

# ========== 2. 5 个渠道二维码 ==========
print("\n=== 5 个渠道 QR 码 ===")
for name, url in channels.items():
    print(f"\n--- {name} ({url}) ---")
    img, _ = make_qr(url)

    png_path = os.path.join(output_dir, f"qr-{name}.png")
    save_png(img, png_path)

    print_png = os.path.join(output_dir, f"qr-{name}-print.png")
    save_print_png(img, print_png)

# ========== 3. 汇总 ==========
print("\n=== 全部完成 ===")
all_files = [
    "grovillant-qr-code.png",
    "grovillant-qr-code-print.png",
    "grovillant-qr-code.svg",
]
for name in channels:
    all_files.append(f"qr-{name}.png")
    all_files.append(f"qr-{name}-print.png")

for f in all_files:
    path = os.path.join(output_dir, f)
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"  {f} - {size / 1024:.1f} KB")
