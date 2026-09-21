from pathlib import Path

folder_path = Path("../data")

urls = []

for txt_file in folder_path.rglob("*.txt"):
    with open(txt_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("URL:"):
                urls.append(line.split("URL:", 1)[1].strip())
                break

print(f"總共找到 {len(urls)} 個 URL")

for url in urls:
    print(url)