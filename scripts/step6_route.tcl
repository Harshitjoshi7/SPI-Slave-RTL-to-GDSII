###############################################################################
# STEP 6: Filler Insertion + Routing + Post-Route Optimization
# Usage inside Innovus:  source scripts/step6_route.tcl
###############################################################################

# Insert filler cells (try both GPDK naming conventions)
catch {addFiller -cell {FILL64 FILL32 FILL16 FILL8 FILL4 FILL2 FILL1} -prefix FILLER}
catch {addFiller -cell {FILLCELL64 FILLCELL32 FILLCELL16 FILLCELL8 FILLCELL4 FILLCELL2 FILLCELL1} -prefix FILLER}

# Verify no gaps
checkPlace

# Run NanoRoute
routeDesign

# Enable OCV analysis with CPPR
setAnalysisMode -analysisType onChipVariation -cppr both

# Post-route optimization (setup + hold)
optDesign -postRoute
optDesign -postRoute -hold

# Post-route timing reports
timeDesign -postRoute -outDir reports
timeDesign -postRoute -hold -outDir reports

puts "\n=== STEP 6 COMPLETE: Routing done ==="
puts "=== Check reports/ for post-route timing ==="
puts "=== Next: source scripts/step7_export.tcl ==="
