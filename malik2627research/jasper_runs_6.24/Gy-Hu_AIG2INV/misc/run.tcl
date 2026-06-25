clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/benchmark_folder/cnt-zeros -incdir /home/rk6650/VeriTriples/malik2627research/benchmark_folder/cnt1 /home/rk6650/VeriTriples/malik2627research/repos_6.24/Gy-Hu_AIG2INV/benchmark_folder/cnt-zeros/cnt.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/benchmark_folder/cnt-zeros -incdir /home/rk6650/VeriTriples/malik2627research/benchmark_folder/cnt1 /home/rk6650/VeriTriples/malik2627research/repos_6.24/Gy-Hu_AIG2INV/benchmark_folder/cnt1/cnt.v }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/benchmark_folder/cnt-zeros -incdir /home/rk6650/VeriTriples/malik2627research/benchmark_folder/cnt1 /home/rk6650/VeriTriples/malik2627research/repos_6.24/Gy-Hu_AIG2INV/benchmark_folder/cnt-zeros/cnt.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/benchmark_folder/cnt-zeros -incdir /home/rk6650/VeriTriples/malik2627research/benchmark_folder/cnt1 /home/rk6650/VeriTriples/malik2627research/repos_6.24/Gy-Hu_AIG2INV/benchmark_folder/cnt1/cnt.v }


            if {[catch {elaborate -top cnt} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/Gy-Hu_AIG2INV/misc/results.rpt
report_vacuity -out jasper_runs_6.24/Gy-Hu_AIG2INV/misc/vacuity.rpt
exit
