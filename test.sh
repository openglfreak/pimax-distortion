#!/bin/sh

#python calculate_pimax_distortion.py || exit
PYTHONPATH="$PWD:$PYTHONPATH" python -m pimax_distortion || exit
exec gnuplot -e 'plot "/tmp/w.txt", "/tmp/a.txt", "/tmp/b.txt", "/tmp/c.txt"; pause mouse close'
exec gnuplot -e 'plot "/tmp/a.txt", "/tmp/b.txt"; pause mouse close'
