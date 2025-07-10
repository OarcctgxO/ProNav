python -m PyInstaller --onefile ^
    --add-data "land.png;." ^
    --add-data "aircraft.png;." ^
    --add-data "missile.png;." ^
    --add-data "boom.png;." ^
    --noconsole ^
    --hidden-import arcade ^
    --hidden-import arcade.gl ^
    --hidden-import arcade.gl.provider ^
    --hidden-import arcade.gl.backends ^
    --hidden-import arcade.gl.backends.opengl ^
    --hidden-import arcade.gl.backends.opengl.provider ^
    --hidden-import pyglet ^
    --hidden-import pyglet.gl ^
    main.py