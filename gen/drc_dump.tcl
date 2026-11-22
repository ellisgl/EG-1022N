load [lindex $argv end]
select top cell
drc euclidean on
drc style drc(full)
drc check
drc catchup
set f [open drc_boxes.txt w]
foreach {why boxes} [drc listall why] { foreach b $boxes { puts $f "$why|$b" } }
close $f
quit -noprompt
