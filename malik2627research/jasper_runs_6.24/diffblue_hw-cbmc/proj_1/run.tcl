clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/examples/Benchmarks /home/rk6650/VeriTriples/malik2627research/repos_6.24/diffblue_hw-cbmc/examples/Benchmarks/delay_9.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/examples/Benchmarks /home/rk6650/VeriTriples/malik2627research/repos_6.24/diffblue_hw-cbmc/examples/Benchmarks/delay_9.sv }


            if {[catch {elaborate -top DELAY} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/diffblue_hw-cbmc/proj_1/results.rpt
report_vacuity -out jasper_runs_6.24/diffblue_hw-cbmc/proj_1/vacuity.rpt
exit
