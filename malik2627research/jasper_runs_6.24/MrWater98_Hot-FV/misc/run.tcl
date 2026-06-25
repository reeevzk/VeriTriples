clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/benchmark/RocketTile_Small /home/rk6650/VeriTriples/malik2627research/repos_6.24/MrWater98_Hot-FV/benchmark/RocketTile_Small/RocketTile_dut.v }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/benchmark/RocketTile_Small /home/rk6650/VeriTriples/malik2627research/repos_6.24/MrWater98_Hot-FV/benchmark/RocketTile_Small/RocketTile_dut.v }


            if {[catch {elaborate -top RocketTile} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/MrWater98_Hot-FV/misc/results.rpt
report_vacuity -out jasper_runs_6.24/MrWater98_Hot-FV/misc/vacuity.rpt
exit
