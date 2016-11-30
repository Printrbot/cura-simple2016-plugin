# cura-simple2016-plugin

This plugin will post process standard Cura (15.x) output and prepare it for printing with Printrbot Simple 2016. It was written by Rob Giseburt from TinyG team. 
The purpose of it is to demonstrate how to convert standard "Marlin" style gcode into something that Printrbot Simple (TinyG G2) understands.

## Installation

Open Cura, then switch to Plugins Tab. In the bottom left corner you will see "Open Plugin Location" button. Click on it, and then copy Simple_Cura.py file into plugins folder.

After that, restart Cura and you will see new plugin show up in Plugins list. Click on the plugin in the list and then on the small arrow button pointing down to enable it. 

When plugin is enabled, it will automatically post process the files that can then be exported as valid gcode.
