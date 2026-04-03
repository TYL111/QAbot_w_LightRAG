import pdfplumber

def process_complex_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        all_content = []
        for page in pdf.pages:
            # 1. 嘗試提取表格
            table = page.extract_table()
            if table:
                # 將表格轉為 Markdown 格式
                markdown_table = ""
                for i, row in enumerate(table):
                    # 清理換行符號，避免破壞 Markdown 結構
                    clean_row = [str(cell).replace('\n', ' ') if cell else "" for cell in row]
                    markdown_table += "| " + " | ".join(clean_row) + " |\n"
                    if i == 0: # 加入 Markdown 分隔線
                        markdown_table += "| " + " | ".join(["---"] * len(row)) + " |\n"
                all_content.append(markdown_table)
            else:
                # 2. 如果沒表格，才用普通提取
                all_content.append(page.extract_text(layout=True))
                
    return "\n\n".join(all_content)

print(process_complex_pdf("./115年度新北市產業輔導資源手冊_11503更新_公告版.pdf"))