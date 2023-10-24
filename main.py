import json
import base64
import cv2
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode
import io
import myai
import torch
import threading
import time
import requests as re
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
model = torch.hub.load('ultralytics/yolov5', 'custom', 'best.pt')
CORS(app)

# 전역 변수
image = "None"
isDetected = False
qr_data = json.dumps({})
springUrl = "http://localhost:8080"
# 스레드 동기화를 위한 Lock 객체
lock = threading.Lock()

# 요청을 보낼 백그라운드 스레드 활성화 여부를 추적하는 플래그
isThreadActive = False

# QR 코드를 인식하는 함수
def read_qr_code(base64_img):

    # 이미지 로드
    img = base64.b64decode(base64_img)
    img = Image.open(io.BytesIO(img))
    img = np.array(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    global isDetected, qr_data
    # QR 코드 인식
    decoded_objects = decode(img)

    if decoded_objects:
        # AI 처리
        ai_result, label = myai.run(model=model, origin_img=img)

        for obj in decoded_objects:
            # QR 코드 데이터 반환
            x, y, w, h = obj.rect
            qr_data_type = obj.type
            qr_data_raw = obj.data.decode('utf-8')
            cv2.rectangle(ai_result, (x ,y), (x + w, y + h), (255, 0, 0), 5)

            _, qr_image = cv2.imencode('.jpg', ai_result)
            qr_image = base64.b64encode(qr_image).decode('utf-8')
            score = None

            qr_data_raw = qr_data_raw.replace("'", "\"")
            qr_data = json.loads(qr_data_raw)
            qr_data["aiCheckStatus"] = True
            qr_data["aiCheckTime"] = time.strftime('%Y-%m-%d %H:%M:%S')
            isDetected = True
    else:
        qr_data = json.dumps({})
        qr_image = base64_img
        label = None
        score = None
        isDetected = False
    return(qr_data, qr_image, label)

# 백그라운드에서 작업을 수행할 함수
def background_task():
    global isDetected, qr_data, isThreadActive, springUrl
    while True:
        with lock:
            if isDetected and not isThreadActive:
                try:
                    isThreadActive = True  # 백그라운드 스레드 활성화
                    # 여기에 요청을 보냅니다
                    p = re.get(url=f"{springUrl}/product/{qr_data['productid']}")
                    w = re.get(url=f"{springUrl}/warehouse/productId={qr_data['productid']}")
                    b = re.post(url=f"{springUrl}/box/warehouse={w.json()['id']}", json=qr_data)
                    data = {
                        "boxId": b.json()['id'],
                        "productId": p.json()['id'],
                        "quantity": qr_data['quantity'],
                        "fquantity": 0
                    }
                    res3 = re.post(url=f"{springUrl}/productinbox", json=data)
                    print(res3.status_code)
                    # isDetected를 False로 재설정
                    isDetected = False
                    isThreadActive = False
                except Exception as e:
                    # print("오류 발생:", str(e))
                    isThreadActive = False  # 백그라운드 스레드 비활성화

        # 바쁜 대기(busy-waiting)를 피하기 위해 잠시 대기
        time.sleep(3)  # 이 부분은 여전히 백그라운드 스레드에서 수행됩니다


@app.route('/upload', methods=['POST'])
def upload_image():
    data = request.get_json()
    # POST 값을 확인합니다.
    if 'Frame' not in data:
        return jsonify({'error': '이미지 데이터가 없습니다'})

    encoded_image = data['Frame']
    global image
    image = encoded_image
    decoded_image = base64.b64decode(encoded_image)

    response_data = {'message': 'Base64 이미지가 성공적으로 업로드되었습니다'}
    return jsonify(response_data), 200

@app.route('/stream', methods=['GET'])
def stream():
    global image, qr_data, isDetected
    qr_image = None
    label = None
    if image != "None":
        qr_data, qr_image, label = read_qr_code(image)

        # QR 코드가 감지되면 isDetected를 True로 설정
        with lock:
            isDetected = True

    # 백그라운드 스레드가 실행 중이 아닌 경우에만 시작
    if not background_thread.is_alive():
        background_thread.start()

    response_data = {"qr_data": qr_data, "qr_image": qr_image, "label": label}
    return jsonify(response_data), 200

if __name__ == "__main__":
    background_thread = threading.Thread(target=background_task)
    background_thread.daemon = True  # 백그라운드 스레드를 데몬으로 설정하여 주 프로그램이 종료되면 스레드가 종료되도록 함
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)  # 'threaded=True'를 추가하여 멀티 스레딩을 활성화
