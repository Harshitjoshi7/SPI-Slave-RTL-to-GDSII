###############################################################################
# STEP 4: Placement
# Usage inside Innovus:  source scripts/step4_place.tcl
###############################################################################

# Insert end caps (ignore error if cell not found in PDK)
catch {addEndCap -prefix ENDCAP}

# Insert well taps (try both common cell names)
catch {addWellTap -cell FILL1 -cellInterval 30 -prefix WELLTAP}

# Run timing-driven placement with optimization
place_opt_design

# Verify placement legality
checkPlace

# Pre-CTS timing report
timeDesign -preCTS -outDir reports

puts "\n=== STEP 4 COMPLETE: Placement done ==="
puts "=== Check reports/ for pre-CTS timing ==="
puts "=== Next: source scripts/step5_cts.tcl ==="
