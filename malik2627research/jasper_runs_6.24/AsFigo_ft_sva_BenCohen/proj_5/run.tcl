clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/fast_sva/ch7 /home/rk6650/VeriTriples/malik2627research/repos_6.24/AsFigo_ft_sva_BenCohen/fast_sva/ch7/akill.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/fast_sva/ch7 /home/rk6650/VeriTriples/malik2627research/repos_6.24/AsFigo_ft_sva_BenCohen/fast_sva/ch7/akill.sv }


            if {[catch {elaborate -top akill} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/AsFigo_ft_sva_BenCohen/proj_5/results.rpt
report_vacuity -out jasper_runs_6.24/AsFigo_ft_sva_BenCohen/proj_5/vacuity.rpt
exit
