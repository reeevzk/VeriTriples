clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController/Memory.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController/Send_command.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController/Controller_FSM.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController/ReadWrite.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController/CalcMax.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController/Receive_command.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController/Scheduler.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController/Read_data_comm.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController/MemoryController.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController/ShiftReg.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController/Timer.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController/Memory.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController -incdir /home/rk6650/VeriTriples/malik2627research /home/rk6650/VeriTriples/malik2627research/repos_6.24/ananthbhat94_DDR4MemoryController/Controller_FSM.sv }


            if {[catch {elaborate -top receive_read_data} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/ananthbhat94_DDR4MemoryController/proj_0/results.rpt
report_vacuity -out jasper_runs_6.24/ananthbhat94_DDR4MemoryController/proj_0/vacuity.rpt
exit
