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
    
    # 1. Xử lý Lịch sử
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

    # 3. System Prompt: Ép IUPAC và phong cách giáo viên
    system_prompt = (
        "Ban la giao vien Hoa hoc. Xung Thay - Em. "
        "KHONG dung LaTeX (khong dung dau $). "
        "Dung dau cham (.) cho phep nhan. "
        "BAT BUOC: Goi ten cac chat theo danh phap IUPAC (Vi du: Sodium, Oxygen, Hydrogen, Iron(III) oxide...)."
    )

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash", # Doi ve ban 1.5 de tranh loi 429
            contents=content_list,
            config={'system_instruction': system_prompt}
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        # Neu van bi loi quota, thong bao nhe nhang cho nguoi dung
        if "429" in str(e):
            return jsonify({"reply": "He thong dang qua tai mot chut, em doi 30 giay roi bam gui lai nhe!"})
        return jsonify({"reply": f"Loi: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
