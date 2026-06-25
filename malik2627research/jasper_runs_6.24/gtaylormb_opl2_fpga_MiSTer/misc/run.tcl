clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/gtaylormb_opl2_fpga_MiSTer/src/opl2_pkg.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/gtaylormb_opl2_fpga_MiSTer/src/afifo.v }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/gtaylormb_opl2_fpga_MiSTer/src/opl2_exp_lut.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/gtaylormb_opl2_fpga_MiSTer/src/mem_single_bank.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/gtaylormb_opl2_fpga_MiSTer/src/mem_single_bank_reset.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/gtaylormb_opl2_fpga_MiSTer/src/pipeline_sr.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/gtaylormb_opl2_fpga_MiSTer/src/reset_sync.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/gtaylormb_opl2_fpga_MiSTer/src/opl2_log_sine_lut.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/gtaylormb_opl2_fpga_MiSTer/src/edge_detector.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/gtaylormb_opl2_fpga_MiSTer/src/clk_div.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/gtaylormb_opl2_fpga_MiSTer/src/synchronizer.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src /home/rk6650/VeriTriples/malik2627research/repos_6.24/gtaylormb_opl2_fpga_MiSTer/src/control_operators.sv }


            if {[catch {elaborate -top pipeline_sr} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/gtaylormb_opl2_fpga_MiSTer/misc/results.rpt
report_vacuity -out jasper_runs_6.24/gtaylormb_opl2_fpga_MiSTer/misc/vacuity.rpt
exit
