# --- Netgen LVS Configuration for Custom Black-Box NPN ---

# 1. Permissive options to enable black-box matching
set AC_ignore 1
set MV_ignore 1
set LVS_subcircuits 1

# 2. Declare your cell name as a black box
lvs "A_NPN_BJT_6V_fixed" "A_NPN_BJT_6V_fixed"