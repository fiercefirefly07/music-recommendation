import cv2

# Open the default webcam
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Error: Could not open webcam.")
    exit()

while True:
    ret, frame = camera.read()

    if not ret:
        print("Error: Couldn't read frame.")
        break

    cv2.imshow("Webcam Test", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()