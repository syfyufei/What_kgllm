#!/usr/bin/env python3
"""
安装数据处理所需的依赖库
"""

import subprocess
import sys

def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {package} 安装失败")
        return False

def main():
    """安装所有必需的依赖"""
    print("🚀 开始安装数据处理依赖库...")
    print("="*50)

    # 必需的包列表
    packages = [
        "PyPDF2",
        "pdfplumber",
        "opencc-python-reimplemented",
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "networkx",
        "scikit-learn"
    ]

    success_count = 0
    for package in packages:
        print(f"📦 安装 {package}...")
        if install_package(package):
            success_count += 1
        print()

    print("="*50)
    print(f"📊 安装完成: {success_count}/{len(packages)} 个包安装成功")

    if success_count == len(packages):
        print("✅ 所有依赖安装完成！")
    else:
        print("⚠️  部分依赖安装失败，请手动安装")

if __name__ == "__main__":
    main()
