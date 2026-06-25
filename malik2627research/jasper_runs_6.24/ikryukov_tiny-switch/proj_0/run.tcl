clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/ikryukov_tiny-switch/src/cmd_decoder.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/ikryukov_tiny-switch/src/response_collector.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/ikryukov_tiny-switch/src/bf16_adder.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/ikryukov_tiny-switch/src/multicast_engine.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/ikryukov_tiny-switch/src/tswitch.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/ikryukov_tiny-switch/src/reduction_engine.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/ikryukov_tiny-switch/src/parallel_issuer.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/ikryukov_tiny-switch/src/read_requester.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/ikryukov_tiny-switch/src/group_table.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/ikryukov_tiny-switch/src/cmd_decoder.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/ikryukov_tiny-switch/src/multicast_engine.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/ikryukov_tiny-switch/src/parallel_issuer.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/ikryukov_tiny-switch/src/read_requester.sv }


            if {[catch {elaborate -top reduction_engine} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/ikryukov_tiny-switch/proj_0/results.rpt
report_vacuity -out jasper_runs_6.24/ikryukov_tiny-switch/proj_0/vacuity.rpt
exit
