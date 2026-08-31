"""
ESP32 + BioAmp EXG Pill — 30초 ECG 측정 데이터를 JSON으로 저장
================================================================
사용법
  1) pip install pyserial
  2) 아래 PORT 를 본인 것으로 변경 (Arduino IDE의 Tools → Port에서 확인)
  3) Arduino의 Serial Monitor / Serial Plotter 를 닫는다 (포트 충돌 방지)
  4) 실행:  python ecg_record.py
  → 30초 뒤 같은 폴더에 ecg_YYYYMMDD_HHMMSS.json 파일이 생깁니다.

전제: 아두이노가 "Raw:1234,ECG:2048" 형식으로 출력 중.
      ※ 기록할 때는 데이터를 촘촘히 받아야 하므로, 스케치의 출력 솎기(skip)를
        빼고 매 샘플(250Hz) 출력하는 상태에서 측정하세요.
"""
import serial, json, time
from datetime import datetime

# ── 설정 ──────────────────────────────────────────────
PORT     = 'COM4'      # ← 본인 포트로 변경 (예: 'COM5', Mac은 '/dev/cu.usbserial-0001')
BAUD     = 115200
DURATION = 30.0        # 측정 시간(초)
RATE_HZ  = 250         # 아두이노 명목 샘플링 (실측 레이트도 함께 저장됨)
# ─────────────────────────────────────────────────────

def parse(line):
    """'Raw:1234,ECG:2048' → (1234, 2048).  못 읽으면 (None, None)."""
    raw = ecg = None
    for tok in line.split(','):
        tok = tok.strip()
        if ':' not in tok:
            continue
        k, v = tok.split(':', 1)
        k = k.strip().lower()
        try:
            if   k == 'raw': raw = int(v)
            elif k == 'ecg': ecg = int(v)
        except ValueError:
            return None, None
    return raw, ecg

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2.0)              # 포트/보드 안정화
ser.reset_input_buffer()    # 오래된 버퍼 비우기
ser.readline()              # 첫 줄(잘렸을 수 있음) 버림

t_ms, raw_list, ecg_list = [], [], []
print(f"측정 시작 — {DURATION:.0f}초 동안 가만히, 편하게 호흡하세요...")

t0 = time.perf_counter()
next_report = 5.0
while True:
    now = time.perf_counter() - t0
    if now >= DURATION:
        break
    line = ser.readline().decode(errors='ignore').strip()
    if not line:
        continue
    raw, ecg = parse(line)
    if raw is None or ecg is None:
        continue
    t_ms.append(round(now * 1000, 1))
    raw_list.append(raw)
    ecg_list.append(ecg)
    if now >= next_report:
        print(f"  {now:4.1f}s / {DURATION:.0f}s   ({len(raw_list)} samples)")
        next_report += 5.0

ser.close()

eff_rate = round(len(raw_list) / DURATION, 1) if DURATION else 0
out = {
    "device":            "ESP32 + BioAmp EXG Pill",
    "channel":           "ECG (Lead I)",
    "sample_rate_hz":    RATE_HZ,       # 명목 샘플링
    "effective_rate_hz": eff_rate,      # 실제로 받은 샘플/초
    "recorded_at":       datetime.now().isoformat(timespec="seconds"),
    "duration_s":        DURATION,
    "n_samples":         len(raw_list),
    "columns":           ["t_ms", "raw", "ecg"],
    "data": {
        "t_ms": t_ms,        # 측정 시작 후 경과 시간(ms)
        "raw":  raw_list,    # ESP32 ADC 원신호 (0~4095)
        "ecg":  ecg_list,    # 필터 적용 후 신호
    },
}

fname = f"ecg_{datetime.now():%Y%m%d_%H%M%S}.json"
with open(fname, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)

print(f"\n저장 완료 → {fname}")
print(f"  샘플 수: {len(raw_list)}개,  실측 레이트: {eff_rate} Hz")
