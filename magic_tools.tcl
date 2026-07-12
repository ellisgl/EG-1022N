# ==============================================================================
# Magic VLSI Custom Shape Layout Generator TCL Library Script
# ==============================================================================
# This library provides automated geometric functions for layout designs.
# It includes safety filters to prevent manufacturing Design Rule Checks (DRC).
#
# NOTE on units: the circle/ring generators use a scanline fill that steps the
# row index by 1 (`incr y`) and paints 1-unit-tall boxes. This assumes an
# INTEGER grid, which holds for "lambda". If you call these with "microns"/"um"
# and a fractional radius, `incr y` will fail (it requires an integer) and the
# 1-um row height will not match intent. For micron callers, drive the loop in
# integer grid steps and scale only at the `box` call.

# Helper procedure to safely fetch the grid scale ratio
# Magic uses an internal measurement unit called "lambda". This function checks
# how many micrometers (um) equal 1 lambda in your currently loaded technology file.
proc get_lambda_to_um_scale {} {
    # Magic's "cif scale out" reports microns per internal unit for the current
    # cif output style. Bare "cif scale" is a usage error, so we call it with
    # "out" and parse the number, falling back to a safe GF180 default (5 nm).
    if {[catch {cif scale out} scale_str]} {
        return 0.005
    }
    if {[regexp {([0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)} $scale_str match value] \
            && $value > 0} {
        return $value
    }
    return 0.005
}

# Resolve the paint/erase operation. Every generator paints by default; pass
# "erase" (or use the erase_* wrappers) to clear the same geometry instead.
# Guards against arbitrary values since the result is used as a command name.
proc resolve_shape_op {op} {
    if {$op eq "paint" || $op eq "erase"} {
        return $op
    }
    puts "Warning: unknown op '$op'; defaulting to paint."
    return "paint"
}

# Create a filled circle
# cx    Center X coordinate
# cy    Center Y coordinate
# r     The radius of the circle
# layer Layer to use for painting (e.g., metal1, poly, dnwell)
# unit  Units to use for measurements (Optional, defaults to lambda)
# op    "paint" (default) or "erase"
proc make_circle {cx cy r layer {unit "lambda"} {op "paint"}} {
    set op [resolve_shape_op $op]
    # Micron path: fractional radii break the integer scanline (incr), so use
    # the grid-stepped make_arc (a full disc is a 0..360 sector, inner_r = 0).
    if {$unit eq "microns" || $unit eq "um"} {
        make_arc $cx $cy $r $r 0 360 $layer $unit $op
        return
    }
    set old_units [units]
    units $unit
    set lambda_to_um [get_lambda_to_um_scale]

    if {[catch {tech drc width $layer} min_width_lambda]} {
        set min_width_lambda 1
    }

    if {$unit eq "microns" || $unit eq "um"} {
        set min_width_check [expr {$min_width_lambda * $lambda_to_um}]
    } else {
        set min_width_check $min_width_lambda
    }

    select clear
    suspendall

    for {set y [expr {-$r}]} {$y <= $r} {incr y} {
        set term [expr {($r * $r) - ($y * $y)}]
        if {$term >= 0} {
            set x_span [expr {int(sqrt($term))}]
            if {[expr {$x_span * 2}] >= $min_width_check} {
                set x1 [expr {$cx - $x_span}]
                set x2 [expr {$cx + $x_span}]
                set y1 [expr {$cy + $y}]
                set y2 [expr {$y1 + 1}]
                box $x1 $y1 $x2 $y2
                $op $layer
            }
        }
    }

    resumeall
    box $cx $cy $cx $cy
    units $old_units
}

# Create a ring
# cx        Center X coordinate
# cy        Center Y coordinate
# outer_r   The outer radius of the ring
# thickness The thickness of the ring wall, from outer to inner boundary
# layer     Layer to use for painting
# unit      Units to use for measurements (Optional, defaults to lambda)
# op        "paint" (default) or "erase"
proc make_ring {cx cy outer_r thickness layer {unit "lambda"} {op "paint"}} {
    set op [resolve_shape_op $op]
    # Micron path: fractional radii break the integer scanline (incr), so use
    # the grid-stepped make_arc (a full ring is a 0..360 sector).
    if {$unit eq "microns" || $unit eq "um"} {
        make_arc $cx $cy $outer_r $thickness 0 360 $layer $unit $op
        return
    }
    set old_units [units]
    units $unit
    set lambda_to_um [get_lambda_to_um_scale]

    if {[catch {tech drc width $layer} min_width_lambda]} {
        set min_width_lambda 1
    }

    if {$unit eq "microns" || $unit eq "um"} {
        set min_width_check [expr {$min_width_lambda * $lambda_to_um}]
    } else {
        set min_width_check $min_width_lambda
    }

    set inner_r [expr {$outer_r - $thickness}]
    if {$inner_r < 0} {set inner_r 0}

    select clear
    suspendall

    for {set y [expr {-$outer_r}]} {$y <= $outer_r} {incr y} {
        set term_out [expr {($outer_r * $outer_r) - ($y * $y)}]
        if {$term_out < 0} {continue}
        set x_span_out [expr {int(sqrt($term_out))}]
        set term_in [expr {($inner_r * $inner_r) - ($y * $y)}]
        set abs_y1 [expr {$cy + $y}]
        set abs_y2 [expr {$abs_y1 + 1}]

        if {$term_in >= 0 && $inner_r > 0} {
            set x_span_inner [expr {int(sqrt($term_in))}]
            set left_x1 [expr {$cx - $x_span_out}]
            set left_x2 [expr {$cx - $x_span_inner}]
            if {$left_x1 < $left_x2} {
                box $left_x1 $abs_y1 $left_x2 $abs_y2
                $op $layer
            }
            set right_x1 [expr {$cx + $x_span_inner}]
            set right_x2 [expr {$cx + $x_span_out}]
            if {$right_x1 < $right_x2} {
                box $right_x1 $abs_y1 $right_x2 $abs_y2
                $op $layer
            }
        } else {
            if {[expr {$x_span_out * 2}] >= $min_width_check} {
                set x1 [expr {$cx - $x_span_out}]
                set x2 [expr {$cx + $x_span_out}]
                box $x1 $abs_y1 $x2 $abs_y2
                $op $layer
            }
        }
    }

    resumeall
    box $cx $cy $cx $cy
    units $old_units
}

# Create a diagonal line using an overlapping rectilinear staircase pattern.
#
# Each step paints a block of EXACTLY w x h. The painted block size is never
# inflated. w and h set the granularity / "thickness" of the staircase; the
# travel angle is set by `degree` (default 45) and the quadrant by dud/dlr.
#
# The per-step advance is derived from `degree`: the dominant axis advances by
# (block - overlap), and the other axis is scaled by the angle. This keeps
# consecutive blocks edge-overlapping (electrically connected) for any
# 0 <= degree <= 90, EXCEPT the pure-45 / overlap=0 case, which is corner-touch
# only (fine for annotation layers; pass overlap >= 1 for connected metal/poly).
#
# Because advances are snapped to the integer grid, the realized angle is a grid
# approximation of `degree`; larger w/h (more steps) approximate it more closely.
#
# sx      Starting X coordinate
# sy      Starting Y coordinate
# w       Width of each block step (must be >= min_width)
# h       Height of each block step (must be >= min_width)
# l       Length (number of stair steps to generate)
# dud     Vertical direction: "up" or "down"
# dlr     Horizontal direction: "right" or "left"
# layer   Layer to use for painting
# unit    Units to use for measurements (Optional, defaults to lambda)
# overlap Overlap between consecutive steps, in `unit` (Optional, defaults to 0)
# degree  Travel angle in degrees, 0..90 (Optional, defaults to 45)
# op      "paint" (default) or "erase"
proc make_diagonal {sx sy w h l dud dlr layer {unit "lambda"} {overlap 0} {degree 45} {op "paint"}} {
    set op [resolve_shape_op $op]
    set old_units [units]
    units $unit
    set lambda_to_um [get_lambda_to_um_scale]

    if {[catch {tech drc width $layer} min_width_lambda]} {
        set min_width_lambda 1
    }

    if {$unit eq "microns" || $unit eq "um"} {
        set min_width_check [expr {$min_width_lambda * $lambda_to_um}]
        set grid $lambda_to_um
    } else {
        set min_width_check $min_width_lambda
        set grid 1
    }
    if {$grid <= 0} {set grid 1}

    if {$w < $min_width_check || $h < $min_width_check} {
        puts "Warning: Requested block size ($w x $h) is less than minimum ($min_width_check)."
        if {$w < $min_width_check} {set w $min_width_check}
        if {$h < $min_width_check} {set h $min_width_check}
    }

    # Overlap must stay strictly smaller than the block, otherwise the diagonal
    # would fail to advance. Clamp and warn if it is too large.
    if {$w < $h} {set max_block $w} else {set max_block $h}
    if {$overlap < 0} {set overlap 0}
    if {$overlap >= $max_block} {
        set clamped [expr {$max_block - $grid}]
        if {$clamped < 0} {set clamped 0}
        puts "Warning: overlap ($overlap) >= block size ($max_block); clamping to $clamped."
        set overlap $clamped
    }

    # Clamp the requested angle into [0, 90].
    if {$degree < 0}  {set degree 0}
    if {$degree > 90} {set degree 90}

    # Derive per-step advance magnitudes (step_x, step_y) from the angle.
    # The dominant axis steps by (block - overlap); the other axis is scaled by
    # tan/cot of the angle, snapped to the grid resolution (`grid`), and capped
    # at the block extent so consecutive blocks keep overlapping (connected).
    # Snapping to `grid` -- not to integer 1 -- is what makes sub-micron blocks
    # work; round() alone would collapse a 0.05 um y-advance to 0.
    set rad [expr {$degree * acos(-1) / 180.0}]
    if {$degree == 0} {
        set step_x [expr {$w - $overlap}]
        set step_y 0
    } elseif {$degree == 90} {
        set step_x 0
        set step_y [expr {$h - $overlap}]
    } elseif {$degree <= 45} {
        set step_x [expr {$w - $overlap}]
        set step_y [expr {round($step_x * tan($rad) / $grid) * $grid}]
        if {$step_y > $h} {set step_y $h}
    } else {
        set step_y [expr {$h - $overlap}]
        set step_x [expr {round($step_y / tan($rad) / $grid) * $grid}]
        if {$step_x > $w} {set step_x $w}
    }

    set x_dir 1
    if {$dlr eq "left"} {set x_dir -1}
    set y_dir 1
    if {$dud eq "down"} {set y_dir -1}

    set cur_x $sx
    set cur_y $sy
    select clear
    suspendall

    for {set i 0} {$i < $l} {incr i} {
        set x1 $cur_x
        set y1 $cur_y
        set x2 [expr {$cur_x + ($w * $x_dir)}]
        set y2 [expr {$cur_y + ($h * $y_dir)}]

        if {$x1 < $x2} {
            set bx1 $x1
            set bx2 $x2
        } else {
            set bx1 $x2
            set bx2 $x1
        }

        if {$y1 < $y2} {
            set by1 $y1
            set by2 $y2
        } else {
            set by1 $y2
            set by2 $y1
        }

        # Snap corners to the grid so accumulated float error never lands a
        # coordinate off-grid (a no-op in lambda, where grid == 1).
        set bx1 [expr {round($bx1 / $grid) * $grid}]
        set by1 [expr {round($by1 / $grid) * $grid}]
        set bx2 [expr {round($bx2 / $grid) * $grid}]
        set by2 [expr {round($by2 / $grid) * $grid}]

        box $bx1 $by1 $bx2 $by2
        $op $layer

        # Advance along the angle. step_x/step_y were derived from `degree`.
        set cur_x [expr {$cur_x + $step_x * $x_dir}]
        set cur_y [expr {$cur_y + $step_y * $y_dir}]
    }

    resumeall
    box $sx $sy $sx $sy
    units $old_units
}

# Create an annular sector (arc segment). This generalizes make_ring with an
# angular range, and is the building block for pie/gauge style layouts:
#   * thickness >= outer_r (inner_r = 0)         -> solid pie WEDGE
#   * 0 < thickness < outer_r                    -> ARC / ring segment
#   * a small (end_deg - start_deg)              -> radial SPOKE
#   * (end_deg - start_deg) >= 360               -> full ring (== make_ring)
#
# Angles are in degrees, measured counter-clockwise from the +x axis. The sector
# is swept from start_deg toward end_deg in the increasing-angle (CCW) direction,
# so start=0 end=90 fills the first quadrant. The two radial edges are Manhattan
# staircases (same look as make_diagonal), which is expected on a mask grid.
#
# cx        Center X coordinate
# cy        Center Y coordinate
# outer_r   Outer radius
# thickness Radial wall thickness (outer_r -> inner_r). Use outer_r for a wedge.
# start_deg Sector start angle in degrees (CCW from +x)
# end_deg   Sector end angle in degrees (CCW from +x)
# layer     Layer to use for painting
# unit      Units to use for measurements (Optional, defaults to lambda)
# op        "paint" (default) or "erase"
proc make_arc {cx cy outer_r thickness start_deg end_deg layer {unit "lambda"} {op "paint"}} {
    set op [resolve_shape_op $op]
    set old_units [units]
    units $unit
    if {$unit eq "microns" || $unit eq "um"} {
        set grid [get_lambda_to_um_scale]
    } else {
        set grid 1
    }
    if {$grid <= 0} {set grid 1}

    set inner_r [expr {$outer_r - $thickness}]
    if {$inner_r < 0} {set inner_r 0}
    set inner_r2 [expr {$inner_r*$inner_r}]
    set outer_r2 [expr {$outer_r*$outer_r}]

    set pi [expr {acos(-1)}]
    if {[expr {$end_deg-$start_deg}] >= 360.0} {
        set sweep 360.0
    } else {
        set sweep [expr {fmod($end_deg-$start_deg,360.0)}]
        if {$sweep < 0} {set sweep [expr {$sweep+360.0}]}
    }
    set a0 [expr {$start_deg*$pi/180.0}]
    set a1 [expr {($start_deg+$sweep)*$pi/180.0}]
    set s0 [expr {sin($a0)}]; set c0 [expr {cos($a0)}]
    set s1 [expr {sin($a1)}]; set c1 [expr {cos($a1)}]
    set eps 1e-9
    set INF 1e18

    select clear
    suspendall

    set y [expr {-$outer_r}]
    while {$y <= $outer_r + $grid*0.5} {
        set dy2 [expr {$y*$y}]
        if {$dy2 <= $outer_r2 + $eps} {
            set xo [expr {sqrt($outer_r2-$dy2 < 0 ? 0 : $outer_r2-$dy2)}]
            # annulus intervals in local x
            set ann {}
            if {$inner_r > 0 && $dy2 < $inner_r2 - $eps} {
                set xi [expr {sqrt($inner_r2-$dy2)}]
                lappend ann [list [expr {-$xo}] [expr {-$xi}]]
                lappend ann [list $xi $xo]
            } else {
                lappend ann [list [expr {-$xo}] $xo]
            }
            # sector intervals in local x
            if {$sweep >= 360.0} {
                set sec [list [list -$INF $INF]]
            } else {
                # half-line A: c0*y - s0*x >= 0
                if {$s0 > $eps} { set HA [list -$INF [expr {$c0*$y/$s0}]] } \
                elseif {$s0 < -$eps} { set HA [list [expr {$c0*$y/$s0}] $INF] } \
                else { if {$c0*$y >= 0} {set HA [list -$INF $INF]} else {set HA {}} }
                # half-line B: s1*x - c1*y >= 0
                if {$s1 > $eps} { set HB [list [expr {$c1*$y/$s1}] $INF] } \
                elseif {$s1 < -$eps} { set HB [list -$INF [expr {$c1*$y/$s1}]] } \
                else { if {-$c1*$y >= 0} {set HB [list -$INF $INF]} else {set HB {}} }

                set sec {}
                if {$sweep <= 180.0} {
                    if {[llength $HA] && [llength $HB]} {
                        set lo [expr {max([lindex $HA 0],[lindex $HB 0])}]
                        set hi [expr {min([lindex $HA 1],[lindex $HB 1])}]
                        if {$lo < $hi} {lappend sec [list $lo $hi]}
                    }
                } else {
                    # union of two half-lines (reflex wedge)
                    foreach H [list $HA $HB] { if {[llength $H]} {lappend sec $H} }
                    # merge if they overlap into full line
                    if {[llength $sec] == 2} {
                        lassign [lindex $sec 0] la lb
                        lassign [lindex $sec 1] lc ld
                        if {$la <= $lc} { set lo1 $la; set hi1 $lb; set lo2 $lc; set hi2 $ld } \
                        else { set lo1 $lc; set hi1 $ld; set lo2 $la; set hi2 $lb }
                        if {$hi1 >= $lo2} { set sec [list [list $lo1 [expr {max($hi1,$hi2)}]]] }
                    }
                }
            }
            # intersect ann x sec, paint
            foreach A $ann {
                lassign $A alo ahi
                foreach S $sec {
                    lassign $S slo shi
                    set lo [expr {max($alo,$slo)}]
                    set hi [expr {min($ahi,$shi)}]
                    if {$hi - $lo > $eps} {
                        set x1 [expr {round(($cx+$lo)/$grid)*$grid}]
                        set x2 [expr {round(($cx+$hi)/$grid)*$grid}]
                        set y1 [expr {round(($cy+$y)/$grid)*$grid}]
                        set y2 [expr {round(($cy+$y+$grid)/$grid)*$grid}]
                        if {$x2 > $x1} { box $x1 $y1 $x2 $y2; $op $layer }
                    }
                }
            }
        }
        set y [expr {$y + $grid}]
    }
    resumeall
    box $cx $cy $cx $cy
    units $old_units
}


# ==============================================================================
# Convenience wrappers: erase the same geometry instead of painting it.
# Each simply forwards to its generator with op = "erase". Useful for cutting
# notches / holes, e.g. paint a full ring then erase a wedge out of it.
# ==============================================================================

proc erase_circle {cx cy r layer {unit "lambda"}} {
    make_circle $cx $cy $r $layer $unit erase
}

proc erase_ring {cx cy outer_r thickness layer {unit "lambda"}} {
    make_ring $cx $cy $outer_r $thickness $layer $unit erase
}

proc erase_diagonal {sx sy w h l dud dlr layer {unit "lambda"} {overlap 0} {degree 45}} {
    make_diagonal $sx $sy $w $h $l $dud $dlr $layer $unit $overlap $degree erase
}

proc erase_arc {cx cy outer_r thickness start_deg end_deg layer {unit "lambda"}} {
    make_arc $cx $cy $outer_r $thickness $start_deg $end_deg $layer $unit erase
}

# Create a filled triangle from three vertices (absolute coordinates), using a
# scanline fill. Grid-aware and micron-safe like the other generators; honors
# the paint/erase op. Handy for pointer tips / arrowheads and any polygon that
# can be decomposed into triangles.
#
# x1 y1 x2 y2 x3 y3  The three vertices
# layer              Layer to use for painting
# unit               Units to use for measurements (Optional, defaults to lambda)
# op                 "paint" (default) or "erase"
proc make_triangle {x1 y1 x2 y2 x3 y3 layer {unit "lambda"} {op "paint"}} {
    set op [resolve_shape_op $op]
    set old_units [units]
    units $unit
    if {$unit eq "microns" || $unit eq "um"} {
        set grid [get_lambda_to_um_scale]
    } else {
        set grid 1
    }
    if {$grid <= 0} {set grid 1}

    set ymin [expr {min($y1, $y2, $y3)}]
    set ymax [expr {max($y1, $y2, $y3)}]
    set edges [list \
        [list $x1 $y1 $x2 $y2] \
        [list $x2 $y2 $x3 $y3] \
        [list $x3 $y3 $x1 $y1]]
    set eps 1e-9

    select clear
    suspendall

    set y $ymin
    while {$y <= $ymax + $grid * 0.5} {
        set yc [expr {$y + $grid / 2.0}]   ;# sample at row center
        set xs {}
        foreach e $edges {
            lassign $e ax ay bx by
            set lo [expr {min($ay, $by)}]
            set hi [expr {max($ay, $by)}]
            if {$yc >= $lo && $yc < $hi} {
                set t [expr {($yc - $ay) / ($by - $ay)}]
                lappend xs [expr {$ax + $t * ($bx - $ax)}]
            }
        }
        if {[llength $xs] >= 2} {
            set xlo [lindex $xs 0]
            set xhi [lindex $xs 0]
            foreach v $xs {
                if {$v < $xlo} {set xlo $v}
                if {$v > $xhi} {set xhi $v}
            }
            set bx1 [expr {round($xlo / $grid) * $grid}]
            set bx2 [expr {round($xhi / $grid) * $grid}]
            set by1 [expr {round($y / $grid) * $grid}]
            set by2 [expr {round(($y + $grid) / $grid) * $grid}]
            if {$bx2 > $bx1} {
                box $bx1 $by1 $bx2 $by2
                $op $layer
            }
        }
        set y [expr {$y + $grid}]
    }

    resumeall
    box $x1 $y1 $x1 $y1
    units $old_units
}