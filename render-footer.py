from datetime import datetime

year = datetime.now().year

with open("_footer.qmd", "w", encoding="utf-8") as f:
    f.write(f"© Kisung You 2021-{year}\n")