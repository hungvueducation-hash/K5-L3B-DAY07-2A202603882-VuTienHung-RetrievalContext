"""Bước 2: dùng model có vision để mô tả nội dung TRỰC QUAN của từng trang (bảng, biểu đồ, sơ đồ, ảnh, bản đồ).
Kết quả `work/visual.jsonl` là dữ liệu index được (sinh bởi model → có thể sai; benchmark được đối chiếu bản gốc, không dựa vào file này).
Dùng: python describe_pages.py [model]"""
import base64, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import common  # noqa: nạp OPENAI_API_KEY
from openai import OpenAI

MODEL = sys.argv[1] if len(sys.argv) > 1 else "gpt-4.1-mini"
W = Path(__file__).resolve().parent / "work"
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
PROMPT = """Đây là một trang của báo cáo ngân hàng thế giới (tiếng Anh). Chỉ mô tả NỘI DUNG TRỰC QUAN trên trang (bảng, biểu đồ, sơ đồ/khung khái niệm, bản đồ, ảnh); bỏ qua đoạn văn thường.
- Với mỗi BẢNG: chép lại đầy đủ dạng markdown (giữ tiêu đề cột, đơn vị, số liệu).
- Với mỗi BIỂU ĐỒ: nêu số hiệu/tiêu đề, loại biểu đồ, trục (đơn vị), chú giải, rồi đọc các giá trị/nhãn dữ liệu nhìn thấy rõ (ghi "xấp xỉ" nếu ước lượng) và xu hướng chính.
- Với SƠ ĐỒ/BẢN ĐỒ/ẢNH: nêu tiêu đề, các thành phần, nhãn chữ và quan hệ giữa chúng.
Viết bằng tiếng Anh giữ nguyên thuật ngữ gốc. Nếu trang không có nội dung trực quan, trả lời đúng một dòng: NO_VISUAL."""

def one(page):
    out = W / "visual" / f"p{page:03d}.json"
    if out.exists():
        return
    b64 = base64.b64encode((W / "img" / f"p{page:03d}.jpg").read_bytes()).decode()
    for attempt in range(3):
        try:
            r = client.chat.completions.create(model=MODEL, temperature=0, max_tokens=1500, messages=[{"role": "user", "content": [
                {"type": "text", "text": PROMPT}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}}]}])
            out.write_text(json.dumps({"page": page, "model": MODEL, "text": r.choices[0].message.content,
                "prompt_tokens": r.usage.prompt_tokens, "completion_tokens": r.usage.completion_tokens}, ensure_ascii=False), encoding="utf8")
            return
        except Exception as e:
            time.sleep(3 * (attempt + 1)); err = repr(e)[:200]
    (W / "visual" / f"p{page:03d}.error").write_text(err)

if __name__ == "__main__":
    (W / "visual").mkdir(exist_ok=True)
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(one, range(1, 249)))
    print("done")
