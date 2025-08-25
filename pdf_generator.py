from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    KeepInFrame,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json
import sys
import os

# 注册中文字体
pdfmetrics.registerFont(TTFont("STHeitiLight", "STHeiti Light.ttc"))


def create_flashcards_pdf(data, output_filename):
    """
    将JSON数据转换为PDF格式的单词卡片

    Args:
        data: 包含单词信息的列表
        output_filename: 输出PDF文件名
    """
    # 创建PDF文档
    doc = SimpleDocTemplate(output_filename, pagesize=A4)
    doc.title = "单词卡片"
    doc.author = "flash_vocab"
    doc.subject = "单词闪卡"
    doc.keywords = ["单词", "记忆", "闪卡"]

    # 设置页面边距为0
    doc.leftMargin = 0
    doc.rightMargin = 0
    doc.topMargin = 0
    doc.bottomMargin = 0

    # 使用注册的中文字体
    chinese_font = "STHeitiLight"

    # 页面宽度和高度
    page_width, page_height = A4
    usable_width = page_width - doc.leftMargin - doc.rightMargin
    usable_height = page_height - doc.topMargin - doc.bottomMargin - 40

    # 每页3x4的卡片布局
    cards_per_row = 3
    cards_per_column = 4
    total_cards_per_page = cards_per_row * cards_per_column

    # 计算每个卡片的尺寸
    card_width = usable_width / cards_per_row
    card_height = usable_height / cards_per_column

    # 创建样式
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = chinese_font

    # 定义所有样式
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontName=chinese_font,
        fontSize=8,
        alignment=TA_CENTER,
        textColor='gray',
    )
    
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName=chinese_font,
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=6,
        leading=16,
    )

    chinese_style = ParagraphStyle(
        "Chinese",
        parent=styles["Normal"],
        fontName=chinese_font,
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=6,
        leading=14,
    )

    pos_style = ParagraphStyle(
        "PartOfSpeech",
        parent=styles["Normal"],
        fontName=chinese_font,
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=4,
        leading=12,
        textColor='purple',
    )

    example_style = ParagraphStyle(
        "Example",
        parent=styles["Normal"],
        fontName=chinese_font,
        fontSize=9,
        alignment=TA_CENTER,
        leading=10,
        textColor='green',
    )

    # 准备数据
    cards_data = []
    for item in data:
        # 获取单词信息
        english = item.get("english", "")
        chinese = item.get("chinese", "")
        part_of_speech = item.get("part_of_speech", "")
        example_sentence = item.get("example_sentence", "")

        # 为每个卡片创建一个包含4个等高部分的列表
        card_parts = []
        
        # 计算每个部分的高度（卡片高度的1/4）
        quarter_height = card_height / 4
        
        # 1. 英文单词部分 (第一个1/4)
        english_content = []
        english_content.append(Paragraph("English", label_style))
        if english:
            english_content.append(Paragraph(english, title_style))
        else:
            english_content.append(Spacer(1, 10))  # 添加一些空间保持布局
        
        english_frame = KeepInFrame(
            int(card_width - 0.5 * cm), 
            int(quarter_height - 0.1 * cm), 
            english_content,
            mode="shrink"
        )
        card_parts.append(english_frame)
        
        # 2. 词性部分 (第二个1/4)
        pos_content = []
        pos_content.append(Paragraph("Part of Speech", label_style))
        if part_of_speech:
            pos_content.append(Paragraph(part_of_speech, pos_style))
        else:
            pos_content.append(Spacer(1, 10))  # 添加一些空间保持布局
        
        pos_frame = KeepInFrame(
            int(card_width - 0.5 * cm), 
            int(quarter_height - 0.1 * cm), 
            pos_content,
            mode="shrink"
        )
        card_parts.append(pos_frame)
        
        # 3. 中文释义部分 (第三个1/4)
        chinese_content = []
        chinese_content.append(Paragraph("Chinese", label_style))
        if chinese:
            chinese_content.append(Paragraph(chinese, chinese_style))
        else:
            chinese_content.append(Spacer(1, 10))  # 添加一些空间保持布局
        
        chinese_frame = KeepInFrame(
            int(card_width - 0.5 * cm), 
            int(quarter_height - 0.1 * cm), 
            chinese_content,
            mode="shrink"
        )
        card_parts.append(chinese_frame)
        
        # 4. 例句部分 (第四个1/4)
        example_content = []
        example_content.append(Paragraph("Example", label_style))
        if example_sentence:
            example_content.append(Paragraph(example_sentence, example_style))
        else:
            example_content.append(Spacer(1, 10))  # 添加一些空间保持布局
        
        example_frame = KeepInFrame(
            int(card_width - 0.5 * cm), 
            int(quarter_height - 0.1 * cm), 
            example_content,
            mode="shrink"
        )
        card_parts.append(example_frame)

        cards_data.append(card_parts)

    # 补齐卡片数量为total_cards_per_page的倍数
    while len(cards_data) % total_cards_per_page != 0:
        # 添加空卡片，每个空卡片也包含4个等高的部分
        empty_card_parts = []
        quarter_height = card_height / 4
        
        for i in range(4):
            # 为每个空卡片部分添加标签
            empty_content = [Paragraph(["English", "Part of Speech", "Chinese", "Example"][i], label_style)]
            empty_content.append(Spacer(1, 10))  # 添加一些空间保持布局
            
            empty_frame = KeepInFrame(
                int(card_width - 0.5 * cm), 
                int(quarter_height - 0.1 * cm), 
                empty_content,
                mode="shrink"
            )
            empty_card_parts.append(empty_frame)
            
        cards_data.append(empty_card_parts)

    # 构建PDF表格
    elements = []

    # 按页处理
    for page_start in range(0, len(cards_data), total_cards_per_page):
        page_cards = cards_data[page_start : page_start + total_cards_per_page]

        # 构建表格数据
        table_data = []
        for row in range(cards_per_column):
            table_row = []
            for col in range(cards_per_row):
                card_index = row * cards_per_row + col
                if card_index < len(page_cards):
                    # 将卡片的4个部分垂直组合
                    card_content = page_cards[card_index]
                    card_frame = KeepInFrame(
                        int(card_width - 0.3 * cm), 
                        int(card_height - 0.3 * cm), 
                        card_content
                    )
                    table_row.append(card_frame)
                else:
                    table_row.append("")
            table_data.append(table_row)

        # 创建表格
        table = Table(
            table_data,
            colWidths=[card_width] * cards_per_row,
            rowHeights=[card_height] * cards_per_column,
        )

        # 设置表格样式
        table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 1, (0, 0, 0)),  # 边框
                ]
            )
        )

        elements.append(table)

    # 构建PDF
    doc.build(elements)


def main():
    """
    调试入口函数，方便直接测试create_flashcards_pdf功能
    """
    # 默认使用test_data.json作为测试数据
    test_data_file = "test_data.json"
    
    if len(sys.argv) > 1:
        test_data_file = sys.argv[1]
    
    if not os.path.exists(test_data_file):
        print(f"错误: 测试数据文件 {test_data_file} 不存在")
        return
    
    try:
        with open(test_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        output_filename = f"flashcards_{os.path.splitext(os.path.basename(test_data_file))[0]}.pdf"
        create_flashcards_pdf(data, output_filename)
        print(f"PDF文件已生成: {output_filename}")
        
    except Exception as e:
        print(f"生成PDF时出错: {e}")


if __name__ == "__main__":
    main()