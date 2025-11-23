import os
import hashlib
import requests
from PIL import Image, ImageFilter, ImageEnhance
from io import BytesIO

# 获取仓库根目录和目标文件夹路径
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
images_dir = os.path.join(repo_root, "M9A", "api", "images")

# 确保目标文件夹存在
os.makedirs(images_dir, exist_ok=True)

# 禁用SSL警告
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("正在下载图片...")
response = requests.get("https://mojing.org/tjb", verify=False)

if response.status_code == 200:
    # 使用固定文件名
    filename = "mojing_tjb.png"
    filepath = os.path.join(images_dir, filename)

    # 打开图片并优化
    print("正在优化图片...")
    img = Image.open(BytesIO(response.content))

    # 转换为 RGB
    if img.mode != "RGB":
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        else:
            img = img.convert("RGB")

    # 1. 智能裁剪 - 去除白色边缘
    print("  - 智能裁剪...")
    # 转为灰度检测边界
    gray = img.convert("L")
    # 获取非白色区域的边界框 (threshold=250，接近白色都算边缘)
    bbox = gray.point(lambda x: 0 if x > 250 else 255).getbbox()
    if bbox:
        img = img.crop(bbox)
        print(f"    裁剪后尺寸: {img.size}")

    # 2. 转换为灰度
    print("  - 转换为灰度...")
    img = img.convert("L")

    # 2.5. 缩小分辨率（缩小到 60%）
    print("  - 缩小分辨率...")
    new_size = (int(img.width * 0.6), int(img.height * 0.6))
    img = img.resize(new_size, Image.LANCZOS)  # 使用高质量重采样
    print(f"    缩放后尺寸: {img.size}")

    # 3. 锐化文字 - 增强边缘清晰度
    print("  - 锐化文字...")
    # 先用 SHARPEN 滤镜
    img = img.filter(ImageFilter.SHARPEN)
    # 再增强对比度，使文字更清晰
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)  # 增强 30% 对比度

    # 4. 使用 JPEG 保存（极限压缩，quality=50）
    print("  - 压缩保存...")
    compressed_buffer = BytesIO()
    # 极低质量，极高压缩率
    img.save(compressed_buffer, format="JPEG", quality=50, optimize=True)
    compressed_content = compressed_buffer.getvalue()

    original_size = len(response.content)
    compressed_size = len(compressed_content)
    compression_ratio = (1 - compressed_size / original_size) * 100
    print(f"原始大小: {original_size:,} 字节")
    print(f"优化后大小: {compressed_size:,} 字节")
    print(f"压缩率: {compression_ratio:.1f}%")

    # 计算优化后图片的SHA256哈希值
    new_hash = hashlib.sha256(compressed_content).hexdigest()
    print(f"优化图片SHA256: {new_hash}")

    # 检查文件是否已存在并计算其哈希值
    file_updated = False
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            existing_hash = hashlib.sha256(f.read()).hexdigest()
        print(f"现有图片SHA256: {existing_hash}")

        if new_hash == existing_hash:
            print("✓ 图片内容相同，无需更新")
            exit(0)
        else:
            print("✓ 图片内容不同，将更新文件")
            file_updated = True
    else:
        print("✓ 本地无此图片，将保存新文件")
        file_updated = True

    # 保存优化后的 PNG 图片
    with open(filepath, "wb") as f:
        f.write(compressed_content)

    if file_updated:
        print(f"✓ 图片已更新: {filepath}")
    else:
        print(f"✓ 图片已保存: {filepath}")
else:
    print(f"下载失败，状态码: {response.status_code}")
    exit(1)
