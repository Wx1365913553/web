# utils/excel.py
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

def export_to_excel(df, filepath):
    """将 DataFrame 导出到 Excel 文件，自动调整列宽"""
    try:
        # 使用 openpyxl 引擎
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
            
            # 调整列宽
            worksheet = writer.sheets['Sheet1']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        value_len = len(str(cell.value))
                        if value_len > max_length:
                            max_length = value_len
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        return True
    except Exception as e:
        print(f"导出 Excel 失败: {str(e)}")
        return False