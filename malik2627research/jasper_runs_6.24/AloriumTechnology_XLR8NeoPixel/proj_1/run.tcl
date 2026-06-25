clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/extras/modelsim -incdir /home/rk6650/VeriTriples/malik2627research/extras/rtl -incdir /home/rk6650/VeriTriples/malik2627research/extras/rtl/ram2p1024x36 /home/rk6650/VeriTriples/malik2627research/repos_6.24/AloriumTechnology_XLR8NeoPixel/extras/modelsim/xlr8_sim_support.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/extras/modelsim -incdir /home/rk6650/VeriTriples/malik2627research/extras/rtl -incdir /home/rk6650/VeriTriples/malik2627research/extras/rtl/ram2p1024x36 /home/rk6650/VeriTriples/malik2627research/repos_6.24/AloriumTechnology_XLR8NeoPixel/extras/rtl/xlr8_neopixel.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/extras/modelsim -incdir /home/rk6650/VeriTriples/malik2627research/extras/rtl -incdir /home/rk6650/VeriTriples/malik2627research/extras/rtl/ram2p1024x36 /home/rk6650/VeriTriples/malik2627research/repos_6.24/AloriumTechnology_XLR8NeoPixel/extras/rtl/ram2p1024x36/ram2p1024x36_bb.v }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/extras/modelsim -incdir /home/rk6650/VeriTriples/malik2627research/extras/rtl -incdir /home/rk6650/VeriTriples/malik2627research/extras/rtl/ram2p1024x36 /home/rk6650/VeriTriples/malik2627research/repos_6.24/AloriumTechnology_XLR8NeoPixel/extras/rtl/xlr8_neopixel.v }


            if {[catch {elaborate -top ram2p1024x36} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/AloriumTechnology_XLR8NeoPixel/proj_1/results.rpt
report_vacuity -out jasper_runs_6.24/AloriumTechnology_XLR8NeoPixel/proj_1/vacuity.rpt
exit
