;End GCode
G91              ; relative positioning
G0 A-4.5
G90              ; absolute positioning
G28.2 X0 Y0
M100 ({he1st:0}) ; extruder heater off
M100 ({out4:0})  ; fan off
