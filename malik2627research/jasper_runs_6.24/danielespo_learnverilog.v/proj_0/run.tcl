clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/danielespo_learnverilog.v/all-syntax.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/danielespo_learnverilog.v/verilog_tutorial.v }


catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/danielespo_learnverilog.v/all-syntax.sv }


            if {[catch {elaborate -top parameterized_module} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/danielespo_learnverilog.v/proj_0/results.rpt
report_vacuity -out jasper_runs_6.24/danielespo_learnverilog.v/proj_0/vacuity.rpt
exit
