import qrcode, cv2, base64
from pyzbar.pyzbar import decode
# QR 코드에 담을 데이터를 지정합니다.
data = {
    "name":"box2",
    "size":"s",
    "productid":2,
    "quantity":100
}  # 원하는 데이터 (URL, 텍스트, 등)

# QR 코드 객체를 생성합니다.
qr = qrcode.QRCode(
    version=1,  # QR 코드 버전 (1부터 40까지, 1이 가장 작고 40이 가장 큼)
    error_correction=qrcode.constants.ERROR_CORRECT_L,  # 오류 수정 레벨 (L, M, Q, H 중 선택)
    box_size=10,  # 각 QR 코드 블록의 크기 (픽셀 단위)
    border=4,  # QR 코드 주변의 여백 크기 (블록 수)
)

# 데이터를 QR 코드에 추가합니다.
qr.add_data(data)

# QR 코드를 생성합니다.
qr.make(fit=True)

# 생성된 QR 코드를 이미지로 변환합니다.
img = qr.make_image(fill_color="black", back_color="white")

# QR 코드 이미지를 파일로 저장하거나 화면에 표시할 수 있습니다.
img.save("d:/box_qrcode.png")  # 파일로 저장
img.show()  # 화면에 표시

img = cv2.imread("d:/box_qrcode.png", cv2.IMREAD_COLOR)
## qr인식
decoded_objects = decode(img)
if decoded_objects:
    for obj in decoded_objects:
        x, y, w, h = obj.rect
        qr_data_type = obj.type
        qr_data = obj.data.decode('utf-8')
        for _ in qr_data:
            print(_)
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 5)

        # _, qr_image = cv2.imencode('.jpg', img)
        # qr_image = base64.b64encode(qr_image).decode('utf-8')

    print(qr_data)
    cv2.imshow("qr",img)
    cv2.waitKey(0)
    cv2.destroyWindow()