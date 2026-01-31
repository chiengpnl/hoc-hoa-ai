import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from google import genai
import io

app = Flask(__name__)
CORS(app)

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
    
    try:
        history = json.loads(history_raw)
        for item in history:
            content_list.append(f"Ban: {item.get('user')}")
            content_list.append(f"Minh: {item.get('ai')}")
    except: pass

    if user_text:
        content_list.append(user_text)
    
    if "file" in request.files:
        file = request.files["file"]
        if file.filename != '':
            # TỐI ƯU ẢNH: Nén ảnh lại để tránh lỗi Server bận
            img = Image.open(file.stream).convert("RGB")
            img.thumbnail((1024, 1024)) # Giảm kích thước nếu ảnh quá to
            content_list.append(img)

    if not content_list:
        return jsonify({"reply": "Minh dang doi cau hoi cua ban."})

    system_prompt = (
        "Ban la AI Hoa hoc. Xung Minh - Ban. "
        "KHONG dung LaTeX. Dung dau cham (.) cho phep nhan. "
        "BAT BUOC: Goi ten cac chat theo danh phap IUPAC."
    )

    # Sử dụng duy nhất gemini-1.5-flash vì nó hỗ trợ ảnh tốt nhất và ổn định nhất
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=content_list,
            config={'system_instruction': system_prompt}
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return jsonify({"reply": "Google dang bao het luot dung (Quota). Em hay doi 1-2 phut nhe."})
        return jsonify({"reply": f"Loi he thong: {error_msg}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
