# Kapho Street Pursuit — Android Build

โปรเจกต์นี้ดัดแปลงจากเกม Pygame เดิมให้เหมาะกับมือถือ:
- เล่นแนวนอน (landscape)
- เต็มจอ
- มีปุ่มซ้าย/ขวาบนหน้าจอสัมผัส
- รองรับ touch events และ mouse events
- ใช้ virtual canvas 900x650 แล้วปรับขนาดตามจอมือถือ
- ยังรองรับคีย์บอร์ด A/D และลูกศรสำหรับทดสอบบน PC

## สร้าง APK

แนะนำให้ Build บน Linux/WSL ด้วย Buildozer:

```bash
pip install buildozer
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libtinfo5 cmake libffi-dev libssl-dev
buildozer android debug
```

เมื่อ Build สำเร็จ APK จะอยู่ในโฟลเดอร์ `bin/`

สำหรับ APK ปล่อยใช้งานจริง ให้ใช้:

```bash
buildozer android release
```

หมายเหตุ: การ Build Android ต้องใช้ Android SDK/NDK และเครื่องมือ native จึงไม่ได้เกิดจากการรันไฟล์ `.py` บนมือถือโดยตรง
