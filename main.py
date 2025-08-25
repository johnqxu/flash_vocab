import json
import sys
import os
import glob
from pdf_generator import create_flashcards_pdf
from dashscope_client import analyze_file_with_dashscope

# 加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("警告: 未安装 python-dotenv，无法自动加载 .env 文件")


def main():
    """
    主函数，处理命令行参数或标准输入
    """
    # 检查workspace目录中的jpeg或pdf文件
    workspace_files = []
    for ext in ["*.jpeg", "*.jpg", "*.pdf"]:
        workspace_files.extend(glob.glob(os.path.join("workspace", ext)))

    if workspace_files:
        # 如果找到文件，则逐一上传到阿里百炼大模型API进行分析，并生成对应的PDF
        print("找到以下文件:")
        for file in workspace_files:
            print(f"  {file}")

        # 逐一处理每个文件
        for i, file_path in enumerate(workspace_files, 1):
            print(f"正在处理文件 ({i}/{len(workspace_files)}): {file_path}")

            # 调用阿里百炼大模型API进行分析
            data = analyze_file_with_dashscope(file_path)

            # 生成PDF文件
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_filename = f"flashcards_{base_name}.pdf"
            create_flashcards_pdf(data, output_filename)
            print(f"已生成PDF文件: {output_filename}")


if __name__ == "__main__":
    main()
