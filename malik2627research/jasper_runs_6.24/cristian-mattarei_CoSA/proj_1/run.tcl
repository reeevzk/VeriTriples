clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/examples/fifo_async -incdir /home/rk6650/VeriTriples/malik2627research/tests/parametric -incdir /home/rk6650/VeriTriples/malik2627research/tests/synchronize-clocks -incdir /home/rk6650/VeriTriples/malik2627research/tutorial /home/rk6650/VeriTriples/malik2627research/repos_6.24/cristian-mattarei_CoSA/tutorial/robot.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/examples/fifo_async -incdir /home/rk6650/VeriTriples/malik2627research/tests/parametric -incdir /home/rk6650/VeriTriples/malik2627research/tests/synchronize-clocks -incdir /home/rk6650/VeriTriples/malik2627research/tutorial /home/rk6650/VeriTriples/malik2627research/repos_6.24/cristian-mattarei_CoSA/tests/synchronize-clocks/counters2clks.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/examples/fifo_async -incdir /home/rk6650/VeriTriples/malik2627research/tests/parametric -incdir /home/rk6650/VeriTriples/malik2627research/tests/synchronize-clocks -incdir /home/rk6650/VeriTriples/malik2627research/tutorial /home/rk6650/VeriTriples/malik2627research/repos_6.24/cristian-mattarei_CoSA/examples/fifo_async/oh_fifo_generic-single.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/examples/fifo_async -incdir /home/rk6650/VeriTriples/malik2627research/tests/parametric -incdir /home/rk6650/VeriTriples/malik2627research/tests/synchronize-clocks -incdir /home/rk6650/VeriTriples/malik2627research/tutorial /home/rk6650/VeriTriples/malik2627research/repos_6.24/cristian-mattarei_CoSA/tests/parametric/pipelined_counter.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/examples/fifo_async -incdir /home/rk6650/VeriTriples/malik2627research/tests/parametric -incdir /home/rk6650/VeriTriples/malik2627research/tests/synchronize-clocks -incdir /home/rk6650/VeriTriples/malik2627research/tutorial /home/rk6650/VeriTriples/malik2627research/repos_6.24/cristian-mattarei_CoSA/tutorial/fifo.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/examples/fifo_async -incdir /home/rk6650/VeriTriples/malik2627research/tests/parametric -incdir /home/rk6650/VeriTriples/malik2627research/tests/synchronize-clocks -incdir /home/rk6650/VeriTriples/malik2627research/tutorial /home/rk6650/VeriTriples/malik2627research/repos_6.24/cristian-mattarei_CoSA/tutorial/robot.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/examples/fifo_async -incdir /home/rk6650/VeriTriples/malik2627research/tests/parametric -incdir /home/rk6650/VeriTriples/malik2627research/tests/synchronize-clocks -incdir /home/rk6650/VeriTriples/malik2627research/tutorial /home/rk6650/VeriTriples/malik2627research/repos_6.24/cristian-mattarei_CoSA/tutorial/fifo.sv }


            if {[catch {elaborate -top oh_rsync} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/cristian-mattarei_CoSA/proj_1/results.rpt
report_vacuity -out jasper_runs_6.24/cristian-mattarei_CoSA/proj_1/vacuity.rpt
exit
