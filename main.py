import json
import sys
import os
import glob
from pdf_generator import create_flashcards_pdf
from dashscope_client import analyze_files_with_dashscope


def main():
    """
    主函数，处理命令行参数或标准输入
    """
    # 检查workspace目录中的jpeg或pdf文件
    workspace_files = []
    for ext in ["*.jpeg", "*.jpg", "*.pdf"]:
        workspace_files.extend(glob.glob(os.path.join("workspace", ext)))

    if workspace_files:
        # 如果找到文件，则将这些文件作为参数上传到阿里百炼大模型API进行分析
        print("找到以下文件:")
        for file in workspace_files:
            print(f"  {file}")

        # 调用阿里百炼大模型API进行分析
        data = analyze_files_with_dashscope(workspace_files)
    elif len(sys.argv) > 1:
        # 如果提供了文件路径参数
        input_file = sys.argv[1]
        if input_file.endswith(".json"):
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            print("请提供JSON格式的文件")
            return
    else:
        # 从标准输入读取JSON数据
        print("请输入JSON格式的单词数据（输入完成后按Ctrl+D）:")
        input_text = sys.stdin.read()
        try:
            data = json.loads(input_text)
        except json.JSONDecodeError:
            print("输入的不是有效的JSON格式")
            return

    # 生成PDF文件
    output_filename = "flashcards.pdf"
    create_flashcards_pdf(data, output_filename)
    print(f"已生成PDF文件: {output_filename}")


if __name__ == "__main__":
    main()
