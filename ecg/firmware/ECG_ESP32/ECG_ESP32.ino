/*
 * ECG_ESP32.ino — ESP32 + BioAmp EXG Pill 심전도(ECG) 측정
 * ---------------------------------------------------------
 * 배선 : BioAmp VCC → 3V3, GND → GND, OUT → GPIO34 (ADC1, 입력 전용)
 * 전극 : IN+ 왼쪽 쇄골 아래(또는 왼손목), IN− 오른쪽 쇄골 아래(또는 오른손목),
 *        REF 왼쪽 갈비뼈 아래(또는 오른발목)  — Lead I 기준
 * 출력 : "Raw:<0~4095>,ECG:<필터 결과>"  @ 250 Hz, 115200 baud
 * 필터 : High-pass(R=0.99) → Notch 60 Hz(biquad) → FIR LPF(1:2:3:2:1)
 *        (뷰어 ecg_viewer.html 은 Raw 값으로 같은 필터를 다시 계산합니다)
 * 보드 : Arduino IDE → Tools → Board → "ESP32 Dev Module"
 *
 * Credit: BioAmp EXG Pill by Upside Down Labs
 *         https://github.com/upsidedownlabs/BioAmp-EXG-Pill (MIT License)
 * ---------------------------------------------------------
 */
const int  ADC_PIN = 34;
const long BAUD    = 115200;

// ── 출력 모드 ─────────────────────────────────────────
//  0 = 매 샘플(250Hz) 출력  → 녹화(JSON)·HTML 뷰어용  ★기본
//  5 = 5개 중 1개만(50Hz)   → Arduino Serial Plotter 느리게 볼 때만
#define PLOT_SKIP 0
// ─────────────────────────────────────────────────────

// ① High-pass : 호흡(기저선) 제거
int x_prev = 2048; float y_hpf = 0; const float R = 0.99;
int highpass(int x){ y_hpf = (x - x_prev) + R*y_hpf; x_prev = x; return (int)(2048 + y_hpf); }

// ② Notch : 60Hz 제거 (변수 nx/ny — math.h y1 충돌 방지)
float nx1=0,nx2=0,ny1=0,ny2=0;
const float b0=0.9525,b1=-0.1196,b2=0.9525,a1=-0.1196,a2=0.9049;
int notch(int x){ float y=b0*x+b1*nx1+b2*nx2-a1*ny1-a2*ny2; nx2=nx1;nx1=x;ny2=ny1;ny1=y; return (int)y; }

// ③ FIR 저역통과 (1:2:3:2:1)
int fir_buf[5]={2048,2048,2048,2048,2048};
int fir(int x){ fir_buf[0]=fir_buf[1];fir_buf[1]=fir_buf[2];fir_buf[2]=fir_buf[3];
  fir_buf[3]=fir_buf[4];fir_buf[4]=x;
  return (fir_buf[0]+2*fir_buf[1]+3*fir_buf[2]+2*fir_buf[3]+fir_buf[4])/9; }

void setup(){
  Serial.begin(BAUD);
  analogReadResolution(12);      // ESP32 12비트 (0~4095)
  delay(1500);
}

void loop() {
  int raw = analogRead(ADC_PIN);
  int ecg = fir(notch(highpass(raw)));

  static int skip = 0;
  if (PLOT_SKIP <= 1 || ++skip >= PLOT_SKIP) {   // 기본(0)은 매 샘플 출력
    skip = 0;
    Serial.print("Raw:");  Serial.print(raw);
    Serial.print(",ECG:"); Serial.println(ecg);
  }

  delay(4);                       // 250Hz 샘플링
}