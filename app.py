import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from google import genai
import io

app = Flask(__name__)
CORS(app)

# Kết nối với Gemini qua Key bí mật
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

@app.route("/", methods=["GET"])
def home():
    return "Server Hoa Hoc dang chay tot!"

@app.route("/chat", methods=["POST"])
def chat():
    user_text = request.form.get("message", "")
    history_raw = request.form.get("history", "[]")
    
    content_list = []
    
    # 1. Xử lý Lịch sử (Dùng Thầy - Em cho thân thiện)
    try:
        history = json.loads(history_raw)
        for item in history:
            content_list.append(f"Em: {item.get('user')}")
            content_list.append(f"Thay: {item.get('ai')}")
    except:
        pass

    # 2. Xử lý nội dung hiện tại
    if user_text:
        content_list.append(user_text)
    
    if "file" in request.files:
        file = request.files["file"]
        if file.filename != '':
            img = Image.open(file.stream).convert("RGB")
            content_list.append(img)

    if not content_list:
        return jsonify({"reply": "Thay dang doi cau hoi cua em."})

    # 3. System Prompt chuẩn IUPAC và phong cách giáo viên
    system_prompt = (
        "Ban la giao vien Hoa hoc. Xung Thay - Em. "
        "KHONG dung LaTeX. Dung dau cham (.) cho phep nhan. "
        "BAT BUOC: Goi ten cac chat theo danh phap IUPAC (Vi du: Sodium, Oxygen, Hydrogen, Iron(III) oxide...)."
    )

    # DANH SÁCH MODEL: Đưa 1.5 Flash lên đầu để tránh lỗi 429 nhanh nhất
    # Gói Free của 1.5 Flash có giới hạn rộng hơn nhiều so với bản 3 Preview.
    model_names = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-3-flash-preview"]
    
    last_error = ""
    for m_name in model_names:
        try:
            response = client.models.generate_content(
                model=m_name, 
                contents=content_list,
                config={'system_instruction': system_prompt}
            )
            return jsonify({"reply": response.text})
        except Exception as e:
            last_error = str(e)
            # Nếu gặp lỗi 429 (hết quota), thử model tiếp theo trong danh sách
            if "429" in last_error or "404" in last_error:
                continue 
            break
            
    # Phản hồi thông minh nếu tất cả model đều bận
    if "429" in last_error:
        return jsonify({"reply": "He thong dang qua tai luot dung mien phi cua Google. Em vui long doi khoang 1 phut roi bam Gui lai nhe!"})
        
    return jsonify({"reply": f"Loi he thong: {last_error}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
