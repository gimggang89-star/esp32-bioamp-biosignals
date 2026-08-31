# ECG 심전도 — ESP32 + BioAmp EXG Pill

## 1. 전극 부착 (Lead I)

| 전극 | 위치 | 대안(손목·발목) |
|---|---|---|
| IN+ | 왼쪽 쇄골 아래 | 왼쪽 손목 |
| IN− | 오른쪽 쇄골 아래 | 오른쪽 손목 |
| REF | 왼쪽 갈비뼈 아래 | 오른쪽 발목 |

- 의자에 편히 앉아 팔다리에 힘을 빼고 측정합니다. 근육에 힘이 들어가면 근전도(EMG)가 섞여 파형이 흐트러집니다.
- 가슴 부착이 손목 부착보다 R파 진폭이 큽니다.

## 2. 펌웨어 — `firmware/ECG_ESP32/ECG_ESP32.ino`

| 항목 | 값 |
|---|---|
| 샘플레이트 | 250 Hz (`delay(4)`) |
| 통신 속도 | 115200 |
| ADC | GPIO34, 12-bit (0–4095) |
| 출력 형식 | `Raw:<raw>,ECG:<filtered>` 한 줄/샘플 |
| 온보드 필터 | High-pass(R=0.99) → Notch 60 Hz(biquad) → FIR(1:2:3:2:1) |

`#define PLOT_SKIP 0` 이 기본값입니다. Arduino Serial Plotter로 느리게 보고 싶을 때만 `5`로 바꾸세요 (5개 중 1개만 출력 → 50 Hz). **녹화·뷰어용으로는 반드시 0** 이어야 250 Hz 데이터가 저장됩니다.

> ESP32의 `math.h`에는 Bessel 함수 `y0`, `y1`, `yn`이 정의되어 있어 같은 이름의 전역 변수를 만들면 컴파일 오류가 납니다. 이 스케치는 `nx1/ny1` 등 다른 이름을 사용합니다.

## 3. 측정·저장 — `tools/ecg_record.py`

```bash
pip install pyserial
python ecg_record.py        # 파일 상단 PORT='COM4' 를 본인 포트로 수정
```

- 30초 동안 측정한 뒤 같은 폴더에 `ecg_YYYYMMDD_HHMMSS.json`을 저장합니다.
- 실행 전 Arduino IDE의 시리얼 모니터/플로터를 닫아야 합니다 (`PermissionError` 가 나면 포트가 점유된 상태입니다).
- 실측 레이트가 250 Hz에 못 미치면 `PLOT_SKIP`이 0인지 확인하세요.

`tools/ecg_ads1146_record.py` 는 ADS1146 기반 ECG 보드(정수 한 줄 형식, 500 Hz, MsTimer2)용 스크립트입니다. 저장 형식이 같아 `ecg_viewer.html`에서 그대로 열립니다.

## 4. 뷰어 — `viewer/ecg_viewer.html`

브라우저에서 파일을 열고 JSON을 끌어다 놓으면 됩니다 (설치 없음).

- **필터 6종** 원본 · 이동평균 · Median · IIR · High-pass · Notch · FIR · 전체 조합 — 모두 `raw`에서 브라우저가 다시 계산
- **단계별 보기** 원본 → Median → High-pass → Notch → FIR 을 한 화면에 쌓아서 비교
- **심박수** R-피크 검출 → R-R 간격 중앙값 → BPM (극성 자동 판별로 S파 이중 계수 방지)
- **탐색** 구간 이동 막대 · 5초/10초/전체 · ＋/－ · 마우스 휠 확대
- 라이트/다크 테마

`common/bioamp_live_viewer.html` 은 Web Serial로 포트에 직접 연결해 실시간 파형과 BPM을 보여줍니다 (Chrome/Edge, `file://`로 열어도 동작).

## 5. 샘플 데이터 — `samples/`

`ecg_20260822_224224.json` — 손목 부착, 30초, 250 Hz, 약 70 BPM. 뷰어 동작 확인용 실측 데이터입니다.
