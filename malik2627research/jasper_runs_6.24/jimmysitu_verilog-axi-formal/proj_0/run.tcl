clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_axil_master.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_priority_encoder.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_axil_slave.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_axil_register_rd.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_arbiter.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_axil_register.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_axil_ram.v }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_axil_master.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_priority_encoder.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_axil_slave.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_axil_register_rd.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_arbiter.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_axil_register.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/formal /home/rk6650/VeriTriples/malik2627research/repos_6.24/jimmysitu_verilog-axi-formal/formal/f_axil_ram.v }


            if {[catch {elaborate -top f_axil_register_rd} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/jimmysitu_verilog-axi-formal/proj_0/results.rpt
report_vacuity -out jasper_runs_6.24/jimmysitu_verilog-axi-formal/proj_0/vacuity.rpt
exit
