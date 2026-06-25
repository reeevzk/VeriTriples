clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/modelsim_files /home/rk6650/VeriTriples/malik2627research/repos_6.24/PeterW-XD_MSI_Formal_Verification/cache_datapath.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/modelsim_files /home/rk6650/VeriTriples/malik2627research/repos_6.24/PeterW-XD_MSI_Formal_Verification/cache_controller.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/modelsim_files /home/rk6650/VeriTriples/malik2627research/repos_6.24/PeterW-XD_MSI_Formal_Verification/cache.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/modelsim_files /home/rk6650/VeriTriples/malik2627research/repos_6.24/PeterW-XD_MSI_Formal_Verification/memory.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/modelsim_files /home/rk6650/VeriTriples/malik2627research/repos_6.24/PeterW-XD_MSI_Formal_Verification/main.v }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/modelsim_files /home/rk6650/VeriTriples/malik2627research/repos_6.24/PeterW-XD_MSI_Formal_Verification/cache_controller.v }


            if {[catch {elaborate -top cache_controller} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/PeterW-XD_MSI_Formal_Verification/proj_0/results.rpt
report_vacuity -out jasper_runs_6.24/PeterW-XD_MSI_Formal_Verification/proj_0/vacuity.rpt
exit
