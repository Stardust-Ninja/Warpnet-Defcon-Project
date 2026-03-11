# 🔒 Pico Security Monitor

Een hardware-based security monitoring systeem dat Windows beveiligingsstatus visualiseert via een Raspberry Pi Pico met LEDs.

## 📋 Overzicht

Dit project bestaat uit twee componenten:
- **Windows API** (`security_monitor.py`) - Scant je systeem op beveiligingsrisico's
- **Pico Firmware** (`code.py`) - Visualiseert bedreigingsniveaus via gekleurde LEDs

## 🛠️ Hardware Benodigdheden

| Component | Pin | Functie |
|-----------|-----|---------|
| Groene LED | GP0 | Level 5 (Veilig) |
| Blauwe LED | GP1 | Level 4 (Laag) |
| Gele LED | GP2 | Level 3 (Medium) |
| Rode LED | GP3 | Level 2 (Hoog) |
| Witte LED + Buzzer | GP4 | Level 1 (Kritiek) |

| Level | Kleur        | Patroon             | Betekenis         |
| ----- | ------------ | ------------------- | ----------------- |
| 5     | 🟢 Groen     | Solid               | Systeem veilig    |
| 4     | 🔵 Blauw     | Langzaam knipperend | Lage bedreiging   |
| 3     | 🟡 Geel      | Knipperend          | Medium bedreiging |
| 2     | 🔴 Rood      | Snel knipperend     | Hoge bedreiging   |
| 1     | 🔴⚪ Rood/Wit | Politie lichten     | Kritiek + buzzer  |
