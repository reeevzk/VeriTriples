clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/dbretwolfe_UARTsv/TestPackage.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/dbretwolfe_UARTsv/RX_FSM.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/dbretwolfe_UARTsv/FIFO - Copy.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/dbretwolfe_UARTsv/RX_FSM.sv }


            if {[catch {elaborate -top FIFO} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/dbretwolfe_UARTsv/misc/results.rpt
report_vacuity -out jasper_runs_6.24/dbretwolfe_UARTsv/misc/vacuity.rpt
exit
