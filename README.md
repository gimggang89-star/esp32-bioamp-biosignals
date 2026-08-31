# ESP32 + BioAmp EXG Pill 생체신호 측정 · 필터링 · 시각화

> ESP32와 BioAmp EXG Pill로 **ECG · EMG · EOG · EEG**를 측정하고, 디지털 필터를 적용해 브라우저에서 시각화하는 실습 프로젝트입니다.
> *Biosignal acquisition, digital filtering and web visualization with ESP32 + BioAmp EXG Pill.*

| 신호 | 상태 | 샘플레이트 | 통신 속도 | 필터 |
|---|---|---|---|---|
| **ECG** 심전도 | ✅ 완료 | 250 Hz | 115200 | High-pass · Notch 60 Hz · FIR (+ 뷰어에서 6종 비교) |
| **EMG** 근전도 | 🔜 예정 | 500 Hz | 250000 | Band-pass 74.5–149.5 Hz · 정류 · 엔벨로프 |
| **EOG** 안구전위도 | 🔜 예정 | 75 Hz | 115200 | Band-pass 0.5–19.5 Hz |
| **EEG** 뇌파 | 🔜 예정 | 256 Hz | 115200 | Band-pass 0.5–29.5 Hz · θ/α/β · FFT |

---

## 미리보기

**저장한 측정 데이터 분석 — `ecg_viewer.html`** (실제 측정 데이터, 30초 · 250 Hz)

![ecg_viewer](docs/ecg_viewer.png)

**실시간 파형 — `bioamp_live_viewer.html`** (Web Serial, Python 불필요)

![live_viewer](docs/live_viewer.png)

---

## 하드웨어

| 항목 | 내용 |
|---|---|
| MCU | ESP32 (ESP-WROOM-32 개발보드), 12-bit ADC |
| AFE | [BioAmp EXG Pill](https://github.com/upsidedownlabs/BioAmp-EXG-Pill) (Upside Down Labs) — 계측 증폭기·필터 내장 |
| 전극 | 일회용 젤 전극 3개 (IN+ · IN− · REF) |

**배선**

| BioAmp EXG Pill | ESP32 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| OUT | GPIO34 (ADC1, 입력 전용) |

> ⚠️ VCC/GND를 반대로 연결하지 마세요. GPIO34는 입력 전용 핀입니다.

---

## 빠른 시작 (ECG)

```text
1) 펌웨어 업로드   ecg/firmware/ECG_ESP32/ECG_ESP32.ino  →  Arduino IDE, 보드 "ESP32 Dev Module"
2) 측정·저장       python ecg/tools/ecg_record.py       →  PORT 수정 후 실행, 30초 측정 → ecg_YYYYMMDD_HHMMSS.json
3) 분석            ecg/viewer/ecg_viewer.html            →  브라우저에서 열고 JSON 끌어다 놓기
   (실시간)        common/bioamp_live_viewer.html        →  Chrome에서 열고 [연결] → 포트 선택
```

- 측정 스크립트 실행 전 **Arduino 시리얼 모니터/플로터를 닫아야** 합니다 (포트는 한 프로그램만 사용 가능).
- `pip install pyserial` 필요.

---

## 저장소 구조

```text
esp32-bioamp-biosignals/
├── common/
│   └── bioamp_live_viewer.html   # 실시간 뷰어 (Web Serial) — 모든 신호 공용
├── ecg/
│   ├── firmware/ECG_ESP32/       # ESP32 스케치 (HPF → Notch → FIR, 250 Hz)
│   ├── tools/
│   │   ├── ecg_record.py         # ESP32 + BioAmp 측정 → JSON 저장
│   │   └── ecg_ads1146_record.py # (참고) ADS1146 기반 ECG 보드용 — 정수 한 줄 형식 / 500 Hz
│   ├── viewer/ecg_viewer.html    # 필터 6종 비교 · 단계별 보기 · 심박수(BPM)
│   ├── samples/                  # 실측 데이터 (JSON)
│   └── README.md                 # ECG 상세 (전극 위치·필터·데이터 형식)
├── emg/  eog/  eeg/              # (예정)
└── docs/                         # README 이미지
```

---

## 데이터 형식

측정 스크립트가 저장하는 JSON은 뷰어에서 그대로 열립니다. 뷰어는 **`raw` 값으로 모든 필터를 다시 계산**하므로 `raw`만 있어도 됩니다.

```json
{
  "device": "ESP32 + BioAmp EXG Pill",
  "channel": "ECG (Lead I)",
  "sample_rate_hz": 250,
  "duration_s": 30.0,
  "n_samples": 7501,
  "data": { "t_ms": [0.0, 4.0, ...], "raw": [2048, 2051, ...], "ecg": [2048, 2049, ...] }
}
```

---

## 디지털 필터 (ECG)

| 필터 | 역할 | 구현 |
|---|---|---|
| Moving Average (N=8) | 고주파 잡음 완화 | 뷰어 |
| Median (N=5) | 스파이크 제거 | 뷰어 |
| IIR Low-pass (α=0.7) | 고주파 잡음 완화 | 뷰어 |
| High-pass (R=0.99) | 호흡·기저선 변동 제거 | 펌웨어 · 뷰어 |
| Notch 60 Hz (biquad) | 전원 잡음 제거 | 펌웨어 · 뷰어 |
| FIR Low-pass (1:2:3:2:1) | 고주파 잡음 완화 | 펌웨어 · 뷰어 |

뷰어의 **단계별 보기**는 원본 → Median → High-pass → Notch → FIR 순서로 파형이 어떻게 정제되는지 한 화면에서 보여줍니다. 심박수는 R-피크의 R-R 간격 중앙값으로 계산합니다.

---

## 주의

이 프로젝트는 **교육·실습 목적**입니다. 측정 결과는 의료 진단에 사용할 수 없습니다.

## Credits

- [BioAmp EXG Pill](https://github.com/upsidedownlabs/BioAmp-EXG-Pill) — Upside Down Labs (MIT License). 펌웨어의 샘플링 루프와 필터 구성은 공식 예제를 참고했습니다.

