import json
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    KeepInFrame,
    Paragraph,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册中文字体
pdfmetrics.registerFont(TTFont('STHeitiLight', 'STHeiti Light.ttc'))


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
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName=chinese_font,
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    chinese_style = ParagraphStyle(
        "Chinese",
        parent=styles["Normal"],
        fontName=chinese_font,
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    pos_style = ParagraphStyle(
        "PartOfSpeech",
        parent=styles["Normal"],
        fontName=chinese_font,
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    example_style = ParagraphStyle(
        "Example",
        parent=styles["Normal"],
        fontName=chinese_font,
        fontSize=9,
        alignment=TA_CENTER,
        leading=10,
    )

    # 准备数据
    cards_data = []
    for item in data:
        # 获取单词信息
        english = item.get("english", "")
        chinese = item.get("chinese", "")
        part_of_speech = item.get("part_of_speech", "")
        example_sentence = item.get("example_sentence", "")

        # 创建卡片内容
        card_content = []

        # 英文单词
        if english:
            card_content.append(Paragraph(english, title_style))

        # 词性
        if part_of_speech:
            card_content.append(Paragraph(f"({part_of_speech})", pos_style))
        elif not part_of_speech and english:
            # 如果有英文但没有词性，则添加空行保持格式一致
            card_content.append(Paragraph("&nbsp;", pos_style))

        # 中文释义
        if chinese:
            card_content.append(Paragraph(chinese, chinese_style))

        # 例句
        if example_sentence:
            card_content.append(Paragraph(example_sentence, example_style))

        cards_data.append(card_content)

    # 补齐卡片数量为total_cards_per_page的倍数
    while len(cards_data) % total_cards_per_page != 0:
        cards_data.append([])

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
                    # 使用KeepInFrame确保内容适应卡片大小
                    content = page_cards[card_index]
                    frame = KeepInFrame(
                        int(card_width - 0.5 * cm), int(card_height - 0.5 * cm), content
                    )
                    table_row.append(frame)
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