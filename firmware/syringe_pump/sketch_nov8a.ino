#include <AccelStepper.h>

// Configuratia actuala de pini (cu IN2 pe D6 si IN3 pe D7)
#define IN1 8
#define IN2 6
#define IN3 7
#define IN4 11

AccelStepper motor(AccelStepper::HALF4WIRE, IN1, IN3, IN2, IN4);

const float PAS_SURUB_MM = 0.5;
const float PASI_PE_ROTATIE = 4076.0;
const float PASI_PE_MM = PASI_PE_ROTATIE / PAS_SURUB_MM; // 8152 pasi/mm

struct Syringe {
  const char* name;
  float diameter_mm;
  float area_mm2;
  float max_length_mm;
};

Syringe presetSeringi[] = {
  {"Hamilton 0.5mL", 3.26, 8.347,  60.0},
  {"Popper 1.0mL",   4.50, 15.904, 60.0},
  {"CarlRoth 1.0mL", 6.70, 35.256, 30.0}
};

int seringaActiva = 2; // CarlRoth 1.0mL implicit
bool isZeroSet = false;
bool isMoving = false;

void setup() {
  Serial.begin(115200);
  // Viteza de 400 pasi/sec asigura cuplu maxim pe alimentare USB
  motor.setMaxSpeed(400.0);
  motor.setAcceleration(300.0);
  Serial.println("READY: Sistem pregatit pe pinii D8, D6, D7, D11.");
}

void proceseazaComanda(String cmd) {
  cmd.trim();

  if (cmd == "SET_ZERO" || cmd == "HOME") {
    motor.setCurrentPosition(0);
    isZeroSet = true;
    Serial.println("HOMED: Pozitia curenta a fost setata ca Zero (0).");
  }
  else if (cmd == "STOP") {
    motor.stop();
    motor.moveTo(motor.currentPosition());
    isMoving = false;
    Serial.println("STOPPED: Motor oprit de urgenta!");
  }
  else if (cmd.startsWith("JOG:")) {
    long pasi = cmd.substring(4).toInt();
    motor.move(pasi);
    isMoving = true;
    Serial.print("INFO: Deplasare manuala cu ");
    Serial.print(pasi);
    Serial.println(" pasi.");
  }
  else if (cmd.startsWith("SYRINGE:")) {
    int index = cmd.substring(8).toInt();
    if (index >= 0 && index <= 2) {
      seringaActiva = index;
      Serial.print("INFO: Seringa selectata -> ");
      Serial.println(presetSeringi[seringaActiva].name);
    }
  }
  else if (cmd.startsWith("SPEED:")) {
    float vit = cmd.substring(6).toFloat();
    if (vit >= 50 && vit <= 800) {
      motor.setMaxSpeed(vit);
      Serial.print("INFO: Viteza setata la ");
      Serial.print(vit);
      Serial.println(" pasi/sec.");
    }
  }
  else if (cmd.startsWith("DOSE:")) {
    if (!isZeroSet) {
      Serial.println("AVERTISMENT: Apasa 'Seteaza ZERO' inainte de dozarea automata!");
      return;
    }
    float volum_uL = cmd.substring(5).toFloat();
    float arie = presetSeringi[seringaActiva].area_mm2;
    float cursa_mm = volum_uL / arie;
    long pasiDeFacut = lround(cursa_mm * PASI_PE_MM);

    Serial.print("DOZARE: ");
    Serial.print(volum_uL);
    Serial.print(" uL (");
    Serial.print(pasiDeFacut);
    Serial.println(" pasi)...");

    motor.move(pasiDeFacut);
    isMoving = true;
  }
}

void loop() {
  if (Serial.available() > 0) {
    String comanda = Serial.readStringUntil('\n');
    proceseazaComanda(comanda);
  }
  motor.run();
  if (isMoving && motor.distanceToGo() == 0) {
    isMoving = false;
    Serial.print("DONE: Miscare finalizata. Pozitie totala: ");
    Serial.print(motor.currentPosition());
    Serial.println(" pasi.");
  }
}