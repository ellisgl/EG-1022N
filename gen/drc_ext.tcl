set cell [lindex $argv end]
load $cell
select top cell
drc euclidean on
drc style drc(full)
drc check
drc catchup
set n [drc list count total]
puts "DRC_TOTAL $n"
foreach {why boxes} [drc listall why] {
    puts "DRC_ERR [llength $boxes] :: $why"
    puts "   first: [lindex $boxes 0]"
}
extract do local
extract all
ext2spice lvs
ext2spice -o ${cell}_lvs.spice
ext2spice cthresh 0
ext2spice -o ${cell}.spice
gds write ${cell}.gds
quit -noprompt
