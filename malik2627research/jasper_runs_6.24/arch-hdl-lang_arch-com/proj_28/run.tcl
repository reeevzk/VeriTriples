clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/tests/cvdp /home/rk6650/VeriTriples/malik2627research/repos_6.24/arch-hdl-lang_arch-com/tests/cvdp/TLB.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/tests/cvdp /home/rk6650/VeriTriples/malik2627research/repos_6.24/arch-hdl-lang_arch-com/tests/cvdp/TLB.sv }


            if {[catch {elaborate -top TLB} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/arch-hdl-lang_arch-com/proj_28/results.rpt
report_vacuity -out jasper_runs_6.24/arch-hdl-lang_arch-com/proj_28/vacuity.rpt
exit
