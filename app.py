# -*- coding: utf-8 -*-
# 重写 Flask-MCMOTD,早期版本用的是面向过程的方式进行写的，一个文件写了400多行，真是要爆了T.T

# API
from flask import Flask, request, jsonify , send_file
from flask_cors import CORS

# Java版查询模块
from JavaServerStatus import java_status
# 基岩版查询模块
from BedrockServerStatus import bedrock_status
# 此API优先解析 srv 记录
from dnslookup import dns_lookup

# 格式化文本
from FormatData import format_java_data, format_bedrock_data, format_index, format_java_index, format_bedrock_index

# 图片API
from mcstatus_img.get_background import download_image_with_httpx_auto_redirect
from mcstatus_img.create_image import create_image
import base64
from io import BytesIO

app = Flask(__name__)
app.json.sort_keys = False
app.json.ensure_ascii = False
app.json.mimetype = 'application/json;charset=UTF-8'
app.json.compact = False
CORS(app)

@app.route('/')
def index():
    message = format_index()
    return jsonify(message), 200

# Java 服务器状态查询
@app.route('/java')
def get_java_status():
    ip = request.args.get('ip')
    # 空值输出 API 用法
    if not ip:
        message = format_java_index()
        return jsonify(message), 400

    try:
        ip, type = dns_lookup(ip)
        print(f"解析Java版IP: {ip}, 是否为 SRV: {type}")
        status = java_status(ip)

        data = format_java_data(ip, type, status)

        return jsonify(data), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 基岩版服务器状态查询
@app.route('/bedrock')
def get_bedrock_status():
    ip = request.args.get('ip')
    # 空值输出 API 用法
    if not ip:
        message = format_bedrock_index()
        return jsonify(message), 400
    
    try:
        print(f"解析基岩版IP: {ip}")
        status = bedrock_status(ip)

        data = format_bedrock_data(ip, status)

        return jsonify(data), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 服务器状态图片
@app.route('/img')
def get_status_image():
    ip = request.args.get('ip')
    type = request.args.get('type')
    if type not in ['java', 'bedrock'] and not type:
        return jsonify({"error": "类型参数无效, 仅支持 'java' 或 'bedrock'"}), 400
    if not ip:
        return jsonify({"error": "缺少 IP 参数"}), 400
    if type == 'java':
        try:
            ip, type = dns_lookup(ip)
            status = java_status(ip)
            data = format_java_data(ip, type, status)
        except Exception as e:
            print(f"查询服务器时出错: {e}")
            return
    if type == 'bedrock':
        try:
            status = bedrock_status(ip)
            data = format_bedrock_data(ip, status)
            data['type'] = 'normal'
            status.icon = None
        except Exception as e:
            print(f"查询服务器时出错: {e}")
            return
    BACKGROUND_URL = "https://www.loliapi.com/acg/"
    background_data = download_image_with_httpx_auto_redirect(BACKGROUND_URL)
    if not background_data:
        background_data = None
    motd_list = data['motd'].split("\n")
    text_list = [
        f"ip: {data['ip']}",
        f"type: {data['type']}",
        f"version: {data['version']}",
        f"latency: {data['latency']} ms",
        f"players: {data['players']['online']}/{data['players']['max']}",
    ]
    if status.icon:
        image = create_image(background_data, base64.b64decode(status.icon.split(",")[1]), text_list, motd_list)
    else:
        image = create_image(background_data, None, text_list, motd_list)
    img_io = BytesIO()
    image.save(img_io, 'JPEG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(debug=True, port=5000)