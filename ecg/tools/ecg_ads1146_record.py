"""
ADS1146 ECG 보드 — 심전도(ECG) 측정 데이터를 JSON으로 저장
================================================================
이 스크립트는 업체에서 받은 ADS1146 기반 ECG 기기용입니다.
(아두이노 예제: ADS1146 + MsTimer2로 2ms마다=500Hz 샘플링 →
 Serial.println(readValue) 로 '정수 한 줄'씩 출력, 115200 baud)

  → 앞의 BioAmp 기기와 달리 "Raw:...,ECG:..." 형식이 아니라
    -1234  처럼 '부호 있는 정수 한 줄'만 나옵니다. 이 스크립트는 그 형식을 읽습니다.

사용법
  1) pip install pyserial
  2) 아래 PORT 를 본인 것으로 변경 (Arduino IDE의 Tools → Port)
  3) Arduino의 Serial Monitor / Serial Plotter 를 닫는다 (포트 충돌 방지)
  4) 실행:  python ecg_ads1146_record.py
  → 끝나면 같은 폴더에 ecg_ads1146_YYYYMMDD_HHMMSS.json 파일이 생깁니다.
  → 이 JSON은 기존 ecg_viewer.html 에 그대로 끌어놓아 필터/BPM을 볼 수 있습니다.

※ 만약 값이 자꾸 깨져서(스킵이 많이) 들어오면, 아두이노 코드의
   mySerial.SendEcg(readValue);  줄이 같은 시리얼 포트로 바이너리를 함께
   보내서일 수 있습니다. PC 기록만 할 때는 그 줄을 잠시 주석 처리하면 깔끔합니다.
"""
import serial, json, time, re
from datetime import datetime

# ── 설정 ──────────────────────────────────────────────
PORT     = 'COM7'      # ← 본인 포트로 변경 (Mac은 '/dev/cu.usbserial-0001')
BAUD     = 115200      # 아두이노 Serial.begin(115200) 과 동일
DURATION = 30.0        # 측정 시간(초)
RATE_HZ  = 500         # MsTimer2::set(2, ...) → 2ms = 500Hz
# ─────────────────────────────────────────────────────

# '정수 한 줄'만 허용(부호 옵션). 바이너리로 깨진 줄은 통째로 건너뜀 → 잘못된 값 저장 방지.
# ※ 아두이노 IDE 시리얼 모니터의 '타임스탬프 표시'를 켜면 화면엔
#    '23:34:09.660 -> 8431' 처럼 보이지만, 그 앞부분은 IDE가 화면에만 붙이는 것이라
#    pyserial(이 스크립트)로 포트를 직접 읽으면 실제로는 '8431' 만 들어옵니다.
#    그래도 혹시 몰라 두 형식('8431' / '…-> 8431')을 모두 처리합니다.
INT_RE = re.compile(r'^[-+]?\d+$')
def parse(line):
    line = line.strip()
    if '->' in line:                      # '…-> 8431' 형태면 화살표 뒤의 숫자만 취함
        line = line.rsplit('->', 1)[1].strip()
    return int(line) if INT_RE.match(line) else None

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2.0)
ser.reset_input_buffer()
ser.readline()   # 첫 줄(반쪽일 수 있음) 버림

t_ms, raw_list = [], []
skipped = 0
print(f"측정 시작 — {DURATION:.0f}초 동안 가만히, 편하게 측정하세요 (ADS1146 · 500Hz)")
t0 = time.perf_counter()
next_report = 5.0
while True:
    now = time.perf_counter() - t0
    if now >= DURATION:
        break
    line = ser.readline().decode(errors='ignore')
    val = parse(line)
    if val is None:
        if line.strip():
            skipped += 1
        continue
    t_ms.append(round(now * 1000, 1))
    raw_list.append(val)
    if now >= next_report:
        print(f"  {now:4.1f}s / {DURATION:.0f}s   ({len(raw_list)} samples)")
        next_report += 5.0
ser.close()

eff = round(len(raw_list) / DURATION, 1) if DURATION else 0
out = {
    "device":            "ADS1146 ECG board",
    "channel":           "ECG",
    "sample_rate_hz":    RATE_HZ,
    "effective_rate_hz": eff,
    "recorded_at":       datetime.now().isoformat(timespec="seconds"),
    "duration_s":        DURATION,
    "n_samples":         len(raw_list),
    "columns":           ["t_ms", "raw"],
    "data": { "t_ms": t_ms, "raw": raw_list },
}
fname = f"ecg_ads1146_{datetime.now():%Y%m%d_%H%M%S}.json"
with open(fname, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)

print(f"\n저장 완료 → {fname}")
print(f"  샘플 수: {len(raw_list)}개,  실측 레이트: {eff} Hz,  건너뛴 줄: {skipped}개")
if eff < RATE_HZ * 0.8:
    print("  ⚠ 실측 레이트가 낮습니다 — BAUD 115200 확인. 깨진 줄이 많으면 위 주석의 SendEcg 안내를 참고하세요.")
print("  → ecg_viewer.html 에 끌어놓아 필터(Moving Average·Median·IIR·HPF·Notch·FIR)와 BPM을 확인하세요.")
