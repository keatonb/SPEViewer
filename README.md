# SPEViewer
This simple pyqtgraph application allows the user to view images contained in the SPE file format 3.0, 
specifically data acquired with the LightField software and the ProEM 1024B camera.

 - command+O opens a new SPE file.
 - command+W writes a file with the timestamp information.

Inherited pyqtgraph ImageView functionality:
 - left/right arrows step forward/backward 1 frame when pressed, seek at 20fps when held.
 - up/down arrows seek at 100fps

Click in the image to get pixel location.  Scroll to zoom.  Click and drag to pan.  The slider on the bottom changes frame number.  The slider on the right changes brightness settings.
