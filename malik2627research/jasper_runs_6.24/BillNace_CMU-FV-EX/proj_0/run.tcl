clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/task1 -incdir /home/rk6650/VeriTriples/malik2627research/task4 /home/rk6650/VeriTriples/malik2627research/repos_6.24/BillNace_CMU-FV-EX/task1/tb.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/task1 -incdir /home/rk6650/VeriTriples/malik2627research/task4 /home/rk6650/VeriTriples/malik2627research/repos_6.24/BillNace_CMU-FV-EX/task1/dut.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/task1 -incdir /home/rk6650/VeriTriples/malik2627research/task4 /home/rk6650/VeriTriples/malik2627research/repos_6.24/BillNace_CMU-FV-EX/task4/fifo_bad_8.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/task1 -incdir /home/rk6650/VeriTriples/malik2627research/task4 /home/rk6650/VeriTriples/malik2627research/repos_6.24/BillNace_CMU-FV-EX/task1/tb.sv }


            if {[catch {elaborate -top TB} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/BillNace_CMU-FV-EX/proj_0/results.rpt
report_vacuity -out jasper_runs_6.24/BillNace_CMU-FV-EX/proj_0/vacuity.rpt
exit
