###############################################################################
# STEP 7: Verification + Export (DRC, connectivity, netlist, SPEF, SDF, GDSII)
# Usage inside Innovus:  source scripts/step7_export.tcl
###############################################################################

#--- Physical Verification ---
verify_drc
verifyConnectivity -type all -error 1000 -warning 50
catch {verifyProcessAntenna}

#--- Export Netlists ---
saveNetlist netlist/spi_slave_postroute.v
saveNetlist -includePowerGround netlist/spi_slave_postroute_pg.v

#--- Parasitic Extraction (low effort — no QRC tech file needed) ---
setExtractRCMode -engine postRoute -effortLevel low
extractRC
rcOut -spef netlist/spi_slave_postroute.spef

#--- SDF for Post-Route Gate-Level Simulation ---
write_sdf -version 3.0 netlist/spi_slave_postroute.sdf

#--- Final Signoff Timing ---
timeDesign -signoff -outDir reports
timeDesign -signoff -hold -outDir reports

#--- GDSII Export (units 2000 + mapFile + merge standard cell GDS for complete physical LVS/DRC) ---
catch {streamOut output/spi_slave.gds -mapFile /home/ec/install/Physical_Verification/STREAM_MAP/45nmNew_streamOut.map -merge {/home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/gds/gsclib045.gds} -libName spi_slave -structureName spi_slave -units 2000 -mode ALL}

#--- Save Design Database ---
saveDesign output/spi_slave_final.enc

puts "\n=========================================="
puts "=== INNOVUS PnR FLOW COMPLETE ==="
puts "=========================================="
puts "Output files:"
puts "  Netlist:     netlist/spi_slave_postroute.v"
puts "  Netlist+PG:  netlist/spi_slave_postroute_pg.v"
puts "  SPEF:        netlist/spi_slave_postroute.spef"
puts "  SDF:         netlist/spi_slave_postroute.sdf"
puts "  GDSII:       output/spi_slave.gds"
puts "  Database:    output/spi_slave_final.enc"
puts "  Reports:     reports/"
puts "=========================================="
