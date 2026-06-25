clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/01_Projects -incdir /home/rk6650/VeriTriples/malik2627research/02_OOP -incdir /home/rk6650/VeriTriples/malik2627research/03_cache_oop(cpp) /home/rk6650/VeriTriples/malik2627research/repos_6.24/chinthacharan_DV-Interview-Prep-Guide/SV_design.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/01_Projects -incdir /home/rk6650/VeriTriples/malik2627research/02_OOP -incdir /home/rk6650/VeriTriples/malik2627research/03_cache_oop(cpp) /home/rk6650/VeriTriples/malik2627research/repos_6.24/chinthacharan_DV-Interview-Prep-Guide/important_questions.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/01_Projects -incdir /home/rk6650/VeriTriples/malik2627research/02_OOP -incdir /home/rk6650/VeriTriples/malik2627research/03_cache_oop(cpp) /home/rk6650/VeriTriples/malik2627research/repos_6.24/chinthacharan_DV-Interview-Prep-Guide/SV_design.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/01_Projects -incdir /home/rk6650/VeriTriples/malik2627research/02_OOP -incdir /home/rk6650/VeriTriples/malik2627research/03_cache_oop(cpp) /home/rk6650/VeriTriples/malik2627research/repos_6.24/chinthacharan_DV-Interview-Prep-Guide/important_questions.sv }


            if {[catch {elaborate -top synchronizer} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/chinthacharan_DV-Interview-Prep-Guide/proj_0/results.rpt
report_vacuity -out jasper_runs_6.24/chinthacharan_DV-Interview-Prep-Guide/proj_0/vacuity.rpt
exit
