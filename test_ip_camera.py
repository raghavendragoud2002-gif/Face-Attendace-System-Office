import cv2
import time

def test_camera_connection(url):
    print(f"Attempting to connect to: {url}")
    print("Please wait...")
    
    cap = cv2.VideoCapture(url)
    
    if not cap.isOpened():
        print("❌ FAILED: Could not connect to the camera.")
        print("Check if:")
        print("1. The phone and laptop are on the same Wi-Fi network.")
        print("2. The IP Webcam app is running and 'Start Server' is clicked.")
        print("3. The URL is correct (check for typos).")
        return False
    
    print("✅ SUCCESS: Connected to camera!")
    print("Reading a frame...")
    
    ret, frame = cap.read()
    if ret:
        print("✅ SUCCESS: Frame read successfully!")
        print(f"Resolution: {frame.shape[1]}x{frame.shape[0]}")
        
        # Try to show the frame (might fail in some headless envs, but good to try)
        try:
            cv2.imshow("IP Camera Test", frame)
            print("Press any key in the window to close, or wait 3 seconds...")
            cv2.waitKey(3000)
            cv2.destroyAllWindows()
        except:
            pass
    else:
        print("❌ FAILED: Connected but could not read frame.")
        
    cap.release()
    return True

if __name__ == "__main__":
    print("--- Android IP Camera Test ---")
    url = input("Enter the IP Camera URL (e.g., http://192.168.1.5:8080/video): ").strip()
    
    if not url:
        print("No URL entered. Exiting.")
    else:
        test_camera_connection(url)
