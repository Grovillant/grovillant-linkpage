import qrcode
from PIL import Image, ImageDraw
import os

url = "https://grovillant.com"
output_dir = os.path.expanduser("~/grovillant-linkpage")
os.makedirs(output_dir, exist_ok=True)

# ========== 1. 生成高清 PNG ==========
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
logo_path = os.path.expanduser("~/grovillant-linkpage/logo.jpg")
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    logo_size = int(img.size[0] * 0.22)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
    
    pos = ((img.size[0] - logo_size) // 2, (img.size[1] - logo_size) // 2)
    
    # 白色圆形背景
    bg_size = logo_size + 40
    bg_pos = ((img.size[0] - bg_size) // 2, (img.size[1] - bg_size) // 2)
    draw_img = ImageDraw.Draw(img)
    draw_img.ellipse((bg_pos[0], bg_pos[1], bg_pos[0]+bg_size, bg_pos[1]+bg_size), fill="white")
    
    img.paste(logo, pos)

png_path = os.path.join(output_dir, "grovillant-qr-code.png")
img.save(png_path, "PNG", dpi=(300, 300))
print(f"PNG saved: {png_path} ({img.size[0]}x{img.size[1]} px)")

# ========== 2. 生成 SVG ==========
import qrcode.image.svg
factory = qrcode.image.svg.SvgImage
qr_svg = qrcode.QRCode(
    version=qr.version,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
qr_svg.add_data(url)
qr_svg.make(fit=True)

svg_img = qr_svg.make_image(image_factory=factory, fill_color="#1a1a2e", back_color="white")
svg_path = os.path.join(output_dir, "grovillant-qr-code.svg")
svg_img.save(svg_path)
print(f"SVG saved: {svg_path}")

# ========== 3. 印刷版（带白边距） ==========
padding = 200
new_size = (img.size[0] + padding*2, img.size[1] + padding*2)
padded_img = Image.new('RGB', new_size, 'white')
padded_img.paste(img, (padding, padding))

padded_path = os.path.join(output_dir, "grovillant-qr-code-print.png")
padded_img.save(padded_path, "PNG", dpi=(300, 300))
print(f"Print PNG saved: {padded_path} ({padded_img.size[0]}x{padded_img.size[1]} px)")

print("\nFiles:")
for f in [png_path, padded_path, svg_path]:
    size = os.path.getsize(f)
    print(f"  {os.path.basename(f)} - {size/1024:.1f} KB")
