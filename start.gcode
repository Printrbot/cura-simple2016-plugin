M100(?sr:{line:t,he1t:t,he1st:t,he1at:t,stat:t}?)
M100 (?he1st:{print_temperature}?)
M100 (?out4:0?)
G92.1 X0 Y0 Z0 A0 B0
G28.2 X0 Y0
G0 X110
M100({_leds:2})
M101 ({he1at:t})
M100({_leds:3})
G28.2 Z0
G0 X0 Y145 Z6
G38.2 Z-10 F200
G0 Z5
M100({_leds:5})
G0 X210 Y65
G38.2 Z-10 F200
G0 Z5
M100({_leds:6})
G0 X0 Y10
G38.2 Z-10 F200
G0 Z5
M100({_leds:3})
M100 ({tram:1})
G92 A0
M100({_leds:1})
G0 Z5
; apply hotend offset
G92 Z5.00 ; we are 0.18 too low: 5 - (-0.18) = 5.18
; clean the nozzle
G0 X0 Y0 Z0.3
G1 X210.000 A12 F1200
G0 Y0.4
G1 X110.000 A18
G0 Z1
G92 A0
