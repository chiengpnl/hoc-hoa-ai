import os
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
    return "Server dang chay tot!"

@app.route("/chat", methods=["POST"])
def chat():
    user_text = request.form.get("message", "")
    content_list = []
    
    if user_text:
        content_list.append(user_text)
    
    if "file" in request.files:
        file = request.files["file"]
        if file.filename != '':
            img = Image.open(file.stream).convert("RGB")
            content_list.append(img)

    if not content_list:
        return jsonify({"reply": "Thay dang doi cau hoi cua em."})

    system_prompt = "Ban la giao vien Hoa hoc. Khong dung LaTeX. Dung dau cham (.) cho phep nhan. Xung Thay - Em."

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=content_list,
            config={'system_instruction': system_prompt}
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"reply": f"Loi: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))