import os
import hashlib
import requests

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

    # 计算新图片的SHA256哈希值
    new_hash = hashlib.sha256(response.content).hexdigest()
    print(f"新图片SHA256: {new_hash}")

    # 检查文件是否已存在并计算其哈希值
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            existing_hash = hashlib.sha256(f.read()).hexdigest()
        print(f"现有图片SHA256: {existing_hash}")

        if new_hash == existing_hash:
            print("图片内容相同，跳过保存")
            exit(0)
        else:
            print("图片内容不同，将更新文件")

    # 保存PNG图片
    with open(filepath, "wb") as f:
        f.write(response.content)

    print(f"图片已保存到: {filepath}")
    print(f"文件大小: {len(response.content)} 字节")
else:
    print(f"下载失败，状态码: {response.status_code}")
    exit(1)
