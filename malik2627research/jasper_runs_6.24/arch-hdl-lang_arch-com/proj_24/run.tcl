clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/tests/cvdp /home/rk6650/VeriTriples/malik2627research/repos_6.24/arch-hdl-lang_arch-com/tests/cvdp/FILO_RTL.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/tests/cvdp /home/rk6650/VeriTriples/malik2627research/repos_6.24/arch-hdl-lang_arch-com/tests/cvdp/FILO_RTL.sv }


            if {[catch {elaborate -top FILO_RTL} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/arch-hdl-lang_arch-com/proj_24/results.rpt
report_vacuity -out jasper_runs_6.24/arch-hdl-lang_arch-com/proj_24/vacuity.rpt
exit
