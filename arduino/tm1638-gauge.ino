// Original version by TronicGr (Thanos) 4-26-2012 for X-sim3
#include <TM1638.h> //can be downloaded from http://code.google.com/p/tm1638-library/
// define a module on data pin 5, clock pin 4 and strobe pin 3
TM1638 module(5, 4, 3);
void setup() {
  //Create Serial Object
  Serial.begin(115200);
  // initialize the screen:
  module.clearDisplay();              //clears the display from garbage if any
  String name = "DiRT";               //sets a custom logo start up banner
  module.setDisplayToString(name);    //prints the banner
  delay(1500);                        //small delay 1.5 sec
  module.clearDisplay();              //clears the display
}

word rpm_led_set [10] = {
  0b00000000 | 0b00000000<< 8,
  0b00000001 | 0b00000000<< 8,
  0b00000011 | 0b00000000<< 8,
  0b00000111 | 0b00000000<< 8,
  0b00001111 | 0b00000000<< 8,
  0b00011111 | 0b00000000<< 8,
  0b00111111 | 0b00000000<< 8,
  0b00111111 | 0b01000000<< 8,
  0b00111111 | 0b11000000<< 8,
  0b00000000 | 0b11111111<< 8,
};

float led_ranges[10] = {
  0.0,
  0.15,
  0.31, //16
  0.45, //14
  0.57, //12
  0.69, //10
  0.78, //09
  0.85, //07
  0.9,  //05
  0.95, //05
};

//blink variables
byte blink_interval = 50;
boolean blink_on = false;
unsigned long current_millis = 0;
unsigned long previous_millis = 0;
unsigned long update_millis = 0;

void loop() {
  int i;
  char bufferArray[20];              // holds all serial data into a array

  unsigned int rpm;                  //holds the rpm data (0-65535 size)
  unsigned int rpmleds = 0;              //holds the 8 leds values
  unsigned int rpmmax;
  float rpm_percent = 0;

  signed int carspeed;               //holds the speed data (0-65535 size)
  byte gear;                         // holds gear value data
  byte d1;                           // high byte temp variable
  byte d2;                           // low byte temp variable

  byte rpmdata = 0;                  // marker that new data are available
  byte speeddata = 0;                // marker that new data are available
  byte geardata = 0;                 // marker that new data are available

  long time = millis();

  if (Serial.available() >= 10)  {    //if 10 bytes available in the Serial buffer...
    for (i=0; i<10; i++) {            // for each byte
      bufferArray[i] = Serial.read();        // put into array
    }
    update_millis = time;
  } else {
    if (time - update_millis > 10000) {
      module.clearDisplay();
      module.setLEDs(rpm_led_set[0]);
    }
    return;
  }

  if (bufferArray[0] == 'R' ) {      // if new bytes have been recieved
     d1 = bufferArray[1];            // store high byte of rpm
     d2 = bufferArray[2];            // store low byte of rpm
     rpm = ((d1<<8) + d2);           // concatenate bytes (shift 8 bits)

     d1 = bufferArray[3];            // store high byte of rpm
     d2 = bufferArray[4];            // store low byte of rpm
     rpmmax = ((d1<<8) + d2);

     if (rpm && rpmmax && rpmmax > 0) {
       rpmdata=1;                          // we got new data!
     }
   }

   if (bufferArray[5] == 'S' ) {
     d1 = bufferArray[6];         // store high byte of speed
     d2 = bufferArray[7];         //arduino string store low byte of speed
     carspeed = ((d1<<8) + d2);   // concatenate bytes (shift 8 bits)
     speeddata=1;
   }

   if (bufferArray[8] == 'G' ) {
     gear = bufferArray[9];         // retrieves the single byte of gear
     geardata=1;
   }

   if (speeddata == 1) {
     char speed[20];
     sprintf(speed, "%3d", carspeed);
     module.setDisplayToString(speed);
     speeddata=0;
   }

   if (geardata == 1) {
     char* neutral = "n";                // sets the character for neutral
     char* reverse = "r";                // sets the character for reverse

     if (gear >= 1 and gear <10 ){
        module.setDisplayDigit(gear, 7, false);
      } else if (gear == 0){
        module.setDisplayToString(neutral, 0, 7);
     } else if (gear == 10){
        module.setDisplayToString(reverse, 0, 7);
      }

      geardata=0;
    }

    if (rpmdata == 1) {
      rpm_percent = rpm / (float)rpmmax;
      for(unsigned int a = 9; a >= 0; a--) {
        if (led_ranges[a] <= rpm_percent) {
          rpmleds = a;
          break;
        }
      }

     if (rpmleds == 9){
       current_millis = time;
       if (current_millis - previous_millis > blink_interval)
       {
         previous_millis = current_millis;
         blink_on = !blink_on;
       }

       if (!blink_on) {
         rpmleds = 0;
       }
     }
     
     module.setLEDs(rpm_led_set[rpmleds]);
     rpmdata=0;
   }
 }