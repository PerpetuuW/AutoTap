import subprocess
import sys
import re

def get_connected_devices():
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    return result.stdout

def connect_wifi_adb(ip, port="5555"):
    target = f"{ip}:{port}"
    print(f"🚀 Попытка подключения к {target}...")

    # Отправка команды подключения
    res = subprocess.run(["adb", "connect", target], capture_output=True, text=True)
    print(res.stdout.strip())

    # Проверка списка активных устройств
    devices = get_connected_devices()
    print("\n📱 Активные устройства ADB:")
    print(devices)

    if target in devices and "device" in devices:
        print(f"✅ Успешно подключено к {target}!")
        return True
    else:
        print(f"❌ Не удалось подключиться к {target}. Проверьте IP и Wi-Fi сеть.")
        return False

def setup_tcpip_from_usb(port="5555"):
    print("🔌 Настройка TCP/IP через USB...")
    res = subprocess.run(["adb", "tcpip", port], capture_output=True, text=True)
    print(res.stdout.strip())

if __name__ == "__main__":
    print("=== АВТОМАТИЗАЦИЯ ADB ПО WI-FI ===")
    
    mode = input("Выберите режим:\n 1 — Подключиться по IP (Wi-Fi)\n 2 — Включить TCP/IP через USB\nВаш выбор (1/2): ").strip()
    
    if mode == "2":
        setup_tcpip_from_usb()
    else:
        ip_address = input("Введите IP-адрес телефона (например, 192.168.1.45):172.17.18.140").strip()
        if not ip_address:
            print("🔴 IP-адрес не может быть пустым!")
            sys.exit(1)
        
        port_num = input("Введите порт (по умолчанию 5555):40681 ").strip() or "5555"
        connect_wifi_adb(ip_address, port_num)